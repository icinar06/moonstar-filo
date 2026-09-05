import glob
import os
import re
import shutil
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="MOONSTAR EXPRESS LLC — Executive Fleet Console",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# MOONSTAR ORİJİNAL LOGO VE SADE LÜKS KURUMSAL STİLLER
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #f8fafc !important;
        color: #0f172a;
    }
    
    /* Üst Konsol Header */
    .top-header {
        background: linear-gradient(135deg, #0b1f3a 0%, #0f2c59 60%, #0284c7 100%);
        padding: 12px 24px;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(11, 31, 58, 0.15);
        border-bottom: 3px solid #f97316;
    }

    /* Üst KPI Metrik Kartları */
    .kpi-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 16px 20px;
        border: 1px solid #cbd5e1;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
        margin-bottom: 20px;
    }
    .kpi-title {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        color: #64748b;
        letter-spacing: 0.8px;
    }
    .kpi-num {
        font-family: 'Montserrat', sans-serif;
        font-size: 24px;
        font-weight: 900;
        color: #0b1f3a;
        margin-top: 6px;
    }

    /* SADE VE ŞIK PORTAL KARTLARI (GÖNDERDİĞİNİZ FORM STİLİNDE) */
    div[data-testid*="stButton"] > button {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 10px !important;
        padding: 18px 20px !important;
        min-height: 190px !important;
        height: auto !important;
        width: 100% !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03) !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: flex-start !important;
        justify-content: space-between !important;
        text-align: left !important;
        white-space: pre-wrap !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        margin-bottom: 16px !important;
    }
    
    div[data-testid*="stButton"] > button:hover {
        border-color: #0284c7 !important;
        box-shadow: 0 8px 20px rgba(2, 132, 199, 0.12) !important;
        transform: translateY(-2px) !important;
        background-color: #ffffff !important;
    }
    div[data-testid*="stButton"] > button p {
        font-family: 'Inter', sans-serif !important;
        font-size: 12px !important;
        font-weight: 500 !important;
        margin: 0 !important;
        line-height: 1.6 !important;
        text-align: left !important;
        white-space: pre-wrap !important;
        width: 100% !important;
        color: #0f172a !important;
    }
</style>
""", unsafe_allow_html=True)

DB_FILE = "fleet_database.db"
UPLOAD_DIR = "arsiv_dosyalari"
DRIVERS_FILE = "Drivers.xlsx"
SERVICE_LOGS_CSV = "Service logs.csv"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- WEB SİTESİ / GİRİŞ EKRANI ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "web_page" not in st.session_state:
    st.session_state["web_page"] = "Home"

if not st.session_state["authenticated"]:
    hdr_left, hdr_right = st.columns([1.5, 3.5])
    with hdr_left:
        if os.path.exists("logo.jpg"):
            st.image("logo.jpg", width=180)
        else:
            st.markdown("""
            <div style="font-family:'Montserrat',sans-serif; font-size:22px; font-weight:900; color:#0b1f3a; padding: 10px 0;">
                MOON<span style="color:#0284c7;">★</span>TAR <span style="font-size:10px; color:#f97316;">EXPRESS</span>
            </div>
            """, unsafe_allow_html=True)
    with hdr_right:
        nav_b1, nav_b2, nav_b3, nav_b4, nav_b5 = st.columns(5)
        with nav_b1:
            if st.button("HOME", key="nav_home"):
                st.session_state["web_page"] = "Home"
                st.rerun()
        with nav_b2:
            if st.button("ABOUT US", key="nav_about"):
                st.session_state["web_page"] = "About Us"
                st.rerun()
        with nav_b3:
            if st.button("CONTACT US", key="nav_contact"):
                st.session_state["web_page"] = "Contact Us"
                st.rerun()
        with nav_b4:
            if st.button("SERVICES", key="nav_services"):
                st.session_state["web_page"] = "Services"
                st.rerun()
        with nav_b5:
            if st.button("PORTAL LOGIN", key="nav_login"):
                st.session_state["web_page"] = "Login"
                st.rerun()

    st.markdown("<hr style='margin:0 0 20px 0; border-color:#e2e8f0;'>", unsafe_allow_html=True)

    if st.session_state["web_page"] == "Home":
        st.markdown("""
        
            
                RELIABLE TRANSPORTATION SOLUTIONS
                Your trusted partner for safe and efficient travel across the United States.
                📞 +1 215-666-0595
            
        
        """"""
        <div class="hero-container">
            <div class="hero-right" style="padding:40px; background:#0b1f3a; border-radius:10px; color:white; margin-bottom:20px;">
                <h1 style="font-family:'Montserrat',sans-serif; font-size:26px; font-weight:900; margin-bottom:10px;">RELIABLE TRANSPORTATION SOLUTIONS</h1>
                <p style="font-size:13px; color:#cbd5e1; margin-bottom:15px;">Your trusted partner for safe and efficient travel across the United States.</p>
                <div style="font-size:13px; color:#38bdf8; font-weight:700;">📞 +1 215-666-0595</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        c_l, c_r = st.columns([2, 1])
        with c_r:
            st.markdown("### 🔐 Secure Fleet Login")
            with st.form("login_form"):
                email = st.text_input("Corporate Email", placeholder="ismail@moonstarpa.com")
                pwd = st.text_input("Password", type="password")
                if st.form_submit_button("Sign In to Portal", use_container_width=True):
                    if "@moonstarpa" in email.strip().lower() and pwd == "Moonstar2026!":
                        st.session_state["authenticated"] = True
                        st.session_state["current_user"] = email.strip().lower()
                        st.rerun()
                    else:
                        st.error("Invalid credentials!")

    elif st.session_state["web_page"] == "Contact Us":
        co1, co2 = st.columns(2)
        with co1:
            st.markdown("## 📞 CONTACT US")
            st.markdown("#### **SAFETY MANAGER CALL:** `717-666-2343`""#### **SAFETY MANAGER CALL:** `717-666-2343`")
            st.write("Report dangerous driving like speeding and weaving. If you see something, say something.")
            st.markdown("---")
            st.markdown("#### **MOONSTAR EXPRESS LLC**")
            st.write("2750 Grant Avenue, Philadelphia, PA, USA")
            st.markdown("SUITE B / Phone : `215-666-0595`""SUITE B / Phone : `215-666-0595`")
            st.markdown("#### **Hours**")
            st.write("Open today `09:00 am - 05:00 pm`")
        with co2:
            st.markdown("### 📍 Location & Directions")
            st.markdown("""
            <div style="background:#e2e8f0; border-radius:10px; padding:40px; text-align:center; color:#475569; font-weight:700;">
                📍 2750 Grant Avenue, Philadelphia, PA 19114<br><span style="font-size:12px; font-weight:400;">Ashton Wooden Bridge Area</span>
            </div>
            """, unsafe_allow_html=True)

    elif st.session_state["web_page"] == "About Us":
        st.markdown("## About Moonstar Express LLC")
        st.write("Moonstar Express LLC is a premier commercial freight and logistics provider based in Bensalem / Philadelphia, PA. Operating a state-of-the-art fleet of Volvo and Mack semi-trucks, we ensure on-time nationwide delivery with unmatched corporate excellence.")

    elif st.session_state["web_page"] == "Services":
        st.markdown("## Our Fleet Logistics Services")
        st.write("• Nationwide Dry Van & Reefer Transportation\n• Dedicated Fleet Management & Telematics\n• 24/7 Dispatch Operations & Driver Compliance\n• Automated P&L and Fuel Expense Tracking")

    elif st.session_state["web_page"] == "Login":
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown("### 🔒 Executive Portal Login")
            with st.form("login_form_direct"):
                email = st.text_input("Corporate Email", placeholder="ismail@moonstarpa.com")
                pwd = st.text_input("Password", type="password")
                if st.form_submit_button("Sign In", use_container_width=True):
                    if "@moonstarpa" in email.strip().lower() and pwd == "Moonstar2026!":
                        st.session_state["authenticated"] = True
                        st.session_state["current_user"] = email.strip().lower()
                        st.rerun()
                    else:
                        st.error("Invalid credentials!")
    st.stop()

