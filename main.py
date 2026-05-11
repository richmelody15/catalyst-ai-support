from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from routers import auth, subscription, tickets, admin, admin_auth, chat, telegram_webhook, analytics, tournaments, referrals, settings, giveaways, paywall, notifications
from routers import vip_challenge, full_analytics, community
from database import init_db
from middleware import paywall_middleware

app = FastAPI(title="Catalyst AI Support", version="4.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.middleware("http")(paywall_middleware)

app.include_router(admin_auth.router)   # must be before admin so /api/admin/login is found first
app.include_router(auth.router)
app.include_router(subscription.router)
app.include_router(tickets.router)
app.include_router(admin.router)
app.include_router(paywall.router)
app.include_router(notifications.router)
app.include_router(chat.router)
app.include_router(telegram_webhook.router)
app.include_router(analytics.router)
app.include_router(full_analytics.router)
app.include_router(tournaments.router)
app.include_router(vip_challenge.router)
app.include_router(referrals.router)
app.include_router(settings.router)
app.include_router(giveaways.router)
app.include_router(community.router)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    return {"status": "AI Support System Active", "version": "4.0"}

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CATALYST AI — Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0a0e17;--card:#111827;--border:#1e293b;--accent:#3b82f6;--green:#22c55e;--red:#ef4444;--yellow:#eab308;--text:#e2e8f0;--muted:#64748b;--purple:#a855f7;--gold:#ffd700}
body.light-mode{--bg:#f1f5f9;--card:#ffffff;--border:#e2e8f0;--text:#1e293b;--muted:#64748b}
body{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;transition:background .3s,color .3s}
.header{background:linear-gradient(135deg,#0f172a,#1e1b4b);padding:1.25rem 2rem;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
body.light-mode .header{background:linear-gradient(135deg,#3b82f6,#7c3aed)}
.header h1{font-size:1.4rem;font-weight:700;background:linear-gradient(135deg,var(--accent),var(--purple));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
body.light-mode .header h1{-webkit-text-fill-color:#fff}
.header .status{display:flex;align-items:center;gap:.5rem;font-size:.8rem;color:var(--muted)}
body.light-mode .header .status{color:#fff}
.header .dot{width:8px;height:8px;border-radius:50%;background:var(--green);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
.theme-toggle{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);border-radius:20px;padding:4px 10px;color:#fff;cursor:pointer;font-size:.75rem}
.container{max-width:1400px;margin:0 auto;padding:1.25rem}
.tab-bar{display:flex;gap:.4rem;margin-bottom:1rem;overflow-x:auto;padding-bottom:.25rem;flex-wrap:wrap}
.tab-btn{padding:.5rem 1rem;background:rgba(255,255,255,.03);border:1px solid var(--border);border-radius:8px;font-size:.8rem;cursor:pointer;color:var(--muted);transition:all .2s;white-space:nowrap}
.tab-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.tab-btn:hover:not(.active){border-color:var(--accent);color:var(--text)}
.tab-content{display:none}
.tab-content.active{display:block}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.25rem;margin-bottom:1rem}
.card-title{font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.75rem;margin-bottom:1rem}
.stat{text-align:center;padding:.75rem;background:rgba(255,255,255,.03);border-radius:8px}
.stat .num{font-size:1.5rem;font-weight:700}
.stat .label{font-size:.7rem;color:var(--muted);margin-top:.15rem}
.btn{padding:.5rem 1rem;border:none;border-radius:8px;font-size:.8rem;font-weight:600;cursor:pointer;transition:all .15s}
.btn:hover{transform:translateY(-1px);filter:brightness(1.1)}
.btn-primary{background:var(--accent);color:#fff}
.btn-green{background:rgba(34,197,94,.15);color:var(--green);border:1px solid rgba(34,197,94,.3)}
.btn-red{background:rgba(239,68,68,.15);color:var(--red);border:1px solid rgba(239,68,68,.3)}
.btn-yellow{background:rgba(234,179,8,.15);color:var(--yellow);border:1px solid rgba(234,179,8,.3)}
.btn-gold{background:rgba(255,215,0,.15);color:var(--gold);border:1px solid rgba(255,215,0,.3)}
.btn-purple{background:rgba(168,85,247,.15);color:var(--purple);border:1px solid rgba(168,85,247,.3)}
.giveaway-card{background:rgba(255,255,255,.03);border:1px solid var(--border);border-radius:8px;padding:1rem;margin-bottom:.75rem}
.giveaway-card h4{margin-bottom:.25rem}
input,textarea,select{background:rgba(255,255,255,.05);border:1px solid var(--border);border-radius:8px;padding:.5rem .75rem;color:var(--text);font-size:.85rem;outline:none;width:100%;margin-bottom:.5rem}
input:focus,textarea:focus{border-color:var(--accent)}
.chat-container{background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden}
.chat-messages{height:320px;overflow-y:auto;padding:1rem}
.chat-msg{margin-bottom:.6rem;display:flex;flex-direction:column}
.chat-msg.user{align-items:flex-end}
.chat-msg.ai{align-items:flex-start}
.chat-msg.system{align-items:center}
.chat-bubble{max-width:80%;padding:.6rem .9rem;border-radius:12px;font-size:.85rem;line-height:1.4}
.chat-msg.user .chat-bubble{background:var(--accent);color:#fff;border-bottom-right-radius:4px}
.chat-msg.ai .chat-bubble{background:rgba(255,255,255,.05);border:1px solid var(--border);border-bottom-left-radius:4px}
.chat-msg.system .chat-bubble{background:rgba(255,215,0,.1);border:1px solid rgba(255,215,0,.2);color:var(--gold);font-size:.75rem;border-radius:4px}
.chat-input{display:flex;gap:.5rem;padding:.75rem;border-top:1px solid var(--border)}
.chat-input input{flex:1;margin:0}
.chat-input button{background:var(--accent);color:#fff;border:none;border-radius:8px;padding:.5rem 1rem;cursor:pointer;font-weight:600}
.toggle{display:flex;align-items:center;gap:.5rem;margin-bottom:.75rem}
.toggle label{font-size:.85rem;color:var(--muted)}
.toggle input[type=checkbox]{width:auto;accent-color:var(--accent)}
.toast{position:fixed;bottom:1.5rem;right:1.5rem;padding:.6rem 1rem;border-radius:8px;font-size:.85rem;z-index:1000;display:none}
.toast.success{background:rgba(34,197,94,.9);color:#fff}
.toast.error{background:rgba(239,68,68,.9);color:#fff}
.admin-login-box{background:rgba(26,26,46,.9);padding:15px;border-radius:12px;margin-bottom:15px;border:1px solid var(--border)}
.admin-login-box h4{color:var(--green);margin-bottom:.5rem}
.admin-panel-box{background:rgba(10,10,46,.95);padding:15px;border-radius:12px;margin-bottom:15px;border:1px solid rgba(255,215,0,.2)}
.admin-panel-box h4{color:var(--gold);margin-bottom:.5rem}
.plans-table{width:100%;border-collapse:collapse;margin-bottom:.75rem}
.plans-table th,.plans-table td{padding:.4rem .6rem;border:1px solid var(--border);font-size:.8rem}
.plans-table th{background:rgba(255,255,255,.05);color:var(--muted);text-align:left}
.plans-table input{background:rgba(255,255,255,.05);border:1px solid var(--border);border-radius:4px;padding:.3rem .5rem;color:var(--text);font-size:.8rem;width:100%;margin:0}
.user-info-box{background:rgba(26,26,46,.9);padding:15px;border-radius:12px;margin-bottom:15px;border:1px solid var(--border)}
.user-info-box h4{color:var(--green);margin-bottom:.5rem}
.equity-chart-container{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1rem;margin-bottom:1rem}
.equity-chart-container canvas{max-height:200px}
.journal-table{width:100%;border-collapse:collapse;font-size:.8rem}
.journal-table th,.journal-table td{padding:.4rem .6rem;border:1px solid var(--border);text-align:left}
.journal-table th{background:rgba(255,255,255,.05);color:var(--muted)}
.risk-card{background:rgba(255,255,255,.03);border:1px solid var(--border);border-radius:8px;padding:1rem;margin-bottom:.75rem}
.risk-card .advice{color:var(--gold);font-size:.9rem;margin-top:.5rem}
.vip-card{background:rgba(168,85,247,.05);border:1px solid rgba(168,85,247,.2);border-radius:8px;padding:1rem;margin-bottom:.75rem}
.vip-card h4{color:var(--purple);margin-bottom:.25rem}
.community-user{font-weight:600;margin-right:.4rem}
@media(max-width:768px){.header{padding:1rem}.container{padding:1rem}.stat-grid{grid-template-columns:1fr 1fr}}
</style>
</head>
<body>
<div class="header">
  <h1>CATALYST AI</h1>
  <div style="display:flex;align-items:center;gap:1rem;">
    <button class="theme-toggle" onclick="toggleTheme()" id="theme-btn">☀ Light</button>
    <div class="status"><div class="dot"></div><span id="status-text">Live</span></div>
  </div>
</div>
<div class="container">

  <!-- User Info Form (shown if email missing) -->
  <div id="user-info-form" class="user-info-box" style="display:none;">
    <h4>Complete Your Profile</h4>
    <input id="user-fullname" placeholder="Full Name" style="width:100%;padding:8px;margin:5px 0;">
    <input id="user-email" placeholder="Email address" type="email" style="width:100%;padding:8px;margin:5px 0;">
    <button onclick="saveUserInfo()" class="btn btn-primary">Save & Continue</button>
  </div>

  <!-- Admin Login Panel (hidden by default) -->
  <div id="admin-login" class="admin-login-box" style="display:none;">
    <h4>Admin Login</h4>
    <input type="email" id="admin-email" placeholder="Email address">
    <input type="password" id="admin-password" placeholder="Password">
    <div class="toggle" style="margin:5px 0 8px;"><input type="checkbox" id="remember-me"><label>Remember Me</label></div>
    <button onclick="adminLogin()" class="btn" style="background:var(--green);color:#000;width:100%;padding:10px;">Login</button>
    <p id="login-error" style="color:var(--red);margin-top:8px;"></p>
  </div>

  <!-- Admin Panel (after login) -->
  <div id="admin-panel" class="admin-panel-box" style="display:none;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
      <h4 style="margin:0;">Admin Panel</h4>
      <button onclick="adminLogout()" class="btn btn-red">Logout</button>
    </div>
    <div id="admin-stats" style="font-size:.85rem;color:var(--muted);margin-bottom:10px;"></div>

    <!-- Activity Log -->
    <div style="background:rgba(255,255,255,.03);padding:10px;border-radius:8px;margin-bottom:12px;max-height:150px;overflow-y:auto;">
      <h5 style="color:var(--gold);margin-bottom:5px;font-size:.8rem;">Recent Activity</h5>
      <div id="activity-list" style="font-size:.75rem;color:var(--muted);"></div>
    </div>

    <!-- Paywall Settings -->
    <div id="admin-paywall-settings" style="margin-top:15px;border-top:1px solid var(--border);padding-top:15px;">
      <h4 style="color:var(--gold);margin-bottom:8px;">Paywall Settings</h4>
      <div class="toggle">
        <input type="checkbox" id="paywall-toggle" onchange="togglePaywall()">
        <label>Enable Paywall</label>
      </div>
      <div class="toggle">
        <input type="checkbox" id="email-alerts-toggle" onchange="toggleEmailAlerts()">
        <label>Email Alerts on Paywall Bypass</label>
      </div>

      <h5 style="color:var(--muted);margin:10px 0 5px;">Subscription Plans <button class="btn btn-green" onclick="addPlanRow()" style="font-size:.7rem;padding:.3rem .6rem;">+ Add Plan</button></h5>
      <table class="plans-table" id="plans-table">
        <thead><tr><th>Key</th><th>Name</th><th>Price ($)</th><th>Days</th><th></th></tr></thead>
        <tbody id="plans-tbody"></tbody>
      </table>
      <button class="btn btn-primary" onclick="savePlans()" style="font-size:.8rem;">Save Plans</button>

      <label style="font-size:.8rem;color:var(--muted);margin-top:12px;display:block;">Protected Routes (comma-separated):</label>
      <input type="text" id="protected-routes" placeholder="/dashboard,/signals" onchange="saveRoutes()" style="margin-top:4px;">
    </div>
  </div>

  <!-- Tab Bar -->
  <div class="tab-bar">
    <button class="tab-btn active" onclick="showTab('signals')">Signals</button>
    <button class="tab-btn" onclick="showTab('analytics')">Analytics</button>
    <button class="tab-btn" onclick="showTab('full-analytics')">Full Analytics</button>
    <button class="tab-btn" onclick="showTab('vip')">VIP Challenges</button>
    <button class="tab-btn" onclick="showTab('tournaments')">Tournaments</button>
    <button class="tab-btn" onclick="showTab('giveaways')">Giveaways</button>
    <button class="tab-btn" onclick="showTab('referrals')">Referrals</button>
    <button class="tab-btn" onclick="showTab('community')">Community</button>
    <button class="tab-btn" onclick="showTab('settings')">Settings</button>
    <button class="tab-btn" onclick="showTab('chat')">AI Chat</button>
  </div>

  <!-- ═══ Signals ═══ -->
  <div id="tab-signals" class="tab-content active">
    <div class="stat-grid" id="signal-stats"></div>
    <div class="card">
      <div class="card-title">Recent Signals — Click Win / Loss / Ignored</div>
      <div id="signal-list" style="max-height:500px;overflow-y:auto"></div>
    </div>
  </div>

  <!-- ═══ Analytics ═══ -->
  <div id="tab-analytics" class="tab-content">
    <div class="stat-grid" id="analytics-stats"></div>
    <div class="card">
      <div class="card-title">Per-Pair Breakdown</div>
      <div id="pair-breakdown"></div>
    </div>
    <div class="card">
      <div class="card-title">Platform Performance</div>
      <div id="platform-breakdown"></div>
    </div>
  </div>

  <!-- ═══ Full Analytics ═══ -->
  <div id="tab-full-analytics" class="tab-content">
    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem;flex-wrap:wrap;">
      <h3 style="color:var(--accent);margin:0;">Full Analytics</h3>
      <select id="analytics-period" onchange="loadFullAnalytics()" style="width:auto;margin:0;">
        <option value="7">7 days</option>
        <option value="30" selected>30 days</option>
        <option value="90">90 days</option>
        <option value="365">1 year</option>
      </select>
    </div>

    <!-- Trade Overview -->
    <div class="stat-grid" id="trade-overview-stats"></div>

    <!-- Equity Chart -->
    <div class="equity-chart-container">
      <div class="card-title">Equity Curve</div>
      <canvas id="equity-chart" height="150"></canvas>
    </div>

    <!-- Subscriber Stats -->
    <div class="card">
      <div class="card-title">Subscriber Analytics</div>
      <div id="subscriber-stats"></div>
    </div>

    <!-- Risk Snapshot -->
    <div class="risk-card" id="risk-advice-card">
      <div class="card-title">Risk Management Snapshot</div>
      <div id="risk-advice"></div>
    </div>

    <!-- Trading Journal -->
    <div class="card">
      <div class="card-title">Trading Journal</div>
      <table class="journal-table" id="journal-table">
        <thead><tr><th>Symbol</th><th>Dir</th><th>TF</th><th>Platform</th><th>Time</th><th>Outcome</th><th>Conf</th></tr></thead>
        <tbody></tbody>
      </table>
      <div style="display:flex;gap:.5rem;margin-top:.75rem;justify-content:center;">
        <button class="btn btn-primary" onclick="loadJournal(1)" style="font-size:.75rem;">First</button>
        <button class="btn btn-primary" id="journal-prev" onclick="loadJournal(journalPage-1)" style="font-size:.75rem;">Prev</button>
        <span id="journal-page-info" style="font-size:.8rem;color:var(--muted);padding:.3rem;"></span>
        <button class="btn btn-primary" id="journal-next" onclick="loadJournal(journalPage+1)" style="font-size:.75rem;">Next</button>
      </div>
    </div>
  </div>

  <!-- ═══ VIP Challenges ═══ -->
  <div id="tab-vip" class="tab-content">
    <div class="card">
      <div class="card-title">Active VIP Challenges</div>
      <div id="vip-challenge-list"></div>
    </div>
    <div class="card" id="create-vip-challenge" style="display:none">
      <div class="card-title" style="color:var(--purple);">Create VIP Challenge (Admin)</div>
      <input id="vip-name" placeholder="Challenge name">
      <textarea id="vip-desc" placeholder="Description" rows="2"></textarea>
      <div style="display:flex;gap:.5rem;">
        <input id="vip-start" type="datetime-local" style="flex:1;" placeholder="Start">
        <input id="vip-end" type="datetime-local" style="flex:1;" placeholder="End">
      </div>
      <div style="display:flex;gap:.5rem;">
        <input id="vip-fee" type="number" placeholder="Entry fee ($)" value="0" style="flex:1;">
        <input id="vip-prize" type="number" placeholder="Prize pool ($)" style="flex:1;">
      </div>
      <button class="btn btn-purple" onclick="createVIPChallenge()">Create VIP Challenge</button>
    </div>
  </div>

  <!-- ═══ Tournaments ═══ -->
  <div id="tab-tournaments" class="tab-content">
    <div class="card">
      <div class="card-title">Active Tournaments</div>
      <div id="tournament-list"></div>
    </div>
    <div class="card" id="create-tournament" style="display:none">
      <div class="card-title" style="color:var(--gold);">Create Tournament (Admin)</div>
      <input id="t-name" placeholder="Tournament name">
      <input id="t-start" type="datetime-local"> Start
      <input id="t-end" type="datetime-local"> End
      <input id="t-fee" type="number" placeholder="Entry fee ($)" value="0">
      <input id="t-prize" type="number" placeholder="Prize pool ($)">
      <button class="btn btn-primary" onclick="createTournament()">Create Tournament</button>
    </div>
  </div>

  <!-- ═══ Giveaways ═══ -->
  <div id="tab-giveaways" class="tab-content">
    <div class="card">
      <div class="card-title">Active Giveaways</div>
      <div id="giveaway-list"></div>
    </div>
    <div class="card" id="create-giveaway" style="display:none">
      <div class="card-title" style="color:var(--gold);">Create Giveaway (Admin)</div>
      <input id="gw-title" placeholder="Title">
      <textarea id="gw-desc" placeholder="Description"></textarea>
      <input id="gw-start" type="datetime-local"> Start
      <input id="gw-end" type="datetime-local"> End
      <input id="gw-prize" placeholder="Prize">
      <input id="gw-winners" type="number" value="1" placeholder="Number of winners">
      <button class="btn btn-primary" onclick="createGiveaway()">Create Giveaway</button>
    </div>
    <div class="card" id="draw-giveaway" style="display:none">
      <div class="card-title" style="color:var(--gold);">Draw Winner (Admin)</div>
      <input id="draw-id" type="number" placeholder="Giveaway ID">
      <button class="btn btn-gold" onclick="drawGiveaway()">Draw Winners</button>
    </div>
  </div>

  <!-- ═══ Referrals ═══ -->
  <div id="tab-referrals" class="tab-content">
    <div class="card">
      <div class="card-title">Your Referral Link</div>
      <div id="referral-link" style="font-size:.9rem;color:var(--accent);word-break:break-all"></div>
    </div>
    <div class="stat-grid" id="referral-stats"></div>
    <div class="card">
      <div class="card-title">Register a Referral</div>
      <input id="ref-name" placeholder="Referred person's name">
      <input id="ref-email" placeholder="Referred person's email">
      <button class="btn btn-primary" onclick="registerReferral()">Register</button>
    </div>
  </div>

  <!-- ═══ Community Chat ═══ -->
  <div id="tab-community" class="tab-content">
    <div class="chat-container" style="height:500px;display:flex;flex-direction:column;">
      <div class="chat-messages" id="community-messages" style="flex:1;"></div>
      <div class="chat-input">
        <input id="community-input" placeholder="Type a message..." onkeypress="if(event.key==='Enter')sendCommunityMsg()">
        <button onclick="sendCommunityMsg()">Send</button>
      </div>
    </div>
  </div>

  <!-- ═══ Settings ═══ -->
  <div id="tab-settings" class="tab-content">
    <div class="card">
      <div class="card-title">Your Settings</div>
      <div class="toggle"><input type="checkbox" id="set-tg-alerts" checked><label>Telegram Alerts</label></div>
      <div class="toggle"><input type="checkbox" id="set-email-alerts"><label>Email Alerts</label></div>
      <label style="font-size:.8rem;color:var(--muted)">Timezone</label>
      <select id="set-timezone">
        <option value="UTC">UTC</option><option value="US/Eastern">US/Eastern</option>
        <option value="US/Pacific">US/Pacific</option><option value="Europe/London">Europe/London</option>
        <option value="Asia/Tokyo">Asia/Tokyo</option><option value="Africa/Lagos">Africa/Lagos</option>
      </select>
      <label style="font-size:.8rem;color:var(--muted)">Risk Level</label>
      <select id="set-risk">
        <option value="low">Low</option><option value="medium" selected>Medium</option><option value="high">High</option>
      </select>
      <button class="btn btn-primary" onclick="saveSettings()" style="margin-top:.5rem">Save Settings</button>
    </div>
  </div>

  <!-- ═══ AI Chat ═══ -->
  <div id="tab-chat" class="tab-content">
    <div class="chat-container">
      <div class="chat-messages" id="chat-messages">
        <div class="chat-msg ai"><div class="chat-bubble">Hello! I'm the CATALYST AI assistant. How can I help?</div></div>
      </div>
      <div class="chat-input">
        <input id="chat-input" placeholder="Type your message..." onkeypress="if(event.key==='Enter')sendChat()">
        <button onclick="sendChat()">Send</button>
      </div>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const UID = localStorage.getItem('user_id') || '1';
const STORAGE_KEY = 'admin_access_token';
let journalPage = 1;
let communityWs = null;
let equityChartInstance = null;

// ── Theme Toggle ──────────────────────────────────────────────────
function toggleTheme() {
  document.body.classList.toggle('light-mode');
  const isLight = document.body.classList.contains('light-mode');
  localStorage.setItem('theme', isLight ? 'light' : 'dark');
  document.getElementById('theme-btn').textContent = isLight ? '🌙 Dark' : '☀ Light';
}
// Init theme from localStorage
(function() {
  const saved = localStorage.getItem('theme');
  if (saved === 'light') {
    document.body.classList.add('light-mode');
    document.getElementById('theme-btn').textContent = '🌙 Dark';
  }
})();

// ── Toast Notification ─────────────────────────────────────────────
function showToast(msg, type='success') {
  const t = document.getElementById('toast');
  t.textContent = msg; t.className = 'toast ' + type; t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 3000);
}

// ── User Info ──────────────────────────────────────────────────────
function checkUserInfo() {
  const tgId = localStorage.getItem('user_id');
  if (!tgId) return;
  fetch(`/api/auth/me/${tgId}`)
    .then(r => { if (!r.ok) throw new Error(); return r.json(); })
    .then(user => {
      if (!user.email || !user.full_name) {
        document.getElementById('user-info-form').style.display = 'block';
      } else {
        document.getElementById('user-info-form').style.display = 'none';
      }
    })
    .catch(() => {});
}

function saveUserInfo() {
  const tgId = localStorage.getItem('user_id');
  const fullName = document.getElementById('user-fullname').value;
  const email = document.getElementById('user-email').value;
  if (!fullName || !email) return showToast('Please fill both fields', 'error');
  fetch('/api/notifications/save-user-info', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ telegram_id: parseInt(tgId), email, full_name: fullName })
  })
  .then(r => r.json())
  .then(d => {
    document.getElementById('user-info-form').style.display = 'none';
    showToast('Profile saved!');
  })
  .catch(() => showToast('Failed to save profile', 'error'));
}

// ── Admin Auth (JWT with refresh tokens) ───────────────────────────
async function adminLogin() {
  const email = document.getElementById('admin-email').value;
  const password = document.getElementById('admin-password').value;
  const remember = document.getElementById('remember-me').checked;
  if (!email || !password) return;
  try {
    const resp = await fetch('/api/admin/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ email, password, remember_me: remember, platform: 'web' }),
      credentials: 'include'
    });
    if (!resp.ok) {
      document.getElementById('login-error').textContent = 'Invalid email or password';
      return;
    }
    const data = await resp.json();
    localStorage.setItem(STORAGE_KEY, data.access_token);
    document.getElementById('login-error').textContent = '';
    document.getElementById('admin-login').style.display = 'none';
    document.getElementById('admin-panel').style.display = 'block';
    showAdminSections();
    loadAdminStats();
    loadPaywallSettings();
    loadActivityLog();
  } catch(e) {
    document.getElementById('login-error').textContent = 'Connection error';
  }
}

async function adminLogout() {
  await fetch('/api/admin/logout', { method: 'POST', credentials: 'include' });
  localStorage.removeItem(STORAGE_KEY);
  document.getElementById('admin-panel').style.display = 'none';
  document.getElementById('admin-login').style.display = 'block';
  hideAdminSections();
}

// Auto-login via refresh token (httpOnly cookie)
async function tryAutoLogin() {
  try {
    const resp = await fetch('/api/admin/refresh', { method: 'POST', credentials: 'include' });
    if (resp.ok) {
      const data = await resp.json();
      localStorage.setItem(STORAGE_KEY, data.access_token);
      document.getElementById('admin-login').style.display = 'none';
      document.getElementById('admin-panel').style.display = 'block';
      showAdminSections();
      loadAdminStats();
      loadPaywallSettings();
      loadActivityLog();
      return true;
    }
  } catch(e) {}
  document.getElementById('admin-login').style.display = 'block';
  return false;
}

// Activity Log
function loadActivityLog() {
  adminFetch('/api/admin/activity?limit=15')
    .then(r => r.json())
    .then(data => {
      let html = '';
      data.forEach(log => {
        html += '<div style="border-bottom:1px solid var(--border);padding:3px 0;"><strong>' + log.action + '</strong> &mdash; ' + new Date(log.timestamp).toLocaleString() + (log.details ? '<br><small>' + log.details + '</small>' : '') + '</div>';
      });
      document.getElementById('activity-list').innerHTML = html || '<div>No activity yet</div>';
    })
    .catch(() => {});
}
setInterval(() => { if (localStorage.getItem(STORAGE_KEY)) loadActivityLog(); }, 30000);

function adminFetch(url, options = {}) {
  const token = localStorage.getItem(STORAGE_KEY);
  if (!token) return Promise.reject('Not logged in');
  options.headers = options.headers || {};
  options.headers['Authorization'] = 'Bearer ' + token;
  return fetch(url, options);
}

function showAdminSections() {
  ['create-tournament','create-giveaway','draw-giveaway','create-vip-challenge'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'block';
  });
}

function hideAdminSections() {
  ['create-tournament','create-giveaway','draw-giveaway','create-vip-challenge'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });
}

async function loadAdminStats() {
  try {
    const r = await adminFetch('/api/admin/stats');
    if (!r.ok) throw new Error('Unauthorized');
    const d = await r.json();
    document.getElementById('admin-stats').innerHTML =
      'Users: ' + d.total_users + ' | Premium: ' + d.premium_users +
      ' | Open Tickets: ' + d.open_tickets + ' | Signals: ' + d.total_signals;
  } catch(e) {}
}

// ── Paywall Settings ───────────────────────────────────────────────
async function loadPaywallSettings() {
  try {
    const r = await adminFetch('/api/admin/settings/paywall');
    if (!r.ok) return;
    const d = await r.json();
    document.getElementById('paywall-toggle').checked = d.paywall_enabled;
    document.getElementById('email-alerts-toggle').checked = d.email_alerts;
    document.getElementById('protected-routes').value = (d.protected_routes || []).join(',');
    renderPlansTable(d.plans || {});
  } catch(e) {}
}

function renderPlansTable(plans) {
  const tbody = document.getElementById('plans-tbody');
  tbody.innerHTML = '';
  Object.entries(plans).forEach(([key, plan]) => {
    tbody.innerHTML += `<tr>
      <td><input data-field="key" value="${key}" style="width:70px;"></td>
      <td><input data-field="name" value="${plan.name}"></td>
      <td><input data-field="price" type="number" step="0.01" value="${plan.price}" style="width:70px;"></td>
      <td><input data-field="days" type="number" value="${plan.days}" style="width:60px;"></td>
      <td><button class="btn btn-red" onclick="this.closest('tr').remove()" style="font-size:.7rem;padding:.2rem .5rem;">X</button></td>
    </tr>`;
  });
}

function addPlanRow() {
  const tbody = document.getElementById('plans-tbody');
  tbody.innerHTML += `<tr>
    <td><input data-field="key" value="" placeholder="e.g. weekly" style="width:70px;"></td>
    <td><input data-field="name" value="" placeholder="Plan name"></td>
    <td><input data-field="price" type="number" step="0.01" value="9.99" style="width:70px;"></td>
    <td><input data-field="days" type="number" value="30" style="width:60px;"></td>
    <td><button class="btn btn-red" onclick="this.closest('tr').remove()" style="font-size:.7rem;padding:.2rem .5rem;">X</button></td>
  </tr>`;
}

function savePlans() {
  const rows = document.querySelectorAll('#plans-tbody tr');
  const plans = {};
  rows.forEach(row => {
    const inputs = row.querySelectorAll('input');
    const key = inputs[0].value.trim();
    if (!key) return;
    plans[key] = {
      name: inputs[1].value.trim(),
      price: parseFloat(inputs[2].value) || 0,
      days: parseInt(inputs[3].value) || 30
    };
  });
  adminFetch('/api/admin/settings/paywall/plans', {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(plans)
  })
  .then(r => { if (!r.ok) throw new Error('Failed'); return r.json(); })
  .then(d => showToast('Plans saved!'))
  .catch(e => showToast('Failed: ' + e.message, 'error'));
}

function togglePaywall() {
  const enabled = document.getElementById('paywall-toggle').checked;
  adminFetch('/api/admin/settings/paywall/toggle?enabled=' + enabled, {method: 'PUT'})
    .then(r => r.json())
    .then(d => showToast('Paywall ' + (d.paywall_enabled ? 'enabled' : 'disabled')))
    .catch(() => showToast('Failed', 'error'));
}

function toggleEmailAlerts() {
  const enabled = document.getElementById('email-alerts-toggle').checked;
  adminFetch('/api/admin/settings/paywall/email-alerts', {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({enabled})
  })
  .then(() => showToast('Email alerts ' + (enabled ? 'enabled' : 'disabled')))
  .catch(() => showToast('Failed', 'error'));
}

function saveRoutes() {
  const routes = document.getElementById('protected-routes').value;
  adminFetch('/api/admin/settings/paywall/routes?routes=' + encodeURIComponent(routes), {method: 'PUT'})
    .then(r => r.json())
    .then(d => showToast('Routes updated'))
    .catch(() => showToast('Failed', 'error'));
}

// Check admin session on page load
window.addEventListener('load', () => {
  checkUserInfo();
  const token = localStorage.getItem(STORAGE_KEY);
  if (token) {
    adminFetch('/api/admin/stats')
      .then(r => {
        if (r.ok) {
          document.getElementById('admin-panel').style.display = 'block';
          showAdminSections();
          loadAdminStats();
          loadPaywallSettings();
          loadActivityLog();
        } else {
          localStorage.removeItem(STORAGE_KEY);
          tryAutoLogin();
        }
      })
      .catch(() => tryAutoLogin());
  } else {
    tryAutoLogin();
  }
});

// ── Tab Navigation ─────────────────────────────────────────────────
function showTab(tab) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-' + tab).classList.add('active');
  event.target.classList.add('active');
  if (tab === 'analytics') loadAnalytics();
  if (tab === 'full-analytics') loadFullAnalytics();
  if (tab === 'vip') loadVIPChallenges();
  if (tab === 'tournaments') loadTournaments();
  if (tab === 'giveaways') loadGiveaways();
  if (tab === 'referrals') loadReferrals();
  if (tab === 'community') connectCommunity();
  if (tab === 'settings') loadSettings();
  if (tab === 'signals') loadSignals();
}

// ── Signals ──────────────────────────────────────────────────────
async function loadSignals() {
  try {
    const r = await fetch('/api/analytics/summary?days=1');
    const d = await r.json();
    document.getElementById('signal-stats').innerHTML = `
      <div class="stat"><div class="num" style="color:var(--accent)">${d.total_signals}</div><div class="label">Today</div></div>
      <div class="stat"><div class="num" style="color:var(--green)">${d.wins}</div><div class="label">Wins</div></div>
      <div class="stat"><div class="num" style="color:var(--red)">${d.losses}</div><div class="label">Losses</div></div>
      <div class="stat"><div class="num" style="color:${d.win_rate>=93?'var(--green)':'var(--yellow)'}">${d.win_rate}%</div><div class="label">Win Rate</div></div>`;
  } catch(e) {}
  try {
    const r = await fetch('/api/analytics/export');
    const data = await r.json();
    const pending = data.filter(s => s.outcome === 'pending').slice(0, 20);
    document.getElementById('signal-list').innerHTML = pending.length ? pending.map(s => `
      <div style="display:flex;justify-content:space-between;align-items:center;padding:.6rem 0;border-bottom:1px solid var(--border)">
        <div><strong>${s.symbol}</strong> <span style="color:var(--muted);font-size:.8rem">${s.direction} ${s.timeframe} [${s.platform||'N/A'}]</span></div>
        <div style="display:flex;gap:.4rem">
          <button class="btn btn-green" onclick="reportOutcome(${s.id},'win')">Win</button>
          <button class="btn btn-red" onclick="reportOutcome(${s.id},'loss')">Loss</button>
          <button class="btn btn-yellow" onclick="reportOutcome(${s.id},'ignored')">Ignored</button>
        </div>
      </div>`).join('') : '<div style="color:var(--muted);padding:1rem;text-align:center">No pending signals</div>';
  } catch(e) {}
}

async function reportOutcome(id, outcome) {
  await fetch('/api/analytics/outcome/' + id + '?outcome=' + outcome, {method:'PATCH'});
  showToast('Recorded: ' + outcome.toUpperCase());
  loadSignals();
}

// ── Analytics ─────────────────────────────────────────────────────
async function loadAnalytics() {
  try {
    const r = await fetch('/api/analytics/summary?days=7');
    const d = await r.json();
    document.getElementById('analytics-stats').innerHTML = `
      <div class="stat"><div class="num" style="color:var(--accent)">${d.total_signals}</div><div class="label">7d Signals</div></div>
      <div class="stat"><div class="num" style="color:var(--green)">${d.wins}</div><div class="label">Wins</div></div>
      <div class="stat"><div class="num" style="color:var(--red)">${d.losses}</div><div class="label">Losses</div></div>
      <div class="stat"><div class="num" style="color:var(--yellow)">${d.ignored}</div><div class="label">Ignored</div></div>
      <div class="stat"><div class="num" style="color:${d.win_rate>=93?'var(--green)':'var(--yellow)'}">${d.win_rate}%</div><div class="label">Win Rate</div></div>`;
    const pairs = d.by_pair || {};
    document.getElementById('pair-breakdown').innerHTML = Object.entries(pairs).map(([sym, s]) => `
      <div style="display:flex;justify-content:space-between;padding:.4rem 0;border-bottom:1px solid var(--border)">
        <span>${sym}</span>
        <span style="color:${s.win_rate>=93?'var(--green)':'var(--yellow)'}">${s.win_rate}% (${s.total})</span>
      </div>`).join('') || '<div style="color:var(--muted)">No data yet</div>';
  } catch(e) {}
  try {
    const r = await fetch('/api/analytics/weekly-report');
    const d = await r.json();
    const platforms = d.by_platform || {};
    document.getElementById('platform-breakdown').innerHTML = Object.entries(platforms).map(([p, s]) => `
      <div style="display:flex;justify-content:space-between;padding:.4rem 0;border-bottom:1px solid var(--border)">
        <span>${p}</span>
        <span style="color:${s.win_rate>=93?'var(--green)':'var(--yellow)'}">${s.win_rate}% (${s.total})</span>
      </div>`).join('') || '<div style="color:var(--muted)">No platform data</div>';
  } catch(e) {}
}

// ── Full Analytics ──────────────────────────────────────────────────
async function loadFullAnalytics() {
  const days = document.getElementById('analytics-period').value;

  // Trade Overview
  try {
    const r = await fetch(`/api/analytics/full/trade-overview?days=${days}`);
    const d = await r.json();
    document.getElementById('trade-overview-stats').innerHTML = `
      <div class="stat"><div class="num" style="color:var(--accent)">${d.total_signals}</div><div class="label">${days}d Signals</div></div>
      <div class="stat"><div class="num" style="color:var(--green)">${d.wins}</div><div class="label">Wins</div></div>
      <div class="stat"><div class="num" style="color:var(--red)">${d.losses}</div><div class="label">Losses</div></div>
      <div class="stat"><div class="num" style="color:var(--yellow)">${d.ignored}</div><div class="label">Ignored</div></div>
      <div class="stat"><div class="num" style="color:${d.win_rate>=93?'var(--green)':'var(--yellow)'}">${d.win_rate}%</div><div class="label">Win Rate</div></div>
      <div class="stat"><div class="num" style="color:var(--green)">${d.best_pair}</div><div class="label">Best Pair</div></div>
      <div class="stat"><div class="num" style="color:var(--red)">${d.worst_pair}</div><div class="label">Worst Pair</div></div>
      <div class="stat"><div class="num" style="color:var(--accent)">$${d.final_balance}</div><div class="label">Sim Balance</div></div>`;

    // Equity Chart
    drawEquityChart(d.equity_curve);
  } catch(e) { console.error('Trade overview failed:', e); }

  // Subscriber Stats
  try {
    const r = await fetch(`/api/analytics/full/subscribers?days=${days}`);
    const d = await r.json();
    document.getElementById('subscriber-stats').innerHTML = `
      <div class="stat-grid">
        <div class="stat"><div class="num" style="color:var(--accent)">${d.total_users}</div><div class="label">Total Users</div></div>
        <div class="stat"><div class="num" style="color:var(--green)">${d.new_users_last_30d}</div><div class="label">New (30d)</div></div>
        <div class="stat"><div class="num" style="color:var(--purple)">${d.premium_users}</div><div class="label">Premium</div></div>
        <div class="stat"><div class="num" style="color:var(--yellow)">${d.active_users_last_30d}</div><div class="label">Active</div></div>
        <div class="stat"><div class="num">${d.avg_trades_per_active_user}</div><div class="label">Avg Trades/User</div></div>
      </div>`;
  } catch(e) {}

  // Risk Snapshot
  try {
    const r = await fetch('/api/analytics/full/risk-snapshot');
    const d = await r.json();
    if (d.message) {
      document.getElementById('risk-advice').innerHTML = `<p>${d.message}</p>`;
    } else {
      document.getElementById('risk-advice').innerHTML = `
        <p>Recent Win Rate: <strong>${d.recent_win_rate}%</strong> | Max Loss Streak: <strong style="color:var(--red)">${d.max_loss_streak}</strong></p>
        <p class="advice">${d.risk_advice}</p>`;
    }
  } catch(e) {}

  // Journal
  loadJournal(1);
}

function drawEquityChart(curve) {
  const ctx = document.getElementById('equity-chart').getContext('2d');
  if (equityChartInstance) equityChartInstance.destroy();
  equityChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: curve.map(p => p.time ? p.time.slice(5,16) : ''),
      datasets: [{
        label: 'Balance ($)',
        data: curve.map(p => p.balance),
        borderColor: '#22c55e',
        backgroundColor: 'rgba(34,197,94,0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#94a3b8' } } },
      scales: {
        x: { ticks: { color: '#64748b', maxTicksLimit: 10 }, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } }
      }
    }
  });
}

function loadJournal(page) {
  journalPage = page;
  const days = document.getElementById('analytics-period').value;
  fetch(`/api/analytics/full/journal?days=${days}&page=${page}`)
    .then(r => r.json())
    .then(data => {
      const tbody = document.querySelector('#journal-table tbody');
      tbody.innerHTML = '';
      data.trades.forEach(t => {
        const outcomeColor = t.outcome === 'win' ? 'var(--green)' : t.outcome === 'loss' ? 'var(--red)' : 'var(--yellow)';
        tbody.innerHTML += `<tr>
          <td>${t.symbol||'N/A'}</td><td>${t.direction||''}</td><td>${t.timeframe||''}</td>
          <td>${t.platform||''}</td>
          <td style="font-size:.7rem;">${t.entry_time ? new Date(t.entry_time).toLocaleString() : ''}</td>
          <td style="color:${outcomeColor}">${t.outcome}</td>
          <td>${t.confidence ? t.confidence+'%' : ''}</td>
        </tr>`;
      });
      document.getElementById('journal-page-info').textContent = `Page ${data.page} / ${data.pages || 1}`;
    });
}

// ── VIP Challenges ──────────────────────────────────────────────────
async function loadVIPChallenges() {
  try {
    const r = await fetch('/api/vip-challenge/active');
    const data = await r.json();
    if (!data.length) {
      document.getElementById('vip-challenge-list').innerHTML = '<div style="color:var(--muted)">No active VIP challenges right now.</div>';
      return;
    }
    let html = '';
    for (const c of data) {
      // Fetch leaderboard for each
      html += `<div class="vip-card">
        <h4>${c.name}</h4>
        <p style="font-size:.8rem;color:var(--muted);">${c.description || ''}</p>
        <p style="font-size:.85rem;">Prize: <strong style="color:var(--gold)">$${c.prize_pool}</strong> | Entry: $${c.entry_fee} | ${c.participants_count} players | ${c.status}</p>
        <p style="font-size:.75rem;color:var(--muted);">Ends: ${new Date(c.end).toLocaleString()}</p>
        <div style="display:flex;gap:.5rem;margin-top:.5rem;">
          <button class="btn btn-purple" onclick="joinVIP(${c.id})">Join</button>
          <button class="btn btn-primary" onclick="loadVIPLeaderboard(${c.id})">Leaderboard</button>
        </div>
        <div id="vip-lb-${c.id}" style="margin-top:.5rem;display:none;"></div>
      </div>`;
    }
    document.getElementById('vip-challenge-list').innerHTML = html;
  } catch(e) {}
}

function joinVIP(challengeId) {
  const userId = localStorage.getItem('user_id') || UID;
  fetch(`/api/vip-challenge/${challengeId}/join?user_id=${userId}`, {method:'POST'})
    .then(r => r.json())
    .then(d => {
      if (d.status === 'joined') showToast('You have joined the VIP challenge! 🏆');
      else if (d.status === 'already_joined') showToast('Already joined!');
      else showToast(d.detail || d.status, 'error');
    })
    .catch(() => showToast('Failed to join', 'error'));
}

function loadVIPLeaderboard(challengeId) {
  const el = document.getElementById(`vip-lb-${challengeId}`);
  if (el.style.display !== 'none') { el.style.display = 'none'; return; }
  fetch(`/api/vip-challenge/${challengeId}/leaderboard`)
    .then(r => r.json())
    .then(data => {
      let html = '<table class="journal-table" style="margin-top:.5rem;"><thead><tr><th>#</th><th>User</th><th>Score</th><th>W/L</th><th>WR</th></tr></thead><tbody>';
      data.leaderboard.forEach(p => {
        html += `<tr><td>${p.rank}</td><td>${p.username}</td><td>${p.score}</td><td>${p.wins}/${p.losses}</td><td>${p.win_rate}%</td></tr>`;
      });
      html += '</tbody></table>';
      if (!data.leaderboard.length) html = '<div style="color:var(--muted);font-size:.8rem;">No participants yet</div>';
      el.innerHTML = html;
      el.style.display = 'block';
    });
}

function createVIPChallenge() {
  const body = {
    name: document.getElementById('vip-name').value,
    description: document.getElementById('vip-desc').value,
    start_time: new Date(document.getElementById('vip-start').value).toISOString(),
    end_time: new Date(document.getElementById('vip-end').value).toISOString(),
    entry_fee: parseFloat(document.getElementById('vip-fee').value) || 0,
    prize_pool: parseFloat(document.getElementById('vip-prize').value) || 0
  };
  adminFetch('/api/vip-challenge/create', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  })
  .then(r => { if (!r.ok) throw new Error('Admin auth required'); return r.json(); })
  .then(d => { showToast('VIP Challenge created! ID: ' + d.challenge_id); loadVIPChallenges(); })
  .catch(e => showToast('Failed: ' + e.message, 'error'));
}

