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
    initial_sidebar_state="collapsed"
)

# MODERN ENTERPRISE LOGISTICS THEME (EDGE-TO-EDGE & CLEAN WHITE TILES)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #f8fafc !important;
    }
    
    /* Üst Kurumsal Header */
    .top-header {
        background: linear-gradient(90deg, #0b1f3a 0%, #172554 60%, #0284c7 100%);
        padding: 12px 24px;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .brand-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 20px;
        font-weight: 800;
        letter-spacing: 0.5px;
        color: #ffffff;
        margin: 0;
    }
    
    /* Beyaz Temiz Kart Stili (Clean Card) */
    .clean-tile {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        margin-bottom: 8px;
        transition: border-color 0.15s ease;
    }
    .clean-tile:hover {
        border-color: #0284c7;
    }
    
    .tile-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    .tile-unit-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 15px;
        font-weight: 800;
        color: #0f172a;
        margin: 0;
    }
    
    /* Sadece Rozetler Renkli */
    .badge {
        font-size: 10px;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-ready { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
    .badge-due { background: #fef9c3; color: #854d0e; border: 1px solid #fef08a; }
    .badge-overdue { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
    
    .tile-body {
        font-size: 11px;
        color: #475569;
        line-height: 1.5;
    }
    
    /* Modal / Dossier Container */
    .dossier-card {
        background: #ffffff;
        border: 2px solid #0284c7;
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 20px;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.08);
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
            return f"Expired ({abs(diff)}d)", "badge-overdue", diff
        elif diff <= 30:
            return f"Due Soon ({diff}d)", "badge-due", diff
        else:
            return f"Valid ({diff}d)", "badge-ready", diff
    except Exception:
        return "Invalid", "⚪", 999

def check_oil_status(row):
    if row.get("unit_type") == "TRAILER":
        return "Exempt", "badge-ready", "-"
    try:
        c_m = int(row.get("current_mileage") or 0)
        l_o = int(row.get("last_oil_mileage") or 0)
        interval = int(row.get("oil_interval") or 25000)
        if interval <= 0 or (l_o == 0 and c_m == 0):
            return "No Record", "badge-ready", "-"
        rem = interval - (c_m - l_o)
        if rem < 0:
            return f"Overdue ({abs(rem):,} mi)", "badge-overdue", f"{rem:,}"
        elif rem <= 3000:
            return f"Due Soon ({rem:,} mi)", "badge-due", f"{rem:,}"
        else:
            return f"Good ({rem:,} mi)", "badge-ready", f"{rem:,}"
    except Exception:
        return "Calc Error", "badge-ready", "-"

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
        CREATE TABLE IF NOT EXISTS asset_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_type TEXT, -- 'EQUIPMENT' or 'DRIVER'
            target_id TEXT,
            file_category TEXT,
            filename TEXT,
            uploaded_at TEXT
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
                    return "OVERDUE ❌", "badge-overdue"
                elif diff <= 30:
                    return "EXPIRING ⚠️", "badge-due"
            except:
                pass
    return "VALID", "badge-ready"

insp_res = df_v.apply(evaluate_insp, axis=1)
df_v["insp_status"] = [r[0] for r in insp_res]
df_v["insp_badge"] = [r[1] for r in insp_res]

oil_res = df_v.apply(check_oil_status, axis=1)
df_v["oil_status"] = [r[0] for r in oil_res]
df_v["oil_badge"] = [r[1] for r in oil_res]
df_v["remaining_oil_mi"] = [r[2] for r in oil_res]

# DRIVERS VERİLERİ
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
    df_d["CDL_Badge"] = df_d["License Expiry"].apply(lambda d: check_date_status(d)[1])
    df_d["Med_Status"] = df_d["Next Medical"].apply(lambda d: check_date_status(d)[0])
    df_d["Med_Badge"] = df_d["Next Medical"].apply(lambda d: check_date_status(d)[1])

# -------------------------------------------------------------
# ÜST KURUMSAL HEADER & YATAY MENÜ (SIDEBARSIZ TAM EKRAN)
# -------------------------------------------------------------
st.markdown(f"""
<div class="top-header">
    <div style="display:flex; align-items:center; gap:16px;">
        <span class="brand-title">MOONSTAR <span style="color:#38bdf8;">EXPRESS LLC</span></span>
        <span style="font-size:12px; color:#93c5fd; border-left:1px solid #334155; padding-left:12px;">Fleet Portal</span>
    </div>
    <div style="font-size:12px; color:#f1f5f9;">
        Active User: <b>{st.session_state.get('current_user')}</b>
    </div>
</div>
""", unsafe_allow_html=True)

# YATAY NAVİGASYON (ÜST MENÜ BAR)
nav_col1, nav_col2 = st.columns([5, 1])
with nav_col1:
    top_menu = st.radio(
        "Navigation",
        ["🚛 Trucks & Trailers", "👤 Drivers Compliance", "💬 Dispatch Team Chat", "🔧 Service Ledger"],
        horizontal=True,
        label_visibility="collapsed"
    )
with nav_col2:
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. MODÜL: TRUCKS & TRAILERS (BEYAZ TİLE + DİREKT TIKLAMALI DOSYA)
# -------------------------------------------------------------
if top_menu == "🚛 Trucks & Trailers":
    # Session state for selected vehicle
    if "selected_unit" not in st.session_state:
        st.session_state["selected_unit"] = None

    # TIKLANAN ARACIN DOSYASI (ÜSTTE AÇILIR)
    if st.session_state["selected_unit"]:
        u = st.session_state["selected_unit"]
        row_sel = df_v[df_v["unit_number"] == u].iloc[0]
        
        st.markdown(f"""
        <div class="dossier-card">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #e2e8f0; padding-bottom:8px; margin-bottom:12px;">
                <h3 style="margin:0; color:#0b1f3a;">📂 Equipment Dossier: Unit #{row_sel['unit_number']} ({row_sel['unit_type']})</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        c_close, _ = st.columns([1, 5])
        with c_close:
            if st.button("✖️ Close Dossier"):
                st.session_state["selected_unit"] = None
                st.rerun()

        dt1, dt2, dt3 = st.tabs(["✏️ Edit Specifications & Mileage", "📎 Upload Documents & Photos", "🚨 Decommission Asset"])
        
        with dt1:
            with st.form(f"form_veh_{u}"):
                ev_c1, ev_c2, ev_c3 = st.columns(3)
                with ev_c1:
                    e_drv = st.text_input("Assigned Driver", value=row_sel['driver'] or "")
                    e_plt = st.text_input("Plate Number", value=row_sel['plate_number'] or "")
                with ev_c2:
                    e_vin = st.text_input("VIN / Serial", value=row_sel['vin'] or "")
                    e_mdl = st.text_input("Make / Model / Year", value=row_sel['make_model'] or "")
                with ev_c3:
                    e_cur = st.number_input("Current Odometer", value=int(row_sel['current_mileage'] or 0))
                    e_oil = st.number_input("Last Oil Change Mileage", value=int(row_sel['last_oil_mileage'] or 0))
                
                if st.form_submit_button("Save Updates to Database"):
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE vehicles 
                        SET driver=?, plate_number=?, vin=?, make_model=?, current_mileage=?, last_oil_mileage=?
                        WHERE unit_number=?
                    """, (e_drv, e_plt, e_vin, e_mdl, e_cur, e_oil, u))
                    conn.commit()
                    st.success(f"Unit #{u} specifications successfully updated!")
                    st.rerun()

        with dt2:
            st.markdown(f"**Attach Documents / Inspection Photos for Unit #{u}**")
            up_col1, up_col2 = st.columns([2, 3])
            with up_col1:
                v_cat = st.selectbox("Document Type", ["Registration Card", "Annual DOT Inspection Report", "Truck/Trailer Photo", "Insurance Certificate", "Repair Invoice"], key=f"cat_{u}")
                v_file = st.file_uploader("Select File / Photo", type=["pdf", "png", "jpg", "jpeg"], key=f"file_{u}")
                if v_file and st.button("Upload to Asset Dossier", key=f"btn_up_{u}"):
                    s_name = f"EQUIP_{u}_{v_cat.replace(' ','_')}_{v_file.name}"
                    with open(os.path.join(UPLOAD_DIR, s_name), "wb") as f:
                        f.write(v_file.getbuffer())
                    st.success("File uploaded to asset file!")
                    st.rerun()
            with up_col2:
                st.markdown("**Archived Documents & Condition Photos:**")
                found_v = [f for f in os.listdir(UPLOAD_DIR) if f"EQUIP_{u}_" in f]
                if found_v:
                    for doc in found_v:
                        st.write(f"📄 `{doc}`")
                else:
                    st.caption("No files uploaded for this equipment yet.")

        with dt3:
            st.markdown(f"Permanently remove Unit #{u} from active fleet operations.")
            if st.button(f"🚨 Delete Equipment #{u} from Fleet", type="secondary"):
                cur = conn.cursor()
                cur.execute("DELETE FROM vehicles WHERE unit_number = ?", (u,))
                conn.commit()
                st.session_state["selected_unit"] = None
                st.warning(f"Unit #{u} removed!")
                st.rerun()

        st.markdown("---")

    # FİLTRELER & YENİ ARAÇ EKLEME
    f1, f2, f3, f4 = st.columns([1.5, 1.5, 2, 1.2])
    with f1:
        f_type = st.selectbox("Equipment Type:", ["All Equipment", "Trucks Only", "Trailers Only"])
    with f2:
        f_stat = st.selectbox("Status Filter:", ["All Statuses", "🚨 Red Overdue", "🟡 Yellow Warning", "🟢 Green Ready"])
    with f3:
        f_srch = st.text_input("Quick Search (Unit, Driver, Make):", placeholder="Type to filter...")
    with f4:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        btn_new_eq = st.button("➕ Add Equipment", use_container_width=True)

    if btn_new_eq:
        with st.form("new_asset_top_form"):
            st.markdown("##### ➕ Register New Equipment to Fleet")
            na_c1, na_c2 = st.columns(2)
            with na_c1:
                nu_comp = st.selectbox("Company", ["MOONSTAR", "LIONSTAR"])
                nu_type = st.selectbox("Type", ["TRUCK", "TRAILER"])
                nu_num = st.text_input("Unit Number (e.g. 95)")
                nu_drv = st.text_input("Assigned Driver")
            with na_c2:
                nu_vin = st.text_input("VIN")
                nu_plt = st.text_input("Plate Number")
                nu_mdl = st.text_input("Make / Model / Year")
            if st.form_submit_button("Save Equipment") and nu_num:
                cur = conn.cursor()
                cur.execute("INSERT INTO vehicles (company, unit_type, unit_number, driver, vin, plate_number, make_model) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (nu_comp, nu_type, nu_num.strip(), nu_drv.strip(), nu_vin.strip(), nu_plt.strip(), nu_mdl.strip()))
                conn.commit()
                st.success(f"{nu_type} #{nu_num} registered!")
                st.rerun()

    df_view = df_v.copy()
    if f_type == "Trucks Only":
        df_view = df_view[df_view["unit_type"] == "TRUCK"]
    elif f_type == "Trailers Only":
        df_view = df_view[df_view["unit_type"] == "TRAILER"]

    def calc_overall(row):
        if row["oil_badge"] == "badge-overdue" or row["insp_badge"] == "badge-overdue":
            return "badge-overdue", "OVERDUE"
        elif row["oil_badge"] == "badge-due" or row["insp_badge"] == "badge-due":
            return "badge-due", "DUE SOON"
        else:
            return "badge-ready", "READY"

    ov_data = df_view.apply(calc_overall, axis=1)
    df_view["overall_badge"] = [x[0] for x in ov_data]
    df_view["overall_text"] = [x[1] for x in ov_data]

    if f_stat == "🚨 Red Overdue":
        df_view = df_view[df_view["overall_badge"] == "badge-overdue"]
    elif f_stat == "🟡 Yellow Warning":
        df_view = df_view[df_view["overall_badge"] == "badge-due"]
    elif f_stat == "🟢 Green Ready":
        df_view = df_view[df_view["overall_badge"] == "badge-ready"]

    if f_srch:
        s = f_srch.strip().lower()
        df_view = df_view[
            df_view["unit_number"].str.lower().str.contains(s) |
            df_view["driver"].str.lower().str.contains(s) |
            df_view["make_model"].str.lower().str.contains(s)
        ]

    st.caption(f"Showing **{len(df_view)}** equipment units (Click any box to inspect & edit)")

    # 5 KOLONLU TEMİZ VE BEYAZ TİLE GRID
    cols_v = st.columns(5)
    for i, (_, row) in enumerate(df_view.iterrows()):
        with cols_v[i % 5]:
            oil_text = f"{row['oil_status']}" if row['unit_type'] == 'TRUCK' else "Exempt"
            
            st.markdown(f"""
            <div class="clean-tile">
                <div class="tile-head">
                    <span class="tile-unit-title">#{row['unit_number']} ({row['unit_type']})</span>
                    <span class="badge {row['overall_badge']}">{row['overall_text']}</span>
                </div>
                <div class="tile-body">
                    👤 <b>{row['driver'] if row['driver'] else 'Unassigned'}</b><br>
                    🛢️ Oil: <span class="badge {row['oil_badge']}">{oil_text}</span><br>
                    📋 DOT: <span class="badge {row['insp_badge']}">{row['insp_status']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # KUTUYA TIKLAMA BUTONU
            if st.button(f"Open #{row['unit_number']}", key=f"tile_{row['unit_number']}", use_container_width=True):
                st.session_state["selected_unit"] = row['unit_number']
                st.rerun()

# -------------------------------------------------------------
# 2. MODÜL: DRIVERS COMPLIANCE (BEYAZ TİLE + DİREKT TIKLAMALI DOSYA)
# -------------------------------------------------------------
elif top_menu == "👤 Drivers Compliance":
    if "selected_driver" not in st.session_state:
        st.session_state["selected_driver"] = None

    # TIKLANAN ŞOFÖRÜN DOSYASI (ÜSTTE AÇILIR)
    if st.session_state["selected_driver"] and not df_d.empty:
        s_dr = st.session_state["selected_driver"]
        dr_row = df_d[df_d["Name"] == s_dr].iloc[0]
        
        st.markdown(f"""
        <div class="dossier-card">
            <h3 style="margin:0; color:#0b1f3a;">👤 Driver Master Dossier: {dr_row['Name']}</h3>
            <div style="font-size:12px; color:#64748b; margin-top:4px;">Phone: {dr_row['Telephone']} | CDL #: {dr_row.get('License Number','-')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        c_dr_close, _ = st.columns([1, 5])
        with c_dr_close:
            if st.button("✖️ Close Driver File"):
                st.session_state["selected_driver"] = None
                st.rerun()

        dr_t1, dr_t2, dr_t3 = st.tabs(["✏️ Edit Driver Info", "📸 Upload CDL, Medical & Photos", "🚨 Remove Driver"])
        
        with dr_t1:
            with st.form(f"edit_driver_form_{s_dr}"):
                de_c1, de_c2 = st.columns(2)
                with de_c1:
                    u_phone = st.text_input("Phone Number", value=dr_row['Telephone'])
                    u_email = st.text_input("Email", value=dr_row['E-mail'])
                    u_cdl_no = st.text_input("CDL Number", value=dr_row['License Number'])
                with de_c2:
                    u_cdl_exp = st.text_input("CDL Expiration (YYYY-MM-DD)", value=dr_row['License Expiry'])
                    u_med_exp = st.text_input("Medical Due (YYYY-MM-DD)", value=dr_row['Next Medical'])
                
                if st.form_submit_button("Save Driver Updates"):
                    df_d.loc[df_d["Name"] == s_dr, "Telephone"] = u_phone
                    df_d.loc[df_d["Name"] == s_dr, "E-mail"] = u_email
                    df_d.loc[df_d["Name"] == s_dr, "License Number"] = u_cdl_no
                    df_d.loc[df_d["Name"] == s_dr, "License Expiry"] = u_cdl_exp
                    df_d.loc[df_d["Name"] == s_dr, "Next Medical"] = u_med_exp
                    df_d.to_excel(DRIVERS_FILE, index=False)
                    st.success("Driver profile updated!")
                    st.rerun()

        with dr_t2:
            st.markdown(f"**Upload Documents & Incident Photos for {s_dr}**")
            dup_c1, dup_c2 = st.columns([2, 3])
            with dup_c1:
                d_cat = st.selectbox("Category", ["CDL Scan / PDF", "Medical Card Certificate", "Truck Check-in Photo", "Truck Check-out Photo", "Accident Photo", "DOT Citation"], key=f"dcat_{s_dr}")
                d_file = st.file_uploader("Select File / Photo", type=["pdf", "png", "jpg", "jpeg"], key=f"dfile_{s_dr}")
                if d_file and st.button("Save to Driver Dossier", key=f"dbtn_{s_dr}"):
                    save_dr_name = f"DR_{s_dr.replace(' ','_')}_{d_cat.replace(' ','_')}_{d_file.name}"
                    with open(os.path.join(UPLOAD_DIR, save_dr_name), "wb") as f:
                        f.write(d_file.getbuffer())
                    st.success("File added to driver dossier!")
                    st.rerun()
            with dup_c2:
                st.markdown("**Archived Driver Documents & Photos:**")
                found_dr = [f for f in os.listdir(UPLOAD_DIR) if f"DR_{s_dr.replace(' ','_')}_" in f]
                if found_dr:
                    for doc in found_dr:
                        st.write(f"📄 `{doc}`")
                else:
                    st.caption("No files recorded for this driver yet.")

        with dr_t3:
            if st.button(f"🚨 Offboard / Delete {s_dr}", type="secondary"):
                df_d = df_d[df_d["Name"] != s_dr]
                df_d.to_excel(DRIVERS_FILE, index=False)
                st.session_state["selected_driver"] = None
                st.warning(f"Driver {s_dr} deleted!")
                st.rerun()

        st.markdown("---")

    # FİLTRELER & YENİ ŞOFÖR BUTONU
    df1, df2, df3 = st.columns([2, 2, 1.2])
    with df1:
        d_status_filter = st.selectbox("Driver Status:", ["All Drivers", "🚨 Action Needed (Red)", "🟡 Expiring Soon (Yellow)", "🟢 Fully Compliant (Green)"])
    with df2:
        d_search = st.text_input("Search Driver Name or Phone:")
    with df3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        btn_new_dr = st.button("➕ Onboard Driver", use_container_width=True)

    if btn_new_dr:
        with st.form("modal_add_driver_top"):
            st.markdown("##### ➕ Onboard New Driver")
            in_name = st.text_input("Full Name")
            in_phone = st.text_input("Phone Number")
            in_cdl = st.text_input("CDL Number")
            in_cdl_exp = st.date_input("CDL Expiration")
            in_med_exp = st.date_input("Medical Due Date")
            if st.form_submit_button("Save Driver") and in_name:
                new_row = {"Name": in_name.strip(), "Telephone": in_phone.strip(), "License Number": in_cdl.strip(), "License Expiry": str(in_cdl_exp), "Next Medical": str(in_med_exp)}
                df_d = pd.concat([df_d, pd.DataFrame([new_row])], ignore_index=True)
                df_d.to_excel(DRIVERS_FILE, index=False)
                st.success(f"Driver '{in_name}' added!")
                st.rerun()

    if not df_d.empty:
        df_d_view = df_d.copy()

        def calc_dr_overall(row):
            if row["CDL_Badge"] == "badge-overdue" or row["Med_Badge"] == "badge-overdue":
                return "badge-overdue", "ACTION NEEDED"
            elif row["CDL_Badge"] == "badge-due" or row["Med_Badge"] == "badge-due":
                return "badge-due", "DUE SOON"
            else:
                return "badge-ready", "COMPLIANT"

        dr_ov = df_d_view.apply(calc_dr_overall, axis=1)
        df_d_view["overall_badge"] = [x[0] for x in dr_ov]
        df_d_view["overall_text"] = [x[1] for x in dr_ov]

        if d_status_filter == "🚨 Action Needed (Red)":
            df_d_view = df_d_view[df_d_view["overall_badge"] == "badge-overdue"]
        elif d_status_filter == "🟡 Expiring Soon (Yellow)":
            df_d_view = df_d_view[df_d_view["overall_badge"] == "badge-due"]
        elif d_status_filter == "🟢 Fully Compliant (Green)":
            df_d_view = df_d_view[df_d_view["overall_badge"] == "badge-ready"]

        if d_search:
            ds = d_search.strip().lower()
            df_d_view = df_d_view[
                df_d_view["Name"].str.lower().str.contains(ds) |
                df_d_view["Telephone"].str.lower().str.contains(ds)
            ]

        st.caption(f"Showing **{len(df_d_view)}** driver compliance profiles")

        # 4 KOLONLU ŞOFÖR TİLE GRID
        cols_d = st.columns(4)
        for j, (_, d_row) in enumerate(df_d_view.iterrows()):
            with cols_d[j % 4]:
                st.markdown(f"""
                <div class="clean-tile">
                    <div class="tile-head">
                        <span class="tile-unit-title">{d_row['Name']}</span>
                        <span class="badge {d_row['overall_badge']}">{d_row['overall_text']}</span>
                    </div>
                    <div class="tile-body">
                        📞 {d_row['Telephone']}<br>
                        🪪 CDL: <span class="badge {d_row['CDL_Badge']}">{d_row['CDL_Status']}</span><br>
                        🏥 Med: <span class="badge {d_row['Med_Badge']}">{d_row['Med_Status']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Open {d_row['Name']}", key=f"dr_tile_{j}", use_container_width=True):
                    st.session_state["selected_driver"] = d_row['Name']
                    st.rerun()

# -------------------------------------------------------------
# 3. MODÜL: DISPATCH TEAM CHAT
# -------------------------------------------------------------
elif top_menu == "💬 Dispatch Team Chat":
    st.markdown("#### 💬 Dispatch Operations & Shift Notes")
    with st.form("chat_form_top", clear_on_submit=True):
        cm1, cm2 = st.columns([5, 1])
        with cm1:
            msg_txt = st.text_input("Write note...", placeholder="E.g., Unit 14 delivered in Laredo, driver taking rest.")
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
        <div style="background:#ffffff; border-left:4px solid #0284c7; padding:8px 14px; border-radius:6px; margin-bottom:6px; border:1px solid #e2e8f0;">
            <b style="color:#0b1f3a; font-size:13px;">👤 {r['sender']}</b> <span style="font-size:10px; color:#64748b; margin-left:8px;">🕒 {r['timestamp']}</span>
            <div style="margin-top:2px; font-size:13px; color:#0f172a;">{r['message']}</div>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# 4. MODÜL: SERVICE LEDGER
# -------------------------------------------------------------
elif top_menu == "🔧 Service Ledger":
    st.markdown("#### 🔧 Log Equipment Maintenance & Service Record")
    with st.form("service_top", clear_on_submit=True):
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
        