# ---------------------------------------------
def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def check_date_status(date_str):
    if not date_str or str(date_str).strip() in ["0000-00-00", "nan", "None", "-", ""]:
        return "READY", 999
    try:
        dt = datetime.strptime(str(date_str).strip()[:10], "%Y-%m-%d").date()
        diff = (dt - datetime.now().date()).days
        if diff < 0 or diff <= 30:
            return "DUE SOON", diff
        else:
            return "READY", diff
    except Exception:
        return "READY", 999

def check_oil_status(row):
    if row.get("unit_type") == "TRAILER":
        return "READY"
    try:
        c_m = int(row.get("current_mileage") or 0)
        l_o = int(row.get("last_oil_mileage") or 0)
        interval = int(row.get("oil_interval") or 25000)
        if interval <= 0 or (l_o == 0 and c_m == 0):
            return "READY"
        rem = interval - (c_m - l_o)
        if rem <= 3000:
            return "DUE SOON"
        else:
            return "READY"
    except Exception:
        return "READY"

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
            oil_interval INTEGER DEFAULT 25000,
            monthly_gross REAL DEFAULT 0.0,
            monthly_fuel_cost REAL DEFAULT 0.0,
            hooked_trailer TEXT DEFAULT 'None',
            current_location TEXT DEFAULT 'Yard'
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
            recipient TEXT,
            message TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

conn = get_connection()
df_v = pd.read_sql_query("SELECT * FROM vehicles ORDER BY unit_number ASC", conn)
df_logs = pd.read_sql_query("SELECT * FROM logs", conn)

unit_expenses = df_logs.groupby("unit_number")["cost"].sum().to_dict() if not df_logs.empty else {}
df_v["total_expenses"] = df_v["unit_number"].map(unit_expenses).fillna(0.0)
df_v["monthly_fuel_cost"] = df_v["monthly_fuel_cost"].fillna(0.0)
df_v["net_profit"] = df_v["monthly_gross"] - (df_v["total_expenses"] + df_v["monthly_fuel_cost"])

df_d = pd.DataFrame()
if os.path.exists(DRIVERS_FILE):
    df_d = pd.read_excel(DRIVERS_FILE)
    df_d = df_d[df_d["Name"].notna()].copy()

