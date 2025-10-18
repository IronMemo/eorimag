import os
import base64
import requests


RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_URL = "https://api.resend.com/emails"


def send_email_with_attachments(to: str, subject: str, text: str, attachments, from_email: str | None = None) -> bool:
if not RESEND_API_KEY:
raise RuntimeError("Lipsește RESEND_API_KEY în env.")
if not to:
raise RuntimeError("Setează MAIL_TO în env.")
from_email = from_email or "no-reply@eorieu.app"


files_payload = []
for filename, data in attachments:
files_payload.append({
"filename": filename,
"content": base64.b64encode(data).decode("utf-8")
})


payload = {
"from": from_email,
"to": [to],
"subject": subject,
"text": text,
"attachments": files_payload if files_payload else None,
}


headers = {
"Authorization": f"Bearer {RESEND_API_KEY}",
"Content-Type": "application/json"
}
r = requests.post(RESEND_URL, json=payload, headers=headers, timeout=30)
return r.status_code in (200, 201)
