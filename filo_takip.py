import glob
import os
import re
import shutil
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="MOONSTAR EXPRESS LLC — Fleet Console",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# MODERN SAMSARA-STYLE SQUARE TILE THEME (MINIMALIST & EYE-FRIENDLY)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #f8fafc !important;
    }
    
    .top-header {
        background: linear-gradient(90deg, #0b1f3a 0%, #172554 60%, #0284c7 100%);
        padding: 10px 20px;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
        margin-bottom: 14px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }
    .brand-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 18px;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
    }

    /* KARE VE TERTEMİZ KUTUCUK BUTONLARI (SQUARE TILES) */
    div[data-testid*="stButton"] > button {
        background: #ffffff !important;
        border: 1.5px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 10px 8px !important;
        height: 85px !important;
        width: 100% !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        color: #0b1f3a !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid*="stButton"] > button:hover {
        border-color: #0284c7 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 10px rgba(2, 132, 199, 0.15) !important;
    }
    div[data-testid*="stButton"] > button p {
        font-family: 'Montserrat', sans-serif !important;
        font-size: 15px !important;
        font-weight: 800 !important;
        margin: 0 !important;
        line-height: 1.2 !important;
        text-align: center !important;
        white-space: pre-line !important;
    }

    /* Üst Filtre Segmentleri */
    .filter-bar {
        background: #ffffff;
        padding: 10px 16px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin-bottom: 14px;
    }