def evaluate_insp(row):
    today = datetime.now().date()
    for col in ["plate_expiry", "dot_inspection", "state_inspection"]:
        d_str = str(row.get(col, "")).strip()
        if d_str and d_str not in ["nan", "None", "", "-"]:
            try:
                diff = (datetime.strptime(d_str[:10], "%Y-%m-%d").date() - today).days
                if diff <= 30:
                    return "DUE SOON", 1
            except:
                pass
    return "READY", 2

if not df_v.empty:
    insp_res = df_v.apply(evaluate_insp, axis=1)
    df_v["insp_status"] = [r[0] for r in insp_res]
    df_v["oil_status"] = df_v.apply(check_oil_status, axis=1)

    def get_overall_priority(row):
        if row["oil_status"] == "DUE SOON" or row["insp_status"] == "DUE SOON":
            return "DUE SOON", 1
        else:
            return "READY", 2

    v_prio = df_v.apply(get_overall_priority, axis=1)
    df_v["priority_label"] = [p[0] for p in v_prio]
    df_v["priority_order"] = [p[1] for p in v_prio]

    insp_crit_count = len(df_v[df_v["priority_order"] == 1])
    total_fleet_gross = df_v["monthly_gross"].sum()
    total_fleet_fuel = df_v["monthly_fuel_cost"].sum()
else:
    insp_crit_count, total_fleet_gross, total_fleet_fuel = 0, 0.0, 0.0

if not df_d.empty:
    cdl_res = df_d["License Expiry"].apply(check_date_status)
    df_d["CDL_Status"] = [r[0] for r in cdl_res]
    med_res = df_d["Next Medical"].apply(check_date_status)
    df_d["Med_Status"] = [r[0] for r in med_res]

    def get_dr_priority(row):
        if row["CDL_Status"] == "DUE SOON" or row["Med_Status"] == "DUE SOON":
            return "DUE SOON", 1
        else:
            return "READY", 2

    dr_prio = df_d.apply(get_dr_priority, axis=1)
    df_d["priority_label"] = [p[0] for p in dr_prio]
    df_d["priority_order"] = [p[1] for p in dr_prio]

dr_crit_count = len(df_d[df_d["priority_order"] == 1]) if not df_d.empty else 0

# ---------------------------------------------
# DİYALOG MODALLARI
# ---------------------------------------------
@st.dialog("Equipment Master Dossier & Financial P&L", width="large")
def open_equipment_dossier(unit_no):
    r_sel = df_v[df_v["unit_number"] == unit_no].iloc[0]
    st.subheader(f"Unit #{r_sel['unit_number']} — {r_sel['unit_type']} ({r_sel['company']})")
    
    t1, t2, t3, t4 = st.tabs(["Vehicle Specs & Pairing", "Financial P&L (Gross, Fuel, Net)", "DOT Audit Binder & Photos", "Decommission"])
    
    with t1:
        with st.form(f"form_unit_{unit_no}"):
            c1, c2, c3 = st.columns(3)
            with c1:
                dr_list = ["Unassigned"] + (df_d["Name"].tolist() if not df_d.empty else [])
                curr_drv = r_sel['driver'] if r_sel['driver'] in dr_list else "Unassigned"
                e_drv = st.selectbox("Assigned Driver", dr_list, index=dr_list.index(curr_drv))
                
                e_plt = st.text_input("Plate Number", value=r_sel['plate_number'] or "")
                e_vin = st.text_input("VIN / Serial", value=r_sel['vin'] or "")
            with c2:
                e_mdl = st.text_input("Make / Model / Year", value=r_sel['make_model'] or "")
                e_cur = st.number_input("Current Mileage (mi)", value=int(r_sel['current_mileage'] or 0))
                e_oil = st.number_input("Last Oil Change (mi)", value=int(r_sel['last_oil_mileage'] or 0))
            with c3:
                trailer_list = ["None"] + df_v[df_v["unit_type"] == "TRAILER"]["unit_number"].tolist()
                curr_hook = str(r_sel.get('hooked_trailer', 'None'))
                if curr_hook not in trailer_list:
                    trailer_list.append(curr_hook)
                e_hook = st.selectbox("Hooked Trailer #", trailer_list, index=trailer_list.index(curr_hook))
                
                e_loc = st.text_input("Current Yard / Location", value=str(r_sel.get('current_location', 'Yard')))
                e_dot = st.text_input("Annual DOT (YYYY-MM-DD)", value=str(r_sel['dot_inspection'] or ""))

            if st.form_submit_button("Save Vehicle Details"):
                cur = conn.cursor()
                cur.execute("""
                    UPDATE vehicles 
                    SET driver=?, plate_number=?, vin=?, make_model=?, current_mileage=?, last_oil_mileage=?, hooked_trailer=?, current_location=?, dot_inspection=?
                    WHERE unit_number=?
                """, (e_drv, e_plt, e_vin, e_mdl, e_cur, e_oil, e_hook, e_loc, e_dot, unit_no))
                conn.commit()
                st.success("Vehicle updated successfully!")
                st.rerun()

    with t2:
        st.markdown(f"##### Monthly Profit & Loss Statement for Unit #{unit_no}")
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Gross Revenue (ITS)", f"${r_sel['monthly_gross']:,.2f}")
        p2.metric("Fuel Cost", f"${r_sel['monthly_fuel_cost']:,.2f}")
        p3.metric("Maintenance Cost", f"${r_sel['total_expenses']:,.2f}")
        p4.metric("Net Profit", f"${r_sel['net_profit']:,.2f}")
        
        unit_logs = df_logs[df_logs["unit_number"] == unit_no]
        if not unit_logs.empty:
            st.dataframe(unit_logs[["log_date", "log_type", "mileage", "cost", "notes"]], use_container_width=True, hide_index=True)
        else:
            st.caption("No maintenance expenses recorded for this unit.")

    with t3:
        up1, up2 = st.columns([2, 3])
        with up1:
            f_cat = st.selectbox("Category", ["Registration Card", "Annual DOT Sheet", "Vehicle Photo", "Insurance Certificate", "Repair Order Invoice"], key=f"fcat_{unit_no}")
            f_upl = st.file_uploader("Select File / Photo", type=["pdf", "png", "jpg", "jpeg"], key=f"fupl_{unit_no}")
            if f_upl and st.button("Upload to Dossier", key=f"fbtn_{unit_no}"):
                save_f = f"EQUIP_{unit_no}_{f_cat.replace(' ', '_')}_{f_upl.name}"
                with open(os.path.join(UPLOAD_DIR, save_f), "wb") as f:
                    f.write(f_upl.getbuffer())
                st.success("File archived!")
                st.rerun()
        with up2:
            found_v = [f for f in os.listdir(UPLOAD_DIR) if f"EQUIP_{unit_no}_" in f]
            for doc in found_v:
                st.write(f"📄 `{doc}`")

    with t4:
        st.warning(f"Permanently remove Unit #{unit_no}?")
        if st.button("🚨 Yes, Delete Permanently", type="secondary"):
            cur = conn.cursor()
            cur.execute("DELETE FROM vehicles WHERE unit_number = ?", (unit_no,))
            conn.commit()
            st.rerun()