// ── Tournaments ──────────────────────────────────────────────────
async function loadTournaments() {
  try {
    const r = await fetch('/api/tournaments/list');
    const data = await r.json();
    document.getElementById('tournament-list').innerHTML = data.length ? data.map(t => `
      <div class="giveaway-card">
        <h4 style="color:var(--purple)">${t.name}</h4>
        <p style="font-size:.8rem;color:var(--muted)">${t.start_time} to ${t.end_time}</p>
        <p>Prize: $${t.prize_pool} | Entry: $${t.entry_fee} | ${t.participants} players | ${t.status}</p>
        <button class="btn btn-primary" onclick="joinTournament(${t.id})" style="margin-top:.5rem">Join</button>
      </div>`).join('') : '<div style="color:var(--muted)">No tournaments</div>';
  } catch(e) {}
}

function joinTournament(id) {
  fetch('/api/tournaments/join?tournament_id='+id+'&user_id='+UID, {method:'POST'})
    .then(r=>r.json()).then(d => { showToast(d.status === 'joined' ? 'Joined tournament!' : d.status); loadTournaments(); });
}

function createTournament() {
  const body = new URLSearchParams({
    name: document.getElementById('t-name').value,
    start: new Date(document.getElementById('t-start').value).toISOString(),
    end: new Date(document.getElementById('t-end').value).toISOString(),
    entry_fee: document.getElementById('t-fee').value || '0',
    prize_pool: document.getElementById('t-prize').value || '0',
    admin_id: UID
  });
  fetch('/api/tournaments/create', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body})
    .then(r=>r.json()).then(d => { showToast('Tournament created! ID: '+d.tournament_id); loadTournaments(); });
}

