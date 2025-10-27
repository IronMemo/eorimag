<!doctype html>
<html lang="ro">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>EORIMAG – Simplu, 100% online</title>
  <link rel="icon" type="image/png" href="{{ url_for('static', filename='logo-eorimag.png') }}">
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
  <style>
    /* ====== Meniu sus ====== */
    header.navbar {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      background: #fff;
      border-bottom: 1px solid #ddd;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 20px;
      z-index: 1000;
    }
    .navbar .logo {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: bold;
      color: #111;
      text-decoration: none;
      font-size: 1.1rem;
    }
    .navbar .logo img {
      height: 32px;
      width: auto;
    }
    nav.menu {
      display: flex;
      gap: 20px;
      flex-wrap: wrap;
    }
    nav.menu a {
      text-decoration: none;
      color: #333;
      font-size: 0.95rem;
      font-weight: 500;
      transition: color 0.2s;
    }
    nav.menu a:hover {
      color: #007bff;
    }
    /* Ajustăm layoutul să țină cont de bara fixă */
    body {
      margin: 0;
      padding-top: 70px;
      font-family: system-ui, sans-serif;
    }
  </style>
</head>
<body>

  <!-- ====== Meniu de navigare sus ====== -->
  <header class="navbar">
    <a href="/" class="logo">
      <img src="{{ url_for('static', filename='logo-eorimag.png') }}" alt="EORIMAG">
      EORIMAG
    </a>
    <nav class="menu">
      <a href="#ce-este">Ce este codul EORI?</a>
      <a href="#procedura">Procedura EORI</a>
      <a href="#documente">Documente necesare</a>
      <a href="#faq">Întrebări frecvente</a>
      <a href="#contact">Contact</a>
    </nav>
  </header>

  <div class="layout-two-col">
    <!-- Coloana stângă (informativă) -->
    <aside class="left-info">
      <img src="{{ url_for('static', filename='logo-eorimag.png') }}" alt="EORIMAG" class="logo-img" />
      <h1>Simplu <br>100% online</h1>
      <p class="tagline">
        Completezi formularul, atașezi actele și semnezi — noi depunem solicitarea la autoritatea vamală. Primești confirmarea pe email.
      </p>
      <ul>
        <li>Termen eliberare 1–3 zile</li>
        <li>Semnătură digitală în pagină</li>
        <li>Plată securizată prin Stripe</li>
        <li>Suport prin email</li>
        <li>Procesarea este realizată de autoritatea vamală, timpii pot varia</li>
      </ul>
    </aside>

    <!-- Coloana dreaptă (formular) -->
    <main class="right-form">
      <form id="orderForm" enctype="multipart/form-data" novalidate>
        <!-- Servicii -->
        <div class="service-grid" id="serviceGrid" role="radiogroup" aria-label="Alege serviciul">
          <input type="hidden" name="service_key" id="service_key" value="eori_ro">

          <button type="button" class="service-card selected" data-key="eori_ro" aria-pressed="true">
            <span class="title">Obținere cod EORI: Persoană Fizică</span>
            <span class="price">75 RON</span>
          </button>

          <button type="button" class="service-card" data-key="eori_update" aria-pressed="false">
            <span class="title">Obținere cod EORI: Persoană Juridică</span>
            <span class="price">99 RON</span>
          </button>
        </div>

        <!-- Date solicitant -->
        <div class="grid form-grid">
          <label>Nume și prenume*
            <input name="full_name" placeholder="Ex. Popescu Andrei" required>
          </label>
          <label>Companie (opțional)
            <input name="company" placeholder="Ex. SC Exemplu SRL">
          </label>
          <label>Email*
            <input type="email" name="email" placeholder="adresa@exemplu.ro" required>
          </label>
          <label>Telefon*
            <input type="tel" name="phone" placeholder="07xx xxx xxx" required>
          </label>
        </div>

        <label>CNP/CUI*
          <input name="cnp_cui" required>
        </label>

        <!-- Semnătură -->
        <div class="signature-block">
          <div class="sig-header">
            <strong>Semnătură *</strong>
            <span class="muted">Semnează cu mouse-ul sau degetul (pe telefon)</span>
          </div>
          <div class="sig-wrap">
            <canvas id="sigpad"></canvas>
          </div>
          <div class="sig-actions">
            <button type="button" id="sigClear" class="secondary">Șterge semnătura</button>
            <button type="button" id="sigUndo" class="secondary">Undo</button>
          </div>
          <input type="hidden" name="signature_data" id="signature_data" required>
        </div>

        <!-- Upload documente -->
        <div class="uploads" style="margin-top:12px">
          <div>
            <span>Carte de identitate – față (JPG/PNG/PDF) *</span>
            <input type="file" name="id_front" accept=".pdf,.jpg,.jpeg,.png" required>
          </div>
          <div>
            <span>Carte de identitate – verso (opțional)</span>
            <input type="file" name="id_back" accept=".pdf,.jpg,.jpeg,.png">
          </div>
        </div>

        <!-- Total + Termeni + Submit -->
        <div style="display:flex; flex-direction:column; gap:12px; margin-top:12px;">
          <div style="display:flex; flex-wrap:wrap; gap:10px; align-items:center;">
            <div id="totalBox" class="secondary" style="padding:10px 12px; border-radius:8px; border:1px solid #ddd;">
              <strong>Total estimat:</strong> <span id="totalVal">—</span>
            </div>
          </div>

          <div class="terms-box" style="font-size:0.9rem; line-height:1.4; color:#333; display:flex; align-items:flex-start; gap:8px;">
            <input
              type="checkbox"
              id="accept_terms"
              name="accept_terms"
              required
              style="margin-top:3px; accent-color:#007bff; flex-shrink:0;"
            >
            <label for="accept_terms" style="cursor:pointer;">
              Confirm că am citit și sunt de acord cu
              <a href="/termeni" target="_blank" style="color:#007bff; text-decoration:none;">Termenii și Condițiile</a>,
              și sunt de acord ca datele mele personale și documentele încărcate să fie folosite pentru depunerea solicitării mele de cod EORI la autoritatea vamală.
            </label>
          </div>

          <div>
            <button type="submit" id="payBtn">Trimite solicitarea</button>
          </div>
        </div>

        <p id="msg" class="muted"></p>
      </form>
    </main>
  </div>

  <!-- ====== Secțiuni pentru ancorele din meniu ====== -->
  <section id="ce-este" style="padding:40px 20px;">
    <h2>Ce este codul EORI?</h2>
    <p>Codul EORI este un identificator unic folosit în relațiile cu autoritățile vamale ale Uniunii Europene pentru persoane fizice și juridice implicate în activități de import, export sau alte operațiuni vamale.</p>
  </section>

  <section id="procedura" style="padding:40px 20px; background:#f9f9f9;">
    <h2>Procedura EORI</h2>
    <p>Completarea formularului online, atașarea documentelor și semnătura electronică sunt suficiente. Noi transmitem cererea la autoritatea vamală, iar confirmarea se primește prin email.</p>
  </section>

  <section id="documente" style="padding:40px 20px;">
    <h2>Documente necesare</h2>
    <ul>
      <li>Carte de identitate – față</li>
      <li>Carte de identitate – verso (opțional)</li>
      <li>Împuternicire (dacă se aplică, pentru persoane juridice)</li>
    </ul>
  </section>

  <section id="faq" style="padding:40px 20px; background:#f9f9f9;">
    <h2>Întrebări frecvente</h2>
    <p><strong>Cât durează obținerea codului EORI?</strong><br>De regulă, 1–3 zile lucrătoare.</p>
    <p><strong>Primesc codul pe email?</strong><br>Da, confirmarea vine pe email imediat ce este emis codul EORI.</p>
  </section>

  <section id="contact" style="padding:40px 20px;">
    <h2>Contact</h2>
    <p>Pentru suport sau întrebări, ne poți scrie la <a href="mailto:suport@eorimag.ro">suport@eorimag.ro</a>.</p>
  </section>

  <script>
    // Scriptul original (selectare serviciu, semnătură, submit)
    const serviceGrid  = document.getElementById('serviceGrid');
    const serviceKeyEl = document.getElementById('service_key');
    const totalVal     = document.getElementById('totalVal');

    const PRICE_LABELS = {
      eori_ro: '75 RON',
      eori_update: '99 RON',
      gb_eori: '149 RON',
      resend: '49 RON'
    };

    function updateTotalFromKey(key){
      totalVal.textContent = PRICE_LABELS[key] || '—';
      totalVal.style.opacity = '0.3';
      requestAnimationFrame(() => { totalVal.style.opacity = '1'; });
    }

    updateTotalFromKey(serviceKeyEl.value || 'eori_ro');

    serviceGrid.addEventListener('click', (e) => {
      const btn = e.target.closest('.service-card');
      if (!btn) return;

      document.querySelectorAll('.service-card').forEach(b => {
        b.classList.remove('selected');
        b.setAttribute('aria-pressed', 'false');
      });

      btn.classList.add('selected');
      btn.setAttribute('aria-pressed', 'true');

      const key = btn.dataset.key;
      serviceKeyEl.value = key;
      updateTotalFromKey(key);
    });

    const canvas = document.getElementById('sigpad');
    const ctx = canvas.getContext('2d');
    let drawing = false;
    let strokes = [];
    let currentStroke = [];

    function resizeSigCanvas(){
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      if (!canvas.style.width) canvas.style.width = '100%';
      if (!canvas.style.height) canvas.style.height = '200px';
      const cssWidth  = rect.width  || canvas.clientWidth  || 600;
      const cssHeight = rect.height || canvas.clientHeight || 200;
      canvas.width  = Math.max(1, Math.round(cssWidth * dpr));
      canvas.height = Math.max(1, Math.round(cssHeight * dpr));
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.scale(dpr, dpr);
      redraw();
    }

    function getPos(evt) {
      const rect = canvas.getBoundingClientRect();
      const t = evt.touches ? evt.touches[0] : evt;
      return { x: (t.clientX - rect.left), y: (t.clientY - rect.top) };
    }

    function redraw() {
      ctx.clearRect(0,0,canvas.width,canvas.height);
      ctx.lineWidth = 2 * (window.devicePixelRatio || 1);
      ctx.lineJoin = 'round';
      ctx.lineCap  = 'round';
      ctx.strokeStyle = '#111';
      strokes.forEach(st => {
        ctx.beginPath();
        st.forEach((p,i) => { if (i===0) ctx.moveTo(p.x,p.y); else ctx.lineTo(p.x,p.y); });
        ctx.stroke();
      });
    }

    function startDraw(evt) { drawing = true; currentStroke = []; currentStroke.push(getPos(evt)); evt.preventDefault(); }
    function moveDraw(evt) {
      if (!drawing) return;
      currentStroke.push(getPos(evt));
      redraw();
      ctx.beginPath();
      currentStroke.forEach((p,i)=>{ if(i===0) ctx.moveTo(p.x,p.y); else ctx.lineTo(p.x,p.y); });
      ctx.stroke();
      evt.preventDefault();
    }
    function endDraw(evt) {
      if (!drawing) return;
      drawing = false;
      if (currentStroke.length > 1) { strokes.push(currentStroke); redraw(); }
      evt && evt.preventDefault();
    }

    canvas.addEventListener('mousedown', startDraw);
    canvas.addEventListener('mousemove', moveDraw);
    window.addEventListener('mouseup', endDraw);
    canvas.addEventListener('touchstart', startDraw, {passive:false});
    canvas.addEventListener('touchmove', moveDraw, {passive:false});
    canvas.addEventListener('touchend', endDraw);
    document.getElementById('sigClear').addEventListener('click', () => { strokes = []; redraw(); });
    document.getElementById('sigUndo').addEventListener('click', () => { strokes.pop(); redraw(); });

    function canvasToDataURL() { return strokes.length ? canvas.toDataURL('image/png') : ''; }

    resizeSigCanvas();
    window.addEventListener('resize', resizeSigCanvas);

    const form = document.getElementById('orderForm');
    const msg = document.getElementById('msg');
    const sigHidden = document.getElementById('signature_data');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      msg.textContent = '';
      sigHidden.value = canvasToDataURL();
      const fd = new FormData(form);
      try {
        const resp = await fetch('/create-checkout', { method: 'POST', body: fd });
        const data = await resp.json();
        if (!resp.ok || !data.checkout_url) throw new Error(data.error || 'Eroare la inițierea plății.');
        window.location.href = data.checkout_url;
      } catch (err) {
        msg.textContent = err.message || 'A apărut o eroare. Reîncearcă.';
      }
    });
  </script>
</body>
</html>
