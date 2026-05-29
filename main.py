
from flask import Flask, request, Response, abort, render_template_string
import os

app = Flask(__name__)

# ─── USUARIOS Y CONTRASEÑAS ───────────────────────────────────────────────────
USUARIOS = {
    "mama":    "clave123",
    "papa":    "clave456",
    "hermano": "clave789",
    "yo":      "miclaveadmin",
    "lianny":  "lianny01",
    "mayuli":  "mayuli123",
}
# ─────────────────────────────────────────────────────────────────────────────

LISTA_PATH = os.path.join(os.path.dirname(__file__), "lista.m3u")

PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TV Favorito</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #0f0f1a; color: #e0e0f0; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
    .card { background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 16px; padding: 40px; max-width: 440px; width: 100%; }
    h1 { font-size: 22px; margin-bottom: 4px; color: #fff; }
    .sub { color: #888; font-size: 14px; margin-bottom: 28px; }
    label { display: block; font-size: 13px; color: #aaa; margin-bottom: 6px; }
    input { width: 100%; padding: 10px 14px; background: #0f0f1a; border: 1px solid #2a2a4a; border-radius: 8px; color: #e0e0f0; font-size: 15px; margin-bottom: 16px; outline: none; }
    input:focus { border-color: #5b5bff; }
    button { width: 100%; padding: 12px; background: #5b5bff; color: #fff; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; }
    button:hover { background: #4a4ae0; }
    .url-box { background: #0f0f1a; border: 1px solid #2a2a4a; border-radius: 10px; padding: 16px; margin-top: 24px; display: none; }
    .url-box.show { display: block; }
    .url-label { font-size: 12px; color: #888; margin-bottom: 8px; }
    .url-text { font-size: 13px; color: #a0a0ff; word-break: break-all; margin-bottom: 12px; }
    .copy-btn { width: 100%; padding: 9px; background: #2a2a4a; color: #c0c0ff; border: none; border-radius: 7px; font-size: 13px; cursor: pointer; }
    .copy-btn:hover { background: #3a3a6a; }
    .error { color: #ff6b6b; font-size: 13px; margin-top: -8px; margin-bottom: 12px; display: none; }
    .apps { margin-top: 28px; border-top: 1px solid #2a2a4a; padding-top: 20px; }
    .apps-title { font-size: 12px; color: #666; margin-bottom: 10px; }
    .app-chips { display: flex; flex-wrap: wrap; gap: 6px; }
    .chip { background: #2a2a4a; border-radius: 20px; padding: 4px 12px; font-size: 12px; color: #a0a0c0; }
  </style>
</head>
<body>
<div class="card">
  <h1>📺 TV Favorito</h1>
  <p class="sub">Ingresa tus datos para obtener tu enlace</p>
  <label>Usuario</label>
  <input type="text" id="user" placeholder="tu usuario" autocomplete="username">
  <label>Contraseña</label>
  <input type="password" id="pass" placeholder="tu contraseña" autocomplete="current-password">
  <p class="error" id="err">Usuario o contraseña incorrectos</p>
  <button onclick="generar()">Obtener enlace</button>
  <div class="url-box" id="urlbox">
    <p class="url-label">Tu enlace personalizado (cópialo en tu app IPTV):</p>
    <p class="url-text" id="urltext"></p>
    <button class="copy-btn" onclick="copiar()">📋 Copiar enlace</button>
  </div>
  <div class="apps">
    <p class="apps-title">Compatible con estas apps:</p>
    <div class="app-chips">
      <span class="chip">Tivimate</span>
      <span class="chip">IPTV Smarters Pro</span>
      <span class="chip">GSE Smart IPTV</span>
      <span class="chip">Perfect Player</span>
      <span class="chip">VLC</span>
      <span class="chip">Kodi</span>
    </div>
  </div>
</div>
<script>
const BASE = window.location.origin;
async function generar() {
  const user = document.getElementById('user').value.trim();
  const pass = document.getElementById('pass').value.trim();
  document.getElementById('err').style.display = 'none';
  document.getElementById('urlbox').classList.remove('show');
  if (!user || !pass) return;
  const res = await fetch(`/verificar?user=${encodeURIComponent(user)}&pass=${encodeURIComponent(pass)}`);
  if (res.ok) {
    const url = `${BASE}/get/${encodeURIComponent(user)}/${encodeURIComponent(pass)}/lista.m3u`;
    document.getElementById('urltext').textContent = url;
    document.getElementById('urlbox').classList.add('show');
  } else {
    document.getElementById('err').style.display = 'block';
  }
}
function copiar() {
  const url = document.getElementById('urltext').textContent;
  navigator.clipboard.writeText(url).then(() => {
    const btn = document.querySelector('.copy-btn');
    btn.textContent = '✅ Copiado';
    setTimeout(() => btn.textContent = '📋 Copiar enlace', 2000);
  });
}
document.addEventListener('keydown', e => { if (e.key === 'Enter') generar(); });
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(PAGE)

@app.route("/verificar")
def verificar():
    user = request.args.get("user", "")
    pwd  = request.args.get("pass", "")
    if USUARIOS.get(user) == pwd:
        return "", 200
    abort(401)

@app.route("/get/<user>/<pwd>/lista.m3u")
def lista(user, pwd):
    if USUARIOS.get(user) != pwd:
        abort(401)
    try:
        with open(LISTA_PATH, "r", encoding="utf-8") as f:
            contenido = f.read()
        headers = {
            "Content-Disposition": "attachment; filename=lista.m3u",
            "Content-Type": "application/vnd.apple.mpegurl"
        }
        return Response(contenido, status=200, headers=headers)
    except FileNotFoundError:
        abort(404)

# Mantener la URL vieja también por compatibilidad
@app.route("/lista")
def lista_old():
    user = request.args.get("user", "")
    pwd  = request.args.get("pass", "")
    if USUARIOS.get(user) != pwd:
        abort(401)
    try:
        with open(LISTA_PATH, "r", encoding="utf-8") as f:
            contenido = f.read()
        headers = {
            "Content-Disposition": "attachment; filename=lista.m3u",
            "Content-Type": "application/vnd.apple.mpegurl"
        }
        return Response(contenido, status=200, headers=headers)
    except FileNotFoundError:
        abort(404)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