</style>
""", unsafe_allow_html=True)

DB_FILE = "fleet_database.db"
UPLOAD_DIR = "arsiv_dosyalari"
DRIVERS_FILE = "Drivers.xlsx"
FLEET_EXCEL = "Başlıksız e-tablo (2) copy 2.xlsx"
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
        st.markdown("### 🔒 MOONSTAR EXPRESS LLC — TMS LOGIN")
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
        return "No Date", "⚪", 999
    try:
        dt = datetime.strptime(str(date_str).strip()[:10], "%Y-%m-%d").date()
        diff = (dt - datetime.now().date()).days
        if diff < 0:
            return f"Expired ({abs(diff)}d ago)", "🔴", diff
        elif diff <= 30:
            return f"Due Soon ({diff}d)", "🟡", diff
        else:
            return f"Valid ({diff}d)", "🟢", diff
    except Exception:
        return "Invalid", "⚪", 999

def check_oil_status(row):
    if row.get("unit_type") == "TRAILER":
        return "Exempt (Trailer)", "🟢", "-"
    try:
        c_m = int(row.get("current_mileage") or 0)
        l_o = int(row.get("last_oil_mileage") or 0)
        interval = int(row.get("oil_interval") or 25000)
        if interval <= 0 or (l_o == 0 and c_m == 0):
            return "No Record", "🟢", "-"
        rem = interval - (c_m - l_o)
        if rem < 0:
            return f"Overdue ({abs(rem):,} mi)", "🔴", f"{rem:,}"
        elif rem <= 3000:
            return f"Due Soon ({rem:,} mi)", "🟡", f"{rem:,}"
        else:
            return f"Good ({rem:,} mi)", "🟢", f"{rem:,}"
    except Exception:
        return "Calc Error", "🟢", "-"

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

def evaluate_insp(row):
    today = datetime.now().date()
    for col in ["plate_expiry", "dot_inspection", "state_inspection"]:
        d_str = str(row.get(col, "")).strip()
        if d_str and d_str not in ["nan", "None", "", "-"]:
            try:
                diff = (datetime.strptime(d_str[:10], "%Y-%m-%d").date() - today).days
                if diff < 0:
                    return "OVERDUE", "🔴"
                elif diff <= 30:
                    return "EXPIRING", "🟡"
            except:
                pass
    return "VALID", "🟢"

insp_res = df_v.apply(evaluate_insp, axis=1)
df_v["insp_status"] = [r[0] for r in insp_res]
df_v["insp_dot"] = [r[1] for r in insp_res]

oil_res = df_v.apply(check_oil_status, axis=1)
df_v["oil_status"] = [r[0] for r in oil_res]
df_v["oil_dot"] = [r[1] for r in oil_res]
df_v["remaining_oil_mi"] = [r[2] for r in oil_res]

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
    
    df_d["CDL_Status"] = df_d["License Expiry"].apply(lambda d: check_date_status(d)[0])
    df_d["CDL_Dot"] = df_d["License Expiry"].apply(lambda d: check_date_status(d)[1])
    df_d["Med_Status"] = df_d["Next Medical"].apply(lambda d: check_date_status(d)[0])
    df_d["Med_Dot"] = df_d["Next Medical"].apply(lambda d: check_date_status(d)[1])

# -------------------------------------------------------------
# DİYALOG MODALLARI (KAREYE BASILINCA AÇILAN TEMİZ DOSYA PENCERESİ)
# -------------------------------------------------------------
@st.dialog("Equipment File", width="large")
def open_equipment_dossier(unit_no):
    r_sel = df_v[df_v["unit_number"] == unit_no].iloc[0]
    st.subheader(f"Unit #{r_sel['unit_number']} — {r_sel['unit_type']} ({r_sel['company']})")
    
    t1, t2, t3 = st.tabs(["📋 Details & Edit", "📸 Photos & Documents", "🚨 Delete Unit"])
    
    with t1:
        with st.form(f"f_edit_v_{unit_no}"):
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
                e_reg = st.text_input("Registration Exp (YYYY-MM-DD)", value=str(r_sel['plate_expiry'] or ""))
                e_dot = st.text_input("Annual DOT (YYYY-MM-DD)", value=str(r_sel['dot_inspection'] or ""))
                e_ste = st.text_input("State Insp (YYYY-MM-DD)", value=str(r_sel['state_inspection'] or ""))
            
            st.info(f"🛢️ Oil Status: {r_sel['oil_status']}  |  📋 DOT Status: {r_sel['insp_status']}")

            if st.form_submit_button("💾 Save Changes"):
                cur = conn.cursor()
                cur.execute("""
                    UPDATE vehicles 
                    SET driver=?, plate_number=?, vin=?, make_model=?, current_mileage=?, last_oil_mileage=?, plate_expiry=?, dot_inspection=?, state_inspection=?
                    WHERE unit_number=?
                """, (e_drv, e_plt, e_vin, e_mdl, e_cur, e_oil, e_reg, e_dot, e_ste, unit_no))
                conn.commit()
                st.success("Vehicle updated successfully!")
                st.rerun()

    with t2:
        st.markdown("**Attach Registration, Inspection Sheets, or Condition Photos**")
        up1, up2 = st.columns([2, 3])
        with up1:
            f_cat = st.selectbox("Document Type", ["Registration Card", "Annual DOT Sheet", "Truck Condition Photo", "Insurance Certificate", "Repair Order"], key=f"fcat_{unit_no}")
            f_upl = st.file_uploader("Select File / Image", type=["pdf", "png", "jpg", "jpeg"], key=f"fupl_{unit_no}")
            if f_upl and st.button("Upload to Dossier", key=f"fbtn_{unit_no}"):
                save_f = f"EQUIP_{unit_no}_{f_cat.replace(' ', '_')}_{f_upl.name}"
                with open(os.path.join(UPLOAD_DIR, save_f), "wb") as f:
                    f.write(f_upl.getbuffer())
                st.success("File saved!")
                st.rerun()
        with up2:
            st.markdown("**Archived Equipment Documents:**")
            found_v = [f for f in os.listdir(UPLOAD_DIR) if f"EQUIP_{unit_no}_" in f]
            if found_v:
                for doc in found_v:
                    st.write(f"📄 `{doc}`")
            else:
                st.caption("No files uploaded for this unit yet.")

    with t3:
        st.warning(f"Permanently remove Unit #{unit_no} from the database?")
        if st.button("🚨 Yes, Delete Permanently", type="secondary"):
            cur = conn.cursor()
            cur.execute("DELETE FROM vehicles WHERE unit_number = ?", (unit_no,))
            conn.commit()
            st.rerun()

@st.dialog("Driver File", width="large")
def open_driver_dossier(driver_name):
    d_sel = df_d[df_d["Name"] == driver_name].iloc[0]
    st.subheader(f"Driver File: {d_sel['Name']}")
    
    dt1, dt2, dt3 = st.tabs(["📋 Profile & Compliance", "📸 Photos & Docs", "🚨 Remove Driver"])
    
    with dt1:
        with st.form(f"f_edit_dr_{driver_name}"):
            dc1, dc2 = st.columns(2)
            with dc1:
                dr_p = st.text_input("Phone Number", value=d_sel['Telephone'])
                dr_e = st.text_input("Email", value=d_sel['E-mail'])
                dr_c = st.text_input("CDL Number", value=d_sel['License Number'])
            with dc2:
                dr_ce = st.text_input("CDL Expiry (YYYY-MM-DD)", value=d_sel['License Expiry'])
                dr_me = st.text_input("Next Medical (YYYY-MM-DD)", value=d_sel['Next Medical'])
            
            st.info(f"🪪 CDL Status: {d_sel['CDL_Status']}  |  🏥 Medical Card: {d_sel['Med_Status']}")

            if st.form_submit_button("💾 Save Profile"):
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
            if dr_fil and st.button("Save to Dossier", key=f"drbtn_{driver_name}"):
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
        st.warning(f"Offboard and delete {driver_name} from active drivers?")
        if st.button("🚨 Yes, Offboard Driver", type="secondary"):
            df_new = df_d[df_d["Name"] != driver_name]
            df_new.to_excel(DRIVERS_FILE, index=False)
            st.rerun()

# -------------------------------------------------------------
# TOP NAVBAR (TAM EKRAN FERAH YAPI)
# -------------------------------------------------------------
st.markdown(f"""
<div class="top-header">
    <div style="display:flex; align-items:center; gap:16px;">
        <span class="brand-title">MOONSTAR <span style="color:#38bdf8;">EXPRESS LLC</span></span>
        <span style="font-size:12px; color:#93c5fd; border-left:1px solid #334155; padding-left:12px;">Fleet Operations</span>
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
        ["🚛 Trucks & Trailers", "👤 Drivers Compliance", "💬 Dispatch Team Chat", "🔧 Service Ledger"],
        horizontal=True,
        label_visibility="collapsed"
    )
