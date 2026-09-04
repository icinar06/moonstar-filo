import glob
import os
import re
import shutil
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="MOONSTAR EXPRESS LLC — Fleet Grid",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# MOONSTAR KURUMSAL VE TİLE / KUTUCUK TASARIMI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800;900&family=Inter:wght@500;600;700&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #f8fafc !important;
    }
    
    .moonstar-nav {
        background: linear-gradient(90deg, #0b1f3a 0%, #0f2c59 60%, #0284c7 100%);
        padding: 14px 22px;
        border-radius: 8px;
        color: #ffffff;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        border-bottom: 3px solid #38bdf8;
    }
    .brand-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 22px;
        font-weight: 900;
        color: #ffffff;
        margin: 0;
    }
    
    /* ARAÇ VE ŞOFÖR KARTLARI (TILES) */
    .tile-box {
        background: #ffffff;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 14px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        position: relative;
    }
    .tile-green {
        border-left: 6px solid #22c55e !important;
    }
    .tile-yellow {
        border-left: 6px solid #eab308 !important;
        background: #fffbeb !important;
    }
    .tile-red {
        border-left: 6px solid #ef4444 !important;
        background: #fef2f2 !important;
    }
    
    .tile-unit {
        font-family: 'Montserrat', sans-serif;
        font-size: 20px;
        font-weight: 800;
        color: #0b1f3a;
        margin: 0;
    }
    .tile-sub {
        font-size: 12px;
        color: #64748b;
        margin-top: 2px;
    }
    .tile-status {
        display: inline-block;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        margin-top: 6px;
    }
    .status-green { background: #dcfce7; color: #166534; }
    .status-yellow { background: #fef08a; color: #854d0e; }
    .status-red { background: #fee2e2; color: #991b1b; }
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
        st.markdown("### 🔒 MOONSTAR EXPRESS LLC — PORTAL")
        with st.form("login_form"):
            email = st.text_input("Corporate Email", placeholder="ismail@moonstarpa.com")
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                if "@moonstarpa" in email.strip().lower() and pwd == "Moonstar2026!":
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = email.strip().lower()
                    st.rerun()
                else:
                    st.error("Invalid corporate credentials!")
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
            return f"Good ({diff}d)", "🟢", diff
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
                    return "OVERDUE ❌", "🔴"
                elif diff <= 30:
                    return "EXPIRING ⚠️", "🟡"
            except:
                pass
    return "VALID", "🟢"

insp_res = df_v.apply(evaluate_insp, axis=1)
df_v["insp_status"] = [r[0] for r in insp_res]
df_v["insp_icon"] = [r[1] for r in insp_res]

oil_res = df_v.apply(check_oil_status, axis=1)
df_v["oil_status"] = [r[0] for r in oil_res]
df_v["oil_icon"] = [r[1] for r in oil_res]
df_v["remaining_oil_mi"] = [r[2] for r in oil_res]

# Şoför Verileri
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
    df_d["CDL_Icon"] = df_d["License Expiry"].apply(lambda d: check_date_status(d)[1])
    df_d["Med_Status"] = df_d["Next Medical"].apply(lambda d: check_date_status(d)[0])
    df_d["Med_Icon"] = df_d["Next Medical"].apply(lambda d: check_date_status(d)[1])

# ---------------------------------------------
# SIDEBAR
# ---------------------------------------------
with st.sidebar:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=180)
    st.markdown("### 🏢 **MOONSTAR TMS**")
    st.caption(f"👤 Active: **{st.session_state.get('current_user')}**")
    st.markdown("---")
    
    menu = st.radio(
        "NAVIGATION",
        [
            "🚛 Trucks & Trailers (Grid)",
            "👤 Drivers Compliance (Grid)",
            "💬 Team Chat",
            "🔧 Quick Service Entry"
        ]
    )
    st.markdown("---")
    if st.button("🚪 Sign Out"):
        st.session_state["authenticated"] = False
        st.rerun()

# ---------------------------------------------
# TOP NAVBAR
# ---------------------------------------------
st.markdown(f"""
<div class="moonstar-nav">
    <div>
        <div class="brand-title">MOONSTAR <span style="color:#38bdf8;">EXPRESS LLC</span></div>
        <div style="font-size:12px; color:#bae6fd;">Visual Fleet Status & Driver Compliance Console</div>
    </div>
    <div>
        <span style="background: rgba(255,255,255,0.15); padding: 5px 12px; border-radius: 15px; font-size: 12px;">
            🟢 <b>{st.session_state.get('current_user')}</b>
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. BÖLÜM: TRUCKS & TRAILERS (GRID + ADD / REMOVE)
# -------------------------------------------------------------
if menu == "🚛 Trucks & Trailers (Grid)":
    st.markdown("#### 🚛 Equipment Fleet Boxes *(Color Coded for Fast Action)*")

    # YUKARIYA KONULAN YÖNETİM BUTONU (EKLE / SİL)
    with st.expander("⚙️ Equipment Management (Add New Truck / Trailer or Delete Asset)", expanded=False):
        ca, cb = st.columns(2)
        with ca:
            st.markdown("##### ➕ Add New Equipment")
            with st.form("add_asset_form_top"):
                acomp = st.selectbox("Company", ["MOONSTAR", "LIONSTAR"])
                atype = st.selectbox("Equipment Type", ["TRUCK", "TRAILER"])
                aunit = st.text_input("Unit Number (e.g. 95 or 5312)")
                adriver = st.text_input("Assigned Driver")
                avin = st.text_input("VIN / Serial Number")
                aplate = st.text_input("License Plate #")
                amodel = st.text_input("Make / Model / Year")
                areg = st.date_input("Registration Expiration")
                adot = st.date_input("Annual DOT Inspection Date")
                astate = st.date_input("State / PA Inspection Date")

                if st.form_submit_button("Register Equipment"):
                    if aunit.strip():
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO vehicles 
                            (company, unit_type, unit_number, driver, vin, plate_number, make_model, plate_expiry, dot_inspection, state_inspection)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (acomp, atype, aunit.strip(), adriver.strip(), avin.strip(), aplate.strip(), amodel.strip(), str(areg), str(adot), str(astate)))
                        conn.commit()
                        st.success(f"{atype} #{aunit} successfully registered in fleet database!")
                        st.rerun()
                    else:
                        st.error("Unit Number is mandatory.")

        with cb:
            st.markdown("##### ❌ Decommission / Delete Equipment")
            all_assets = df_v["unit_number"].dropna().tolist()
            u_del = st.selectbox("Select Equipment to Delete:", ["Select..."] + all_assets)
            if st.button("🚨 Delete Equipment Permanently", type="secondary"):
                if u_del != "Select...":
                    cur = conn.cursor()
                    cur.execute("DELETE FROM vehicles WHERE unit_number = ?", (u_del,))
                    conn.commit()
                    st.warning(f"Equipment #{u_del} permanently deleted!")
                    st.rerun()

    st.markdown("---")

    # Filtre Çubuğu
    f_c1, f_c2, f_c3 = st.columns([1, 1, 2])
    with f_c1:
        type_filter = st.selectbox("Filter Equipment:", ["All", "Trucks Only", "Trailers Only"])
    with f_c2:
        status_filter = st.selectbox("Status Filter:", ["All Statuses", "🚨 Red Alerts Only", "🟡 Yellow Warnings Only", "🟢 All Good"])
    with f_c3:
        search_box = st.text_input("Search Unit # or Driver:")

    df_grid = df_v.copy()
    if type_filter == "Trucks Only":
        df_grid = df_grid[df_grid["unit_type"] == "TRUCK"]
    elif type_filter == "Trailers Only":
        df_grid = df_grid[df_grid["unit_type"] == "TRAILER"]

    def get_asset_tile_color(row):
        if row["oil_icon"] == "🔴" or row["insp_icon"] == "🔴":
            return "tile-red", "status-red", "🚨 OVERDUE"
        elif row["oil_icon"] == "🟡" or row["insp_icon"] == "🟡":
            return "tile-yellow", "status-yellow", "🟡 DUE SOON"
        else:
            return "tile-green", "status-green", "🟢 READY"

    tile_data = df_grid.apply(get_asset_tile_color, axis=1)
    df_grid["tile_class"] = [t[0] for t in tile_data]
    df_grid["badge_class"] = [t[1] for t in tile_data]
    df_grid["overall_text"] = [t[2] for t in tile_data]

    if status_filter == "🚨 Red Alerts Only":
        df_grid = df_grid[df_grid["tile_class"] == "tile-red"]
    elif status_filter == "🟡 Yellow Warnings Only":
        df_grid = df_grid[df_grid["tile_class"] == "tile-yellow"]
    elif status_filter == "🟢 All Good":
        df_grid = df_grid[df_grid["tile_class"] == "tile-green"]

    if search_box:
        s = search_box.strip().lower()
        df_grid = df_grid[
            df_grid["unit_number"].str.lower().str.contains(s) |
            df_grid["driver"].str.lower().str.contains(s)
        ]

    st.write(f"Showing **{len(df_grid)}** equipment boxes:")

    # 4 KOLONLU KUTUCUK (CARD/TILE) GRID
    cols = st.columns(4)
    for idx, (_, row) in enumerate(df_grid.iterrows()):
        with cols[idx % 4]:
            oil_line = f"🛢️ Oil: {row['oil_icon']} {row['oil_status']}" if row['unit_type'] == 'TRUCK' else "🛢️ Oil: Exempt (Trailer)"
            insp_line = f"📋 DOT: {row['insp_icon']} {row['insp_status']}"
            
            st.markdown(f"""
            <div class="tile-box {row['tile_class']}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div class="tile-unit">Unit #{row['unit_number']}</div>
                    <span class="tile-status {row['badge_class']}">{row['unit_type']}</span>
                </div>
                <div class="tile-sub">👤 Driver: <b>{row['driver'] if row['driver'] else 'Unassigned'}</b></div>
                <div class="tile-sub">🔖 Model: {row['make_model'] if row['make_model'] else '-'}</div>
                <hr style="margin: 8px 0; border: 0; border-top: 1px solid #e2e8f0;">
                <div style="font-size:12px; font-weight:600; color:#1e293b;">{oil_line}</div>
                <div style="font-size:12px; font-weight:600; color:#1e293b;">{insp_line}</div>
            </div>
            """, unsafe_allow_html=True)

# -------------------------------------------------------------
# 2. BÖLÜM: DRIVERS (GRID + ADD / REMOVE)
# -------------------------------------------------------------
elif menu == "👤 Drivers Compliance (Grid)":
    st.markdown("#### 👤 Driver Compliance Boxes *(Color Coded by CDL & Medical Expiry)*")

    # YUKARIYA KONULAN ŞOFÖR YÖNETİMİ
    with st.expander("👤 Driver Management (Onboard New Driver / Remove Driver)", expanded=False):
        da, db = st.columns(2)
        with da:
            st.markdown("##### ➕ Onboard New Driver")
            with st.form("new_driver_box_top"):
                dn = st.text_input("Driver Full Name (First & Last)")
                dp = st.text_input("Phone Number")
                de_mail = st.text_input("Corporate / Personal Email")
                de_cdl_no = st.text_input("CDL Number")
                de_cdl = st.date_input("CDL Expiration Date")
                de_med = st.date_input("Medical Card Due Date")

                if st.form_submit_button("Save Driver Profile"):
                    if dn.strip():
                        new_r = {
                            "Name": dn.strip(),
                            "Telephone": dp.strip(),
                            "E-mail": de_mail.strip(),
                            "License Number": de_cdl_no.strip(),
                            "License Expiry": str(de_cdl),
                            "Next Medical": str(de_med)
                        }
                        df_d = pd.concat([df_d, pd.DataFrame([new_r])], ignore_index=True)
                        df_d.to_excel(DRIVERS_FILE, index=False)
                        st.success(f"Driver '{dn}' registered successfully!")
                        st.rerun()
                    else:
                        st.error("Driver name is mandatory.")

        with db:
            st.markdown("##### ❌ Remove Driver")
            all_drs = df_d["Name"].dropna().tolist() if not df_d.empty else []
            del_d = st.selectbox("Select Driver to Remove:", ["Select..."] + all_drs)
            if st.button("🚨 Remove Driver from Fleet", type="secondary"):
                if del_d != "Select...":
                    df_d = df_d[df_d["Name"] != del_d]
                    df_d.to_excel(DRIVERS_FILE, index=False)
                    st.warning(f"Driver '{del_d}' removed!")
                    st.rerun()

    st.markdown("---")

    if not df_d.empty:
        df_d_grid = df_d.copy()

        def get_driver_tile_color(row):
            if row["CDL_Icon"] == "🔴" or row["Med_Icon"] == "🔴":
                return "tile-red", "status-red", "🚨 ACTION NEEDED"
            elif row["CDL_Icon"] == "🟡" or row["Med_Icon"] == "🟡":
                return "tile-yellow", "status-yellow", "🟡 EXPIRING SOON"
            else:
                return "tile-green", "status-green", "🟢 FULLY COMPLIANT"

        dr_tile_data = df_d_grid.apply(get_driver_tile_color, axis=1)
        df_d_grid["tile_class"] = [t[0] for t in dr_tile_data]
        df_d_grid["badge_class"] = [t[1] for t in dr_tile_data]
        df_d_grid["overall_text"] = [t[2] for t in dr_tile_data]

        d_filter = st.selectbox("Filter Drivers:", ["All Drivers", "🚨 Expired Only", "🟡 Expiring Soon", "🟢 All Valid"])
        if d_filter == "🚨 Expired Only":
            df_d_grid = df_d_grid[df_d_grid["tile_class"] == "tile-red"]
        elif d_filter == "🟡 Expiring Soon":
            df_d_grid = df_d_grid[df_d_grid["tile_class"] == "tile-yellow"]
        elif d_filter == "🟢 All Valid":
            df_d_grid = df_d_grid[df_d_grid["tile_class"] == "tile-green"]

        d_cols = st.columns(3)
        for idx, (_, d_row) in enumerate(df_d_grid.iterrows()):
            with d_cols[idx % 3]:
                st.markdown(f"""
                <div class="tile-box {d_row['tile_class']}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div class="tile-unit" style="font-size:17px;">{d_row['Name']}</div>
                        <span class="tile-status {d_row['badge_class']}">{d_row['overall_text']}</span>
                    </div>
                    <div class="tile-sub">📞 Phone: {d_row['Telephone']}</div>
                    <hr style="margin: 8px 0; border: 0; border-top: 1px solid #e2e8f0;">
                    <div style="font-size:12px; font-weight:600; color:#1e293b;">🪪 CDL: {d_row['CDL_Icon']} {d_row['CDL_Status']}</div>
                    <div style="font-size:12px; font-weight:600; color:#1e293b;">🏥 Med Card: {d_row['Med_Icon']} {d_row['Med_Status']}</div>
                </div>
                """, unsafe_allow_html=True)

# -------------------------------------------------------------
# 3. BÖLÜM: TEAM CHAT
# -------------------------------------------------------------
elif menu == "💬 Team Chat":
    st.markdown("#### 💬 Dispatch Operations Notes")
    with st.form("chat_form", clear_on_submit=True):
        cm1, cm2 = st.columns([5, 1])
        with cm1:
            msg_txt = st.text_input("Write note...", placeholder="E.g., Unit 14 delivered in Laredo.")
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
        <div style="background:#ffffff; border-left:4px solid #0284c7; padding:10px 14px; border-radius:6px; margin-bottom:8px; border:1px solid #e2e8f0;">
            <b style="color:#0b1f3a;">👤 {r['sender']}</b> <span style="font-size:11px; color:#64748b; margin-left:8px;">🕒 {r['timestamp']}</span>
            <div style="margin-top:4px; font-size:14px; color:#0f172a;">{r['message']}</div>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# 4. BÖLÜM: QUICK SERVICE ENTRY
# -------------------------------------------------------------
elif menu == "🔧 Quick Service Entry":
    st.markdown("#### 🔧 Log Oil Change or Service")
    with st.form("service_quick", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            sel_u = st.selectbox("Unit #", df_v["unit_number"].tolist())
            s_date = st.date_input("Date")
        with c2:
            s_type = st.selectbox("Type", ["Oil Change (PM)", "Tires / Brakes", "Annual DOT", "Repair", "Other"])
            s_mil = st.number_input("Odometer (mi)", min_value=0, step=1000)
        with c3:
            s_cost = st.number_input("Cost ($)", min_value=0.0, step=50.0)
            s_inv = st.file_uploader("Upload Invoice (PDF/JPG)")

        if st.form_submit_button("Record Service"):
            cur = conn.cursor()
            cur.execute("INSERT INTO logs (unit_number, log_date, log_type, mileage, cost) VALUES (?, ?, ?, ?, ?)", (sel_u, str(s_date), s_type, s_mil, s_cost))
            if s_type == "Oil Change (PM)" and s_mil > 0:
                cur.execute("UPDATE vehicles SET last_oil_mileage = ?, current_mileage = MAX(current_mileage, ?) WHERE unit_number = ?", (s_mil, s_mil, sel_u))
            conn.commit()
            st.success("Logged successfully!")
            st.rerun()
