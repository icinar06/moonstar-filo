import glob
import os
import re
import shutil
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="MOONSTAR EXPRESS LLC — Enterprise Fleet Console",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# SAMSARA GERÇEK RENKLİ HTML KART TASARIMI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #f1f5f9 !important;
        color: #0f172a;
    }
    
    .top-header {
        background: linear-gradient(90deg, #0b1f3a 0%, #172554 60%, #0284c7 100%);
        padding: 12px 24px;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
        margin-bottom: 16px;
        border-bottom: 3px solid #38bdf8;
    }
    .brand-title {
        font-size: 20px;
        font-weight: 800;
        letter-spacing: 0.5px;
        color: #ffffff;
        margin: 0;
    }

    /* KPI Blokları */
    .kpi-box {
        background: #ffffff;
        border-radius: 8px;
        padding: 14px 18px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        margin-bottom: 16px;
    }
    .kpi-title {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        color: #64748b;
        letter-spacing: 0.5px;
    }
    .kpi-num {
        font-size: 22px;
        font-weight: 800;
        color: #0b1f3a;
        margin-top: 4px;
    }

    /* GERÇEK RENKLİ SAMSARA KARTLARI (HTML) */
    .samsara-card {
        background-color: #ffffff;
        border: 1.5px solid #cbd5e1;
        border-radius: 8px;
        padding: 14px 16px;
        min-height: 190px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        margin-bottom: 10px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .card-top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 6px;
    }
    .card-title-text {
        font-size: 14px;
        font-weight: 800;
        color: #0b1f3a;
    }
    
    /* Renkli Rozetler */
    .badge {
        font-size: 10px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-critical { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
    .badge-warning { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
    .badge-healthy { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }

    .card-info-line {
        font-size: 12px;
        margin-bottom: 4px;
        color: #334155;
    }
    .info-lbl {
        font-weight: 600;
        color: #64748b;
        display: inline-block;
        width: 85px;
    }
    .info-val {
        font-weight: 600;
        color: #0f172a;
    }
    .val-critical { color: #dc2626 !important; font-weight: 700; }
    .val-warning { color: #d97706 !important; font-weight: 700; }
    .val-healthy { color: #16a34a !important; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

DB_FILE = "fleet_database.db"
UPLOAD_DIR = "arsiv_dosyalari"
DRIVERS_FILE = "Drivers.xlsx"
SERVICE_LOGS_CSV = "Service logs.csv"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- LOGIN ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if os.path.exists("logo.jpg"):
            st.image("logo.jpg", width=220)
        st.markdown("### 🔒 MOONSTAR EXPRESS LLC — FLEET CONSOLE")
        with st.form("login_form"):
            email = st.text_input("Corporate Email", placeholder="ismail@moonstarpa.com")
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
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
        return "No Record", "badge-healthy", "val-healthy", 999
    try:
        dt = datetime.strptime(str(date_str).strip()[:10], "%Y-%m-%d").date()
        diff = (dt - datetime.now().date()).days
        if diff < 0:
            return f"Expired ({abs(diff)}d ago)", "badge-critical", "val-critical", diff
        elif diff <= 30:
            return f"Due in {diff}d", "badge-warning", "val-warning", diff
        else:
            return f"Valid ({diff}d left)", "badge-healthy", "val-healthy", diff
    except Exception:
        return "Invalid", "badge-healthy", "val-healthy", 999

def check_oil_status(row):
    if row.get("unit_type") == "TRAILER":
        return "Exempt (Trailer)", "badge-healthy", "val-healthy"
    try:
        c_m = int(row.get("current_mileage") or 0)
        l_o = int(row.get("last_oil_mileage") or 0)
        interval = int(row.get("oil_interval") or 25000)
        if interval <= 0 or (l_o == 0 and c_m == 0):
            return "No Record", "badge-healthy", "val-healthy"
        rem = interval - (c_m - l_o)
        if rem < 0:
            return f"Overdue by {abs(rem):,} mi", "badge-critical", "val-critical"
        elif rem <= 3000:
            return f"Due in {rem:,} mi", "badge-warning", "val-warning"
        else:
            return f"Valid ({rem:,} mi left)", "badge-healthy", "val-healthy"
    except Exception:
        return "Not Set", "badge-healthy", "val-healthy"

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
            message TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()

    c.execute("PRAGMA table_info(vehicles)")
    cols = [col[1] for col in c.fetchall()]
    if "monthly_gross" not in cols:
        c.execute("ALTER TABLE vehicles ADD COLUMN monthly_gross REAL DEFAULT 0.0")
    if "monthly_fuel_cost" not in cols:
        c.execute("ALTER TABLE vehicles ADD COLUMN monthly_fuel_cost REAL DEFAULT 0.0")
    if "hooked_trailer" not in cols:
        c.execute("ALTER TABLE vehicles ADD COLUMN hooked_trailer TEXT DEFAULT 'None'")
    if "current_location" not in cols:
        c.execute("ALTER TABLE vehicles ADD COLUMN current_location TEXT DEFAULT 'Yard'")
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

def evaluate_insp(row):
    today = datetime.now().date()
    for col in ["plate_expiry", "dot_inspection", "state_inspection"]:
        d_str = str(row.get(col, "")).strip()
        if d_str and d_str not in ["nan", "None", "", "-"]:
            try:
                diff = (datetime.strptime(d_str[:10], "%Y-%m-%d").date() - today).days
                if diff < 0:
                    return f"Expired ({abs(diff)}d ago)", "badge-critical", "val-critical"
                elif diff <= 30:
                    return f"Due in {diff}d", "badge-warning", "val-warning"
            except:
                pass
    return "Valid", "badge-healthy", "val-healthy"

if not df_v.empty:
    insp_res = df_v.apply(evaluate_insp, axis=1)
    df_v["insp_status"] = [r[0] for r in insp_res]
    df_v["insp_badge"] = [r[1] for r in insp_res]
    df_v["insp_val_cls"] = [r[2] for r in insp_res]

    oil_res = df_v.apply(check_oil_status, axis=1)
    df_v["oil_status"] = [r[0] for r in oil_res]
    df_v["oil_badge"] = [r[1] for r in oil_res]
    df_v["oil_val_cls"] = [r[2] for r in oil_res]

    def get_overall_priority(row):
        if row["oil_badge"] == "badge-critical" or row["insp_badge"] == "badge-critical":
            return "CRITICAL ACTION", "badge-critical", 1
        elif row["oil_badge"] == "badge-warning" or row["insp_badge"] == "badge-warning":
            return "DUE SOON", "badge-warning", 2
        else:
            return "READY", "badge-healthy", 3

    v_prio = df_v.apply(get_overall_priority, axis=1)
    df_v["priority_label"] = [p[0] for p in v_prio]
    df_v["priority_badge"] = [p[1] for p in v_prio]
    df_v["priority_order"] = [p[2] for p in v_prio]

    oil_crit_count = len(df_v[df_v["oil_badge"] == "badge-critical"])
    insp_crit_count = len(df_v[df_v["insp_badge"] == "badge-critical"])
    total_fleet_gross = df_v["monthly_gross"].sum()
    total_fleet_fuel = df_v["monthly_fuel_cost"].sum()
else:
    oil_crit_count, insp_crit_count, total_fleet_gross, total_fleet_fuel = 0, 0, 0.0, 0.0

# DRIVERS DATA
df_d = pd.DataFrame()
if os.path.exists(DRIVERS_FILE):
    df_d = pd.read_excel(DRIVERS_FILE)
    df_d = df_d[df_d["Name"].notna()].copy()
    df_d["License Expiry"] = df_d["License Expiry"].astype(str).str.strip()
    df_d["Next Medical"] = df_d["Next Medical"].astype(str).str.strip()
    df_d["Telephone"] = df_d["Telephone"].fillna("-").astype(str).str.strip()
    df_d["E-mail"] = df_d["E-mail"].fillna("-").astype(str).str.strip() if "E-mail" in df_d.columns else "-"
    df_d["License Number"] = df_d["License Number"].fillna("-").astype(str).str.strip() if "License Number" in df_d.columns else "-"

    cdl_res = df_d["License Expiry"].apply(check_date_status)
    df_d["CDL_Status"] = [r[0] for r in cdl_res]
    df_d["CDL_Badge"] = [r[1] for r in cdl_res]
    df_d["CDL_Val_Cls"] = [r[2] for r in cdl_res]

    med_res = df_d["Next Medical"].apply(check_date_status)
    df_d["Med_Status"] = [r[0] for r in med_res]
    df_d["Med_Badge"] = [r[1] for r in med_res]
    df_d["Med_Val_Cls"] = [r[2] for r in med_res]

    def get_dr_priority(row):
        if row["CDL_Badge"] == "badge-critical" or row["Med_Badge"] == "badge-critical":
            return "CRITICAL ACTION", "badge-critical", 1
        elif row["CDL_Badge"] == "badge-warning" or row["Med_Badge"] == "badge-warning":
            return "DUE SOON", "badge-warning", 2
        else:
            return "COMPLIANT", "badge-healthy", 3

    dr_prio = df_d.apply(get_dr_priority, axis=1)
    df_d["priority_label"] = [p[0] for p in dr_prio]
    df_d["priority_badge"] = [p[1] for p in dr_prio]
    df_d["priority_order"] = [p[2] for p in dr_prio]

dr_crit_count = len(df_d[df_d["priority_order"] == 1]) if not df_d.empty else 0

# -------------------------------------------------------------
# DİYALOG MODALLARI
# -------------------------------------------------------------
@st.dialog("Equipment Master Dossier & Financial P&L", width="large")
def open_equipment_dossier(unit_no):
    r_sel = df_v[df_v["unit_number"] == unit_no].iloc[0]
    st.subheader(f"Unit #{r_sel['unit_number']} — {r_sel['unit_type']} ({r_sel['company']})")
    
    t1, t2, t3, t4 = st.tabs(["Vehicle Specs & Pairing", "Financial P&L (Gross, Fuel, Net)", "DOT Audit Binder & Photos", "Decommission"])
    
    with t1:
        with st.form(f"form_unit_{unit_no}"):
            c1, c2, c3 = st.columns(3)
            with c1:
                e_drv = st.text_input("Assigned Driver", value=r_sel['driver'] or "")
                e_plt = st.text_input("Plate Number", value=r_sel['plate_number'] or "")
                e_vin = st.text_input("VIN / Serial", value=r_sel['vin'] or "")
            with c2:
                e_mdl = st.text_input("Make / Model / Year", value=r_sel['make_model'] or "")
                e_cur = st.number_input("Current Mileage (mi)", value=int(r_sel['current_mileage'] or 0))
                e_oil = st.number_input("Last Oil Change (mi)", value=int(r_sel['last_oil_mileage'] or 0))
            with c3:
                e_hook = st.text_input("Hooked Trailer #", value=str(r_sel.get('hooked_trailer', 'None')))
                e_loc = st.text_input("Current Yard / Location", value=str(r_sel.get('current_location', 'Yard')))
                e_dot = st.text_input("Annual DOT (YYYY-MM-DD)", value=str(r_sel['dot_inspection'] or ""))

            st.markdown(f"**Maintenance:** Oil: `{r_sel['oil_status']}` | DOT: `{r_sel['insp_status']}`")

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
        
        st.markdown("**Recorded Service & Maintenance Logs:**")
        unit_logs = df_logs[df_logs["unit_number"] == unit_no]
        if not unit_logs.empty:
            st.dataframe(unit_logs[["log_date", "log_type", "mileage", "cost", "notes"]], use_container_width=True, hide_index=True)
        else:
            st.caption("No maintenance expenses recorded for this unit.")

    with t3:
        st.markdown("**DOT Inspection Binder (Instant Compliance Access)**")
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
            st.markdown("**Archived Documents & Photos:**")
            found_v = [f for f in os.listdir(UPLOAD_DIR) if f"EQUIP_{unit_no}_" in f]
            if found_v:
                for doc in found_v:
                    st.write(f"📄 `{doc}`")
            else:
                st.caption("No files uploaded for this unit yet.")

    with t4:
        st.warning(f"Permanently remove Unit #{unit_no} from active operations?")
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

            st.markdown(f"**Compliance Status:** CDL: `{d_sel['CDL_Status']}` | Medical: `{d_sel['Med_Status']}`")

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
        st.markdown("**Upload CDL Scan, Medical Card, Truck Check-in/out Photos, Citations**")
        d_up1, d_up2 = st.columns([2, 3])
        with d_up1:
            dr_cat = st.selectbox("Category", ["CDL Scan", "Medical Card Certificate", "Truck Check-in Photo", "Truck Check-out Photo", "Accident Photo", "DOT Citation"], key=f"drcat_{driver_name}")
            dr_fil = st.file_uploader("Select File / Photo", type=["pdf", "png", "jpg", "jpeg"], key=f"drfil_{driver_name}")
            if dr_fil and st.button("Save to Driver Dossier", key=f"drbtn_{driver_name}"):
                save_dr = f"DR_{driver_name.replace(' ', '_')}_{dr_cat.replace(' ', '_')}_{dr_fil.name}"
                with open(os.path.join(UPLOAD_DIR, save_dr), "wb") as f:
                    f.write(dr_fil.getbuffer())
                st.success("Saved to driver dossier!")
                st.rerun()
        with d_up2:
            st.markdown("**Archived Driver Documents & Photos:**")
            found_dr = [f for f in os.listdir(UPLOAD_DIR) if f"DR_{driver_name.replace(' ', '_')}_" in f]
            if found_dr:
                for d in found_dr:
                    st.write(f"📄 `{d}`")
            else:
                st.caption("No files recorded for this driver yet.")

    with dt3:
        st.warning(f"Offboard and remove {driver_name} from active fleet drivers?")
        if st.button("🚨 Yes, Offboard Driver", type="secondary"):
            df_new = df_d[df_d["Name"] != driver_name]
            df_new.to_excel(DRIVERS_FILE, index=False)
            st.rerun()

# -------------------------------------------------------------
# TOP NAVBAR
# -------------------------------------------------------------
st.markdown(f"""
<div class="top-header">
    <div style="display:flex; align-items:center; gap:16px;">
        <span class="brand-title">MOONSTAR <span style="color:#38bdf8;">EXPRESS LLC</span></span>
        <span style="font-size:12px; color:#93c5fd; border-left:1px solid #334155; padding-left:12px;">Samsara, ITS Dispatch & Fuel Analytics</span>
    </div>
    <div style="font-size:12px; color:#f1f5f9;">
        User: <b>{st.session_state.get('current_user')}</b>
    </div>
</div>
""", unsafe_allow_html=True)

nav_c1, nav_c2 = st.columns([5, 1])
with nav_c1:
    top_menu = st.radio(
        "Navigation",
        ["Trucks & Trailers", "Drivers Compliance", "Data Imports (Samsara/ITS/Fuel)", "Dispatch Team Chat", "Service Ledger"],
        horizontal=True,
        label_visibility="collapsed"
    )
with nav_c2:
    if st.button("Sign Out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. MODÜL: TRUCKS & TRAILERS (KUTU ÜZERİNDE GERÇEK RENKLİ ROZETLER)
# -------------------------------------------------------------
if top_menu == "Trucks & Trailers":
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="kpi-box" style="border-left: 5px solid #0284c7;">
            <div class="kpi-title">Monthly Fleet Gross (ITS)</div>
            <div class="kpi-num" style="color:#0284c7;">${total_fleet_gross:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="kpi-box" style="border-left: 5px solid #dc2626;">
            <div class="kpi-title">Total Monthly Fuel Cost</div>
            <div class="kpi-num" style="color:#dc2626;">${total_fleet_fuel:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="kpi-box" style="border-left: 5px solid #d97706;">
            <div class="kpi-title">Inspections Overdue / Due</div>
            <div class="kpi-num" style="color:#d97706;">{insp_crit_count} Assets</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="kpi-box" style="border-left: 5px solid #16a34a;">
            <div class="kpi-title">Active Fleet Total</div>
            <div class="kpi-num" style="color:#16a34a;">{len(df_v[df_v['unit_type']=='TRUCK'])} Trucks / {len(df_v[df_v['unit_type']=='TRAILER'])} Trailers</div>
        </div>
        """, unsafe_allow_html=True)

    f1, f2, f3, f4 = st.columns([1.5, 2, 2.5, 1.2])
    with f1:
        f_type = st.selectbox("Equipment Type:", ["All Equipment", "Trucks Only", "Trailers Only"])
    with f2:
        f_stat = st.selectbox(
            "Filter Condition:", 
            [
                f"Needs Urgent Action ({len(df_v[df_v['priority_order']==1])})",
                f"Approaching Deadlines ({len(df_v[df_v['priority_order']==2])})",
                f"All Healthy ({len(df_v[df_v['priority_order']==3])})",
                "Show Complete Fleet"
            ]
        )
    with f3:
        f_srch = st.text_input("Find Unit, Driver or Model:", placeholder="Type Unit # (e.g. 12)...")
    with f4:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        btn_add_v = st.button("+ Add Equipment", use_container_width=True)

    if btn_add_v:
        with st.form("new_veh_top_box"):
            st.markdown("##### Register New Equipment")
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
            if st.form_submit_button("Save Asset") and nu_unit:
                cur = conn.cursor()
                cur.execute("INSERT INTO vehicles (company, unit_type, unit_number, driver, vin, plate_number, make_model) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (nu_comp, nu_type, nu_unit.strip(), nu_driver.strip(), nu_vin.strip(), nu_plate.strip(), nu_model.strip()))
                conn.commit()
                st.success(f"{nu_type} #{nu_unit} added successfully!")
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

    st.caption(f"Showing **{len(df_filtered)}** equipment units (Click any card to open dossier):")

    # 4 KOLONLU GERÇEK HTML KARTLAR (ÜSTÜNE TIKLAYINCA DOSYA AÇILIR)
    cols = st.columns(4)
    for idx, (_, r) in enumerate(df_filtered.iterrows()):
        with cols[idx % 4]:
            driver_str = r['driver'] if r['driver'] else 'Unassigned'
            hook_str = f"Trailer #{r['hooked_trailer']}" if r['hooked_trailer'] and r['hooked_trailer'] != 'None' else 'Bobtail'
            
            # Kartın HTML Görsel Tasarımı (Renkli Rozetler ile)
            card_html = f"""
            <div class="samsara-real-card">
                <div>
                    <div class="card-top-row">
                        <span class="card-title-text">UNIT #{r['unit_number']} <span style="font-size:11px; color:#64748b;">({r['unit_type']})</span></span>
                        <span class="badge {r['priority_badge']}">{r['priority_label']}</span>
                    </div>
                    <div class="card-info-line">
                        <span class="info-lbl">Driver:</span>
                        <span class="info-val">{driver_str}</span>
                    </div>
                    <div class="card-info-line">
                        <span class="info-lbl">Hooked:</span>
                        <span class="info-val">{hook_str}</span>
                    </div>
                    <div class="card-info-line">
                        <span class="info-lbl">Oil Service:</span>
                        <span class="info-val {r['oil_val_cls']}">{r['oil_status']}</span>
                    </div>
                    <div class="card-info-line">
                        <span class="info-lbl">Annual DOT:</span>
                        <span class="info-val {r['insp_val_cls']}">{r['insp_status']}</span>
                    </div>
                    <div class="card-info-line" style="border-top: 1px dashed #e2e8f0; margin-top:6px; padding-top:4px;">
                        <span class="info-lbl">Gross | Fuel:</span>
                        <span class="info-val" style="color:#0284c7;">${r['monthly_gross']:,.0f} | <span style="color:#dc2626;">${r['monthly_fuel_cost']:,.0f}</span></span>
                    </div>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            if st.button(f"Open Dossier 📂 #{r['unit_number']}", key=f"html_card_btn_{r['unit_number']}", use_container_width=True):
                open_equipment_dossier(r['unit_number'])

# -------------------------------------------------------------
# 2. MODÜL: DRIVERS COMPLIANCE
# -------------------------------------------------------------
elif top_menu == "Drivers Compliance":
    if not df_d.empty:
        dk1, dk2, dk3 = st.columns(3)
        with dk1:
            st.markdown(f"""
            <div class="kpi-box" style="border-left: 5px solid #dc2626;">
                <div class="kpi-title">CDL / Medical Expired</div>
                <div class="kpi-num" style="color:#dc2626;">{dr_crit_count} Drivers</div>
            </div>
            """, unsafe_allow_html=True)
        with dk2:
            st.markdown(f"""
            <div class="kpi-box" style="border-left: 5px solid #d97706;">
                <div class="kpi-title">Expiring in 30 Days</div>
                <div class="kpi-num" style="color:#d97706;">{len(df_d[df_d['priority_order']==2])} Drivers</div>
            </div>
            """, unsafe_allow_html=True)
        with dk3:
            st.markdown(f"""
            <div class="kpi-box" style="border-left: 5px solid #16a34a;">
                <div class="kpi-title">Total Drivers Roster</div>
                <div class="kpi-num" style="color:#16a34a;">{len(df_d)} Drivers</div>
            </div>
            """, unsafe_allow_html=True)

        df1, df2, df3 = st.columns([2, 2.5, 1.2])
        with df1:
            dr_stat_filter = st.selectbox("Filter Compliance:", ["All Drivers", "Critical Action Needed", "Expiring Soon", "Fully Compliant"])
        with df2:
            dr_search = st.text_input("Find Driver Name or Phone:")
        with df3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            btn_add_d = st.button("+ Onboard Driver", use_container_width=True)

        if btn_add_d:
            with st.form("modal_add_driver_box"):
                st.markdown("##### Onboard New Driver")
                nd_name = st.text_input("Full Name")
                nd_phone = st.text_input("Phone Number")
                nd_cdl = st.text_input("CDL Number")
                nd_cdl_exp = st.date_input("CDL Expiration")
                nd_med_exp = st.date_input("Medical Due Date")
                if st.form_submit_button("Save Driver") and nd_name:
                    new_dr_entry = {"Name": nd_name.strip(), "Telephone": nd_phone.strip(), "License Number": nd_cdl.strip(), "License Expiry": str(nd_cdl_exp), "Next Medical": str(nd_med_exp)}
                    df_d = pd.concat([df_d, pd.DataFrame([new_dr_entry])], ignore_index=True)
                    df_d.to_excel(DRIVERS_FILE, index=False)
                    st.success(f"Driver '{nd_name}' registered!")
                    st.rerun()

        df_dr_view = df_d.copy()
        if dr_stat_filter == "Critical Action Needed":
            df_dr_view = df_dr_view[df_dr_view["priority_order"] == 1]
        elif dr_stat_filter == "Expiring Soon":
            df_dr_view = df_dr_view[df_dr_view["priority_order"] == 2]
        elif dr_stat_filter == "Fully Compliant":
            df_dr_view = df_dr_view[df_dr_view["priority_order"] == 3]

        if dr_search:
            ds = dr_search.strip().lower()
            df_dr_view = df_dr_view[
                df_dr_view["Name"].str.lower().str.contains(ds) |
                df_dr_view["Telephone"].str.lower().str.contains(ds)
            ]

        st.caption(f"Showing **{len(df_dr_view)}** driver files:")

        d_cols = st.columns(4)
        for j, (_, d_row) in enumerate(df_dr_view.iterrows()):
            with d_cols[j % 4]:
                st.markdown(f"""
                <div class="samsara-real-card">
                    <div>
                        <div class="card-top-row">
                            <span class="card-title-text" style="font-size:13px;">{d_row['Name']}</span>
                            <span class="badge {d_row['priority_badge']}">{d_row['priority_label']}</span>
                        </div>
                        <div class="card-info-line">
                            <span class="info-lbl">Phone:</span>
                            <span class="info-val">{d_row['Telephone']}</span>
                        </div>
                        <div class="card-info-line">
                            <span class="info-lbl">CDL #:</span>
                            <span class="info-val">{d_row['License Number']}</span>
                        </div>
                        <div class="card-info-line">
                            <span class="info-lbl">CDL Expiry:</span>
                            <span class="info-val {d_row['CDL_Val_Cls']}">{d_row['CDL_Status']}</span>
                        </div>
                        <div class="card-info-line">
                            <span class="info-lbl">Medical:</span>
                            <span class="info-val {d_row['Med_Val_Cls']}">{d_row['Med_Status']}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Open Dossier 📂 {d_row['Name'].split('/')[0]}", key=f"html_dr_btn_{j}", use_container_width=True):
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
                cur = conn.cursor()
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
                conn.commit()
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
                cur = conn.cursor()
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
                conn.commit()
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
                cur = conn.cursor()
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
                conn.commit()
                st.success(f"Synced fuel expenses for {updated_fuel_count} records!")
                st.rerun()
            except Exception as ex:
                st.error(f"Error: {ex}")

# -------------------------------------------------------------
# 4. MODÜL: DISPATCH TEAM CHAT
# -------------------------------------------------------------
elif top_menu == "Dispatch Team Chat":
    st.markdown("#### Dispatch Operations & Shift Notes")
    with st.form("chat_form_samsara", clear_on_submit=True):
        cm1, cm2 = st.columns([5, 1])
        with cm1:
            msg_txt = st.text_input("Write shift note...", placeholder="E.g., Unit 14 delivered in Laredo, now available for reloading.")
        with cm2:
            if st.form_submit_button("Post Note") and msg_txt.strip():
                cur = conn.cursor()
                now_s = datetime.now().strftime("%m/%d/%Y %I:%M %p")
                cur.execute("INSERT INTO team_chat (sender, message, timestamp) VALUES (?, ?, ?)", (st.session_state.get("current_user"), msg_txt.strip(), now_s))
                conn.commit()
                st.rerun()

    df_c = pd.read_sql_query("SELECT * FROM team_chat ORDER BY id DESC LIMIT 50", conn)
    for _, r in df_c.iterrows():
        st.markdown(f"""
        <div style="background:#ffffff; border-left:4px solid #0284c7; padding:10px 14px; border-radius:6px; margin-bottom:8px; border:1px solid #e2e8f0; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
            <b style="color:#0b1f3a; font-size:13px;">{r['sender']}</b> <span style="font-size:11px; color:#64748b; margin-left:8px;">🕒 {r['timestamp']}</span>
            <div style="margin-top:3px; font-size:13px; color:#0f172a;">{r['message']}</div>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# 5. MODÜL: SERVICE LEDGER
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
            cur = conn.cursor()
            cur.execute("INSERT INTO logs (unit_number, log_date, log_type, mileage, cost) VALUES (?, ?, ?, ?, ?)", (sel_u, str(s_date), s_type, s_mil, s_cost))
            if s_type == "Oil Change (PM)" and s_mil > 0:
                cur.execute("UPDATE vehicles SET last_oil_mileage = ?, current_mileage = MAX(current_mileage, ?) WHERE unit_number = ?", (s_mil, s_mil, sel_u))
            conn.commit()
            st.success("Service recorded successfully!")
            st.rerun()
