from flask import Flask, request, Response, abort, render_template_string, jsonify
import os, json, re, secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

LISTA_PATH = os.path.join(os.path.dirname(__file__), "lista.m3u")
USUARIOS_PATH = os.path.join(os.path.dirname(__file__), "usuarios.json")

DEFAULT_USUARIOS = {
    "yo":      {"password": "miclaveadmin", "admin": True},
    "lianny":  {"password": "lianny01",     "admin": False},
    "mayuli":  {"password": "mayuli123",    "admin": False},
    "mama":    {"password": "clave123",     "admin": False},
    "papa":    {"password": "clave456",     "admin": False},
    "hermano": {"password": "clave789",     "admin": False},
}

def cargar_usuarios():
    if os.path.exists(USUARIOS_PATH):
        with open(USUARIOS_PATH, "r") as f:
            return json.load(f)
    return DEFAULT_USUARIOS

def guardar_usuarios(u):
    with open(USUARIOS_PATH, "w") as f:
        json.dump(u, f, indent=2)

def parse_m3u():
    canales = []
    try:
        with open(LISTA_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("#EXTINF"):
                m = re.search(r'group-title="([^"]*)"', line)
                group = m.group(1) if m else "Sin categoría"
                name = line.split(",", 1)[1] if "," in line else "Canal"
                url = lines[i+1].strip() if i+1 < len(lines) else ""
                if url.startswith("http"):
                    canales.append({"name": name, "group": group, "url": url})
                i += 2
            else:
                i += 1
    except:
        pass
    return canales

APP_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TV Favorito</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/hls.js/1.4.12/hls.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#141414;color:#e5e5e5;min-height:100vh}

/* LOGIN */
#login-screen{display:flex;align-items:center;justify-content:center;min-height:100vh;background:linear-gradient(135deg,#0f0f1a 0%,#1a0a2e 100%)}
.login-card{background:#1a1a2e;border:1px solid #2a2a4a;border-radius:16px;padding:48px 40px;width:100%;max-width:400px}
.login-logo{font-size:36px;text-align:center;margin-bottom:8px}
.login-title{text-align:center;font-size:24px;font-weight:700;color:#fff;margin-bottom:4px}
.login-sub{text-align:center;color:#888;font-size:14px;margin-bottom:32px}
.form-group{margin-bottom:18px}
.form-group label{display:block;font-size:13px;color:#aaa;margin-bottom:6px}
.form-group input{width:100%;padding:12px 16px;background:#0d0d1a;border:1px solid #2a2a4a;border-radius:8px;color:#e5e5e5;font-size:15px;outline:none;transition:.2s}
.form-group input:focus{border-color:#e50914}
.btn-login{width:100%;padding:13px;background:#e50914;color:#fff;border:none;border-radius:8px;font-size:16px;font-weight:700;cursor:pointer;margin-top:8px}
.btn-login:hover{background:#c4070f}
.login-error{color:#ff6b6b;font-size:13px;text-align:center;margin-top:12px;display:none}

/* APP */
#app-screen{display:none}
nav{background:#000;padding:0 24px;display:flex;align-items:center;justify-content:space-between;height:60px;position:sticky;top:0;z-index:100;border-bottom:1px solid #222}
.nav-logo{font-size:20px;font-weight:900;color:#e50914;letter-spacing:1px}
.nav-right{display:flex;align-items:center;gap:12px}
.nav-user{color:#aaa;font-size:14px}
.btn-logout{background:none;border:1px solid #444;color:#aaa;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:13px}
.btn-logout:hover{border-color:#e50914;color:#e50914}
.btn-admin{background:#e50914;border:none;color:#fff;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:13px;display:none}

.main{padding:24px}
.search-bar{position:relative;margin-bottom:28px}
.search-bar input{width:100%;padding:12px 16px 12px 44px;background:#1a1a1a;border:1px solid #333;border-radius:10px;color:#e5e5e5;font-size:15px;outline:none}
.search-bar input:focus{border-color:#e50914}
.search-icon{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:#666;font-size:18px}

.groups-tabs{display:flex;gap:8px;overflow-x:auto;padding-bottom:12px;margin-bottom:24px;scrollbar-width:none}
.groups-tabs::-webkit-scrollbar{display:none}
.tab{padding:8px 16px;border-radius:20px;border:1px solid #333;background:none;color:#aaa;cursor:pointer;white-space:nowrap;font-size:13px;transition:.2s}
.tab:hover{border-color:#e50914;color:#e50914}
.tab.active{background:#e50914;border-color:#e50914;color:#fff;font-weight:600}

.section-title{font-size:18px;font-weight:700;margin-bottom:14px;color:#fff}
.channels-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px;margin-bottom:32px}
.channel-card{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:10px;padding:14px;cursor:pointer;transition:.2s;position:relative}
.channel-card:hover{border-color:#e50914;background:#222;transform:translateY(-2px)}
.channel-card.playing{border-color:#e50914;background:#2a0a0a}
.channel-name{font-size:13px;font-weight:600;color:#e5e5e5;line-height:1.3}
.channel-group{font-size:11px;color:#666;margin-top:4px}
.play-icon{position:absolute;top:10px;right:10px;color:#e50914;font-size:16px;opacity:0}
.channel-card:hover .play-icon{opacity:1}
.channel-card.playing .play-icon{opacity:1}
.no-results{text-align:center;color:#666;padding:40px;font-size:16px}

/* PLAYER */
#player-bar{display:none;position:sticky;bottom:0;background:#000;border-top:2px solid #e50914;z-index:99;padding:12px 24px}
#player-bar.show{display:block}
.player-bar-inner{display:flex;align-items:center;gap:16px;max-width:1200px;margin:0 auto}
#player-bar video{width:240px;height:135px;background:#111;border-radius:8px;flex-shrink:0}
.player-info{flex:1}
.player-channel-name{font-size:16px;font-weight:700;color:#fff;margin-bottom:4px}
.player-status{font-size:12px;color:#888}
.player-status.error{color:#ff6b6b}
.player-status.loading{color:#f5c518}
.player-status.playing{color:#4ade80}
.player-controls{display:flex;gap:8px;flex-shrink:0}
.btn-fullscreen{background:#e50914;border:none;color:#fff;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.btn-close-player{background:none;border:1px solid #444;color:#aaa;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.btn-close-player:hover{border-color:#e50914;color:#e50914}

/* ADMIN */
#admin-modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.9);z-index:200;align-items:center;justify-content:center}
#admin-modal.show{display:flex}
.admin-card{background:#1a1a2e;border:1px solid #2a2a4a;border-radius:16px;padding:32px;width:100%;max-width:520px;max-height:90vh;overflow-y:auto}
.admin-title{font-size:20px;font-weight:700;margin-bottom:24px;color:#fff}
.user-item{display:flex;align-items:center;justify-content:space-between;padding:12px 14px;background:#0d0d1a;border-radius:8px;margin-bottom:8px;border:1px solid #2a2a4a}
.user-name{font-weight:600;color:#fff}
.user-pass{color:#888;font-size:12px;margin-top:2px}
.user-badge{font-size:10px;background:#e50914;color:#fff;padding:2px 7px;border-radius:10px;margin-left:8px}
.btn-del{background:none;border:1px solid #444;color:#888;padding:5px 12px;border-radius:5px;cursor:pointer;font-size:12px}
.btn-del:hover{border-color:#e50914;color:#e50914}
.add-user-form{border-top:1px solid #2a2a4a;padding-top:20px;margin-top:8px}
.add-user-form h3{font-size:15px;margin-bottom:14px;color:#aaa}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px}
.form-row input{padding:10px 12px;background:#0d0d1a;border:1px solid #2a2a4a;border-radius:7px;color:#e5e5e5;font-size:14px;outline:none}
.form-row input:focus{border-color:#e50914}
.admin-check{display:flex;align-items:center;gap:8px;margin-bottom:14px;font-size:13px;color:#aaa;cursor:pointer}
.btn-add{width:100%;padding:11px;background:#e50914;color:#fff;border:none;border-radius:7px;font-size:14px;font-weight:600;cursor:pointer}
.admin-msg{font-size:13px;text-align:center;margin-top:10px;display:none}
.btn-close-admin{width:100%;padding:10px;background:none;border:1px solid #333;color:#aaa;border-radius:7px;cursor:pointer;margin-top:10px;font-size:13px}

@media(max-width:600px){
  .channels-grid{grid-template-columns:repeat(auto-fill,minmax(130px,1fr))}
  .login-card{padding:32px 24px;margin:16px}
  #player-bar video{width:160px;height:90px}
  .form-row{grid-template-columns:1fr}
}
</style>
</head>
<body>

<!-- LOGIN -->
<div id="login-screen">
  <div class="login-card">
    <div class="login-logo">📺</div>
    <div class="login-title">TV Favorito</div>
    <div class="login-sub">Ingresa tus datos para continuar</div>
    <div class="form-group">
      <label>Usuario</label>
      <input type="text" id="login-user" placeholder="tu usuario" autocomplete="username">
    </div>
    <div class="form-group">
      <label>Contraseña</label>
      <input type="password" id="login-pass" placeholder="tu contraseña" autocomplete="current-password">
    </div>
    <button class="btn-login" onclick="doLogin()">Entrar</button>
    <div class="login-error" id="login-error">Usuario o contraseña incorrectos</div>
  </div>
</div>

<!-- APP -->
<div id="app-screen">
  <nav>
    <div class="nav-logo">📺 TV FAVORITO</div>
    <div class="nav-right">
      <span class="nav-user" id="nav-username"></span>
      <button class="btn-admin" id="btn-admin" onclick="openAdmin()">⚙️ Usuarios</button>
      <button class="btn-logout" onclick="doLogout()">Salir</button>
    </div>
  </nav>
  <div class="main">
    <div class="search-bar">
      <span class="search-icon">🔍</span>
      <input type="text" id="search-input" placeholder="Buscar canal..." oninput="filterChannels()">
    </div>
    <div class="groups-tabs" id="groups-tabs"></div>
    <div id="channels-container"></div>
  </div>
</div>

<!-- PLAYER BAR (sticky abajo) -->
<div id="player-bar">
  <div class="player-bar-inner">
    <video id="video-player" controls></video>
    <div class="player-info">
      <div class="player-channel-name" id="player-channel-name">-</div>
      <div class="player-status" id="player-status">Cargando...</div>
    </div>
    <div class="player-controls">
      <button class="btn-fullscreen" onclick="goFullscreen()">⛶ Pantalla completa</button>
      <button class="btn-close-player" onclick="closePlayer()">✕ Cerrar</button>
    </div>
  </div>
</div>

<!-- ADMIN -->
<div id="admin-modal">
  <div class="admin-card">
    <div class="admin-title">⚙️ Gestión de Usuarios</div>
    <div id="user-list"></div>
    <div class="add-user-form">
      <h3>Agregar nuevo usuario</h3>
      <div class="form-row">
        <input type="text" id="new-user" placeholder="Usuario">
        <input type="password" id="new-pass" placeholder="Contraseña">
      </div>
      <label class="admin-check">
        <input type="checkbox" id="new-admin"> Es administrador
      </label>
      <button class="btn-add" onclick="addUser()">➕ Agregar usuario</button>
      <div class="admin-msg" id="admin-msg"></div>
    </div>
    <button class="btn-close-admin" onclick="closeAdmin()">Cerrar</button>
  </div>
</div>

<script>
let currentUser = null;
let isAdmin = false;
let allChannels = [];
let currentGroup = 'all';
let hlsInstance = null;
let currentCard = null;

async function doLogin() {
  const user = document.getElementById('login-user').value.trim();
  const pass = document.getElementById('login-pass').value.trim();
  document.getElementById('login-error').style.display = 'none';
  if (!user || !pass) return;
  const res = await fetch('/api/login', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({user, pass})
  });
  if (res.ok) {
    const data = await res.json();
    currentUser = user;
    isAdmin = data.admin;
    document.getElementById('nav-username').textContent = '👤 ' + user;
    if (isAdmin) document.getElementById('btn-admin').style.display = 'block';
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('app-screen').style.display = 'block';
    loadChannels();
  } else {
    document.getElementById('login-error').style.display = 'block';
  }
}

function doLogout() {
  closePlayer();
  currentUser = null; isAdmin = false;
  document.getElementById('login-screen').style.display = 'flex';
  document.getElementById('app-screen').style.display = 'none';
  document.getElementById('btn-admin').style.display = 'none';
  document.getElementById('login-user').value = '';
  document.getElementById('login-pass').value = '';
}

async function loadChannels() {
  const res = await fetch('/api/canales?user=' + currentUser);
  allChannels = await res.json();
  renderGroups();
  renderChannels(allChannels);
}

function renderGroups() {
  const groups = ['all', ...new Set(allChannels.map(c => c.group))];
  document.getElementById('groups-tabs').innerHTML = groups.map(g =>
    `<button class="tab ${g==='all'?'active':''}" onclick="selectGroup(this,'${g.replace(/'/g,"\\'")}')">${g==='all'?'🌐 Todos':g}</button>`
  ).join('');
}

function selectGroup(el, group) {
  currentGroup = group;
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  filterChannels();
}

function filterChannels() {
  const q = document.getElementById('search-input').value.toLowerCase();
  let filtered = allChannels;
  if (currentGroup !== 'all') filtered = filtered.filter(c => c.group === currentGroup);
  if (q) filtered = filtered.filter(c => c.name.toLowerCase().includes(q));
  renderChannels(filtered);
}

function cleanName(name) {
  return name.replace(/^(MX|AR|CO|EC|PE|VE|CL|US|USA|ES|UK|PR|RD|GT|HN|CR|PA|URU|UY|24H|HD|FHD|SD|LAT|NEWS|DE|LA) \\| /, '');
}

function renderChannels(channels) {
  const container = document.getElementById('channels-container');
  if (!channels.length) {
    container.innerHTML = '<div class="no-results">😕 No se encontraron canales</div>';
    return;
  }
  const groups = {};
  channels.forEach(c => { if (!groups[c.group]) groups[c.group]=[]; groups[c.group].push(c); });
  container.innerHTML = Object.entries(groups).map(([g, chs]) => `
    <div class="section-title">${g}</div>
    <div class="channels-grid">
      ${chs.map(c => `
        <div class="channel-card">\n          <div onclick="playChannel(this.parentElement,\'${c.url.replace(/\'/g,"\\\\\'")}\',\'${c.name.replace(/\'/g,"\\\\\'")}\')">\n            <div class="channel-name">${cleanName(c.name)}</div>\n            <div class="channel-group">${g}</div>\n            <span class="play-icon">▶</span>\n          </div>\n          <div style="margin-top:8px;display:flex;gap:6px">\n            <button onclick="openVLC(\'${c.url.replace(/\'/g,"\\\\\'")}\');event.stopPropagation()" style="flex:1;padding:5px;background:#1a6b1a;border:none;border-radius:5px;color:#fff;font-size:11px;cursor:pointer">📺 VLC</button>\n            <button onclick="copyURL(\'${c.url.replace(/\'/g,"\\\\\'")}\');event.stopPropagation()" style="flex:1;padding:5px;background:#2a2a4a;border:none;border-radius:5px;color:#aaa;font-size:11px;cursor:pointer">🔗 URL</button>\n          </div>\n        </div>`).join('')}\n    </div>`).join('');
}

function playChannel(card, url, name) {
  if (currentCard) currentCard.classList.remove('playing');
  currentCard = card;
  card.classList.add('playing');

  const cleanedName = cleanName(name);
  document.getElementById('player-channel-name').textContent = cleanedName;
  document.getElementById('player-bar').classList.add('show');

  const status = document.getElementById('player-status');
  status.className = 'player-status loading';
  status.textContent = '⏳ Abriendo canal...';

  // Intentar abrir en Smarters primero
  const smartersUrl = 'smarters://' + url.replace('http://','').replace('https://','');
  window.location.href = smartersUrl;

  // Si Smarters no abre, intentar con VLC después de 1.5 segundos
  setTimeout(() => {
    const vlcUrl = 'vlc://' + url.replace('http://','').replace('https://','');
    window.location.href = vlcUrl;
    status.className = 'player-status error';
    status.textContent = '📱 Abriendo en app externa... Si no abre usa el botón URL';
  }, 1500);
}

function closePlayer() {
  if (hlsInstance) { hlsInstance.destroy(); hlsInstance = null; }
  const video = document.getElementById('video-player');
  video.pause(); video.src = '';
  document.getElementById('player-bar').classList.remove('show');
  if (currentCard) { currentCard.classList.remove('playing'); currentCard = null; }
}

function goFullscreen() {
  const video = document.getElementById('video-player');
  if (video.requestFullscreen) video.requestFullscreen();
  else if (video.webkitRequestFullscreen) video.webkitRequestFullscreen();
}

async function openAdmin() {
  const res = await fetch('/api/usuarios?user=' + currentUser);
  const users = await res.json();
  document.getElementById('user-list').innerHTML = Object.entries(users).map(([u,d]) => `
    <div class="user-item">
      <div>
        <div class="user-name">${u}${d.admin?'<span class="user-badge">Admin</span>':''}</div>
        <div class="user-pass">🔑 ${d.password}</div>
      </div>
      ${u !== currentUser ? `<button class="btn-del" onclick="delUser('${u}')">Eliminar</button>` : '<span style="font-size:11px;color:#555">Tú</span>'}
    </div>`).join('');
  document.getElementById('admin-modal').classList.add('show');
}

function closeAdmin() {
  document.getElementById('admin-modal').classList.remove('show');
  document.getElementById('admin-msg').style.display = 'none';
}

async function addUser() {
  const user = document.getElementById('new-user').value.trim();
  const pass = document.getElementById('new-pass').value.trim();
  const admin = document.getElementById('new-admin').checked;
  if (!user || !pass) return;
  const res = await fetch('/api/usuarios/add', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({requester: currentUser, user, pass, admin})
  });
  const msg = document.getElementById('admin-msg');
  msg.style.display = 'block';
  if (res.ok) {
    msg.style.color = '#4ade80';
    msg.textContent = '✅ Usuario "' + user + '" creado correctamente';
    document.getElementById('new-user').value = '';
    document.getElementById('new-pass').value = '';
    document.getElementById('new-admin').checked = false;
    openAdmin();
  } else {
    msg.style.color = '#ff6b6b';
    msg.textContent = '❌ Error al crear el usuario';
  }
}

async function delUser(user) {
  if (!confirm('¿Eliminar al usuario "' + user + '"?')) return;
  await fetch('/api/usuarios/del', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({requester: currentUser, user})
  });
  openAdmin();
}

function openVLC(url) {
  window.location.href = 'vlc://' + url.replace('http://', '').replace('https://', '');
}

function copyURL(url) {
  navigator.clipboard.writeText(url).then(() => {
    alert('URL copiada. Pégala en VLC u otra app.');
  }).catch(() => {
    prompt('Copia esta URL:', url);
  });
}

function openVLC(url) {\n  window.location.href = 'vlc://' + url.replace('http://', '').replace('https://', '');\n}\n\nfunction copyURL(url) {\n  navigator.clipboard.writeText(url).then(() => {\n    alert('✅ URL copiada. Pégala en VLC u otra app IPTV.');\n  }).catch(() => {\n    prompt('Copia esta URL:', url);\n  });\n}\n\ndocument.addEventListener('keydown', e => {
  if (e.key === 'Escape') { closePlayer(); closeAdmin(); }
  if (e.key === 'Enter' && document.getElementById('login-screen').style.display !== 'none') doLogin();
});
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(APP_HTML)

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json
    usuarios = cargar_usuarios()
    u = data.get("user","")
    p = data.get("pass","")
    if u in usuarios and usuarios[u]["password"] == p:
        return jsonify({"ok": True, "admin": usuarios[u].get("admin", False)})
    abort(401)

@app.route("/api/canales")
def api_canales():
    user = request.args.get("user","")
    usuarios = cargar_usuarios()
    if user not in usuarios:
        abort(401)
    return jsonify(parse_m3u())

@app.route("/api/usuarios")
def api_usuarios():
    user = request.args.get("user","")
    usuarios = cargar_usuarios()
    if user not in usuarios or not usuarios[user].get("admin"):
        abort(403)
    return jsonify(usuarios)

@app.route("/api/usuarios/add", methods=["POST"])
def api_add_usuario():
    data = request.json
    usuarios = cargar_usuarios()
    req = data.get("requester","")
    if req not in usuarios or not usuarios[req].get("admin"):
        abort(403)
    nuevo = data.get("user","").strip()
    if not nuevo:
        abort(400)
    usuarios[nuevo] = {"password": data.get("pass",""), "admin": data.get("admin", False)}
    guardar_usuarios(usuarios)
    return jsonify({"ok": True})

@app.route("/api/usuarios/del", methods=["POST"])
def api_del_usuario():
    data = request.json
    usuarios = cargar_usuarios()
    req = data.get("requester","")
    if req not in usuarios or not usuarios[req].get("admin"):
        abort(403)
    target = data.get("user","")
    if target in usuarios and target != req:
        del usuarios[target]
        guardar_usuarios(usuarios)
    return jsonify({"ok": True})

@app.route("/get/<user>/<pwd>/lista.m3u")
def lista_m3u(user, pwd):
    usuarios = cargar_usuarios()
    if usuarios.get(user, {}).get("password") != pwd:
        abort(401)
    with open(LISTA_PATH, "r", encoding="utf-8") as f:
        contenido = f.read()
    return Response(contenido, status=200, headers={
        "Content-Disposition": "attachment; filename=lista.m3u",
        "Content-Type": "application/vnd.apple.mpegurl"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
