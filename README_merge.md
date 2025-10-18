# EORIEU (merged)
Bazat pe designul *eorieu*, cu funcționalități portate din *eori49*:

- Select 4 servicii (EORI RO, Actualizare, GB EORI, Retrimitere)
- Upload fișiere (față buletin + opțional verso + opțional document)
- Stripe Checkout (mapează `service_key` -> `price_id` via env)
- Webhook Stripe care trimite email cu atașamente (dacă `SEND_EMAIL=1`)
- Log TSV în `data/orders.tsv`

## Setup rapid
1. Creați `.env` pe baza lui `.env.example` și populați cheile dvs.
2. `pip install -r requirements.txt` (folosiți din eorieu)
3. Rulați: `python main.py` (sau Gunicorn în producție).
4. Configurați webhook-ul Stripe: `POST /webhook`

**Notă:** Păstrăm `static/style.css` și aranjamentul din *eorieu*, doar am extins formularul.
