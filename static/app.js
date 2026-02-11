/**
 * Contact Management — app.js
 * Handles: login, stat strip, token countdown,
 *          contacts grid, tickets table (lazy load),
 *          filters, pagination, logout.
 */

const API_BASE = "http://127.0.0.1:8000";

// ── DOM refs ──────────────────────────────────────────────
const el = {
    // login
    loginForm:    document.getElementById("loginForm"),
    loginBtn:     document.getElementById("loginBtn"),
    usernameInput:document.getElementById("username"),
    passwordInput:document.getElementById("password"),
    errorDiv:     document.getElementById("error"),
    loadingDiv:   document.getElementById("loading"),

    // header
    sessionBadge: document.getElementById("sessionBadge"),
    sessionAvatar:document.getElementById("sessionAvatar"),
    sessionName:  document.getElementById("sessionName"),
    sessionDb:    document.getElementById("sessionDb"),
    logoutBtn:    document.getElementById("logoutBtn"),

    // stat strip
    statStrip:    document.getElementById("statStrip"),
    statUser:     document.getElementById("statUser"),
    statDb:       document.getElementById("statDb"),
    statContacts: document.getElementById("statContacts"),
    tokenCountdown:document.getElementById("tokenCountdown"),

    // token strip
    tokenStrip:   document.getElementById("tokenStrip"),
    displayToken: document.getElementById("displayToken"),

    // old compat
    userInfoDiv:  document.getElementById("userInfo"),
    displayUsername: document.getElementById("displayUsername"),
    displayDatabase: document.getElementById("displayDatabase"),
    displayCount:    document.getElementById("displayCount"),

    // tabs
    tabsWrapper:    document.getElementById("tabsWrapper"),
    contactTabCount:document.getElementById("contactTabCount"),
    ticketTabCount: document.getElementById("ticketTabCount"),
    contactsMeta:   document.getElementById("contactsMeta"),
    ticketsMeta:    document.getElementById("ticketsMeta"),

    // contacts
    contactsList: document.getElementById("contactsList"),
    noContacts:   document.getElementById("noContacts"),

    // tickets
    ticketsLoading:   document.getElementById("ticketsLoading"),
    ticketsTableWrap: document.getElementById("ticketsTableWrap"),
    ticketsBody:      document.getElementById("ticketsBody"),
    noTickets:        document.getElementById("noTickets"),
    ticketsPagination:document.getElementById("ticketsPagination"),
    pageInfo:         document.getElementById("pageInfo"),
    pageCurrent:      document.getElementById("pageCurrent"),

    // filters
    statusFilter: document.getElementById("statusFilter"),
    channelFilter:document.getElementById("channelFilter"),
    subjectSearch:document.getElementById("subjectSearch"),
};

// ── App state ─────────────────────────────────────────────
let state = {
    token:      null,
    username:   null,
    database:   null,
    expiresAt:  null,
    allTickets:      [],
    filteredTickets: [],
    ticketPage:      1,
    ticketsPerPage:  10,
    _timerInterval:  null,
};

// ── Lookup maps ───────────────────────────────────────────
const STATUS_MAP = {
    0: ["b-open",    "Open"],
    1: ["b-open",    "Open"],
    6: ["b-closed",  "Closed"],
    9: ["b-pending", "Pending"],
};
const CHANNEL_MAP = { 2:"Telephone", 3:"SMS", 4:"Hotline", 8:"Web" };

// ── Formatting helpers ────────────────────────────────────
function fmtDate(ts) {
    if (!ts || ts === 0 || ts === "0000-00-00 00:00:00") return "—";
    if (typeof ts === "number") {
        return new Date(ts * 1000).toLocaleDateString("en-IN", {
            day: "2-digit", month: "short", year: "2-digit"
        });
    }
    return ts;
}

function nullVal(v) {
    return (v === null || v === undefined || v === "" || v === "NULL") ? "—" : v;
}

// ── Token countdown timer ─────────────────────────────────
function startCountdown(expiresAt) {
    clearInterval(state._timerInterval);
    const el_cd = el.tokenCountdown;
    if (!el_cd) return;

    state._timerInterval = setInterval(() => {
        const diff = Math.max(0, new Date(expiresAt) - Date.now());
        const m    = Math.floor(diff / 60000);
        const s    = Math.floor((diff % 60000) / 1000);
        const str  = `${m}m ${s < 10 ? "0"+s : s}s`;

        el_cd.textContent = diff === 0 ? "Expired" : str;
        el_cd.className   = diff === 0 ? "expired" : m < 3 ? "warning" : "";

        if (diff === 0) {
            clearInterval(state._timerInterval);
            // soft warning — don't force logout, token might be valid longer
        }
    }, 1000);
}