with nav_c2:
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. MODÜL: TRUCKS & TRAILERS (KARE MINIMAL KUTUCUKLAR)
# -------------------------------------------------------------
if top_menu == "🚛 Trucks & Trailers":
    # Genel Araç Sağlığı
    def get_asset_dot(row):
        if row["oil_dot"] == "🔴" or row["insp_dot"] == "🔴":
            return "🔴", "CRITICAL"
        elif row["oil_dot"] == "🟡" or row["insp_dot"] == "🟡":
            return "🟡", "WARNING"
        else:
            return "🟢", "HEALTHY"

    res_dot = df_v.apply(get_asset_dot, axis=1)
    df_v["status_dot"] = [x[0] for x in res_dot]
    df_v["status_group"] = [x[1] for x in res_dot]

    crit_count = len(df_v[df_v["status_group"] == "CRITICAL"])
    warn_count = len(df_v[df_v["status_group"] == "WARNING"])
    good_count = len(df_v[df_v["status_group"] == "HEALTHY"])

    # ÜST FİLTRE & EYLEM BARI (TEK SATIR)
    f1, f2, f3, f4 = st.columns([2, 2, 2.5, 1.2])
    with f1:
        v_filter_type = st.selectbox("Equipment:", ["All Equipment", "Trucks Only", "Trailers Only"])
    with f2:
        v_filter_stat = st.selectbox(
            "Status Filter:", 
            [
                f"🚨 Critical Action Needed ({crit_count})",
                f"🟡 Approaching Deadlines ({warn_count})",
                f"🟢 All Healthy ({good_count})",
                "Show All Equipment"
            ]
        )
    with f3:
        v_search = st.text_input("Quick Find Unit # or Driver:", placeholder="Type unit # (e.g. 12)...")
    with f4:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        btn_add_veh = st.button("➕ New Unit", use_container_width=True)

    if btn_add_veh:
        with st.form("modal_add_v_top"):
            st.markdown("##### ➕ Register New Equipment")
            ac1, ac2 = st.columns(2)
            with ac1:
                n_cmp = st.selectbox("Company", ["MOONSTAR", "LIONSTAR"])
                n_typ = st.selectbox("Type", ["TRUCK", "TRAILER"])
                n_unt = st.text_input("Unit Number")
            with ac2:
                n_drv = st.text_input("Assigned Driver")
                n_plt = st.text_input("Plate Number")
                n_vin = st.text_input("VIN")
            if st.form_submit_button("Save Asset") and n_unt:
                cur = conn.cursor()
                cur.execute("INSERT INTO vehicles (company, unit_type, unit_number, driver, plate_number, vin) VALUES (?, ?, ?, ?, ?, ?)",
                            (n_cmp, n_typ, n_unt.strip(), n_drv.strip(), n_plt.strip(), n_vin.strip()))
                conn.commit()
                st.success(f"Unit #{n_unt} added!")
                st.rerun()

    df_show = df_v.copy()
    if v_filter_type == "Trucks Only":
        df_show = df_show[df_show["unit_type"] == "TRUCK"]
    elif v_filter_type == "Trailers Only":
        df_show = df_show[df_show["unit_type"] == "TRAILER"]

    if "Critical Action Needed" in v_filter_stat:
        df_show = df_show[df_show["status_group"] == "CRITICAL"]
    elif "Approaching Deadlines" in v_filter_stat:
        df_show = df_show[df_show["status_group"] == "WARNING"]
    elif "All Healthy" in v_filter_stat:
        df_show = df_show[df_show["status_group"] == "HEALTHY"]

    if v_search:
        vs = v_search.strip().lower()
        df_show = df_show[
            df_show["unit_number"].str.lower().str.contains(vs) |
            df_show["driver"].str.lower().str.contains(vs)
        ]

    st.caption(f"Displaying **{len(df_show)}** equipment units (Click any square to open full details):")

    # 8 KOLONLU YEPYENİ KARE KUTUCUKLAR (SQUARE APP ICONS)
    cols_grid = st.columns(8)
    for idx, (_, r) in enumerate(df_show.iterrows()):
        with cols_grid[idx % 8]:
            unit_label = f"{r['status_dot']} #{r['unit_number']}\n{r['unit_type'][:2]}"
            if st.button(unit_label, key=f"sq_v_{r['unit_number']}", use_container_width=True, help=f"Driver: {r['driver'] or 'None'} | Oil: {r['oil_status']} | DOT: {r['insp_status']}"):
                open_equipment_dossier(r['unit_number'])