@st.dialog("Driver Master Dossier", width="large")
def open_driver_dossier(driver_name):
    d_sel = df_d[df_d["Name"] == driver_name].iloc[0]
    st.subheader(f"Driver Dossier: {d_sel['Name']}")
    
    dt1, dt2, dt3 = st.tabs(["Profile & Compliance Details", "Archived Documents & Photos", "Offboard Driver"])
    
    with dt1:
        with st.form(f"form_dr_{driver_name}"):
            dc1, dc2 = st.columns(2)
            with dc1:
                dr_p = st.text_input("Phone Number", value=d_sel['Telephone'])
                dr_e = st.text_input("Email", value=d_sel['E-mail'])
                dr_c = st.text_input("CDL Number", value=d_sel['License Number'])
            with dc2:
                dr_ce = st.text_input("CDL Expiry (YYYY-MM-DD)", value=d_sel['License Expiry'])
                dr_me = st.text_input("Next Medical (YYYY-MM-DD)", value=d_sel['Next Medical'])

            if st.form_submit_button("Save Driver Changes"):
                df_d.loc[df_d["Name"] == driver_name, "Telephone"] = dr_p
                df_d.loc[df_d["Name"] == driver_name, "E-mail"] = dr_e
                df_d.loc[df_d["Name"] == driver_name, "License Number"] = dr_c
                df_d.loc[df_d["Name"] == driver_name, "License Expiry"] = dr_ce
                df_d.loc[df_d["Name"] == driver_name, "Next Medical"] = dr_me
                df_d.to_excel(DRIVERS_FILE, index=False)
                st.success("Driver profile updated!")
                st.rerun()

    with dt2:
        d_up1, d_up2 = st.columns([2, 3])
        with d_up1:
            dr_cat = st.selectbox("Category", ["CDL Scan", "Medical Card Certificate", "Truck Check-in/out Photo", "Accident Photo", "DOT Citation"], key=f"drcat_{driver_name}")
            dr_fil = st.file_uploader("Select File / Photo", type=["pdf", "png", "jpg", "jpeg"], key=f"drfil_{driver_name}")
            if dr_fil and st.button("Save to Driver Dossier", key=f"drbtn_{driver_name}"):
                save_dr = f"DR_{driver_name.replace(' ', '_')}_{dr_cat.replace(' ', '_')}_{dr_fil.name}"
                with open(os.path.join(UPLOAD_DIR, save_dr), "wb") as f:
                    f.write(dr_fil.getbuffer())
                st.success("Saved!")
                st.rerun()
        with up2:
            found_dr = [f for f in os.listdir(UPLOAD_DIR) if f"DR_{driver_name.replace(' ', '_')}_" in f]
            for d in found_dr:
                st.write(f"📄 `{d}`")

    with dt3:
        st.warning(f"Offboard {driver_name}?")
        if st.button("🚨 Yes, Offboard Driver", type="secondary"):
            df_new = df_d[df_d["Name"] != driver_name]
            df_new.to_excel(DRIVERS_FILE, index=False)
            st.rerun()

