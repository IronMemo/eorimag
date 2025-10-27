from flask import Flask, render_template, request, jsonify
import os
import base64
import uuid

app = Flask(__name__)

# unde vrem să salvăm upload-urile (temporar)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET"])
def home():
    """
    Route principală.
    Afișează formularul (index.html din folderul templates).
    """
    return render_template("index.html")


@app.route("/create-checkout", methods=["POST"])
def create_checkout():
    """
    Aceasta este ruta pe care o apelează formularul tău cu fetch('/create-checkout').
    Primește:
      - service_key
      - full_name
      - company (opțional)
      - email
      - phone
      - cnp_cui
      - signature_data (base64 din canvas)
      - id_front (fișier)
      - id_back  (fișier, opțional)
      - accept_terms (checkbox)

    Aici poți:
      1. valida datele
      2. salva documentele / semnătura pe disk sau în DB
      3. crea sesiunea Stripe Checkout
      4. returna checkout_url către frontend
    """

    # 1. preluăm datele text
    service_key   = request.form.get("service_key", "").strip()
    full_name     = request.form.get("full_name", "").strip()
    company       = request.form.get("company", "").strip()
    email         = request.form.get("email", "").strip()
    phone         = request.form.get("phone", "").strip()
    cnp_cui       = request.form.get("cnp_cui", "").strip()
    signature_b64 = request.form.get("signature_data", "").strip()
    accept_terms  = request.form.get("accept_terms")

    # validări minimale ca să nu facem Checkout cu date goale
    missing_fields = []
    if not service_key:
        missing_fields.append("service_key")
    if not full_name:
        missing_fields.append("full_name")
    if not email:
        missing_fields.append("email")
    if not phone:
        missing_fields.append("phone")
    if not cnp_cui:
        missing_fields.append("cnp_cui")
    if not signature_b64:
        missing_fields.append("signature_data")
    if not accept_terms:
        # checkbox-ul e obligatoriu
        missing_fields.append("accept_terms")

    # fișiere încărcate
    id_front = request.files.get("id_front")
    id_back  = request.files.get("id_back")

    if id_front is None or id_front.filename == "":
        missing_fields.append("id_front")

    if missing_fields:
        return jsonify({
            "error": f"Lipsesc câmpuri obligatorii: {', '.join(missing_fields)}"
        }), 400

    # 2. salvăm fișierele încărcate local (opțional, doar ca exemplu)
    # poți înlocui cu upload în S3 etc.
    saved_files = {}
    if id_front and id_front.filename:
        front_name = f"{uuid.uuid4().hex}_front_{id_front.filename}"
        front_path = os.path.join(UPLOAD_FOLDER, front_name)
        id_front.save(front_path)
        saved_files["id_front"] = front_path

    if id_back and id_back.filename:
        back_name = f"{uuid.uuid4().hex}_back_{id_back.filename}"
        back_path = os.path.join(UPLOAD_FOLDER, back_name)
        id_back.save(back_path)
        saved_files["id_back"] = back_path

    # 3. salvăm semnătura (signature_data e base64 data URL gen "data:image/png;base64,AAA...")
    signature_path = None
    if signature_b64.startswith("data:image"):
        try:
            header, b64data = signature_b64.split(",", 1)
        except ValueError:
            b64data = ""
        if b64data:
            sig_bytes = base64.b64decode(b64data)
            signature_name = f"{uuid.uuid4().hex}_signature.png"
            signature_path = os.path.join(UPLOAD_FOLDER, signature_name)
            with open(signature_path, "wb") as f:
                f.write(sig_bytes)

    # === 4. aici vii tu cu Stripe Checkout real ===
    #
    # De ex. (schematic, NU este cod complet Stripe oficial):
    #
    # import stripe
    # stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    #
    # if service_key == "eori_ro":
    #     price_amount = 75  # RON
    # elif service_key == "eori_update":
    #     price_amount = 99
    # else:
    #     price_amount = 0
    #
    # checkout_session = stripe.checkout.Session.create(
    #     payment_method_types=["card"],
    #     line_items=[{
    #         "price_data": {
    #             "currency": "ron",
    #             "product_data": {
    #                 "name": f"Serviciu {service_key} - {full_name}",
    #             },
    #             "unit_amount": price_amount * 100,  # bani
    #         },
    #         "quantity": 1,
    #     }],
    #     mode="payment",
    #     success_url="https://eorimag.onrender.com/success",
    #     cancel_url="https://eorimag.onrender.com/cancel",
    #     metadata={
    #         "full_name": full_name,
    #         "company": company,
    #         "email": email,
    #         "phone": phone,
    #         "cnp_cui": cnp_cui,
    #         "service_key": service_key,
    #         "signature_path": signature_path or "",
    #         "id_front_path": saved_files.get("id_front",""),
    #         "id_back_path": saved_files.get("id_back",""),
    #     }
    # )
    #
    # checkout_url = checkout_session.url

    # deocamdată returnăm ceva dummy, ca să nu crape UI-ul
    checkout_url = "https://checkout.stripe.com/test-session"

    # răspunsul pe care frontend-ul îl așteaptă
    return jsonify({
        "checkout_url": checkout_url
    }), 200


@app.route("/success", methods=["GET"])
def success_page():
    """
    Pagina după plată reușită (Stripe success_url).
    Poți face render la un template frumos aici.
    """
    return "Plata a fost procesată cu succes. Vei primi confirmarea codului EORI pe email.", 200


@app.route("/cancel", methods=["GET"])
def cancel_page():
    """
    Pagina dacă utilizatorul abandonează plata (Stripe cancel_url).
    """
    return "Plata a fost anulată. Poți reîncerca oricând.", 200


if __name__ == "__main__":
    # Local dev
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
