import os
import re
import base64
import requests
from pathlib import Path
from typing import Iterable, Union

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_URL = "https://api.resend.com/emails"

# Dacă n-ai domeniul verificat în Resend, folosește onboarding@resend.dev
MAIL_FROM = os.getenv("MAIL_FROM", "").strip() or "onboarding@resend.dev"
MAIL_TO   = os.getenv("MAIL_TO", "").strip()
MAIL_CC   = os.getenv("MAIL_CC", "").strip()

_FROM_NAME_DEFAULT = "EORIMAG"
_EMAIL_RE = re.compile(r"^[^@<>\s]+@[^@<>\s]+\.[^@<>\s]+$")

def _normalize_from(addr: str, display_name: str = _FROM_NAME_DEFAULT) -> str:
    """
    Returnează un 'from' valid pt. Resend:
      - 'Name <email@domain>'
      - sau fallback 'EORIMAG <onboarding@resend.dev>'
    """
    addr = (addr or "").strip()
    if "<" in addr and ">" in addr:
        return addr  # deja în format "Name <email>"
    if _EMAIL_RE.match(addr):
        return f"{display_name} <{addr}>"
    # fallback sigur
    return f"{display_name} <onboarding@resend.dev>"

def _to_attachment(item: Union[str, Path, tuple]) -> dict | None:
    """
    Acceptă:
      - cale către fișier (str/Path) -> citește bytes
      - (filename, bytes)            -> folosește direct
    Returnează dict {filename, content(base64)} sau None dacă nu poate procesa.
    """
    try:
        if isinstance(item, (str, Path)):
            p = Path(item)
            data = p.read_bytes()
            name = p.name
        elif isinstance(item, tuple) and len(item) == 2:
            name, data = item
            if isinstance(data, str):
                data = data.encode("utf-8")
        else:
            return None

        return {
            "filename": str(name),
            "content": base64.b64encode(data).decode("utf-8"),
        }
    except Exception as e:
        print(f"[warn] atașament ignorat ({item}): {e}")
        return None

def _split_emails(csv: str) -> list[str]:
    return [x.strip() for x in (csv or "").split(",") if x.strip()]

def _post_resend(payload: dict) -> bool:
    if not RESEND_API_KEY:
        print("[err] RESEND_API_KEY lipsește din environment.")
        return False

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(RESEND_URL, json=payload, headers=headers, timeout=30)
    except Exception as e:
        print("[err] Resend request failed:", e)
        return False

    if r.status_code not in (200, 201):
        print("[err] Resend email failed:", r.status_code, r.text)
        return False

    # opțional: poți loga id-ul mesajului
    try:
        rid = r.json().get("id")
        if rid:
            print("[info] Resend accepted, id:", rid)
    except Exception:
        pass
    return True

def send_email_to(
    to: Union[str, list[str]],
    subject: str,
    text: str,
    attachments: Iterable[Union[str, Path, tuple]] = (),
    from_email: str | None = None,
    reply_to: str | None = None,
    cc: Union[str, list[str]] | None = None,
) -> bool:
    """
    Trimite email prin Resend către 'to' explicit.
    Attachments poate fi listă de căi sau listă de (filename, bytes).
    """
    to_list = _split_emails(to if isinstance(to, str) else ",".join(to))
    if not to_list:
        print("[err] Destinatarul lipsește (to). Setează MAIL_TO sau transmite parametrul 'to'.")
        return False

    atts = []
    for a in (attachments or []):
        att = _to_attachment(a)
        if att:
            atts.append(att)

    from_addr = _normalize_from(from_email or MAIL_FROM)

    payload = {
        "from": from_addr,
        "to": to_list,
        "subject": subject or "(fără subiect)",
        "text": text or "",
    }

    if reply_to:
        # Resend acceptă string sau listă
        payload["reply_to"] = reply_to

    cc_list = _split_emails(cc if isinstance(cc, str) else (",".join(cc) if cc else ""))
    if cc_list:
        payload["cc"] = cc_list

    if atts:
        payload["attachments"] = atts

    return _post_resend(payload)

def send_email_with_attachments(
    subject: str,
    text: str,
    attachments: Iterable[Union[str, Path, tuple]] = (),
    reply_to: str | None = None,
) -> bool:
    """
    Variantă compatibilă cu apel simplu din main.py:
      send_email_with_attachments(subject, text, attachments, reply_to=email_client)
    Folosește MAIL_TO / MAIL_FROM / MAIL_CC din env.
    """
    if not MAIL_TO:
        print("[err] MAIL_TO lipsește din environment.")
        return False

    return send_email_to(
        to=MAIL_TO,
        subject=subject,
        text=text,
        attachments=attachments,
        from_email=MAIL_FROM,   # va fi normalizat în _normalize_from()
        reply_to=reply_to,
        cc=MAIL_CC or None,
    )