# ---------------------------------------------
# TOP NAVBAR (ORİJİNAL LOGO VE SAĞ ÜST SIGN OUT)
# ---------------------------------------------
header_c1, header_c2 = st.columns([6, 1])
with header_c1:
    st.markdown(f"""
    <div style="display:flex; align-items:center; justify-content:space-between; background:linear-gradient(135deg, #0b1f3a 0%, #0f2c59 60%, #0284c7 100%); padding:12px 20px; border-radius:8px; border-bottom:3px solid #f97316; color:white;">
        <div style="font-family:'Montserrat',sans-serif; font-size:18px; font-weight:900; display:flex; align-items:center; gap:8px;">
            MOON<span style="color:#f97316;">★</span>TAR <span style="font-size:10px; color:#38bdf8;">EXPRESS LLC</span>
        </div>
        <div style="font-size:11px; color:#cbd5e1;">
            Executive Fleet Management Console | User: <b>{st.session_state.get('current_user')}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

with header_c2:
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    if st.button("Sign Out", key="top_sign_out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

top_menu = st.radio(
    "Navigation",
    ["Trucks & Trailers", "Drivers Compliance", "Data Imports (Samsara/ITS/Fuel)", "Service Ledger"],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. MODÜL: TRUCKS & TRAILERS
# -------------------------------------------------------------
if top_menu == "Trucks & Trailers":
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="kpi-card" style="border-left: 5px solid #0284c7;">
            <div class="kpi-title">Monthly Fleet Gross (ITS)</div>
            <div class="kpi-num" style="color:#0284c7;">${total_fleet_gross:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="kpi-card" style="border-left: 5px solid #d97706;">
            <div class="kpi-title">Total Monthly Fuel Cost</div>
            <div class="kpi-num" style="color:#d97706;">${total_fleet_fuel:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="kpi-card" style="border-left: 5px solid #d97706;">
            <div class="kpi-title">Inspections Overdue / Due</div>
            <div class="kpi-num" style="color:#d97706;">{insp_crit_count} Assets</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="kpi-card" style="border-left: 5px solid #16a34a;">
            <div class="kpi-title">Active Fleet Total</div>
            <div class="kpi-num" style="color:#16a34a;">{len(df_v[df_v['unit_type']=='TRUCK'])} Trucks / {len(df_v[df_v['unit_type']=='TRAILER'])} Trailers</div>
        </div>
        """, unsafe_allow_html=True)

    f1, f2, f3, f4 = st.columns([1.5, 2, 2.5, 1.2])
    with f1:
        f_type = st.selectbox("Equipment Type:", ["All Equipment", "Trucks Only", "Trailers Only"])
    with f2:
        f_stat = st.selectbox("Filter Condition:", ["Needs Urgent Action", "Approaching Deadlines", "All Healthy", "Show Complete Fleet"])
    with f3:
        f_srch = st.text_input("Find Unit, Driver or Model:", placeholder="Type Unit # (e.g. 12)...")
    with f4:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("+ Add Equipment", key="add_eq_btn", use_container_width=True):
            st.session_state["show_add_modal"] = True

    if st.session_state.get("show_add_modal", False):
        with st.form("new_veh_modal_box"):
            st.markdown("##### ➕ Register New Equipment")
            nc1, nc2 = st.columns(2)
            with nc1:
                nu_comp = st.selectbox("Company", ["MOONSTAR", "LIONSTAR"])
                nu_type = st.selectbox("Type", ["TRUCK", "TRAILER"])
                nu_unit = st.text_input("Unit Number (e.g. 95)")
                nu_driver = st.text_input("Assigned Driver")
            with nc2:
                nu_vin = st.text_input("VIN / Serial")
                nu_plate = st.text_input("Plate Number")
                nu_model = st.text_input("Make / Model / Year")
            
            sub_col1, sub_col2 = st.columns(2)
            with sub_col1:
                if st.form_submit_button("Save Asset", use_container_width=True) and nu_unit:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO vehicles (company, unit_type, unit_number, driver, vin, plate_number, make_model) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (nu_comp, nu_type, nu_unit.strip(), nu_driver.strip(), nu_vin.strip(), nu_plate.strip(), nu_model.strip()))
                    conn.commit()
                    st.session_state["show_add_modal"] = False
                    st.success(f"{nu_type} #{nu_unit} added successfully!")
                    st.rerun()
            with sub_col2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state["show_add_modal"] = False
                    st.rerun()

    df_filtered = df_v.copy()
    if f_type == "Trucks Only":
        df_filtered = df_filtered[df_filtered["unit_type"] == "TRUCK"]
    elif f_type == "Trailers Only":
        df_filtered = df_filtered[df_filtered["unit_type"] == "TRAILER"]

    if "Needs Urgent Action" in f_stat:
        df_filtered = df_filtered[df_filtered["priority_order"] == 1]
    elif "Approaching Deadlines" in f_stat:
        df_filtered = df_filtered[df_filtered["priority_order"] == 2]
    elif "All Healthy" in f_stat:
        df_filtered = df_filtered[df_filtered["priority_order"] == 3]

    if f_srch:
        s = f_srch.strip().lower()
        df_filtered = df_filtered[
            df_filtered["unit_number"].str.lower().str.contains(s) |
            df_filtered["driver"].str.lower().str.contains(s) |
            df_filtered["make_model"].str.lower().str.contains(s)
        ]

    st.markdown("### 📦 Fleet Equipment Portal (Click any card to open master dossier)")

    cols = st.columns(4)
    for idx, (_, r) in enumerate(df_filtered.iterrows()):
        with cols[idx % 4]:
            driver_str = r['driver'] if r['driver'] else 'Unassigned'
            hook_str = f"Trailer #{r['hooked_trailer']}" if r['hooked_trailer'] and r['hooked_trailer'] != 'None' else 'Bobtail'
            
            badge_color = "#16a34a" if "READY" in r['priority_label'] else "#d97706"
            
            card_title = f"UNIT #{r['unit_number']} ({r['unit_type']})"
            card_status = f"{r['priority_label']}"
            
            card_body = (
                f"Status: {card_status}\n"
                f"Driver: {driver_str}\n"
                f"Hooked: {hook_str}\n"
                f"Oil Service: {r['oil_status']}\n"
                f"Annual DOT: {r['insp_status']}\n"
                f"Gross: ${r['monthly_gross']:,.0f} | Fuel: ${r['monthly_fuel_cost']:,.0f}\n"
                f"Net Profit: ${r['net_profit']:,.0f}"
            )
            
            if st.button(f"{card_title}\n\n{card_body}", key=f"schneider_card_{r['unit_number']}", use_container_width=True):
                open_equipment_dossier(r['unit_number'])

