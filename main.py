import os
import uuid
import base64
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

# Optional local email util
try:
    from utils.emailer import send_email_with_attachments
except Exception:
    def send_email_with_attachments(*args, **kwargs):
        print("[warn] utils.emailer not available; skipping email send.")

# ---------- Config ----------
ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
PUBLIC_URL = os.getenv("PUBLIC_URL", "")
SEND_EMAIL = os.getenv("SEND_EMAIL", "0") == "1"                     # email DUPĂ plată (webhook)
SEND_EMAIL_ON_SUBMIT = os.getenv("SEND_EMAIL_ON_SUBMIT", "1") == "1" # email IMEDIAT, înainte de plată

# Stripe
import stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

PRICE_MAP = {
    # eori_ro  -> PF (75 RON)
    "eori_ro": os.getenv("STRIPE_PRICE_EORI_RO", ""),

    # eori_update -> PJ (99 RON)
    "eori_update": os.getenv("STRIPE_PRICE_EORI_UPDATE", ""),
}

# ---------- App ----------
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

# Limita totală de upload (request body) și erori JSON-friendly
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20 MB total (ajustează după nevoie)

@ app.errorhandler(413)
def too_large(_e):
    return jsonify({"error": "Fișierele sunt prea mari. Max ~20MB per solicitare."}), 413

@ app.errorhandler(500)
def internal_err(_e):
    return jsonify({"error": "Eroare de server. Reîncearcă."}), 500

# Ensure dirs
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@ app.get("/")
def index():
    # (ai UI cu 2 opțiuni – lăsăm options aici dacă le folosești în template)
    options = [
        ("eori_ro", "EORI România (PF)"),
        ("eori_update", "EORI România (PJ)"),
    ]
    return render_template("index.html", options=options)

@ app.post("/create-checkout")
def create_checkout():
    # Collect form fields
    form = request.form
    service_key = form.get("service_key", "eori_ro")
    full_name   = form.get("full_name", "").strip()
    company     = form.get("company", "").strip()
    email       = form.get("email", "").strip()
    phone       = form.get("phone", "").strip()
    cnp_cui     = form.get("cnp_cui", "").strip()
    notes       = form.get("notes", "").strip()

    if service_key not in PRICE_MAP or not PRICE_MAP[service_key]:
        return jsonify({"error": "Serviciu indisponibil"}), 400

    # Save uploads
    saved_files = []
    for field in ("id_front", "id_back", "extra_doc"):
        file = request.files.get(field)
        if file and file.filename and allowed_file(file.filename):
            fname = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            fpath = UPLOAD_DIR / fname
            file.save(fpath)
            saved_files.append(fpath)

    # === Semnătură (base64 PNG din canvas) ===
    signature_data = form.get("signature_data", "")
    if signature_data and signature_data.startswith("data:image/png;base64,"):
        try:
            b64 = signature_data.split(",", 1)[1]
            raw = base64.b64decode(b64)
            sig_name = f"{uuid.uuid4().hex}_signature.png"
            sig_path = UPLOAD_DIR / sig_name
            with open(sig_path, "wb") as f:
                f.write(raw)
            saved_files.append(sig_path)
        except Exception as e:
            print("[warn] failed to save signature:", e)

    # Persist a CSV/TSV log local (backup)
    try:
        logline = (
            f"{datetime.utcnow().isoformat()}\t{service_key}\t{full_name}\t{email}\t"
            f"{phone}\t{cnp_cui}\t{notes}\t{company}\t"
            f"{';'.join(p.name for p in saved_files)}\n"
        )
        (DATA_DIR / "orders.tsv").open("a", encoding="utf-8").write(logline)
    except Exception as e:
        print("[warn] Failed to write log:", e)

        # === TRIMITE EMAIL ACUM (înainte de plată) ===
    if SEND_EMAIL_ON_SUBMIT:
        try:
            subj = f"[EORIMAG] Solicitare nouă (NEPLĂTITĂ încă) — {full_name or '-'}"
            body = (
                "Solicitare nouă primită de pe site (NEPLĂTITĂ ÎNCĂ)\n\n"
                f"Serviciu: {service_key}\n"
                f"Nume: {full_name}\n"
                f"Companie: {company}\n"
                f"Email: {email}\n"
                f"Telefon: {phone}\n"
                f"CNP/CUI: {cnp_cui}\n"
                f"Notițe: {notes}\n"
                f"Fișiere: {', '.join(p.name for p in saved_files) or '-'}\n"
            )
            send_email_with_attachments(
                subject=subj,
                text=body,
                attachments=saved_files,
                reply_to=email or None,
            )
            print("[info] Pre-payment email sent.")
        except Exception as e:
            print("[warn] Pre-payment email failed:", e)

    # Create Stripe Checkout  ⬇️  (TOT ce urmează rămâne INDENTAT în funcție)
    base_url    = (PUBLIC_URL or request.host_url).rstrip("/")
    success_url = f"{base_url}/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url  = f"{base_url}/cancel"

    metadata = {
        "service_key": service_key,
        "full_name": full_name,
        "company": company,
        "email": email,
        "phone": phone,
        "cnp_cui": cnp_cui,
        "notes": notes,
        "uploads": ",".join(p.name for p in saved_files),
    }

    try:
        checkout = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": PRICE_MAP[service_key], "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
            payment_intent_data={
                "description": f"EORIMAG – {full_name} ({service_key})",
                "statement_descriptor_suffix": "EORIMAG",
            },
            custom_text={"submit": {"message": "Plata va fi procesată de EORIMAG"}},
        )
        print(f"[checkout] service_key = {service_key} | price = {PRICE_MAP[service_key]}")
        return jsonify({"checkout_url": checkout.url})
    except Exception as e:
        print("[err] Stripe create session:", e)
        return jsonify({"error": "Eroare la crearea plății"}), 500



@ app.get("/success")
def success():
    return render_template("success.html")

@ app.get("/cancel")
def cancel():
    return render_template("cancel.html")

@ app.post("/webhook")
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        print("[err] webhook verify:", e)
        return "", 400

    print("[webhook] event type =", event.get("type"))

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        meta = session.get("metadata", {}) or {}
        print("[webhook] checkout.session.completed meta:", meta)

        if SEND_EMAIL:
            try:
                subject = f"[EORIMAG] Comandă PLĂTITĂ — {meta.get('full_name','-')}"
                body = (
                    f"Plată confirmată prin Stripe Checkout.\n\n"
                    f"Serviciu: {meta.get('service_key','')}\n"
                    f"Nume: {meta.get('full_name','')}\n"
                    f"Companie: {meta.get('company','')}\n"
                    f"Email: {meta.get('email','')}\n"
                    f"Telefon: {meta.get('phone','')}\n"
                    f"CNP/CUI: {meta.get('cnp_cui','')}\n"
                    f"Notițe: {meta.get('notes','')}\n"
                )

                attachments = []
                uploads = (meta.get("uploads") or "").split(",") if meta.get("uploads") else []
                for name in uploads:
                    p = UPLOAD_DIR / name
                    if p.exists():
                        attachments.append(p)

                send_email_with_attachments(
                    subject=subject,
                    text=body,
                    attachments=attachments,
                    reply_to=meta.get("email", None),
                )
                print("[info] Post-payment email sent.")
            except Exception as e:
                print("[warn] email send failed:", e)

    return "", 200

@ app.get("/healthz")
def healthz():
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