// ── Giveaways ────────────────────────────────────────────────────
async function loadGiveaways() {
  try {
    const r = await fetch('/api/giveaways/active');
    const data = await r.json();
    document.getElementById('giveaway-list').innerHTML = data.length ? data.map(g => `
      <div class="giveaway-card">
        <h4 style="color:var(--green)">${g.title}</h4>
        <p>${g.description || ''}</p>
        <p style="font-size:.85rem">Prize: <strong>${g.prize}</strong> | Ends: ${new Date(g.end_time).toLocaleString()} | ${g.participants} entries</p>
        <button class="btn btn-primary" onclick="joinGiveaway(${g.id})" style="margin-top:.5rem">Join Giveaway</button>
      </div>`).join('') : '<div style="color:var(--muted)">No active giveaways right now.</div>';
  } catch(e) {}
}

function joinGiveaway(id) {
  fetch('/api/giveaways/join/'+id+'?user_id='+UID, {method:'POST'})
    .then(r=>r.json()).then(d => { showToast(d.status === 'joined' ? 'You are in!' : d.status); loadGiveaways(); });
}

function createGiveaway() {
  const body = new URLSearchParams({
    title: document.getElementById('gw-title').value,
    description: document.getElementById('gw-desc').value,
    start_time: new Date(document.getElementById('gw-start').value).toISOString(),
    end_time: new Date(document.getElementById('gw-end').value).toISOString(),
    prize: document.getElementById('gw-prize').value,
    winners_count: document.getElementById('gw-winners').value || '1'
  });
  adminFetch('/api/giveaways/create', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body})
    .then(r => {
      if (!r.ok) throw new Error('Admin auth required');
      return r.json();
    })
    .then(d => { showToast('Giveaway created! ID: '+d.giveaway_id); loadGiveaways(); })
    .catch(e => showToast('Failed: ' + e.message, 'error'));
}