# -------------------------------------------------------------
# 2. MODÜL: DRIVERS COMPLIANCE
# -------------------------------------------------------------
elif top_menu == "Drivers Compliance":
    if not df_d.empty:
        dk1, dk2, dk3 = st.columns(3)
        with dk1:
            st.markdown(f"""
            <div class="kpi-card" style="border-left: 5px solid #d97706;">
                <div class="kpi-title">CDL / Medical Due</div>
                <div class="kpi-num" style="color:#d97706;">{dr_crit_count} Drivers</div>
            </div>
            """, unsafe_allow_html=True)
        with dk2:
            st.markdown(f"""
            <div class="kpi-card" style="border-left: 5px solid #d97706;">
                <div class="kpi-title">Expiring in 30 Days</div>
                <div class="kpi-num" style="color:#d97706;">{len(df_d[df_d['priority_order']==1])} Drivers</div>
            </div>
            """, unsafe_allow_html=True)
        with dk3:
            st.markdown(f"""
            <div class="kpi-card" style="border-left: 5px solid #16a34a;">
                <div class="kpi-title">Total Drivers Roster</div>
                <div class="kpi-num" style="color:#16a34a;">{len(df_d)} Drivers</div>
            </div>
            """, unsafe_allow_html=True)

        df1, df2, df3 = st.columns([2, 2.5, 1.2])
        with df1:
            dr_stat_filter = st.selectbox("Filter Compliance:", ["All Drivers", "Due Action Needed", "Fully Compliant"])
        with df2:
            dr_search = st.text_input("Find Driver Name or Phone:")
        with df3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("+ Onboard Driver", key="add_dr_btn", use_container_width=True):
                st.session_state["show_add_driver_modal"] = True

        if st.session_state.get("show_add_driver_modal", False):
            with st.form("modal_add_driver_box"):
                nd_name = st.text_input("Full Name")
                nd_phone = st.text_input("Phone Number")
                nd_cdl = st.text_input("CDL Number")
                nd_cdl_exp = st.date_input("CDL Expiration")
                nd_med_exp = st.date_input("Medical Due Date")
                
                sub_d1, sub_d2 = st.columns(2)
                with sub_d1:
                    if st.form_submit_button("Save Driver", use_container_width=True) and nd_name:
                        new_dr_entry = {"Name": nd_name.strip(), "Telephone": nd_phone.strip(), "License Number": nd_cdl.strip(), "License Expiry": str(nd_cdl_exp), "Next Medical": str(nd_med_exp)}
                        df_d = pd.concat([df_d, pd.DataFrame([new_dr_entry])], ignore_index=True)
                        df_d.to_excel(DRIVERS_FILE, index=False)
                        st.session_state["show_add_driver_modal"] = False
                        st.success(f"Driver '{nd_name}' registered!")
                        st.rerun()
                with sub_d2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state["show_add_driver_modal"] = False
                        st.rerun()

        df_dr_view = df_d.copy()
        if dr_stat_filter == "Due Action Needed":
            df_dr_view = df_dr_view[df_dr_view["priority_order"] == 1]
        elif dr_stat_filter == "Fully Compliant":
            df_dr_view = df_dr_view[df_dr_view["priority_order"] == 2]

        if dr_search:
            ds = dr_search.strip().lower()
            df_dr_view = df_dr_view[
                df_dr_view["Name"].str.lower().str.contains(ds) |
                df_dr_view["Telephone"].str.lower().str.contains(ds)
            ]

        st.markdown("### 👤 Driver Roster & Safety Portal")

        d_cols = st.columns(4)
        for j, (_, d_row) in enumerate(df_dr_view.iterrows()):
            with d_cols[j % 4]:
                card_title = f"{d_row['Name']}"
                card_status = f"{d_row['priority_label']}"
                card_body = (
                    f"Status: {card_status}\n"
                    f"Phone: {d_row['Telephone']}\n"
                    f"Email: {d_row.get('E-mail', '-')}\n"
                    f"CDL #{d_row['License Number']}: {d_row['CDL_Status']}\n"
                    f"Medical Card: {d_row['Med_Status']}"
                )
                
                if st.button(f"{card_title}\n\n{card_body}", key=f"schneider_dr_{j}", use_container_width=True):
                    open_driver_dossier(d_row['Name'])
    else:
        st.info("No drivers data found.")

