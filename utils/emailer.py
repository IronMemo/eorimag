import os
import base64
import requests
from pathlib import Path
from typing import Iterable, Union

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_URL = "https://api.resend.com/emails"

MAIL_FROM = os.getenv("MAIL_FROM", "noreply@eorimag.ro")  # expeditor verificat în Resend
MAIL_TO   = os.getenv("MAIL_TO", "")                      # adresa ta de primire (una sau mai multe, separate prin virgulă)
MAIL_CC   = os.getenv("MAIL_CC", "")                      # opțional

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
                # dacă a venit greșit ca string, încearcă să-l tratezi ca bytes utf-8
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
        raise RuntimeError("Lipsește RESEND_API_KEY în env.")
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }
    r = requests.post(RESEND_URL, json=payload, headers=headers, timeout=30)
    if r.status_code not in (200, 201):
        print("[err] Resend email failed:", r.status_code, r.text)
        return False
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
        raise RuntimeError("Destinatarul lipsește (to).")

    atts = []
    for a in (attachments or []):
        att = _to_attachment(a)
        if att:
            atts.append(att)

    payload = {
        "from": from_email or MAIL_FROM,
        "to": to_list,
        "subject": subject,
        "text": text,
    }
    if reply_to:
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
        raise RuntimeError("Setează MAIL_TO în env.")
    return send_email_to(
        to=MAIL_TO,
        subject=subject,
        text=text,
        attachments=attachments,
        from_email=MAIL_FROM,
        reply_to=reply_to,
        cc=MAIL_CC or None,
    )