function drawGiveaway() {
  const id = document.getElementById('draw-id').value;
  if (!id) return showToast('Enter a giveaway ID', 'error');
  adminFetch('/api/giveaways/draw/'+id, {method:'POST'})
    .then(r => {
      if (!r.ok) return r.json().then(d => { throw new Error(d.detail || 'Error'); });
      return r.json();
    })
    .then(d => {
      const winners = d.winners.map(w => w.username || 'User#'+w.id).join(', ');
      showToast('Winners: ' + winners);
      loadGiveaways();
    })
    .catch(e => showToast('Draw failed: ' + e.message, 'error'));
}

// ── Referrals ────────────────────────────────────────────────────
async function loadReferrals() {
  try {
    const r = await fetch('/api/referrals/link/'+UID);
    const d = await r.json();
    document.getElementById('referral-link').textContent = d.link;
  } catch(e) {}
  try {
    const r = await fetch('/api/referrals/stats/'+UID);
    const d = await r.json();
    document.getElementById('referral-stats').innerHTML = `
      <div class="stat"><div class="num">${d.total_referrals}</div><div class="label">Total</div></div>
      <div class="stat"><div class="num" style="color:var(--green)">${d.joined}</div><div class="label">Joined</div></div>
      <div class="stat"><div class="num" style="color:var(--yellow)">${d.pending}</div><div class="label">Pending</div></div>`;
  } catch(e) {}
}