# -------------------------------------------------------------
# 3. MODÜL: DATA IMPORTS
# -------------------------------------------------------------
elif top_menu == "Data Imports (Samsara/ITS/Fuel)":
    st.markdown("#### Automated Telematics, Revenue & Fuel Ingestion")
    st.caption("Upload raw export files directly to sync live mileage, monthly settlement revenue, and fuel card expenses.")

    imp_col1, imp_col2, imp_col3 = st.columns(3)
    
    with imp_col1:
        st.markdown("##### 1. Samsara Odometer Sync (CSV)")
        st.write("Upload Samsara 'Vehicle Summary' or 'Mileage Export'.")
        samsara_file = st.file_uploader("Upload Samsara File (CSV)", type=["csv"], key="samsara_uploader")
        
        if samsara_file and st.button("Sync Samsara Mileages"):
            try:
                s_df = pd.read_csv(samsara_file)
                updated_count = 0
                cur = get_connection().cursor()
                asset_col = [c for c in s_df.columns if any(k in c.lower() for k in ["asset", "vehicle", "name"])][0]
                odo_col = [c for c in s_df.columns if any(k in c.lower() for k in ["odometer", "mileage", "miles"])][0]

                for _, s_row in s_df.iterrows():
                    u_num = extract_unit_no(str(s_row[asset_col]))
                    odo_str = str(s_row[odo_col]).replace(",", "").strip()
                    try:
                        odo_val = int(float(odo_str))
                        if odo_val > 0 and u_num:
                            cur.execute("UPDATE vehicles SET current_mileage = MAX(current_mileage, ?) WHERE unit_number = ?", (odo_val, u_num))
                            if cur.rowcount > 0:
                                updated_count += 1
                    except Exception:
                        pass
                cur.connection.commit()
                cur.connection.close()
                st.success(f"Synced odometers for {updated_count} vehicles!")
                st.rerun()
            except Exception as ex:
                st.error(f"Error: {ex}")

    with imp_col2:
        st.markdown("##### 2. ITS Gross Revenue Sync")
        st.write("Upload ITS Dispatch Monthly Gross or Settlement report.")
        its_file = st.file_uploader("Upload ITS Dispatch File", type=["xlsx", "xls", "csv"], key="its_uploader")
        
        if its_file and st.button("Sync ITS Gross Revenues"):
            try:
                its_df = pd.read_csv(its_file) if its_file.name.endswith(".csv") else pd.read_excel(its_file)
                updated_gross_count = 0
                cur = get_connection().cursor()
                unit_c = [c for c in its_df.columns if any(k in c.lower() for k in ["unit", "truck", "asset"])][0]
                gross_c = [c for c in its_df.columns if any(k in c.lower() for k in ["gross", "revenue", "amount", "total"])][0]

                for _, it_row in its_df.iterrows():
                    u_num = extract_unit_no(str(it_row[unit_c]))
                    gross_str = str(it_row[gross_c]).replace("$", "").replace(",", "").strip()
                    try:
                        gross_val = float(gross_str)
                        if gross_val >= 0 and u_num:
                            cur.execute("UPDATE vehicles SET monthly_gross = ? WHERE unit_number = ?", (gross_val, u_num))
                            if cur.rowcount > 0:
                                updated_gross_count += 1
                    except Exception:
                        pass
                cur.connection.commit()
                cur.connection.close()
                st.success(f"Synced gross revenues for {updated_gross_count} units!")
                st.rerun()
            except Exception as ex:
                st.error(f"Error: {ex}")

    with imp_col3:
        st.markdown("##### 3. Fuel Card Expense Sync")
        st.write("Upload fuel card statement (EFS / Fleet One).")
        fuel_file = st.file_uploader("Upload Fuel Statement", type=["xlsx", "xls", "csv"], key="fuel_uploader")
        
        if fuel_file and st.button("Sync Fuel Expenses"):
            try:
                fuel_df = pd.read_csv(fuel_file) if fuel_file.name.endswith(".csv") else pd.read_excel(fuel_file)
                updated_fuel_count = 0
                cur = get_connection().cursor()
                f_unit = [c for c in fuel_df.columns if any(k in c.lower() for k in ["unit", "truck", "asset", "card"])][0]
                f_cost = [c for c in fuel_df.columns if any(k in c.lower() for k in ["cost", "amount", "total", "price", "charge"])][0]

                for _, f_row in fuel_df.iterrows():
                    u_num = extract_unit_no(str(f_row[f_unit]))
                    cost_str = str(f_row[f_cost]).replace("$", "").replace(",", "").strip()
                    try:
                        cost_val = float(cost_str)
                        if cost_val >= 0 and u_num:
                            cur.execute("UPDATE vehicles SET monthly_fuel_cost = monthly_fuel_cost + ? WHERE unit_number = ?", (cost_val, u_num))
                            if cur.rowcount > 0:
                                updated_fuel_count += 1
                    except Exception:
                        pass
                cur.connection.commit()
                cur.connection.close()
                st.success(f"Synced fuel expenses for {updated_fuel_count} records!")
                st.rerun()
            except Exception as ex:
                st.error(f"Error: {ex}")