# -------------------------------------------------------------
# 2. MODÜL: DRIVERS COMPLIANCE (KARE MINIMAL KUTUCUKLAR)
# -------------------------------------------------------------
elif top_menu == "👤 Drivers Compliance":
    if not df_d.empty:
        def get_dr_dot(row):
            if row["CDL_Dot"] == "🔴" or row["Med_Dot"] == "🔴":
                return "🔴", "CRITICAL"
            elif row["CDL_Dot"] == "🟡" or row["Med_Dot"] == "🟡":
                return "🟡", "WARNING"
            else:
                return "🟢", "HEALTHY"

        res_dr_dot = df_d.apply(get_dr_dot, axis=1)
        df_d["status_dot"] = [x[0] for x in res_dr_dot]
        df_d["status_group"] = [x[1] for x in res_dr_dot]

        d_crit = len(df_d[df_d["status_group"] == "CRITICAL"])
        d_warn = len(df_d[df_d["status_group"] == "WARNING"])
        d_good = len(df_d[df_d["status_group"] == "HEALTHY"])

        df1, df2, df3, df4 = st.columns([2, 2, 2.5, 1.2])
        with df1:
            d_filter = st.selectbox(
                "Driver Status:", 
                [
                    f"🚨 Action Needed ({d_crit})",
                    f"🟡 Expiring Soon ({d_warn})",
                    f"🟢 Compliant ({d_good})",
                    "Show All Drivers"
                ]
            )
        with df2:
            d_search = st.text_input("Find Driver Name or Phone:")
        with df3:
            st.write("")
        with df4:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            btn_add_dr = st.button("➕ Onboard", use_container_width=True)

        if btn_add_dr:
            with st.form("modal_add_dr_top"):
                st.markdown("##### ➕ Onboard New Driver")
                nd_n = st.text_input("Full Name")
                nd_p = st.text_input("Phone Number")
                nd_c = st.text_input("CDL Number")
                nd_ce = st.date_input("CDL Expiration")
                nd_me = st.date_input("Medical Due Date")
                if st.form_submit_button("Save Driver") and nd_n:
                    new_r = {"Name": nd_n.strip(), "Telephone": nd_p.strip(), "License Number": nd_c.strip(), "License Expiry": str(nd_ce), "Next Medical": str(nd_me)}
                    df_d = pd.concat([df_d, pd.DataFrame([new_r])], ignore_index=True)
                    df_d.to_excel(DRIVERS_FILE, index=False)
                    st.success(f"Driver '{nd_n}' registered!")
                    st.rerun()

        df_dr_show = df_d.copy()
        if "Action Needed" in d_filter:
            df_dr_show = df_dr_show[df_dr_show["status_group"] == "CRITICAL"]
        elif "Expiring Soon" in d_filter:
            df_dr_show = df_dr_show[df_dr_show["status_group"] == "WARNING"]
        elif "Compliant" in d_filter:
            df_dr_show = df_dr_show[df_dr_show["status_group"] == "HEALTHY"]

        if d_search:
            d_s = d_search.strip().lower()
            df_dr_show = df_dr_show[
                df_dr_show["Name"].str.lower().str.contains(d_s) |
                df_dr_show["Telephone"].str.lower().str.contains(d_s)
            ]

        st.caption(f"Displaying **{len(df_dr_show)}** driver profiles (Click square to open full dossier):")

        # 6 KOLONLU KARE ŞOFÖR KUTUCUKLARI
        cols_dr_grid = st.columns(6)
        for idx, (_, d_row) in enumerate(df_dr_show.iterrows()):
            with cols_dr_grid[idx % 6]:
                # İsimleri temiz ve kısa tut
                short_name = d_row['Name'].split('/')[0].strip()
                if len(short_name) > 14:
                    short_name = short_name[:12] + ".."
                
                dr_label = f"{d_row['status_dot']} {short_name}\n👤"
                if st.button(dr_label, key=f"sq_dr_{idx}", use_container_width=True, help=f"Full: {d_row['Name']} | Phone: {d_row['Telephone']}"):
                    open_driver_dossier(d_row['Name'])
    else:
        st.info("No drivers data found.")