function registerReferral() {
  const body = new URLSearchParams({
    referrer_id: UID,
    name: document.getElementById('ref-name').value,
    email: document.getElementById('ref-email').value
  });
  fetch('/api/referrals/register-referral', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body})
    .then(r=>r.json()).then(d => { showToast('Referral recorded!'); loadReferrals(); });
}

// ── Community Chat (WebSocket) ──────────────────────────────────
function connectCommunity() {
  if (communityWs && communityWs.readyState === WebSocket.OPEN) return;

  const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  communityWs = new WebSocket(`${wsProtocol}//${location.host}/ws/community/${UID}`);

  communityWs.onopen = () => {
    console.log('Community chat connected');
  };

  communityWs.onmessage = (event) => {
    const data = JSON.parse(event.data);
    const chatDiv = document.getElementById('community-messages');

    if (data.type === 'history') {
      // Load history messages
      chatDiv.innerHTML = '';
      data.messages.forEach(m => {
        appendCommunityMsg(m.username, m.content, m.timestamp, false);
      });
      chatDiv.scrollTop = chatDiv.scrollHeight;
      return;
    }

    if (data.type === 'system') {
      const div = document.createElement('div');
      div.className = 'chat-msg system';
      div.innerHTML = `<div class="chat-bubble">${escapeHtml(data.text)}</div>`;
      chatDiv.appendChild(div);
    } else {
      appendCommunityMsg(data.username, data.text, data.timestamp, false);
    }
    chatDiv.scrollTop = chatDiv.scrollHeight;
  };

  communityWs.onclose = () => {
    console.log('Community chat disconnected');
    // Auto reconnect after 3s
    setTimeout(() => {
      const communityTab = document.getElementById('tab-community');
      if (communityTab && communityTab.classList.contains('active')) {
        connectCommunity();
      }
    }, 3000);
  };

  communityWs.onerror = () => {};
}

