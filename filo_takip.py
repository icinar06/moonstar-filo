import glob
import os
import re
import shutil
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="MOONSTAR EXPRESS LLC — Enterprise TMS",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# MOONSTAR CORPORATE COLOR PALETTE (Navy #0b1f3a, Sky Blue #0284c7, Ice Blue #38bdf8)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #f1f5f9 !important;
        color: #0f172a;
    }
    
    .moonstar-nav {
        background: linear-gradient(90deg, #0b1f3a 0%, #0f2c59 60%, #0284c7 100%);
        padding: 16px 24px;
        border-radius: 8px;
        color: #ffffff;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 14px rgba(11, 31, 58, 0.15);
        border-bottom: 3px solid #38bdf8;
    }
    .brand-text {
        font-family: 'Montserrat', sans-serif;
        font-size: 24px;
        font-weight: 900;
        letter-spacing: 0.5px;
        color: #ffffff;
        margin: 0;
    }
    .brand-sub {
        font-size: 12px;
        color: #bae6fd;
        margin-top: 2px;
        font-weight: 500;
    }
    
    .kpi-card {
        background: #ffffff;
        border-radius: 8px;
        padding: 16px 18px;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #0284c7;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 12px;
    }
    .kpi-card-alert {
        border-left: 5px solid #ef4444 !important;
    }
    .kpi-card-warn {
        border-left: 5px solid #f59e0b !important;
    }
    .kpi-label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b;
    }
    .kpi-val {
        font-family: 'Montserrat', sans-serif;
        font-size: 22px;
        font-weight: 800;
        color: #0b1f3a;
        margin-top: 4px;
    }
    
    .dossier-box {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
    }
</style>
""", unsafe_allow_html=True)

DB_FILE = "fleet_database.db"
UPLOAD_DIR = "arsiv_dosyalari"
DRIVERS_FILE = "Drivers.xlsx"
FLEET_EXCEL = "Başlıksız e-tablo (2) copy 2.xlsx"
SERVICE_LOGS_CSV = "Service logs.csv"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- CORPORATE LOGIN ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if os.path.exists("logo.jpg"):
            st.image("logo.jpg", width=240)
        st.markdown("### 🔒 MOONSTAR EXPRESS LLC — TMS PORTAL")
        with st.form("login_form"):
            email = st.text_input("Corporate Email", placeholder="ismail@moonstarpa.com")
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                if "@moonstarpa" in email.strip().lower() and pwd == "Moonstar2026!":
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = email.strip().lower()
                    st.rerun()
                else:
                    st.error("Invalid corporate email or password!")
    st.stop()

# ---------------------------------------------
def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def check_date_status(date_str):
    if not date_str or str(date_str).strip() in ["0000-00-00", "nan", "None", "-", ""]:
        return "No Date", "⚪", 999
    try:
        dt = datetime.strptime(str(date_str).strip()[:10], "%Y-%m-%d").date()
        diff = (dt - datetime.now().date()).days
        if diff < 0:
            return f"Expired ({abs(diff)}d ago)", "🔴", diff
        elif diff <= 30:
            return f"Critical ({diff}d left)", "🟡", diff
        elif diff <= 60:
            return f"Approaching ({diff}d left)", "🟠", diff
        else:
            return f"Valid ({diff}d left)", "🟢", diff
    except Exception:
        return "Invalid", "⚪", 999

def check_oil_status(row):
    if row.get("unit_type") == "TRAILER":
        return "Exempt (Trailer)", "⚪", "-"
    try:
        c_m = int(row.get("current_mileage") or 0)
        l_o = int(row.get("last_oil_mileage") or 0)
        interval = int(row.get("oil_interval") or 25000)
        if interval <= 0 or (l_o == 0 and c_m == 0):
            return "No Record", "⚪", "-"
        rem = interval - (c_m - l_o)
        if rem < 0:
            return f"Overdue ({abs(rem):,} mi)", "🔴", f"{rem:,}"
        elif rem <= 3000:
            return f"Due Soon ({rem:,} mi)", "🟡", f"{rem:,}"
        else:
            return f"Good ({rem:,} mi)", "🟢", f"{rem:,}"
    except Exception:
        return "Calc Error", "⚪", "-"

def extract_unit_no(asset_str):
    if not isinstance(asset_str, str):
        return ""
    m = re.search(r'\b\d+\b', asset_str)
    return m.group(0) if m else asset_str.strip()

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            unit_type TEXT,
            unit_number TEXT UNIQUE,
            driver TEXT,
            vin TEXT,
            plate_number TEXT,
            make_model TEXT,
            plate_expiry TEXT,
            dot_inspection TEXT,
            state_inspection TEXT,
            current_mileage INTEGER DEFAULT 0,
            last_oil_mileage INTEGER DEFAULT 0,
            oil_interval INTEGER DEFAULT 25000
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_number TEXT,
            log_date TEXT,
            log_type TEXT,
            mileage INTEGER,
            cost REAL,
            invoice_filename TEXT,
            notes TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS team_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            message TEXT,
            timestamp TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS driver_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_name TEXT,
            record_type TEXT,
            unit_truck TEXT,
            unit_trailer TEXT,
            event_date TEXT,
            description TEXT,
            cost REAL DEFAULT 0,
            photo_file TEXT,
            created_by TEXT
        )
    """)
    conn.commit()

    if os.path.exists(SERVICE_LOGS_CSV):
        try:
            df_csv = pd.read_csv(SERVICE_LOGS_CSV)
            for _, s_row in df_csv.iterrows():
                u_extracted = extract_unit_no(str(s_row.get("Asset", "")))
                odo = str(s_row.get("Odometer (mi)", "0")).replace(",", "").strip()
                try:
                    odo_val = int(float(odo))
                    if odo_val > 0 and u_extracted:
                        c.execute("""
                            UPDATE vehicles 
                            SET last_oil_mileage = MAX(last_oil_mileage, ?),
                                current_mileage = MAX(current_mileage, ?)
                            WHERE unit_number = ?
                        """, (odo_val, odo_val, u_extracted))
                except Exception:
                    pass
            conn.commit()
        except Exception:
            pass
    conn.close()

