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

# MODERN ENTERPRISE LOGISTICS MODAL THEME
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #f8fafc !important;
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
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .brand-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 20px;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
    }
    
    /* Doğrudan Tıklanabilir Kart Butonu */
    div[data-testid*="stButton"] > button.unit-card-btn {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 12px 14px !important;
        text-align: left !important;
        height: auto !important;
        min-height: 110px !important;
        width: 100% !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        color: #1e293b !important;
    }
    div[data-testid*="stButton"] > button.unit-card-btn:hover {
        border-color: #0284c7 !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.12) !important;
    }

    /* Sadece Rozetler Renkli */
    .badge-ready { background: #dcfce7; color: #15803d; padding: 2px 6px; border-radius: 4px; font-weight: 700; font-size: 10px; }
    .badge-due { background: #fef9c3; color: #854d0e; padding: 2px 6px; border-radius: 4px; font-weight: 700; font-size: 10px; }
    .badge-overdue { background: #fee2e2; color: #991b1b; padding: 2px 6px; border-radius: 4px; font-weight: 700; font-size: 10px; }
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
    df_d["CDL_Badge"] = df_d["License Expiry"].apply(lambda d: check_date_status(d)[1])
    df_d["Med_Status"] = df_d["Next Medical"].apply(lambda d: check_date_status(d)[0])
    df_d["Med_Badge"] = df_d["Next Medical"].apply(lambda d: check_date_status(d)[1])

# -------------------------------------------------------------
# POPUP MODAL DIALOGS (DİREKT KUTUYA TIKLAYINCA AÇILAN PENCERELER)
# -------------------------------------------------------------
@st.dialog("Equipment Master Dossier", width="large")
def show_equipment_modal(unit_no):
    r_sel = df_v[df_v["unit_number"] == unit_no].iloc[0]
    st.subheader(f"Unit #{r_sel['unit_number']} — {r_sel['unit_type']} ({r_sel['company']})")
    
    m_tab1, m_tab2, m_tab3 = st.tabs(["✏️ Edit Vehicle Information", "📎 Documents & Photos", "🚨 Decommission Asset"])
    
    with m_tab1:
        with st.form(f"modal_edit_v_{unit_no}"):
            c1, c2, c3 = st.columns(3)
            with c1:
                me_drv = st.text_input("Assigned Driver", value=r_sel['driver'] or "")
                me_plt = st.text_input("Plate Number", value=r_sel['plate_number'] or "")
            with c2:
                me_vin = st.text_input("VIN / Serial", value=r_sel['vin'] or "")
                me_mdl = st.text_input("Make / Model / Year", value=r_sel['make_model'] or "")
            with c3:
                me_cur = st.number_input("Current Mileage (mi)", value=int(r_sel['current_mileage'] or 0))
                me_oil = st.number_input("Last Oil Change (mi)", value=int(r_sel['last_oil_mileage'] or 0))

            if st.form_submit_button("Save Vehicle Changes"):
                cur = conn.cursor()
                cur.execute("""
                    UPDATE vehicles 
                    SET driver=?, plate_number=?, vin=?, make_model=?, current_mileage=?, last_oil_mileage=?
                    WHERE unit_number=?
                """, (me_drv, me_plt, me_vin, me_mdl, me_cur, me_oil, unit_no))
                conn.commit()
                st.success("Vehicle updated successfully!")
                st.rerun()

    with m_tab2:
        st.markdown("**Upload Registration, DOT Inspections, or Condition Photos**")
        doc_col1, doc_col2 = st.columns([2, 3])
        with doc_col1:
            doc_cat = st.selectbox("Category", ["Registration Card", "Annual DOT Inspection", "Truck Photo", "Insurance", "Repair Order"], key=f"m_cat_{unit_no}")
            doc_file = st.file_uploader("Select File", type=["pdf", "png", "jpg", "jpeg"], key=f"m_file_{unit_no}")
            if doc_file and st.button("Upload to Dossier", key=f"m_btn_{unit_no}"):
                s_name = f"EQUIP_{unit_no}_{doc_cat.replace(' ', '_')}_{doc_file.name}"
                with open(os.path.join(UPLOAD_DIR, s_name), "wb") as f:
                    f.write(doc_file.getbuffer())
                st.success("File archived!")
                st.rerun()
        with doc_col2:
            st.markdown("**Archived Documents & Photos:**")
            found_v = [f for f in os.listdir(UPLOAD_DIR) if f"EQUIP_{unit_no}_" in f]
            if found_v:
                for doc in found_v:
                    st.write(f"📄 `{doc}`")
            else:
                st.caption("No files uploaded for this equipment yet.")

    with m_tab3:
        st.warning(f"Are you sure you want to permanently delete Unit #{unit_no}?")
        if st.button("🚨 Yes, Delete Equipment Permanently", type="secondary"):
            cur = conn.cursor()
            cur.execute("DELETE FROM vehicles WHERE unit_number = ?", (unit_no,))
            conn.commit()
            st.rerun()

@st.dialog("Driver Master Dossier", width="large")
def show_driver_modal(driver_name):
    d_sel = df_d[df_d["Name"] == driver_name].iloc[0]
    st.subheader(f"Driver Dossier: {d_sel['Name']}")
    
    d_tab1, d_tab2, d_tab3 = st.tabs(["✏️ Edit Driver Profile", "📸 Documents & Photos", "🚨 Remove Driver"])
    
    with d_tab1:
        with st.form(f"modal_edit_dr_{driver_name}"):
            dc1, dc2 = st.columns(2)
            with dc1:
                de_phone = st.text_input("Phone", value=d_sel['Telephone'])
                de_email = st.text_input("Email", value=d_sel['E-mail'])
                de_cdl = st.text_input("CDL Number", value=d_sel['License Number'])
            with dc2:
                de_cdl_exp = st.text_input("CDL Expiration (YYYY-MM-DD)", value=d_sel['License Expiry'])
                de_med_exp = st.text_input("Medical Due (YYYY-MM-DD)", value=d_sel['Next Medical'])

            if st.form_submit_button("Save Driver Profile"):
                df_d.loc[df_d["Name"] == driver_name, "Telephone"] = de_phone
                df_d.loc[df_d["Name"] == driver_name, "E-mail"] = de_email
                df_d.loc[df_d["Name"] == driver_name, "License Number"] = de_cdl
                df_d.loc[df_d["Name"] == driver_name, "License Expiry"] = de_cdl_exp
                df_d.loc[df_d["Name"] == driver_name, "Next Medical"] = de_med_exp
                df_d.to_excel(DRIVERS_FILE, index=False)
                st.success("Driver updated successfully!")
                st.rerun()

    with d_tab2:
        st.markdown("**Upload CDL, Medical Card, Truck Check-in/out Photos, or Citations**")
        d_col1, d_col2 = st.columns([2, 3])
        with d_col1:
            dr_cat = st.selectbox("Document Category", ["CDL License Scan", "Medical Card Certificate", "Truck Check-in Photo", "Truck Check-out Photo", "Accident Report", "DOT Citation"], key=f"dr_cat_{driver_name}")
            dr_file = st.file_uploader("Select File", type=["pdf", "png", "jpg", "jpeg"], key=f"dr_file_{driver_name}")
            if dr_file and st.button("Save to Driver File", key=f"dr_btn_{driver_name}"):
                save_name = f"DR_{driver_name.replace(' ', '_')}_{dr_cat.replace(' ', '_')}_{dr_file.name}"
                with open(os.path.join(UPLOAD_DIR, save_name), "wb") as f:
                    f.write(dr_file.getbuffer())
                st.success("File added to driver dossier!")
                st.rerun()
        with d_col2:
            st.markdown("**Archived Driver Files:**")
            found_dr = [f for f in os.listdir(UPLOAD_DIR) if f"DR_{driver_name.replace(' ', '_')}_" in f]
            if found_dr:
                for d in found_dr:
                    st.write(f"📄 `{d}`")
            else:
                st.caption("No files uploaded for this driver yet.")

    with d_tab3:
        st.warning(f"Are you sure you want to remove {driver_name} from active fleet drivers?")
        if st.button("🚨 Yes, Offboard Driver", type="secondary"):
            df_new = df_d[df_d["Name"] != driver_name]
            df_new.to_excel(DRIVERS_FILE, index=False)
            st.rerun()

# -------------------------------------------------------------
# TOP NAVBAR & YATAY MENÜ (SIDEBARSIZ TAM EKRAN)
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
# 1. MODÜL: TRUCKS & TRAILERS (TEK KUTUYA TIKLAMALI POPUP)
# -------------------------------------------------------------
if top_menu == "🚛 Trucks & Trailers":
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
            st.markdown("##### ➕ Register New Equipment")
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

    st.caption(f"Showing **{len(df_view)}** equipment units (Click any box to open full dossier)")

    # 5 KOLONLU BEYAZ KARTLAR (TEK BUTONLA DOĞRUDAN POPUP AÇILIR)
    cols_v = st.columns(5)
    for i, (_, row) in enumerate(df_view.iterrows()):
        with cols_v[i % 5]:
            status_symbol = "🔴" if row["overall_text"] == "OVERDUE" else ("🟡" if row["overall_text"] == "DUE SOON" else "🟢")
            oil_str = row['oil_status'] if row['unit_type'] == 'TRUCK' else "Exempt"
            driver_str = row['driver'] if row['driver'] else 'Unassigned'
            
            card_label = f"#{row['unit_number']} ({row['unit_type']})  [{status_symbol} {row['overall_text']}]\n👤 {driver_str}\n🛢️ {oil_str}\n📋 {row['insp_status']}"
            
            if st.button(card_label, key=f"btn_tile_v_{row['unit_number']}", use_container_width=True):
                show_equipment_modal(row['unit_number'])

# -------------------------------------------------------------
# 2. MODÜL: DRIVERS COMPLIANCE (TEK KUTUYA TIKLAMALI POPUP)
# -------------------------------------------------------------
elif top_menu == "👤 Drivers Compliance":
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

        st.caption(f"Showing **{len(df_d_view)}** driver compliance profiles (Click any box to open full dossier)")

        # 4 KOLONLU ŞOFÖR BEYAZ KARTLARI
        cols_d = st.columns(4)
        for j, (_, d_row) in enumerate(df_d_view.iterrows()):
            with cols_d[j % 4]:
                dr_sym = "🔴" if d_row["overall_text"] == "ACTION NEEDED" else ("🟡" if d_row["overall_text"] == "DUE SOON" else "🟢")
                
                dr_card_label = f"{d_row['Name']}  [{dr_sym} {d_row['overall_text']}]\n📞 {d_row['Telephone']}\n🪪 CDL: {d_row['CDL_Status']}\n🏥 Med: {d_row['Med_Status']}"
                
                if st.button(dr_card_label, key=f"btn_tile_dr_{j}", use_container_width=True):
                    show_driver_modal(d_row['Name'])

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