function appendCommunityMsg(username, text, timestamp, isSelf) {
  const chatDiv = document.getElementById('community-messages');
  const div = document.createElement('div');
  const time = timestamp ? new Date(timestamp).toLocaleTimeString() : '';
  div.className = 'chat-msg ' + (isSelf ? 'user' : '');
  div.innerHTML = `<div class="chat-bubble"><span class="community-user" style="color:var(--purple);">${escapeHtml(username)}</span><span style="font-size:.7rem;color:var(--muted);">${time}</span><br>${escapeHtml(text)}</div>`;
  chatDiv.appendChild(div);
}

function sendCommunityMsg() {
  const input = document.getElementById('community-input');
  const msg = input.value.trim();
  if (!msg) return;

  if (communityWs && communityWs.readyState === WebSocket.OPEN) {
    communityWs.send(JSON.stringify({message: msg}));
    input.value = '';
    // Show own message immediately
    appendCommunityMsg('You', msg, new Date().toISOString(), true);
    document.getElementById('community-messages').scrollTop = document.getElementById('community-messages').scrollHeight;
  } else {
    showToast('Community chat not connected', 'error');
  }
}

// ── Settings ─────────────────────────────────────────────────────
async function loadSettings() {
  try {
    const r = await fetch('/api/settings/'+UID);
    const d = await r.json();
    document.getElementById('set-tg-alerts').checked = d.telegram_alerts;
    document.getElementById('set-email-alerts').checked = d.email_alerts;
    document.getElementById('set-timezone').value = d.timezone;
    document.getElementById('set-risk').value = d.risk_level;
  } catch(e) {}
}