// ── API ───────────────────────────────────────────────────
const API = {
    async login(username, password) {
        const res = await fetch(`${API_BASE}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Accept": "application/json" },
            mode: "cors",
            body: JSON.stringify({ username, password }),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }
        return res.json();
    },

    async fetchTickets(token, limit = 500) {
        const res = await fetch(`${API_BASE}/protected/tickets?limit=${limit}`, {
            headers: {
                "Authorization": `Bearer ${token}`,
                "Accept": "application/json",
            },
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }
        return res.json();
    },

    async verifyToken(token) {
        const res = await fetch(`${API_BASE}/verify-token?token=${token}`, {
            headers: { "Accept": "application/json" },
        });
        if (!res.ok) throw new Error("Invalid token");
        return res.json();
    },
};

// ── UI helpers ────────────────────────────────────────────
const UI = {
    showLoading() {
        el.errorDiv.classList.remove("show");
        el.loadingDiv.classList.add("show");
        el.loginBtn.disabled    = true;
        el.loginBtn.textContent = "Signing in…";
    },
    hideLoading() {
        el.loadingDiv.classList.remove("show");
        el.loginBtn.disabled    = false;
        el.loginBtn.textContent = "Login";
    },
    showError(msg) {
        el.errorDiv.textContent = `Error: ${msg}`;
        el.errorDiv.classList.add("show");
    },
    reset() {
        el.errorDiv.classList.remove("show");
        if (el.userInfoDiv) el.userInfoDiv.classList.remove("show");
        el.tabsWrapper.classList.remove("show");
        if (el.statStrip)  el.statStrip.classList.remove("show");
        if (el.tokenStrip) el.tokenStrip.classList.remove("show");
        if (el.sessionBadge) el.sessionBadge.classList.remove("show");
        if (el.logoutBtn)  el.logoutBtn.classList.remove("show");
        el.contactsList.innerHTML = "";
        el.ticketsBody.innerHTML  = "";
        el.noContacts.classList.remove("show");
        el.noTickets.classList.remove("show");
        el.ticketsPagination.classList.remove("show");
        el.ticketsTableWrap.classList.remove("show");
    },
};

// ── Show post-login UI ────────────────────────────────────
function showDashboard(data) {
    state.token     = data.access_token;
    state.username  = data.username;
    state.database  = data.database;
    state.expiresAt = data.expires_at;

    // ── Stat strip ──
    if (el.statStrip) {
        if (el.statUser)     el.statUser.textContent     = data.username;
        if (el.statDb)       el.statDb.textContent       = data.database;
        if (el.statContacts) el.statContacts.textContent = data.contact_count ?? (data.contacts?.length ?? 0);
        el.statStrip.classList.add("show");
    }

    // ── Token strip ──
    if (el.tokenStrip) {
        if (el.displayToken) el.displayToken.textContent = data.access_token;
        el.tokenStrip.classList.add("show");
    }

    // ── Session badge in header ──
    if (el.sessionBadge) {
        const initials = data.username.substring(0, 2).toUpperCase();
        if (el.sessionAvatar) el.sessionAvatar.textContent = initials;
        if (el.sessionName)   el.sessionName.textContent   = data.username;
        if (el.sessionDb)     el.sessionDb.textContent     = data.database;
        el.sessionBadge.classList.add("show");
    }
    if (el.logoutBtn) el.logoutBtn.classList.add("show");

    // ── Token countdown ──
    if (data.expires_at) startCountdown(data.expires_at);

    // ── Contacts ──
    showContacts(data.contacts || []);

    // ── Show tabs ──
    el.tabsWrapper.classList.add("show");

    // ── Save session ──
    try {
        sessionStorage.setItem("access_token", data.access_token);
        sessionStorage.setItem("username",     data.username);
        sessionStorage.setItem("database",     data.database);
        if (data.expires_at)
            sessionStorage.setItem("expires_at", data.expires_at);
    } catch (_) {}
}

// ── Contact card ──────────────────────────────────────────
function createContactCard(contact) {
    const div = document.createElement("div");
    div.className = "contact-card";

    const name       = [contact.f_name, contact.l_name].filter(Boolean).join(" ") || "—";
    const isActive   = contact.status == 2;
    const statusCls  = isActive ? "status-active"   : "status-inactive";
    const statusText = isActive ? "Active"           : `Status ${contact.status ?? "—"}`;

    div.innerHTML = `
        <div class="contact-header">
            <div class="contact-name">${name}</div>
            <div class="contact-status ${statusCls}">${statusText}</div>
        </div>
        <div class="contact-details">
            <div class="detail-item"><span class="detail-label">Email</span>${nullVal(contact.email)}</div>
            <div class="detail-item"><span class="detail-label">Phone</span>${nullVal(contact.phonefax)}</div>
            <div class="detail-item"><span class="detail-label">Created</span>${nullVal(contact.creation_date)}</div>
            <div class="detail-item"><span class="detail-label">ID</span>${nullVal(contact.id)}</div>
        </div>`;
    return div;
}

function showContacts(contacts) {
    el.contactsList.innerHTML = "";
    el.noContacts.classList.remove("show");

    const count = contacts?.length ?? 0;
    if (el.contactTabCount)  el.contactTabCount.textContent  = count;
    if (el.contactsMeta)     el.contactsMeta.textContent     = `${count} total`;

    if (!count) {
        el.noContacts.classList.add("show");
        return;
    }
    contacts.forEach(c => el.contactsList.appendChild(createContactCard(c)));
}

// ── Ticket rendering ──────────────────────────────────────
function renderTicketsPage() {
    const { filteredTickets, ticketPage, ticketsPerPage } = state;
    const start = (ticketPage - 1) * ticketsPerPage;
    const page  = filteredTickets.slice(start, start + ticketsPerPage);
    const total = filteredTickets.length;

    el.ticketsBody.innerHTML = "";
    el.noTickets.classList.remove("show");
    el.ticketsTableWrap.classList.remove("show");
    el.ticketsPagination.classList.remove("show");

    if (el.ticketTabCount) el.ticketTabCount.textContent = total;

    if (total === 0) {
        el.noTickets.classList.add("show");
        return;
    }

    const fragment = document.createDocumentFragment();
    page.forEach(t => {
        const [badgeCls, badgeLabel] = STATUS_MAP[t.status_id] || ["b-unknown", `#${t.status_id}`];
        const channel = CHANNEL_MAP[t.channel_id] || `Ch.${t.channel_id ?? "—"}`;
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><span class="ticket-id">#${t.ticket_id}</span></td>
            <td class="subject-cell" title="${(t.subject || "").replace(/"/g,"&quot;")}">${nullVal(t.subject)}</td>
            <td><span class="badge ${badgeCls}">${badgeLabel}</span></td>
            <td class="muted-cell">${nullVal(t.category_id)}</td>
            <td><span class="channel-tag">${channel}</span></td>
            <td class="contact-name-cell">${t.l_name ? t.l_name : `<span style="color:var(--muted)">ID #${t.customer_id}</span>`}</td>
            <td class="mono-cell">${nullVal(t.phonefax)}</td>
            <td class="mono-cell">${nullVal(t.email)}</td>
            <td class="date-cell">${fmtDate(t.cr_date)}</td>
            <td class="date-cell">${fmtDate(t.updt_date)}</td>`;
        fragment.appendChild(tr);
    });
    el.ticketsBody.appendChild(fragment);

    el.ticketsTableWrap.classList.add("show");
    el.ticketsPagination.classList.add("show");

    const end = Math.min(start + ticketsPerPage, total);
    el.pageInfo.textContent    = `Showing ${start + 1}–${end} of ${total}`;
    el.pageCurrent.textContent = `Page ${ticketPage} of ${Math.ceil(total / ticketsPerPage)}`;

    // disable prev/next buttons at edges
    const prevBtn = document.querySelector(".page-btn:first-of-type");
    const nextBtn = document.querySelector(".page-btn:last-of-type");
    if (prevBtn) prevBtn.disabled = ticketPage <= 1;
    if (nextBtn) nextBtn.disabled = ticketPage >= Math.ceil(total / ticketsPerPage);
}

// ── Load tickets (lazy) ───────────────────────────────────
async function loadTickets() {
    if (!state.token) return;

    el.ticketsLoading.classList.add("show");
    el.ticketsTableWrap.classList.remove("show");
    el.noTickets.classList.remove("show");
    el.ticketsPagination.classList.remove("show");

    try {
        const data = await API.fetchTickets(state.token, 500);
        state.allTickets      = data.tickets || [];
        state.filteredTickets = [...state.allTickets];
        state.ticketPage      = 1;

        const total = state.allTickets.length;
        if (el.ticketsMeta)
            el.ticketsMeta.textContent = `${total} total · joined on customer_id = contact.id`;

    } catch (err) {
        console.error("Tickets fetch error:", err);
        if (el.ticketsMeta)
            el.ticketsMeta.textContent = "Failed to load — " + err.message;
        state.allTickets = state.filteredTickets = [];
    } finally {
        el.ticketsLoading.classList.remove("show");
        renderTicketsPage();
    }
}

// ── Tab switching ─────────────────────────────────────────
window.switchTab = function(name) {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));

    const cap = name.charAt(0).toUpperCase() + name.slice(1);
    const tabEl   = document.getElementById("tab"   + cap);
    const panelEl = document.getElementById("panel" + cap);
    if (tabEl)   tabEl.classList.add("active");
    if (panelEl) panelEl.classList.add("active");

    if (name === "tickets" && state.allTickets.length === 0 && state.token) {
        loadTickets();
    }
};

// ── Ticket filters ────────────────────────────────────────
window.applyTicketFilter = function() {
    const status  = el.statusFilter?.value  ?? "";
    const channel = el.channelFilter?.value ?? "";
    const subject = (el.subjectSearch?.value ?? "").toLowerCase().trim();

    state.filteredTickets = state.allTickets.filter(t => {
        const okStatus  = !status  || String(t.status_id)  === status;
        const okChannel = !channel || String(t.channel_id) === channel;
        const okSubject = !subject || (t.subject || "").toLowerCase().includes(subject);
        return okStatus && okChannel && okSubject;
    });
    state.ticketPage = 1;
    renderTicketsPage();
};

// ── Pagination ────────────────────────────────────────────
window.changePage = function(dir) {
    const maxPage = Math.ceil(state.filteredTickets.length / state.ticketsPerPage);
    state.ticketPage = Math.max(1, Math.min(maxPage, state.ticketPage + dir));
    renderTicketsPage();
};

// ── Login ─────────────────────────────────────────────────
async function handleLogin(e) {
    e.preventDefault();
    UI.reset();
    UI.showLoading();

    // clear previous session
    try { sessionStorage.clear(); } catch (_) {}
    clearInterval(state._timerInterval);
    state = {
        ...state,
        token: null, username: null, database: null, expiresAt: null,
        allTickets: [], filteredTickets: [], ticketPage: 1,
    };

    try {
        const username = el.usernameInput.value.trim();
        const password = el.passwordInput.value;

        const data = await API.login(username, password);
        console.log(`✓ Login: ${data.username} → ${data.database} (${data.contact_count} contacts)`);

        UI.hideLoading();
        showDashboard(data);

    } catch (err) {
        console.error("Login error:", err);
        UI.hideLoading();
        UI.showError(err.message);
    }
}

// ── Logout ────────────────────────────────────────────────
function handleLogout() {
    clearInterval(state._timerInterval);
    try { sessionStorage.clear(); } catch (_) {}

    state = {
        token: null, username: null, database: null, expiresAt: null,
        allTickets: [], filteredTickets: [],
        ticketPage: 1, ticketsPerPage: 10, _timerInterval: null,
    };

    UI.reset();
    el.passwordInput.value = "";

    // reset tab to contacts
    window.switchTab("contacts");
}

// ── Init ──────────────────────────────────────────────────
function init() {
    el.loginForm.addEventListener("submit", handleLogin);
    if (el.logoutBtn) el.logoutBtn.addEventListener("click", handleLogout);

    // restore username from session if token still valid
    const savedToken = sessionStorage.getItem("access_token");
    if (savedToken) {
        API.verifyToken(savedToken)
            .then(info => {
                el.usernameInput.value = info.username
                    || sessionStorage.getItem("username")
                    || el.usernameInput.value;
            })
            .catch(() => {
                try { sessionStorage.clear(); } catch (_) {}
            });
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}