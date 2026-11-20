from datetime import datetime
from pathlib import Path
import logging
import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st

from src.config import get_settings, Settings
from src.loader import load_contacts, load_reminders, load_template
from src.personalizer import render_message
from src.scheduler import is_reminder_due
from src.mailer import send_email
from src.reporter import save_report

# ---------------------------------------------------------------------------
# Page Setup & Multi-Color Theme
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Email Automation & Reminder Studio",
    page_icon="🌈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 45%, #3b0764 100%);
        color: #f8fafc;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e1b4b 0%, #312e81 55%, #0f172a 100%);
        border-right: 1px solid rgba(168, 85, 247, 0.35);
    }
    .centered-shell {
        max-width: 1220px;
        margin: 0 auto;
    }
    .hero-rainbow {
        background: linear-gradient(90deg, #f97316 0%, #ec4899 35%, #8b5cf6 70%, #06b6d4 100%);
        padding: 24px 30px;
        border-radius: 18px;
        color: #ffffff;
        text-align: center;
        box-shadow: 0 12px 30px rgba(139, 92, 246, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.25);
        margin-bottom: 18px;
    }
    .hero-rainbow h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
    }
    .hero-rainbow p {
        margin: 6px 0 0 0;
        font-size: 0.98rem;
        color: #fdf4ff;
    }
    .color-kpi {
        border-radius: 16px;
        padding: 18px 20px;
        color: #ffffff;
        text-align: center;
        box-shadow: 0 8px 22px rgba(0, 0, 0, 0.28);
        border: 1px solid rgba(255, 255, 255, 0.22);
        transition: transform 0.2s ease;
    }
    .color-kpi:hover {
        transform: translateY(-3px);
    }
    .kpi-coral  { background: linear-gradient(135deg, #f97316 0%, #e11d48 100%); }
    .kpi-cyan   { background: linear-gradient(135deg, #06b6d4 0%, #2563eb 100%); }
    .kpi-violet { background: linear-gradient(135deg, #8b5cf6 0%, #c026d3 100%); }
    .kpi-emerald{ background: linear-gradient(135deg, #10b981 0%, #0d9488 100%); }

    .kpi-lbl {
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        opacity: 0.95;
    }
    .kpi-num {
        font-size: 2rem;
        font-weight: 800;
        margin: 6px 0;
    }
    .kpi-tag {
        display: inline-block;
        background: rgba(255, 255, 255, 0.22);
        padding: 3px 12px;
        border-radius: 999px;
        font-size: 0.78rem;
    }
    .section-title-center {
        text-align: center;
        font-size: 1.35rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #f472b6, #facc15, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 20px 0 12px 0;
    }
    .center-preview-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.95), rgba(49, 46, 129, 0.85));
        border: 1px solid rgba(244, 114, 182, 0.45);
        border-radius: 16px;
        padding: 20px;
        color: #f8fafc;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.3);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def ensure_file_logger(log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not any(isinstance(h, logging.FileHandler) for h in root.handlers):
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root.addHandler(fh)


def load_all_reports(output_dir: Path) -> pd.DataFrame:
    if not output_dir.exists():
        return pd.DataFrame()
    files = sorted(output_dir.glob("delivery_report_*.csv"), reverse=True)
    if not files:
        return pd.DataFrame()
    frames = []
    for f in files:
        try:
            df = pd.read_csv(f, dtype=str).fillna("")
            df["report_file"] = f.name
            frames.append(df)
        except Exception:
            continue
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def run_dispatch_batch(
    settings: Settings,
    contacts_df: pd.DataFrame,
    reminders_df: pd.DataFrame,
    subject_tmpl: str,
    body_tmpl: str,
    dry_run: bool,
    send_all: bool,
) -> tuple[pd.DataFrame, Path | None]:
    contacts_map = contacts_df.set_index("contact_id").to_dict(orient="index")
    now = datetime.now()
    records: list[dict] = []

    for _, rem in reminders_df.iterrows():
        rem_id = rem["reminder_id"]
        contact_id = rem["contact_id"]
        due_dt = rem["due_dt"]
        freq = rem["frequency"]

        if not is_reminder_due(due_dt, freq, now, send_all=send_all):
            continue

        contact = contacts_map.get(contact_id)
        if not contact:
            err_msg = f"Unknown contact_id '{contact_id}'"
            logging.error("[FAILED] Reminder %s -> %s", rem_id, err_msg)
            records.append(
                {
                    "timestamp": now.isoformat(timespec="seconds"),
                    "reminder_id": rem_id,
                    "contact_id": contact_id,
                    "recipient_name": "",
                    "recipient_email": "",
                    "subject": rem["reminder_title"],
                    "status": "FAILED",
                    "detail": err_msg,
                }
            )
            continue

        context = {
            "name": contact.get("name", ""),
            "email": contact.get("email", ""),
            "role": contact.get("role", ""),
            "reminder_title": rem.get("reminder_title", ""),
            "due_at": rem.get("due_at", ""),
            "frequency": freq,
            "notes": rem.get("notes", ""),
            "sender_name": settings.sender_name,
        }

        subject, body, _ = render_message(subject_tmpl, body_tmpl, context)
        status, detail = send_email(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_user=settings.smtp_user,
            smtp_pass=settings.smtp_pass,
            sender_name=settings.sender_name,
            sender_email=settings.sender_email,
            recipient_email=contact.get("email", ""),
            subject=subject,
            body=body,
            dry_run=dry_run,
        )

        records.append(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "reminder_id": rem_id,
                "contact_id": contact_id,
                "recipient_name": contact.get("name", ""),
                "recipient_email": contact.get("email", ""),
                "subject": subject,
                "status": status,
                "detail": detail,
            }
        )

    if not records:
        return pd.DataFrame(), None

    report_path = save_report(records, settings.output_dir)
    return pd.DataFrame(records), report_path


# ---------------------------------------------------------------------------
# Load Data
# ---------------------------------------------------------------------------
settings = get_settings()
ensure_file_logger(settings.log_file)

try:
    contacts_df = load_contacts(settings.contacts_csv)
    reminders_df = load_reminders(settings.reminders_csv)
    subject_tmpl, body_tmpl = load_template(settings.template_file)
except Exception as exc:
    st.error(f"Error loading files: {exc}")
    st.stop()

history_df = load_all_reports(settings.output_dir)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🎨 Studio Controls")
    dry_run_mode = st.toggle(
        "🧪 Safe Dry-Run Mode",
        value=settings.dry_run,
        help="Simulate sends safely without connecting to an external SMTP server.",
    )
    st.markdown(
        f"**Active Mode:** `{'DRY-RUN SIMULATION' if dry_run_mode else 'LIVE SMTP'}`\n\n"
        f"**SMTP Host:** `{settings.smtp_host}:{settings.smtp_port}`\n\n"
        f"**Sender:** `{settings.sender_email or 'Not set'}`"
    )
    if st.button("🔄 Reload Dashboard", use_container_width=True):
        st.rerun()

# ---------------------------------------------------------------------------
# Centered Hero + Multi-Color KPIs
# ---------------------------------------------------------------------------
st.markdown('<div class="centered-shell">', unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="hero-rainbow">
        <h1>🌈 Email Automation & Reminder Studio</h1>
        <p>Multi-Color Campaign Control • Live Template Preview • Delivery Analytics & Contact Map • Mode: <strong>{'DRY-RUN' if dry_run_mode else 'LIVE SMTP'}</strong></p>
    </div>
    """,
    unsafe_allow_html=True,
)

total_contacts = len(contacts_df)
total_reminders = len(reminders_df)
total_runs = len(history_df)
ok_rate = (
    f"{(history_df['status'].isin(['SENT', 'DRY_RUN']).sum() / total_runs) * 100:.0f}%"
    if total_runs > 0
    else "—"
)

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(
        f'<div class="color-kpi kpi-coral"><div class="kpi-lbl">👥 Contacts</div><div class="kpi-num">{total_contacts}</div><div class="kpi-tag">CSV Recipients</div></div>',
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        f'<div class="color-kpi kpi-cyan"><div class="kpi-lbl">⏰ Reminders</div><div class="kpi-num">{total_reminders}</div><div class="kpi-tag">Scheduled Rules</div></div>',
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        f'<div class="color-kpi kpi-violet"><div class="kpi-lbl">📨 Dispatches</div><div class="kpi-num">{total_runs}</div><div class="kpi-tag">Report Rows</div></div>',
        unsafe_allow_html=True,
    )
with k4:
    st.markdown(
        f'<div class="color-kpi kpi-emerald"><div class="kpi-lbl">✨ Success Rate</div><div class="kpi-num">{ok_rate}</div><div class="kpi-tag">SENT / DRY_RUN</div></div>',
        unsafe_allow_html=True,
    )

st.markdown('<div class="section-title-center">⚡ Quick Batch Action & Output Center</div>', unsafe_allow_html=True)
b1, b2, b3 = st.columns([1, 1.4, 1])
with b2:
    col_a, col_b = st.columns(2)
    run_now = col_a.button("🚀 Run All Now", type="primary", use_container_width=True)
    run_due = col_b.button("🕒 Run Due Only", use_container_width=True)

if run_now or run_due:
    res_df, r_path = run_dispatch_batch(
        settings=settings,
        contacts_df=contacts_df,
        reminders_df=reminders_df,
        subject_tmpl=subject_tmpl,
        body_tmpl=body_tmpl,
        dry_run=dry_run_mode,
        send_all=run_now,
    )
    if res_df.empty:
        st.info("No reminders due at this exact timestamp. Click **Run All Now** to test all rows.")
    else:
        st.success(f"Completed **{len(res_df)}** reminder(s) → Saved `{r_path.name}`")
        st.dataframe(res_df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Centered Tabs: Charts + Map, Data Editors, Template Preview, Logs
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["🗺️ Map & Charts", "📝 Contacts & Reminders", "✉️ Template Studio", "📜 Logs & CSVs"]
)

with tab1:
    st.markdown('<div class="section-title-center">📊 Multi-Color Charts & Recipient Location Map</div>', unsafe_allow_html=True)
    c_left, c_right = st.columns(2)

    with c_left:
        if not reminders_df.empty:
            freq_df = reminders_df["frequency"].value_counts().reset_index()
            freq_df.columns = ["Frequency", "Count"]
            fig_bar = px.bar(
                freq_df,
                x="Frequency",
                y="Count",
                color="Frequency",
                title="Reminders by Frequency",
                color_discrete_sequence=["#f97316", "#06b6d4", "#ec4899", "#10b981"],
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(15,23,42,0.5)",
                plot_bgcolor="rgba(15,23,42,0.3)",
                font_color="#f8fafc",
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    with c_right:
        if not history_df.empty:
            st_df = history_df["status"].value_counts().reset_index()
            st_df.columns = ["Status", "Count"]
            fig_pie = px.pie(
                st_df,
                names="Status",
                values="Count",
                hole=0.45,
                title="Dispatch Status Distribution",
                color="Status",
                color_discrete_map={"SENT": "#10b981", "DRY_RUN": "#38bdf8", "FAILED": "#f43f5e"},
            )
            fig_pie.update_layout(
                paper_bgcolor="rgba(15,23,42,0.5)",
                font_color="#f8fafc",
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Run a batch above to populate the Dispatch Status chart.")

    # Colorful Pydeck Map for Contacts with lat/lon
    if {"lat", "lon"}.issubset(contacts_df.columns):
        map_df = contacts_df.copy()
        map_df["lat_num"] = pd.to_numeric(map_df["lat"], errors="coerce")
        map_df["lon_num"] = pd.to_numeric(map_df["lon"], errors="coerce")
        map_df = map_df.dropna(subset=["lat_num", "lon_num"])

        if not map_df.empty:
            palette = [
                [249, 115, 22, 230],
                [6, 182, 212, 230],
                [236, 72, 153, 230],
                [16, 185, 129, 230],
            ]
            map_df["fill_color"] = [palette[i % len(palette)] for i in range(len(map_df))]

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_df,
                get_position="[lon_num, lat_num]",
                get_fill_color="fill_color",
                get_line_color=[255, 255, 255, 255],
                line_width_min_pixels=3,
                stroked=True,
                get_radius=45000,
                pickable=True,
            )
            view = pdk.ViewState(
                latitude=float(map_df["lat_num"].mean()),
                longitude=float(map_df["lon_num"].mean()),
                zoom=4.2,
                pitch=25,
            )
            deck = pdk.Deck(
                map_style="https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
                initial_view_state=view,
                layers=[layer],
                tooltip={"text": "👤 {name} ({role})\n📍 {city}\n✉️ {email}"},
            )
            st.pydeck_chart(deck, use_container_width=True)

with tab2:
    st.markdown('<div class="section-title-center">📝 Edit Contacts & Reminders</div>', unsafe_allow_html=True)
    ed1, ed2 = st.columns(2)
    with ed1:
        st.markdown("**Contacts (`data/contacts.csv`)**")
        new_c = st.data_editor(contacts_df, num_rows="dynamic", use_container_width=True, key="ed_c")
        if st.button("💾 Save Contacts", use_container_width=True):
            new_c.to_csv(settings.contacts_csv, index=False, encoding="utf-8")
            st.success("Saved `data/contacts.csv`")
            st.rerun()
    with ed2:
        st.markdown("**Reminders (`data/reminders.csv`)**")
        new_r = st.data_editor(
            reminders_df.drop(columns=["due_dt"], errors="ignore"),
            num_rows="dynamic",
            use_container_width=True,
            key="ed_r",
        )
        if st.button("💾 Save Reminders", use_container_width=True):
            new_r.to_csv(settings.reminders_csv, index=False, encoding="utf-8")
            st.success("Saved `data/reminders.csv`")
            st.rerun()

with tab3:
    st.markdown('<div class="section-title-center">✉️ Live Centered Message Preview</div>', unsafe_allow_html=True)
    p_col1, p_col2 = st.columns(2)
    with p_col1:
        edit_subj = st.text_input("Subject", value=subject_tmpl)
        edit_body = st.text_area("Body", value=body_tmpl, height=220)
        if st.button("💾 Save Template"):
            settings.template_file.write_text(f"Subject: {edit_subj.strip()}\n{edit_body.strip()}\n", encoding="utf-8")
            st.success("Template saved!")
            st.rerun()
    with p_col2:
        if not reminders_df.empty:
            pick_id = st.selectbox("Preview Reminder", reminders_df["reminder_id"].tolist())
            r_sel = reminders_df[reminders_df["reminder_id"] == pick_id].iloc[0]
            c_match = contacts_df[contacts_df["contact_id"] == r_sel["contact_id"]]
            c_info = c_match.iloc[0].to_dict() if not c_match.empty else {"name": "Recipient", "email": "test@example.com", "role": ""}
            ctx = {
                "name": c_info.get("name", ""),
                "email": c_info.get("email", ""),
                "role": c_info.get("role", ""),
                "reminder_title": r_sel.get("reminder_title", ""),
                "due_at": r_sel.get("due_at", ""),
                "frequency": r_sel.get("frequency", ""),
                "notes": r_sel.get("notes", ""),
                "sender_name": settings.sender_name,
            }
            r_subj, r_body, _ = render_message(edit_subj, edit_body, ctx)
            st.markdown(
                f"""
                <div class="center-preview-card">
                    <div><strong>To:</strong> {c_info.get('name')} &lt;{c_info.get('email')}&gt;</div>
                    <div style="font-size:1.1rem;font-weight:700;color:#f472b6;margin:8px 0;">{r_subj}</div>
                    <hr style="border-color:rgba(255,255,255,0.18);">
                    <pre style="white-space:pre-wrap;font-family:inherit;margin:0;color:#e2e8f0;">{r_body}</pre>
                </div>
                """,
                unsafe_allow_html=True,
            )

with tab4:
    st.markdown('<div class="section-title-center">📜 Delivery Reports & Execution Logs</div>', unsafe_allow_html=True)
    if not history_df.empty:
        st.dataframe(history_df, use_container_width=True, hide_index=True)
    if settings.log_file.exists():
        st.code("\n".join(settings.log_file.read_text(encoding="utf-8").splitlines()[-60:]), language="log")

st.markdown("</div>", unsafe_allow_html=True)