init_db()

conn = get_connection()
df_v = pd.read_sql_query("SELECT * FROM vehicles ORDER BY unit_number ASC", conn)
df_logs = pd.read_sql_query("SELECT * FROM logs ORDER BY log_date DESC", conn)

def evaluate_insp(row):
    today = datetime.now().date()
    for col in ["plate_expiry", "dot_inspection", "state_inspection"]:
        d_str = str(row.get(col, "")).strip()
        if d_str and d_str not in ["nan", "None", "", "-"]:
            try:
                diff = (datetime.strptime(d_str[:10], "%Y-%m-%d").date() - today).days
                if diff < 0:
                    return "OVERDUE ❌"
                elif diff <= 30:
                    return "EXPIRING ⚠️"
            except:
                pass
    return "VALID"

df_v["insp_status"] = df_v.apply(evaluate_insp, axis=1)
oil_res = df_v.apply(check_oil_status, axis=1)
df_v["oil_status"] = [r[0] for r in oil_res]
df_v["oil_icon"] = [r[1] for r in oil_res]
df_v["remaining_oil_mi"] = [r[2] for r in oil_res]

df_d = pd.DataFrame()
if os.path.exists(DRIVERS_FILE):
    df_d = pd.read_excel(DRIVERS_FILE)
    df_d = df_d[df_d["Name"].notna()].copy()
    df_d["License Expiry"] = df_d["License Expiry"].astype(str).str.strip()
    df_d["Next Medical"] = df_d["Next Medical"].astype(str).str.strip()
    df_d["Telephone"] = df_d["Telephone"].fillna("-").astype(str).str.strip()
    df_d["License Number"] = df_d["License Number"].fillna("-").astype(str).str.strip()
    
    df_d["CDL_Status"] = df_d["License Expiry"].apply(lambda d: check_date_status(d)[0])
    df_d["CDL_Icon"] = df_d["License Expiry"].apply(lambda d: check_date_status(d)[1])
    df_d["Med_Status"] = df_d["Next Medical"].apply(lambda d: check_date_status(d)[0])
    df_d["Med_Icon"] = df_d["Next Medical"].apply(lambda d: check_date_status(d)[1])

