import streamlit as st


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

        :root {
            --bg: #0a0f1a;
            --bg-soft: #0d1420;
            --surface: #121a2b;
            --surface-2: #182339;
            --border: #253048;
            --text: #eef2f8;
            --text-muted: #8894a8;
            --text-faint: #56617a;
            --accent: #5eead4;
            --accent-strong: #2dd4bf;
            --accent-soft: rgba(94, 234, 212, 0.12);
            --ok: #34d399;
            --ok-soft: rgba(52, 211, 153, 0.14);
            --warn: #fbbf24;
            --warn-soft: rgba(251, 191, 36, 0.14);
            --danger: #fb7185;
            --danger-soft: rgba(251, 113, 133, 0.14);
            --font-display: 'Space Grotesk', sans-serif;
            --font-body: 'Inter', sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }

        html, body, [class*="css"] { font-family: var(--font-body); }

        .stApp {
            background:
                radial-gradient(circle at 12% -10%, rgba(94, 234, 212, 0.07) 0%, transparent 45%),
                radial-gradient(circle at 100% 0%, rgba(94, 234, 212, 0.04) 0%, transparent 40%),
                var(--bg);
            color: var(--text);
        }

        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 3rem;
            max-width: 1360px;
        }

        h1, h2, h3, h4 { font-family: var(--font-display) !important; letter-spacing: -0.01em; }

        /* ---------- Sidebar ---------- */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0d1524 0%, #0a0f1a 100%);
            border-right: 1px solid var(--border);
        }
        section[data-testid="stSidebar"] * { color: var(--text); }
        section[data-testid="stSidebar"] .block-container { padding-top: 1.2rem; }

        .brand-block {
            padding: 0.2rem 0.1rem 1.1rem 0.1rem;
            border-bottom: 1px solid var(--border);
            margin-bottom: 1.1rem;
        }
        .brand-mark {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-family: var(--font-mono);
            font-size: 0.72rem;
            letter-spacing: 0.14em;
            color: var(--accent);
            text-transform: uppercase;
            margin-bottom: 0.55rem;
        }
        .brand-dot {
            width: 7px; height: 7px; border-radius: 50%;
            background: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-soft);
            animation: pulse-dot 2.4s ease-in-out infinite;
        }
        .brand-title {
            font-family: var(--font-display);
            font-weight: 700;
            font-size: 1.1rem;
            line-height: 1.25;
            color: var(--text);
        }
        .brand-subtitle {
            font-size: 0.82rem;
            color: var(--text-muted);
            margin-top: 0.3rem;
        }

        .nav-eyebrow {
            font-family: var(--font-mono);
            font-size: 0.68rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--text-faint);
            margin: 0.2rem 0 0.5rem 0.1rem;
        }

        section[data-testid="stSidebar"] div[data-testid="stPageLink"] {
            border-radius: 10px;
            margin-bottom: 0.15rem;
            transition: background 0.15s ease;
        }
        section[data-testid="stSidebar"] div[data-testid="stPageLink"]:hover {
            background: var(--surface-2);
        }
        section[data-testid="stSidebar"] div[data-testid="stPageLink"] p {
            font-size: 0.92rem !important;
            font-weight: 500;
        }

        /* Trace rail: signature element showing the request pipeline */
        .trace-rail { position: relative; padding-left: 1.4rem; margin-top: 0.3rem; }
        .trace-rail::before {
            content: "";
            position: absolute;
            left: 5px; top: 6px; bottom: 6px;
            width: 2px;
            background: linear-gradient(180deg, var(--accent) 0%, var(--border) 85%);
            opacity: 0.55;
        }
        .trace-node { position: relative; padding: 0.32rem 0 0.32rem 0.65rem; }
        .trace-node::before {
            content: "";
            position: absolute;
            left: -1.4rem; top: 50%; transform: translateY(-50%);
            width: 8px; height: 8px; border-radius: 50%;
            background: var(--bg-soft);
            border: 2px solid var(--accent);
            z-index: 1;
        }
        .trace-node span {
            font-family: var(--font-mono);
            font-size: 0.76rem;
            color: var(--text-muted);
        }
        .trace-node:first-child span, .trace-node:last-child span { color: var(--text); font-weight: 600; }
        .trace-node:last-child::before {
            background: var(--accent);
            box-shadow: 0 0 0 4px var(--accent-soft);
            animation: pulse-dot 2.4s ease-in-out infinite;
        }

        @keyframes pulse-dot {
            0%, 100% { box-shadow: 0 0 0 3px var(--accent-soft); }
            50% { box-shadow: 0 0 0 6px transparent; }
        }

        /* ---------- Top nav (header) ---------- */
        .top-nav-bar {
            display: flex;
            gap: 0.4rem;
            flex-wrap: wrap;
            margin-bottom: 1.1rem;
            padding: 0.4rem;
            border: 1px solid var(--border);
            border-radius: 14px;
            background: var(--surface);
        }
        .top-nav-bar a { color: var(--text-muted) !important; text-decoration: none; font-weight: 500; font-size: 0.9rem; }
        .top-nav-bar div[data-testid="stPageLink"] { border-radius: 10px; }
        .top-nav-bar div[data-testid="stPageLink"]:hover { background: var(--surface-2); }

        /* ---------- Hero header ---------- */
        .hero-card {
            background: linear-gradient(120deg, rgba(94, 234, 212, 0.10) 0%, var(--surface) 55%);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 1.4rem 1.6rem;
            color: var(--text);
            margin-bottom: 1.3rem;
        }
        .hero-card h2 {
            margin: 0 0 0.3rem 0;
            font-size: 1.5rem;
            color: var(--text);
        }
        .hero-card p { margin: 0; color: var(--text-muted); font-size: 0.94rem; }
        .pill {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.38rem 0.75rem;
            border-radius: 999px;
            background: var(--accent-soft);
            border: 1px solid rgba(94, 234, 212, 0.35);
            color: var(--accent);
            font-family: var(--font-mono);
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            white-space: nowrap;
        }
        .pill-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); }

        /* ---------- Generic cards ---------- */
        .panel-card {
            background: var(--surface);
            color: var(--text);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1rem 1.15rem;
            margin-bottom: 1rem;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            border-color: var(--border) !important;
            background: var(--surface);
            border-radius: 16px !important;
        }

        /* Status chip system, used across pages */
        .status-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.28rem 0.65rem;
            border-radius: 999px;
            font-family: var(--font-mono);
            font-size: 0.74rem;
            font-weight: 600;
            letter-spacing: 0.03em;
        }
        .status-chip.ok { background: var(--ok-soft); color: var(--ok); }
        .status-chip.warn { background: var(--warn-soft); color: var(--warn); }
        .status-chip.danger { background: var(--danger-soft); color: var(--danger); }
        .status-chip.neutral { background: var(--surface-2); color: var(--text-muted); }
        .status-chip .dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

        /* ---------- Metrics ---------- */
        div[data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 0.75rem 0.9rem;
        }
        div[data-testid="stMetricLabel"] p {
            font-family: var(--font-mono) !important;
            font-size: 0.72rem !important;
            font-weight: 500 !important;
            color: var(--text-faint) !important;
            text-transform: uppercase !important;
            letter-spacing: 0.08em !important;
        }
        div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] > div {
            font-family: var(--font-display) !important;
            font-size: 1.25rem !important;
            font-weight: 600 !important;
            color: var(--text) !important;
            word-wrap: break-word !important;
        }

        /* ---------- Chat ---------- */
        div[data-testid="stChatMessage"] {
            background: transparent !important;
            padding: 0 !important;
            gap: 0.6rem;
        }
        .chat-bubble {
            border-radius: 14px;
            padding: 0.7rem 0.95rem;
            border: 1px solid var(--border);
            font-size: 0.94rem;
            line-height: 1.5;
        }
        .chat-bubble.user {
            background: var(--accent-soft);
            border-color: rgba(94, 234, 212, 0.3);
        }
        .chat-bubble.assistant {
            background: var(--surface-2);
        }
        .chat-role-label {
            font-family: var(--font-mono);
            font-size: 0.68rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--text-faint);
            margin-bottom: 0.3rem;
        }

        /* ---------- Data / mono text ---------- */
        .mono { font-family: var(--font-mono); }
        .kv-row {
            display: flex; justify-content: space-between; align-items: center;
            padding: 0.45rem 0; border-bottom: 1px dashed var(--border);
            font-size: 0.86rem;
        }
        .kv-row:last-child { border-bottom: none; }
        .kv-label { color: var(--text-muted); }
        .kv-value { font-family: var(--font-mono); color: var(--text); font-weight: 500; }

        /* ---------- Buttons & inputs ---------- */
        .stButton > button {
            border-radius: 10px;
            padding: 0.5rem 1.1rem;
            font-weight: 600;
            border: 1px solid var(--border);
        }
        .stButton > button[kind="primary"] {
            background: var(--accent);
            color: #06231f;
            border: none;
        }
        .stButton > button[kind="primary"]:hover { background: var(--accent-strong); }
        .stTextInput > div > div > input,
        .stTextArea > div > textarea {
            border-radius: 10px;
            border: 1px solid var(--border);
            color: var(--text);
            background: var(--surface-2);
        }
        .stTextInput > div > div > input:focus,
        .stTextArea > div > textarea:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 1px var(--accent);
        }
        div[data-testid="stForm"] {
            border: 1px solid var(--border);
            border-radius: 16px;
            background: var(--surface);
        }

        hr, div[data-testid="stDivider"] { border-color: var(--border) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str, badge: str | None = None) -> None:
    badge_html = (
        f'<span class="pill"><span class="pill-dot"></span>{badge}</span>'
        if badge
        else ""
    )
    st.markdown(
        f"""
        <div class="hero-card">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:1rem; flex-wrap:wrap;">
                <div>
                    <h2>{title}</h2>
                    <p>{subtitle}</p>
                </div>
                {badge_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_chip(label: str, tone: str = "neutral") -> str:
    """Return HTML for a small status chip. tone: ok | warn | danger | neutral"""
    return f'<span class="status-chip {tone}"><span class="dot"></span>{label}</span>'
