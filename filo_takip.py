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
    initial_sidebar_state="expanded"
)

# MOONSTAR COMPACT TILE DESIGN
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800;900&family=Inter:wght@500;600;700&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #f8fafc !important;
    }
    
    .moonstar-nav {
        background: linear-gradient(90deg, #0b1f3a 0%, #0f2c59 60%, #0284c7 100%);
        padding: 12px 20px;
        border-radius: 6px;
        color: #ffffff;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        border-bottom: 3px solid #38bdf8;
    }
    .brand-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 20px;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
    }

    /* COMPACT TILE STYLES */
    .mini-tile {
        background: #ffffff;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 10px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .tile-green { border-left: 5px solid #22c55e !important; }
    .tile-yellow { border-left: 5px solid #eab308 !important; background: #fffdf5 !important; }
    .tile-red { border-left: 5px solid #ef4444 !important; background: #fef8f8 !important; }
    
    .tile-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }
    .tile-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 15px;
        font-weight: 800;
        color: #0b1f3a;
        margin: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .tile-badge {
        font-size: 10px;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .badge-green { background: #dcfce7; color: #166534; }
    .badge-yellow { background: #fef08a; color: #854d0e; }
    .badge-red { background: #fee2e2; color: #991b1b; }
    
    .tile-meta {
        font-size: 11px;
        color: #475569;
        line-height: 1.4;
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
            st.image("logo.jpg", width=200)
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

# DRIVERS READ
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
        st.image("logo.jpg", width=170)
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
        <div style="font-size:11px; color:#bae6fd;">Compact Fleet & Driver Asset Dossier Console</div>
    </div>
    <div>
        <span style="background: rgba(255,255,255,0.15); padding: 4px 10px; border-radius: 12px; font-size: 11px;">
            🟢 <b>{st.session_state.get('current_user')}</b>
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. BÖLÜM: TRUCKS & TRAILERS (MINI TILES & IN-CARD EDIT/DOCS)
# -------------------------------------------------------------
if menu == "🚛 Trucks & Trailers (Grid)":
    # FİLTRELEME & YENİ ARAÇ BUTONU
    f_c1, f_c2, f_c3, f_c4 = st.columns([1.5, 1.5, 2, 1.5])
    with f_c1:
        type_filter = st.selectbox("Equipment:", ["All", "Trucks Only", "Trailers Only"])
    with f_c2:
        status_filter = st.selectbox("Status:", ["All Statuses", "🚨 Red Overdue", "🟡 Yellow Warning", "🟢 Green Good"])
    with f_c3:
        search_box = st.text_input("Search Unit #, Driver, Make:", placeholder="e.g. 95, Cascadia...")
    with f_c4:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        add_new_veh = st.button("➕ New Equipment", use_container_width=True)

    # Yeni Araç Ekleme Modalı
    if add_new_veh:
        with st.form("modal_add_v"):
            st.markdown("##### ➕ Register New Equipment")
            nv_col1, nv_col2 = st.columns(2)
            with nv_col1:
                acomp = st.selectbox("Company", ["MOONSTAR", "LIONSTAR"])
                atype = st.selectbox("Type", ["TRUCK", "TRAILER"])
                aunit = st.text_input("Unit Number")
                adriver = st.text_input("Assigned Driver")
            with nv_col2:
                avin = st.text_input("VIN")
                aplate = st.text_input("Plate")
                amodel = st.text_input("Make / Model / Year")
            if st.form_submit_button("Save Asset") and aunit:
                cur = conn.cursor()
                cur.execute("INSERT INTO vehicles (company, unit_type, unit_number, driver, vin, plate_number, make_model) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                            (acomp, atype, aunit.strip(), adriver.strip(), avin.strip(), aplate.strip(), amodel.strip()))
                conn.commit()
                st.success(f"{atype} #{aunit} registered!")
                st.rerun()

    df_grid = df_v.copy()
    if type_filter == "Trucks Only":
        df_grid = df_grid[df_grid["unit_type"] == "TRUCK"]
    elif type_filter == "Trailers Only":
        df_grid = df_grid[df_grid["unit_type"] == "TRAILER"]

    def get_asset_tile_color(row):
        if row["oil_icon"] == "🔴" or row["insp_icon"] == "🔴":
            return "tile-red", "badge-red", "OVERDUE"
        elif row["oil_icon"] == "🟡" or row["insp_icon"] == "🟡":
            return "tile-yellow", "badge-yellow", "DUE SOON"
        else:
            return "tile-green", "badge-green", "READY"

    tile_data = df_grid.apply(get_asset_tile_color, axis=1)
    df_grid["tile_class"] = [t[0] for t in tile_data]
    df_grid["badge_class"] = [t[1] for t in tile_data]
    df_grid["overall_text"] = [t[2] for t in tile_data]

    if status_filter == "🚨 Red Overdue":
        df_grid = df_grid[df_grid["tile_class"] == "tile-red"]
    elif status_filter == "🟡 Yellow Warning":
        df_grid = df_grid[df_grid["tile_class"] == "tile-yellow"]
    elif status_filter == "🟢 Green Good":
        df_grid = df_grid[df_grid["tile_class"] == "tile-green"]

    if search_box:
        s = search_box.strip().lower()
        df_grid = df_grid[
            df_grid["unit_number"].str.lower().str.contains(s) |
            df_grid["driver"].str.lower().str.contains(s) |
            df_grid["make_model"].str.lower().str.contains(s)
        ]

    st.caption(f"Showing **{len(df_grid)}** equipment boxes")

    # 4 KOLONLU KOMPAKT KUTULAR
    cols = st.columns(4)
    for idx, (_, row) in enumerate(df_grid.iterrows()):
        with cols[idx % 4]:
            oil_line = f"{row['oil_icon']} Oil: {row['oil_status']}" if row['unit_type'] == 'TRUCK' else "⚪ Oil: Exempt"
            insp_line = f"{row['insp_icon']} DOT: {row['insp_status']}"
            
            st.markdown(f"""
            <div class="mini-tile {row['tile_class']}">
                <div class="tile-header">
                    <span class="tile-title">#{row['unit_number']} ({row['unit_type']})</span>
                    <span class="tile-badge {row['badge_class']}">{row['overall_text']}</span>
                </div>
                <div class="tile-meta">
                    👤 <b>{row['driver'] if row['driver'] else 'Unassigned'}</b><br>
                    🔖 {row['make_model'] if row['make_model'] else '-'}<br>
                    🛢️ {oil_line}<br>
                    📋 {insp_line}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # KART İÇİNDEN DOSYA VE DÜZENLEME AÇMA
            with st.expander(f"📂 Unit #{row['unit_number']} Dossier & Edit"):
                u_tab1, u_tab2, u_tab3 = st.tabs(["✏️ Edit", "📎 Files", "🚨 Delete"])
                with u_tab1:
                    with st.form(f"edit_veh_{row['unit_number']}"):
                        e_driver = st.text_input("Assigned Driver", value=row['driver'])
                        e_plate = st.text_input("Plate", value=row['plate_number'])
                        e_vin = st.text_input("VIN", value=row['vin'])
                        e_curr_mil = st.number_input("Current Odometer", value=int(row['current_mileage'] or 0))
                        e_oil_mil = st.number_input("Last Oil Change", value=int(row['last_oil_mileage'] or 0))
                        if st.form_submit_button("Update Info"):
                            cur = conn.cursor()
                            cur.execute("""
                                UPDATE vehicles SET driver=?, plate_number=?, vin=?, current_mileage=?, last_oil_mileage=?
                                WHERE unit_number=?
                            """, (e_driver, e_plate, e_vin, e_curr_mil, e_oil_mil, row['unit_number']))
                            conn.commit()
                            st.success("Updated!")
                            st.rerun()
                with u_tab2:
                    st.markdown("**Attach Photo / Document to Unit**")
                    u_file = st.file_uploader(f"File for #{row['unit_number']}", type=["pdf","png","jpg","jpeg"], key=f"f_{row['unit_number']}")
                    if u_file and st.button("Upload to Dossier", key=f"btn_u_{row['unit_number']}"):
                        f_name = f"Unit_{row['unit_number']}_{u_file.name}"
                        with open(os.path.join(UPLOAD_DIR, f_name), "wb") as f:
                            f.write(u_file.getbuffer())
                        st.success("File uploaded!")
                        st.rerun()
                    
                    found = [f for f in os.listdir(UPLOAD_DIR) if f"Unit_{row['unit_number']}_" in f]
                    for f in found:
                        st.write(f"📄 `{f}`")
                with u_tab3:
                    if st.button(f"🗑️ Delete Unit #{row['unit_number']}", type="secondary", key=f"del_{row['unit_number']}"):
                        cur = conn.cursor()
                        cur.execute("DELETE FROM vehicles WHERE unit_number = ?", (row['unit_number'],))
                        conn.commit()
                        st.warning(f"Unit #{row['unit_number']} deleted!")
                        st.rerun()

# -------------------------------------------------------------
# 2. BÖLÜM: DRIVERS (MINI TILES & IN-CARD EDIT/DOCS)
# -------------------------------------------------------------
elif menu == "👤 Drivers Compliance (Grid)":
    st.markdown("#### 👤 Driver Compliance Boxes *(Click Box to Open Dossier, Edit or Add Docs)*")

    # FİLTRELEME & YENİ ŞOFÖR BUTONU
    df_c1, df_c2, df_c3 = st.columns([2, 2, 1.5])
    with df_c1:
        d_filter = st.selectbox("Status Filter:", ["All Drivers", "🚨 Action Needed (Red)", "🟡 Expiring Soon (Yellow)", "🟢 Fully Compliant (Green)"])
    with df_c2:
        d_srch = st.text_input("Search Driver Name or Phone:")
    with df_c3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        add_new_dr = st.button("➕ Onboard Driver", use_container_width=True)

    if add_new_dr:
        with st.form("modal_add_dr"):
            st.markdown("##### ➕ Onboard New Driver")
            nd_name = st.text_input("Full Name")
            nd_phone = st.text_input("Phone")
            nd_email = st.text_input("Email")
            nd_cdl = st.text_input("CDL Number")
            nd_cdl_exp = st.date_input("CDL Expiration")
            nd_med_exp = st.date_input("Medical Due Date")
            if st.form_submit_button("Save Driver") and nd_name:
                new_dr_entry = {
                    "Name": nd_name.strip(), "Telephone": nd_phone.strip(), "E-mail": nd_email.strip(),
                    "License Number": nd_cdl.strip(), "License Expiry": str(nd_cdl_exp), "Next Medical": str(nd_med_exp)
                }
                df_d = pd.concat([df_d, pd.DataFrame([new_dr_entry])], ignore_index=True)
                df_d.to_excel(DRIVERS_FILE, index=False)
                st.success(f"Driver '{nd_name}' added!")
                st.rerun()

    if not df_d.empty:
        df_d_grid = df_d.copy()

        def get_driver_tile_color(row):
            if row["CDL_Icon"] == "🔴" or row["Med_Icon"] == "🔴":
                return "tile-red", "badge-red", "ACTION NEEDED"
            elif row["CDL_Icon"] == "🟡" or row["Med_Icon"] == "🟡":
                return "tile-yellow", "badge-yellow", "EXPIRING SOON"
            else:
                return "tile-green", "badge-green", "COMPLIANT"

        dr_tile_data = df_d_grid.apply(get_driver_tile_color, axis=1)
        df_d_grid["tile_class"] = [t[0] for t in dr_tile_data]
        df_d_grid["badge_class"] = [t[1] for t in dr_tile_data]
        df_d_grid["overall_text"] = [t[2] for t in dr_tile_data]

        if d_filter == "🚨 Action Needed (Red)":
            df_d_grid = df_d_grid[df_d_grid["tile_class"] == "tile-red"]
        elif d_filter == "🟡 Expiring Soon (Yellow)":
            df_d_grid = df_d_grid[df_d_grid["tile_class"] == "tile-yellow"]
        elif d_filter == "🟢 Fully Compliant (Green)":
            df_d_grid = df_d_grid[df_d_grid["tile_class"] == "tile-green"]

        if d_srch:
            ds = d_srch.strip().lower()
            df_d_grid = df_d_grid[
                df_d_grid["Name"].str.lower().str.contains(ds) |
                df_d_grid["Telephone"].str.lower().str.contains(ds)
            ]

        st.caption(f"Showing **{len(df_d_grid)}** driver profiles")

        # 3 KOLONLU KOMPAKT KUTULAR
        d_cols = st.columns(3)
        for idx, (_, d_row) in enumerate(df_d_grid.iterrows()):
            with d_cols[idx % 3]:
                st.markdown(f"""
                <div class="mini-tile {d_row['tile_class']}">
                    <div class="tile-header">
                        <span class="tile-title">{d_row['Name']}</span>
                        <span class="tile-badge {d_row['badge_class']}">{d_row['overall_text']}</span>
                    </div>
                    <div class="tile-meta">
                        📞 {d_row['Telephone']}<br>
                        🪪 CDL: {d_row['CDL_Icon']} {d_row['CDL_Status']}<br>
                        🏥 Med: {d_row['Med_Icon']} {d_row['Med_Status']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # ŞOFÖR KARTININ İÇİNDEN AÇILAN DOSYA & DÜZENLEME
                with st.expander(f"👤 {d_row['Name']} Dossier & Edit"):
                    d_tab1, d_tab2, d_tab3 = st.tabs(["✏️ Edit Info", "📸 Photos & Docs", "🚨 Remove"])
                    with d_tab1:
                        with st.form(f"edit_dr_{idx}"):
                            ed_phone = st.text_input("Phone", value=d_row['Telephone'])
                            ed_email = st.text_input("Email", value=d_row['E-mail'])
                            ed_cdl_no = st.text_input("CDL #", value=d_row['License Number'])
                            ed_cdl_exp = st.text_input("CDL Expiry (YYYY-MM-DD)", value=d_row['License Expiry'])
                            ed_med_exp = st.text_input("Next Med (YYYY-MM-DD)", value=d_row['Next Medical'])
                            if st.form_submit_button("Save Driver Info"):
                                df_d.loc[df_d["Name"] == d_row["Name"], "Telephone"] = ed_phone
                                df_d.loc[df_d["Name"] == d_row["Name"], "E-mail"] = ed_email
                                df_d.loc[df_d["Name"] == d_row["Name"], "License Number"] = ed_cdl_no
                                df_d.loc[df_d["Name"] == d_row["Name"], "License Expiry"] = ed_cdl_exp
                                df_d.loc[df_d["Name"] == d_row["Name"], "Next Medical"] = ed_med_exp
                                df_d.to_excel(DRIVERS_FILE, index=False)
                                st.success("Driver updated!")
                                st.rerun()
                    with d_tab2:
                        st.markdown("**Upload Check-in/out Photos, Accident or Citations**")
                        doc_type = st.selectbox("Category", ["Check-in/out Photo", "Accident / Damage", "DOT / Citation", "CDL/Med Document"], key=f"cat_{idx}")
                        dr_up_file = st.file_uploader("Select File / Photo", type=["pdf","png","jpg","jpeg"], key=f"dr_up_{idx}")
                        if dr_up_file and st.button("Save to Dossier", key=f"btn_dr_{idx}"):
                            safe_name = f"DR_{d_row['Name'].replace(' ','_')}_{doc_type.replace(' ','_')}_{dr_up_file.name}"
                            with open(os.path.join(UPLOAD_DIR, safe_name), "wb") as f:
                                f.write(dr_up_file.getbuffer())
                            st.success("File added to driver dossier!")
                            st.rerun()

                        st.markdown("**Archived Files for this Driver:**")
                        d_found = [f for f in os.listdir(UPLOAD_DIR) if f"DR_{d_row['Name'].replace(' ','_')}_" in f]
                        for f in d_found:
                            st.write(f"📄 `{f}`")
                    with d_tab3:
                        if st.button(f"🚨 Offboard {d_row['Name']}", type="secondary", key=f"del_dr_{idx}"):
                            df_d = df_d[df_d["Name"] != d_row['Name']]
                            df_d.to_excel(DRIVERS_FILE, index=False)
                            st.warning(f"Driver {d_row['Name']} removed!")
                            st.rerun()

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
        <div style="background:#ffffff; border-left:4px solid #0284c7; padding:8px 12px; border-radius:6px; margin-bottom:6px; border:1px solid #e2e8f0;">
            <b style="color:#0b1f3a; font-size:13px;">👤 {r['sender']}</b> <span style="font-size:10px; color:#64748b; margin-left:8px;">🕒 {r['timestamp']}</span>
            <div style="margin-top:2px; font-size:13px; color:#0f172a;">{r['message']}</div>
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