crit_oil = df_v[df_v["oil_icon"].isin(["🔴", "🟡"])]
crit_insp = df_v[df_v["insp_status"].str.contains("❌|⚠️")]
crit_cdl = df_d[df_d["CDL_Icon"].isin(["🔴", "🟡"])] if not df_d.empty else pd.DataFrame()
crit_med = df_d[df_d["Med_Icon"].isin(["🔴", "🟡"])] if not df_d.empty else pd.DataFrame()

# -------------------------------------------------------------
# SIDEBAR (LEFT NAVIGATION PANEL)
# -------------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=190)
    st.markdown("### 🏢 **MOONSTAR TMS**")
    st.caption(f"👤 Active: **{st.session_state.get('current_user')}**")
    st.markdown("---")
    
    menu = st.radio(
        "MODULES",
        [
            "📊 Operations & Alert Center",
            "👤 Driver Dossier & Compliance",
            "🚛 Fleet Dispatch & Asset Board",
            "💬 Team Dispatch Chat",
            "🔧 Service, Maintenance & Invoicing"
        ]
    )
    st.markdown("---")
    if st.button("🚪 Sign Out"):
        st.session_state["authenticated"] = False
        st.rerun()

# -------------------------------------------------------------
# TOP CORPORATE NAVBAR
# -------------------------------------------------------------
st.markdown(f"""
<div class="moonstar-nav">
    <div>
        <div class="brand-text">MOONSTAR <span style="color:#38bdf8;">EXPRESS LLC</span></div>
        <div class="brand-sub">Enterprise Fleet Management, Driver Dossier & Operations Console • Bensalem, PA</div>
    </div>
    <div style="text-align: right;">
        <span style="background: rgba(255,255,255,0.15); padding: 6px 14px; border-radius: 20px; font-size: 12px; border: 1px solid #38bdf8;">
            🟢 Online: <b>{st.session_state.get('current_user')}</b>
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. MODULE: OPERATIONS & ALERT CENTER
# -------------------------------------------------------------
if menu == "📊 Operations & Alert Center":
    st.markdown("#### 📌 Operations Health Cockpit *(Click any card below to view details)*")
    
    if "op_view" not in st.session_state:
        st.session_state["op_view"] = "ALL"

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Active Equipment</div>
            <div class="kpi-val">{len(df_v[df_v['unit_type']=='TRUCK'])} Trucks / {len(df_v[df_v['unit_type']=='TRAILER'])} Trailers</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📋 Show All Fleet", use_container_width=True):
            st.session_state["op_view"] = "ALL"

    with k2:
        st.markdown(f"""
        <div class="kpi-card kpi-card-alert">
            <div class="kpi-label">🚨 Oil Change Alert</div>
            <div class="kpi-val" style="color:#ef4444;">{len(crit_oil)} Trucks</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔍 View Oil Alerts", use_container_width=True):
            st.session_state["op_view"] = "OIL"

    with k3:
        st.markdown(f"""
        <div class="kpi-card kpi-card-warn">
            <div class="kpi-label">⚠️ Inspection / DOT Alert</div>
            <div class="kpi-val" style="color:#d97706;">{len(crit_insp)} Assets</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔍 View Inspection Alerts", use_container_width=True):
            st.session_state["op_view"] = "INSP"

    with k4:
        st.markdown(f"""
        <div class="kpi-card kpi-card-alert">
            <div class="kpi-label">🔴 Driver CDL Alert</div>
            <div class="kpi-val" style="color:#ef4444;">{len(crit_cdl)} Drivers</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔍 View CDL Alerts", use_container_width=True):
            st.session_state["op_view"] = "CDL"

    with k5:
        st.markdown(f"""
        <div class="kpi-card kpi-card-warn">
            <div class="kpi-label">🟡 Medical Card Alert</div>
            <div class="kpi-val" style="color:#d97706;">{len(crit_med)} Drivers</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔍 View Medical Alerts", use_container_width=True):
            st.session_state["op_view"] = "MED"

    st.markdown("---")

    view = st.session_state["op_view"]

    if view == "OIL":
        st.markdown("### 🚨 Overdue or Approaching Oil Changes (< 3,000 mi)")
        if not crit_oil.empty:
            st.dataframe(
                crit_oil[["unit_number", "company", "driver", "current_mileage", "last_oil_mileage", "oil_icon", "oil_status", "remaining_oil_mi"]].rename(columns={
                    "unit_number": "Unit #", "company": "Company", "driver": "Assigned Driver", "current_mileage": "Current Odo", "last_oil_mileage": "Last Oil Change", "oil_icon": "Status", "oil_status": "Alert Detail", "remaining_oil_mi": "Remaining (mi)"
                }), use_container_width=True, hide_index=True
            )
        else:
            st.success("All trucks are well within their scheduled maintenance interval!")

    elif view == "INSP":
        st.markdown("### ⚠️ Overdue or Approaching Asset Inspections (Registration / DOT / State)")
        if not crit_insp.empty:
            st.dataframe(
                crit_insp[["unit_number", "unit_type", "company", "driver", "plate_number", "plate_expiry", "dot_inspection", "state_inspection", "insp_status"]].rename(columns={
                    "unit_number": "Unit #", "unit_type": "Type", "company": "Company", "driver": "Driver", "plate_number": "Plate", "plate_expiry": "Registration Exp", "dot_inspection": "Annual DOT Exp", "state_inspection": "State / PA Exp", "insp_status": "Inspection Status"
                }), use_container_width=True, hide_index=True
            )
        else:
            st.success("All asset inspections and registrations are valid!")

    elif view == "CDL":
        st.markdown("### 🔴 CDL Licenses Expired or Expiring in Less Than 30 Days")
        if not crit_cdl.empty:
            st.dataframe(
                crit_cdl[["Name", "Telephone", "License Number", "License Expiry", "CDL_Icon", "CDL_Status"]].rename(columns={
                    "Name": "Driver Full Name", "Telephone": "Phone Number", "License Number": "CDL #", "License Expiry": "Expiration Date", "CDL_Icon": "Status", "CDL_Status": "Detail"
                }), use_container_width=True, hide_index=True
            )
        else:
            st.success("All driver CDLs are up to date!")

    elif view == "MED":
        st.markdown("### 🟡 Medical Examination Cards Expired or Due Soon")
        if not crit_med.empty:
            st.dataframe(
                crit_med[["Name", "Telephone", "Next Medical", "Med_Icon", "Med_Status"]].rename(columns={
                    "Name": "Driver Full Name", "Telephone": "Phone Number", "Next Medical": "Medical Due Date", "Med_Icon": "Status", "Med_Status": "Detail"
                }), use_container_width=True, hide_index=True
            )
        else:
            st.success("All Medical Cards are fully compliant!")

    else:
        st.markdown("### 📋 Complete Fleet Operations Overview")
        st.dataframe(
            df_v[["unit_number", "company", "unit_type", "driver", "make_model", "current_mileage", "last_oil_mileage", "oil_icon", "insp_status"]].rename(columns={
                "unit_number": "Unit #", "company": "Company", "unit_type": "Asset Type", "driver": "Assigned Driver", "make_model": "Make/Model", "current_mileage": "Current Odo", "last_oil_mileage": "Last Oil (mi)", "oil_icon": "Oil", "insp_status": "Compliance Status"
            }), use_container_width=True, height=450, hide_index=True
        )

# -------------------------------------------------------------
# 2. MODULE: DRIVER DOSSIER & COMPLIANCE
# -------------------------------------------------------------
elif menu == "👤 Driver Dossier & Compliance":
    st.markdown("#### 👤 Driver Master Dossier (Profile, Check-in/out Photos & Safety History)")
    
    driver_names = df_d["Name"].dropna().tolist() if not df_d.empty else []
    
    col_d1, col_d2 = st.columns([2, 3])
    with col_d1:
        selected_dr = st.selectbox("Select Driver Dossier to Inspect:", ["Select..."] + driver_names)
        
    if selected_dr != "Select...":
        dr_info = df_d[df_d["Name"] == selected_dr].iloc[0]
        
        st.markdown(f"""
        <div class="dossier-box">
            <h3 style="color:#0b1f3a; margin-top:0;">📁 DRIVER PROFILE: {dr_info['Name']}</h3>
            <div style="display:flex; justify-content:space-between; flex-wrap:wrap; font-size:14px; margin-top:10px;">
                <div>📞 <b>Phone:</b> {dr_info['Telephone']}</div>
                <div>✉️ <b>Email:</b> {dr_info.get('E-mail', '-')}</div>
                <div>🪪 <b>CDL Number:</b> {dr_info['License Number']}</div>
                <div>📅 <b>CDL Expiration:</b> {dr_info['License Expiry']} ({dr_info['CDL_Icon']} {dr_info['CDL_Status']})</div>
                <div>🏥 <b>Medical Card:</b> {dr_info['Next Medical']} ({dr_info['Med_Icon']} {dr_info['Med_Status']})</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        t_sub1, t_sub2, t_sub3 = st.tabs([
            "🚚 Truck/Trailer Check-in & Check-out Photos",
            "💥 Accidents, Violations & Citations",
            "➕ Add Photo, Incident or Documents"
        ])

        with t_sub1:
            st.markdown("##### 📸 Equipment Custody & Condition Photos")
            conn_dr = get_connection()
            rec_checkin = pd.read_sql_query("""
                SELECT * FROM driver_records 
                WHERE driver_name = ? AND record_type IN ('Equipment Pick-up (Check-in)', 'Equipment Drop-off (Check-out)')
                ORDER BY id DESC
            """, conn_dr, params=(selected_dr,))
            conn_dr.close()

            if not rec_checkin.empty:
                for _, r in rec_checkin.iterrows():
                    with st.expander(f"📌 {r['record_type']} — Date: {r['event_date']} (Truck: #{r['unit_truck']} | Trailer: #{r['unit_trailer']})"):
                        st.write(f"**Condition / Handoff Notes:** {r['description']}")
                        if r['photo_file']:
                            p_path = os.path.join(UPLOAD_DIR, r['photo_file'])
                            if os.path.exists(p_path):
                                if p_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                                    st.image(p_path, caption=f"Uploaded Condition Photo", width=400)
                                else:
                                    st.markdown(f"📄 [View Attached Document ({r['photo_file']})]({p_path})")
            else:
                st.info("No equipment handoff or check-in photos recorded for this driver yet.")

        with t_sub2:
            st.markdown("##### 💥 Accident Reports, Collision Photos & DOT Violations")
            conn_dr = get_connection()
            rec_violations = pd.read_sql_query("""
                SELECT * FROM driver_records 
                WHERE driver_name = ? AND record_type IN ('Accident / Damage', 'DOT / Traffic Citation', 'General Safety Memo')
                ORDER BY id DESC
            """, conn_dr, params=(selected_dr,))
            conn_dr.close()

            if not rec_violations.empty:
                for _, v in rec_violations.iterrows():
                    with st.expander(f"⚠️ {v['record_type']} — Date: {v['event_date']} — Cost: ${v['cost']:,.2f}"):
                        st.write(f"**Associated Asset:** Truck #{v['unit_truck']} / Trailer #{v['unit_trailer']}")
                        st.write(f"**Incident Summary & Officer Report:** {v['description']}")
                        if v['photo_file']:
                            vp_path = os.path.join(UPLOAD_DIR, v['photo_file'])
                            if os.path.exists(vp_path):
                                if vp_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                                    st.image(vp_path, caption=f"Incident Photo / Citation Scan", width=400)
                                else:
                                    st.write(f"📄 File: `{v['photo_file']}`")
            else:
                st.success("Clean safety record! No accidents or DOT citations reported for this driver.")

        with t_sub3:
            st.markdown(f"##### ➕ Add Record or Photo to {selected_dr}'s File")
            with st.form("add_driver_record_form", clear_on_submit=True):
                r_c1, r_c2, r_c3 = st.columns(3)
                with r_c1:
                    rec_type = st.selectbox("Record Type", [
                        "Equipment Pick-up (Check-in)",
                        "Equipment Drop-off (Check-out)",
                        "Accident / Damage",
                        "DOT / Traffic Citation",
                        "General Safety Memo"
                    ])
                    rec_date = st.date_input("Event Date")
                with r_c2:
                    truck_units = ["None"] + df_v[df_v["unit_type"] == "TRUCK"]["unit_number"].tolist()
                    sel_truck = st.selectbox("Truck Assigned", truck_units)
                    trailer_units = ["None"] + df_v[df_v["unit_type"] == "TRAILER"]["unit_number"].tolist()
                    sel_trailer = st.selectbox("Trailer Assigned", trailer_units)
                with r_c3:
                    rec_cost = st.number_input("Cost / Fine Amount ($)", min_value=0.0, step=50.0)
                    rec_upload = st.file_uploader("Upload Photo / Report / Citation (PDF/JPG)", type=["pdf", "png", "jpg", "jpeg"])

                rec_desc = st.text_area("Detailed Notes (Damage location, inspection findings, police report info, etc.)")
                
                if st.form_submit_button("Submit Record to Dossier"):
                    saved_photo_name = ""
                    if rec_upload:
                        saved_photo_name = f"DR_{selected_dr.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{rec_upload.name}"
                        with open(os.path.join(UPLOAD_DIR, saved_photo_name), "wb") as f:
                            f.write(rec_upload.getbuffer())

                    c_ins = get_connection()
                    c_cur = c_ins.cursor()
                    c_cur.execute("""
                        INSERT INTO driver_records 
                        (driver_name, record_type, unit_truck, unit_trailer, event_date, description, cost, photo_file, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (selected_dr, rec_type, sel_truck, sel_trailer, str(rec_date), rec_desc, rec_cost, saved_photo_name, st.session_state.get("current_user")))
                    c_ins.commit()
                    c_ins.close()
                    st.success("New record and files successfully logged into driver dossier!")
                    st.rerun()

    st.markdown("---")
    st.markdown("#### 📋 Driver Fleet Compliance Table")
    st.dataframe(
        df_d[["Name", "Telephone", "License Number", "License Expiry", "CDL_Icon", "CDL_Status", "Next Medical", "Med_Icon", "Med_Status"]].rename(columns={
            "Name": "Driver", "Telephone": "Phone", "License Number": "CDL #", "License Expiry": "CDL Expiration", "CDL_Icon": "CDL Status", "Next Medical": "Medical Due", "Med_Icon": "Medical Status"
        }), use_container_width=True, hide_index=True
    )

# -------------------------------------------------------------
# 3. MODULE: FLEET DISPATCH & ASSET BOARD
# -------------------------------------------------------------
elif menu == "🚛 Fleet Dispatch & Asset Board":
    st.markdown("#### 🚛 Equipment Roster & Active Maintenance Tracking")
    
    fa, fb, fc = st.columns([1, 1, 2])
    with fa:
        f_co = st.selectbox("Company Filter:", ["ALL", "MOONSTAR", "LIONSTAR"])
    with fb:
        f_ty = st.selectbox("Asset Type:", ["ALL", "TRUCK", "TRAILER", "🚨 Oil Alerts Only"])
    with fc:
        f_sc = st.text_input("Quick Search by Unit #, Driver or Plate:")

    df_filt = df_v.copy()
    if f_co != "ALL":
        df_filt = df_filt[df_filt["company"] == f_co]
    if f_ty == "TRUCK":
        df_filt = df_filt[df_filt["unit_type"] == "TRUCK"]
    elif f_ty == "TRAILER":
        df_filt = df_filt[df_filt["unit_type"] == "TRAILER"]
    elif f_ty == "🚨 Oil Alerts Only":
        df_filt = df_filt[df_filt["oil_icon"].isin(["🔴", "🟡"])]

    if f_sc:
        s = f_sc.strip().lower()
        df_filt = df_filt[
            df_filt["unit_number"].str.lower().str.contains(s) |
            df_filt["driver"].str.lower().str.contains(s) |
            df_filt["plate_number"].str.lower().str.contains(s)
        ]

    st.dataframe(
        df_filt[[
            "unit_number", "company", "unit_type", "driver", "make_model",
            "current_mileage", "last_oil_mileage", "oil_icon", "oil_status",
            "plate_number", "plate_expiry", "dot_inspection", "insp_status"
        ]].rename(columns={
            "unit_number": "Unit #", "company": "Company", "unit_type": "Type", "driver": "Driver",
            "make_model": "Make/Model", "current_mileage": "Current Odo", "last_oil_mileage": "Last Oil Change",
            "oil_icon": "Oil Status", "oil_status": "Remaining Oil Mileage", "plate_number": "License Plate",
            "plate_expiry": "Registration", "dot_inspection": "Annual DOT", "insp_status": "Inspection Status"
        }), use_container_width=True, height=480, hide_index=True
    )

# -------------------------------------------------------------
# 4. MODULE: TEAM DISPATCH CHAT
# -------------------------------------------------------------
elif menu == "💬 Team Dispatch Chat":
    st.markdown("#### 💬 Dispatch Operations & Shift Notes")
    with st.form("chat_form", clear_on_submit=True):
        cm1, cm2 = st.columns([5, 1])
        with cm1:
            msg_txt = st.text_input("Type your update here...", placeholder="E.g., Unit 14 delivered load in Laredo, now available for dispatch.")
        with cm2:
            if st.form_submit_button("Post Note 🚀") and msg_txt.strip():
                cur = conn.cursor()
                now_s = datetime.now().strftime("%m/%d/%Y %I:%M %p")
                cur.execute("INSERT INTO team_chat (sender, message, timestamp) VALUES (?, ?, ?)", (st.session_state.get("current_user"), msg_txt.strip(), now_s))
                conn.commit()
                st.rerun()

    df_c = pd.read_sql_query("SELECT * FROM team_chat ORDER BY id DESC LIMIT 50", conn)
    for _, r in df_c.iterrows():
        st.markdown(f"""
        <div style="background:#ffffff; border-left:4px solid #0284c7; padding:10px 14px; border-radius:6px; margin-bottom:8px; border:1px solid #e2e8f0;">
            <b style="color:#0b1f3a;">👤 {r['sender']}</b> <span style="font-size:11px; color:#64748b; margin-left:8px;">🕒 {r['timestamp']}</span>
            <div style="margin-top:4px; font-size:14px; color:#0f172a;">{r['message']}</div>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# 5. MODULE: SERVICE, MAINTENANCE & INVOICING
# -------------------------------------------------------------
elif menu == "🔧 Service, Maintenance & Invoicing":
    st.markdown("#### 🔧 Log New Maintenance, Repair or Invoice")
    with st.form("add_log_form", clear_on_submit=True):
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            sel_u = st.selectbox("Select Asset (Unit #)", df_v["unit_number"].tolist())
            l_date = st.date_input("Service Date")
        with sc2:
            l_type = st.selectbox("Work Performed", ["Oil Change (PM)", "Tires / Brakes", "Annual DOT Inspection", "Breakdown / Repair", "PM Service", "Other"])
            l_mil = st.number_input("Odometer (mi)", min_value=0, step=1000)
        with sc3:
            l_cost = st.number_input("Invoice Total ($)", min_value=0.0, step=50.0)
            l_inv = st.file_uploader("Upload Invoice / Repair Order (PDF/JPG)", type=["pdf", "png", "jpg", "jpeg"])

        l_desc = st.text_area("Detailed Scope of Work & Replaced Parts")
        if st.form_submit_button("Record Service Entry"):
            inv_name = ""
            if l_inv:
                inv_name = f"Unit_{sel_u}_{l_inv.name}"
                with open(os.path.join(UPLOAD_DIR, inv_name), "wb") as f:
                    f.write(l_inv.getbuffer())
            cur = conn.cursor()
            cur.execute("INSERT INTO logs (unit_number, log_date, log_type, mileage, cost, invoice_filename, notes) VALUES (?, ?, ?, ?, ?, ?, ?)", (sel_u, str(l_date), l_type, l_mil, l_cost, inv_name, l_desc))
            if l_type == "Oil Change (PM)" and l_mil > 0:
                cur.execute("UPDATE vehicles SET last_oil_mileage = ?, current_mileage = MAX(current_mileage, ?) WHERE unit_number = ?", (l_mil, l_mil, sel_u))
            elif l_mil > 0:
                cur.execute("UPDATE vehicles SET current_mileage = MAX(current_mileage, ?) WHERE unit_number = ?", (l_mil, sel_u))
            conn.commit()
            st.success("Service record successfully updated in the fleet ledger!")
            st.rerun()