# -------------------------------------------------------------
# 3. MODÜL: DISPATCH TEAM CHAT
# -------------------------------------------------------------
elif top_menu == "💬 Dispatch Team Chat":
    st.markdown("#### 💬 Dispatch Operations & Shift Notes")
    with st.form("chat_form_clean", clear_on_submit=True):
        cm1, cm2 = st.columns([5, 1])
        with cm1:
            msg_txt = st.text_input("Write operational note...", placeholder="E.g., Unit 14 delivered in Laredo, ready for reload.")
        with cm2:
            if st.form_submit_button("Post Note") and msg_txt.strip():
                cur = conn.cursor()
                now_s = datetime.now().strftime("%m/%d/%Y %I:%M %p")
                cur.execute("INSERT INTO team_chat (sender, message, timestamp) VALUES (?, ?, ?)", (st.session_state.get("current_user"), msg_txt.strip(), now_s))
                conn.commit()
                st.rerun()

    df_c = pd.read_sql_query("SELECT * FROM team_chat ORDER BY id DESC LIMIT 40", conn)
    for _, r in df_c.iterrows():
        st.markdown(f"""
        <div style="background:#ffffff; border-left:4px solid #0284c7; padding:8px 14px; border-radius:6px; margin-bottom:6px; border:1px solid #e2e8f0;">
            <b style="color:#0b1f3a; font-size:13px;">👤 {r['sender']}</b> <span style="font-size:10px; color:#64748b; margin-left:8px;">🕒 {r['timestamp']}</span>
            <div style="margin-top:2px; font-size:13px; color:#0f172a;">{r['message']}</div>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# 4. MODÜL: SERVICE LEDGER
# -------------------------------------------------------------
elif top_menu == "🔧 Service Ledger":
    st.markdown("#### 🔧 Equipment Service & Maintenance Entry")
    with st.form("service_clean", clear_on_submit=True):
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            sel_u = st.selectbox("Unit #", df_v["unit_number"].tolist())
            s_date = st.date_input("Service Date")
        with sc2:
            s_type = st.selectbox("Type", ["Oil Change (PM)", "Tires / Brakes", "Annual DOT", "Repair", "Other"])
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