async function saveSettings() {
  const data = {
    telegram_alerts: document.getElementById('set-tg-alerts').checked,
    email_alerts: document.getElementById('set-email-alerts').checked,
    timezone: document.getElementById('set-timezone').value,
    risk_level: document.getElementById('set-risk').value
  };
  await fetch('/api/settings/'+UID, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  showToast('Settings saved!');
}

// ── AI Chat ─────────────────────────────────────────────────────
async function sendChat() {
  const input = document.getElementById('chat-input');
  const msg = input.value.trim();
  if (!msg) return;
  const chatDiv = document.getElementById('chat-messages');
  chatDiv.innerHTML += '<div class="chat-msg user"><div class="chat-bubble">' + escapeHtml(msg) + '</div></div>';
  input.value = '';
  chatDiv.scrollTop = chatDiv.scrollHeight;
  try {
    const r = await fetch('/api/chat/message', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({user_id: parseInt(UID), message: msg, source:'web'})
    });
    const d = await r.json();
    chatDiv.innerHTML += '<div class="chat-msg ai"><div class="chat-bubble">' + escapeHtml(d.reply) + '</div></div>';
  } catch(e) {
    chatDiv.innerHTML += '<div class="chat-msg ai"><div class="chat-bubble" style="color:var(--red)">Error. Try again.</div></div>';
  }
  chatDiv.scrollTop = chatDiv.scrollHeight;
}

function escapeHtml(t) { const d=document.createElement('div'); d.textContent=t; return d.innerHTML; }

// ── Init ─────────────────────────────────────────────────────────
loadSignals();

// Auto-refresh analytics every 30 seconds when on analytics tab
setInterval(() => {
  const analyticsTab = document.getElementById('tab-analytics');
  if (analyticsTab && analyticsTab.classList.contains('active')) {
    loadAnalytics();
  }
}, 30000);
</script>
</body>
</html>"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