# -------------------------------------------------------------
# 4. MODÜL: SERVICE LEDGER
# -------------------------------------------------------------
elif top_menu == "Service Ledger":
    st.markdown("#### Equipment Service & Maintenance Record Entry")
    with st.form("service_samsara", clear_on_submit=True):
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            sel_u = st.selectbox("Select Equipment (Unit #)", df_v["unit_number"].tolist())
            s_date = st.date_input("Service Date")
        with sc2:
            s_type = st.selectbox("Service Type", ["Oil Change (PM)", "Tires / Brakes", "Annual DOT Inspection", "Breakdown / Repair", "Other"])
            s_mil = st.number_input("Odometer (mi)", min_value=0, step=1000)
        with sc3:
            s_cost = st.number_input("Cost ($)", min_value=0.0, step=50.0)
            s_inv = st.file_uploader("Upload Invoice (PDF/JPG)")

        if st.form_submit_button("Record Service Entry"):
            cur = get_connection().cursor()
            cur.execute("INSERT INTO logs (unit_number, log_date, log_type, mileage, cost) VALUES (?, ?, ?, ?, ?)", (sel_u, str(s_date), s_type, s_mil, s_cost))
            if s_type == "Oil Change (PM)" and s_mil > 0:
                cur.execute("UPDATE vehicles SET last_oil_mileage = ?, current_mileage = MAX(current_mileage, ?) WHERE unit_number = ?", (s_mil, s_mil, sel_u))
            cur.connection.commit()
            cur.connection.close()
            st.success("Service recorded successfully!")
            st.rerun()

# -------------------------------------------------------------
# MULTI-USER CHAT & DIRECT MESSAGING (ŞİRKET İÇİ MESAJLAŞMA)
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### 💬 Executive Dispatch & Team Chat")
    
    team_members = ["ismail@moonstarpa.com", "seha@moonstarpa.com", "dispatch@moonstarpa.com", "safety@moonstarpa.com"]
    current_active_profile = st.selectbox("My Active Profile", team_members)
    
    st.markdown("---")
    chat_mode = st.radio("Messaging Mode", ["Global Fleet Group", "Direct Message (DM)"], horizontal=True)
    
    recipient = "Everyone"
    if chat_mode == "Direct Message (DM)":
        other_members = [m for m in team_members if m != current_active_profile]
        recipient = st.selectbox("Select Recipient", other_members)
    
    st.markdown("---")
    with st.form("active_chat_form", clear_on_submit=True):
        msg_input = st.text_area("Type message...", placeholder="Write dispatch note or instructions...")
        if st.form_submit_button("Send Message", use_container_width=True) and msg_input.strip():
            cur = get_connection().cursor()
            timestamp_str = datetime.now().strftime("%m/%d %I:%M %p")
            cur.execute("INSERT INTO team_chat (sender, recipient, message, timestamp) VALUES (?, ?, ?, ?)", 
                        (current_active_profile, recipient, msg_input.strip(), timestamp_str))
            cur.connection.commit()
            cur.connection.close()
            st.success("Message sent!")
            st.rerun()

    st.markdown("#### 📜 Message History")
    chat_conn = get_connection()
    if chat_mode == "Global Fleet Group":
        chat_df = pd.read_sql_query("SELECT * FROM team_chat WHERE recipient = 'Everyone' ORDER BY id DESC LIMIT 30", chat_conn)
    else:
        chat_df = pd.read_sql_query("""
            SELECT * FROM team_chat 
            WHERE (sender = ? AND recipient = ?) OR (sender = ? AND recipient = ?) 
            ORDER BY id DESC LIMIT 30
        """, chat_conn, params=(current_active_profile, recipient, recipient, current_active_profile))
    chat_conn.close()
    
    if not chat_df.empty:
        for _, chat_row in chat_df.iterrows():
            is_me = chat_row['sender'] == current_active_profile
            bg_col = "#e0f2fe" if is_me else "#ffffff"
            align_style = "text-align: right;" if is_me else "text-align: left;"
            st.markdown(f"""
            <div style="background:{bg_col}; padding:8px 12px; border-radius:6px; margin-bottom:8px; border:1px solid #cbd5e1; {align_style}">
                <div style="font-size:10px; font-weight:700; color:#0284c7;">{chat_row['sender']} {('➔ ' + chat_row['recipient']) if chat_row['recipient'] != 'Everyone' else ''}</div>
                <div style="font-size:12px; color:#0f172a; margin-top:2px;">{chat_row['message']}</div>
                <div style="font-size:9px; color:#64748b; margin-top:2px;">{chat_row['timestamp']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No messages in this thread yet.")
