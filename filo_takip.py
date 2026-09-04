import glob
import os
import re
import shutil
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="MOONSTAR TMS - Fleet Portal",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SIKI VE TEMİZ KURUMSAL TMS ARAYÜZ STİLİ ---
st.markdown("""
<style>
    /* Üst Kurumsal Header */
    .tms-navbar {
        background-color: #0b1f3a;
        background: linear-gradient(90deg, #0b1f3a 0%, #1e3a8a 100%);
        padding: 14px 20px;
        border-radius: 6px;
        color: #ffffff;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }
    .tms-title {
        font-size: 20px;
        font-weight: 800;
        letter-spacing: 0.5px;
        margin: 0;
        color: #ffffff !important;
    }
    .tms-subtitle {
        font-size: 12px;
        color: #93c5fd;
        margin: 0;
    }
    .tms-user {
        font-size: 12px;
        background: rgba(255,255,255,0.15);
        padding: 5px 12px;
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,0.25);
    }
    /* Metrik Kartları */
    div[data-testid="metric-container"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 10px 14px;
        border-radius: 6px;
    }
    /* Chat Balonu */
    .chat-card {
        background: #f8fafc;
        border-left: 4px solid #0284c7;
        padding: 8px 12px;
        border-radius: 4px;
        margin-bottom: 8px;
        border-top: 1px solid #e2e8f0;
        border-right: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

DB_FILE = "fleet_database.db"
INVOICE_DIR = "faturalar"
DRIVERS_FILE = "Drivers.xlsx"
FLEET_EXCEL = "Başlıksız e-tablo (2) copy 2.xlsx"
SERVICE_LOGS_CSV = "Service logs.csv"

os.makedirs(INVOICE_DIR, exist_ok=True)

# --- KURUMSAL GİRİŞ KONTROLÜ ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logo.jpg"):
            st.image("logo.jpg", width=220)
        st.markdown("### 🔒 MOONSTAR EXPRESS LLC — TMS PORTAL")
        with st.form("login_form"):
            email = st.text_input("Kurumsal E-Posta", placeholder="ornek@moonstarpa...")
            password = st.text_input("Şifre", type="password")
            submit = st.form_submit_button("Giriş Yap")
        if submit:
            if "@moonstarpa" in email.strip().lower() and password == "Moonstar2026!":
                st.session_state["authenticated"] = True
                st.session_state["current_user"] = email.strip().lower()
                st.rerun()
            else:
                st.error("Yetkisiz erişim! Geçersiz kurumsal e-posta veya şifre.")
    st.stop()

# ---------------------------------------------
def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def check_driver_expiry(date_str):
    if not date_str or str(date_str).strip() in ["0000-00-00", "nan", "None", "-", ""]:
        return "Tarih Yok", "⚪"
    try:
        dt = datetime.strptime(str(date_str).strip()[:10], "%Y-%m-%d").date()
        today = datetime.now().date()
        diff = (dt - today).days
        if diff < 0:
            return f"Doldu ({abs(diff)}g)", "🔴"
        elif diff <= 30:
            return f"Kritik ({diff}g)", "🟡"
        elif diff <= 60:
            return f"Yaklaşıyor ({diff}g)", "🟠"
        else:
            return f"Geçerli ({diff}g)", "🟢"
    except Exception:
        return "Geçersiz", "⚪"

def check_oil_status(row):
    if row.get("unit_type") == "TRAILER":
        return "Muaf (Dorse)", "⚪", "-"
    try:
        c_m = int(row.get("current_mileage") or 0)
        l_o = int(row.get("last_oil_mileage") or 0)
        interval = int(row.get("oil_interval") or 25000)
        if interval <= 0 or (l_o == 0 and c_m == 0):
            return "Kayıt Yok", "⚪", "-"
        miles_driven = c_m - l_o
        rem = interval - miles_driven
        if rem < 0:
            return f"Geçti ({abs(rem):,} mi)", "🔴", f"{rem:,}"
        elif rem <= 3000:
            return f"Yaklaşıyor ({rem:,} mi)", "🟡", f"{rem:,}"
        else:
            return f"Geçerli ({rem:,} mi)", "🟢", f"{rem:,}"
    except Exception:
        return "Hesap Hatası", "⚪", "-"

def extract_unit_no(asset_str):
    if not isinstance(asset_str, str):
        return ""
    m = re.search(r'\b\d+\b', asset_str)
    return m.group(0) if m else asset_str.strip()

def parse_updated_sheet(filepath):
    try:
        df_raw = pd.read_excel(filepath)
    except Exception:
        return []
    records = []
    curr_company = "MOONSTAR"
    curr_type = "TRUCK"

    for _, row in df_raw.iterrows():
        m_val = str(row.get("MOONSTAR", "")).strip().upper()
        u_val = str(row.get("UNIT", "")).strip()

        if "TRAILER" in m_val:
            curr_type = "TRAILER"
            continue
        elif "LIONSTAR" in m_val:
            curr_company = "LIONSTAR"
            curr_type = "TRUCK"
            continue

        if not u_val or u_val.upper() == "UNIT" or u_val.lower() == "nan":
            continue

        records.append({
            "company": curr_company,
            "unit_type": curr_type,
            "unit_number": u_val,
            "driver": str(row.get("DRIVER", "")).strip() if pd.notna(row.get("DRIVER")) else "",
            "vin": str(row.get("VIN", "")).strip() if pd.notna(row.get("VIN")) else "",
            "plate_number": str(row.get("PLATE", "")).strip() if pd.notna(row.get("PLATE")) else "",
            "make_model": str(row.get("MAKE-MODEL-YEAR", "")).strip() if pd.notna(row.get("MAKE-MODEL-YEAR")) else "",
            "plate_expiry": str(row.get("REGISTRATION", "")).split(" ")[0].replace("0000-00-00", "") if pd.notna(row.get("REGISTRATION")) else "",
            "dot_inspection": str(row.get("ANNUAL INSPECTION", "")).split(" ")[0].replace("0000-00-00", "") if pd.notna(row.get("ANNUAL INSPECTION")) else "",
            "state_inspection": str(row.get("PA INSPECTION", "")).split(" ")[0].replace("0000-00-00", "") if pd.notna(row.get("PA INSPECTION")) else "",
            "current_mileage": 0,
            "last_oil_mileage": 0,
            "oil_interval": 25000 if curr_type == "TRUCK" else 0
        })
    return records

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

    c.execute("SELECT COUNT(*) FROM vehicles")
    if c.fetchone()[0] == 0 and os.path.exists(FLEET_EXCEL):
        records = parse_updated_sheet(FLEET_EXCEL)
        for r in records:
            c.execute("""
                INSERT OR IGNORE INTO vehicles 
                (company, unit_type, unit_number, driver, vin, plate_number, make_model, plate_expiry, dot_inspection, state_inspection, current_mileage, last_oil_mileage, oil_interval)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r["company"], r["unit_type"], r["unit_number"], r["driver"], r["vin"],
                r["plate_number"], r["make_model"], r["plate_expiry"], r["dot_inspection"],
                r["state_inspection"], r["current_mileage"], r["last_oil_mileage"], r["oil_interval"]
            ))
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

def evaluate_status(row):
    status = "GEÇERLİ"
    today = datetime.now().date()
    for col in ["plate_expiry", "dot_inspection", "state_inspection"]:
        d_str = str(row.get(col, "")).strip()
        if d_str and d_str not in ["nan", "None", "", "-"]:
            try:
                dt = datetime.strptime(d_str[:10], "%Y-%m-%d").date()
                days = (dt - today).days
                if days < 0:
                    return "GECİKMİŞ ❌"
                elif days <= 30:
                    status = "YAKLAŞIYOR ⚠️"
            except:
                pass
    return status

conn = get_connection()
df_v = pd.read_sql_query("SELECT * FROM vehicles ORDER BY unit_number ASC", conn)
df_logs = pd.read_sql_query("SELECT * FROM logs ORDER BY log_date DESC", conn)

cost_totals = df_logs.groupby("unit_number")["cost"].sum().to_dict() if not df_logs.empty else {}
df_v["total_spent"] = df_v["unit_number"].map(cost_totals).fillna(0.0).apply(lambda x: f"${x:,.2f}")
df_v["muayene_durum"] = df_v.apply(evaluate_status, axis=1)

oil_results = df_v.apply(check_oil_status, axis=1)
df_v["yag_durumu"] = [res[0] for res in oil_results]
df_v["yag_ikon"] = [res[1] for res in oil_results]
df_v["kalan_yag_mili"] = [res[2] for res in oil_results]

total_trucks = len(df_v[df_v["unit_type"] == "TRUCK"])
total_trailers = len(df_v[df_v["unit_type"] == "TRAILER"])
crit_oil_df = df_v[df_v["yag_ikon"].isin(["🔴", "🟡"])]
crit_insp_df = df_v[df_v["muayene_durum"].str.contains("❌|⚠️")]
all_spending = df_logs["cost"].sum() if not df_logs.empty else 0.0

# -------------------------------------------------------------
# YAN PANEL (SOL MENÜ)
# -------------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=170)
    st.markdown("### 🏢 MOONSTAR TMS")
    st.caption(f"Aktif Kullanıcı: **{st.session_state.get('current_user')}**")
    
    st.markdown("---")
    menu = st.radio(
        "ANA MODÜLLER",
        [
            "🚛 Dispatch & Filo Tablosu",
            "👤 Şoförler & CDL/Medical",
            "💬 Ekip İçi Chat (Operasyon)",
            "🔧 Bakım & Servis Kaydı Ekle",
            "📁 Evrak & Fatura Arşivi"
        ],
        index=0
    )
    
    st.markdown("---")
    st.markdown("**Hızlı Filo Özeti**")
    st.write(f"🚛 **Truck:** {total_trucks}  |  🚚 **Trailer:** {total_trailers}")
    st.write(f"🚨 **Yağ Alarmı:** {len(crit_oil_df)} çekici")
    st.write(f"⚠️ **Muayene Alarmı:** {len(crit_insp_df)} araç")
    
    st.markdown("---")
    if st.button("🚪 Güvenli Çıkış"):
        st.session_state["authenticated"] = False
        st.rerun()

# -------------------------------------------------------------
# ÜST KURUMSAL ŞERİT (NAVBAR)
# -------------------------------------------------------------
st.markdown(f"""
<div class="tms-navbar">
    <div>
        <div class="tms-title">MOONSTAR EXPRESS LLC — DISPATCH & OPERATIONS PORTAL</div>
        <div class="tms-subtitle">Bensalem, PA • Fleet Maintenance, Driver Compliance & Live Tracking</div>
    </div>
    <div class="tms-user">
        🟢 Canlı Oturum: <b>{st.session_state.get('current_user')}</b>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. BÖLÜM: DİSPATCH & FİLO TABLOSU (GERÇEK TMS GÖRÜNÜMÜ)
# -------------------------------------------------------------
if menu == "🚛 Dispatch & Filo Tablosu":
    # 4 Temiz ve Şık Metrik
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Kayıtlı Ekipman", f"{total_trucks} Çekici / {total_trailers} Dorse")
    m2.metric("Yağ Değişimi Alarmı", f"{len(crit_oil_df)} Çekici", delta_color="inverse")
    m3.metric("Muayene Alarmı", f"{len(crit_insp_df)} Araç", delta_color="inverse")
    m4.metric("Toplam Servis Harcaması", f"${all_spending:,.2f}")

    st.markdown("---")

    # FİLTRELEME ÇUBUĞU (TEK SIRADA TEMİZ)
    f1, f2, f3, f4 = st.columns([1, 1, 1, 2])
    with f1:
        f_comp = st.selectbox("Firma:", ["HEPSİ", "MOONSTAR", "LIONSTAR"])
    with f2:
        f_type = st.selectbox("Ekipman:", ["HEPSİ", "TRUCK", "TRAILER"])
    with f3:
        f_alert = st.selectbox("Filtre:", ["Tümü", "🚨 Sadece Yağ Alarmları", "⚠️ Sadece Muayene Alarmları"])
    with f4:
        f_search = st.text_input("Ara (Unit, Şoför, Plaka, Model):")

    df_view = df_v.copy()
    if f_comp != "HEPSİ":
        df_view = df_view[df_view["company"] == f_comp]
    if f_type == "TRUCK":
        df_view = df_view[df_view["unit_type"] == "TRUCK"]
    elif f_type == "TRAILER":
        df_view = df_view[df_view["unit_type"] == "TRAILER"]
    
    if f_alert == "🚨 Sadece Yağ Alarmları":
        df_view = df_view[df_view["yag_ikon"].isin(["🔴", "🟡"])]
    elif f_alert == "⚠️ Sadece Muayene Alarmları":
        df_view = df_view[df_view["muayene_durum"].str.contains("❌|⚠️")]

    if f_search:
        s = f_search.strip().lower()
        df_view = df_view[
            df_view["unit_number"].str.lower().str.contains(s) |
            df_view["driver"].str.lower().str.contains(s) |
            df_view["plate_number"].str.lower().str.contains(s) |
            df_view["make_model"].str.lower().str.contains(s)
        ]

    # CANLI DÜZENLENEBİLİR VE NET TABLO (ITS DISPATCH TARZI)
    cols = [
        "unit_number", "company", "unit_type", "driver", "make_model", 
        "current_mileage", "last_oil_mileage", "yag_ikon", "yag_durumu",
        "plate_number", "plate_expiry", "dot_inspection", "state_inspection", "muayene_durum"
    ]

    st.dataframe(
        df_view[cols].rename(columns={
            "unit_number": "Unit",
            "company": "Şirket",
            "unit_type": "Tür",
            "driver": "Şoför",
            "make_model": "Model / Yıl",
            "current_mileage": "Güncel Mil",
            "last_oil_mileage": "Son Yağ Mili",
            "yag_ikon": "Yağ",
            "yag_durumu": "Yağ Durumu",
            "plate_number": "Plaka",
            "plate_expiry": "Registration",
            "dot_inspection": "Annual / DOT",
            "state_inspection": "PA / State",
            "muayene_durum": "Muayene"
        }),
        use_container_width=True,
        height=500,
        hide_index=True
    )

    # ALTTAN HIZLI EKLEME / SİLME FORMU
    with st.expander("⚙️ Araç Yönetimi (Yeni Çekici / Dorse Ekle & Sil)"):
        ca, cb = st.columns(2)
        with ca:
            st.markdown("**➕ Yeni Ekipman Ekle**")
            with st.form("add_v_form"):
                acomp = st.selectbox("Firma", ["MOONSTAR", "LIONSTAR"])
                atype = st.selectbox("Tür", ["TRUCK", "TRAILER"])
                aunit = st.text_input("Unit No (Örn: 95)")
                adriver = st.text_input("Şoför")
                avin = st.text_input("VIN")
                aplate = st.text_input("Plaka")
                amodel = st.text_input("Model / Yıl")
                areg = st.date_input("Registration Bitiş")
                adot = st.date_input("DOT Muayene")
                astate = st.date_input("State Muayene")
                if st.form_submit_button("Aracı Kaydet"):
                    if aunit:
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO vehicles (company, unit_type, unit_number, driver, vin, plate_number, make_model, plate_expiry, dot_inspection, state_inspection)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (acomp, atype, aunit.strip(), adriver.strip(), avin.strip(), aplate.strip(), amodel.strip(), str(areg), str(adot), str(astate)))
                        conn.commit()
                        st.success(f"{atype} #{aunit} kaydedildi!")
                        st.rerun()
                    else:
                        st.error("Unit No zorunludur.")
        with cb:
            st.markdown("**❌ Sistemden Araç Sil**")
            all_u = df_v["unit_number"].dropna().tolist()
            u_to_del = st.selectbox("Silinecek Araç:", ["Seçiniz..."] + all_u)
            if st.button("🚨 Seçili Aracı Sil", type="secondary"):
                if u_to_del != "Seçiniz...":
                    cur = conn.cursor()
                    cur.execute("DELETE FROM vehicles WHERE unit_number = ?", (u_to_del,))
                    conn.commit()
                    st.warning(f"Unit #{u_to_del} silindi!")
                    st.rerun()

# -------------------------------------------------------------
# 2. BÖLÜM: ŞOFÖRLER & COMPLIANCE
# -------------------------------------------------------------
elif menu == "👤 Şoförler & CDL/Medical":
    st.markdown("#### 👤 Şoförler, CDL Ehliyet & Medical Card Masası")

    if os.path.exists(DRIVERS_FILE):
        df_d = pd.read_excel(DRIVERS_FILE)
        df_d = df_d[df_d["Name"].notna()].copy()
        df_d["License Expiry"] = df_d["License Expiry"].astype(str).str.strip()
        df_d["Next Medical"] = df_d["Next Medical"].astype(str).str.strip()
        df_d["E-mail"] = df_d["E-mail"].fillna("-").astype(str).str.strip()
        df_d["Telephone"] = df_d["Telephone"].fillna("-").astype(str).str.strip()
        df_d["License Number"] = df_d["License Number"].fillna("-").astype(str).str.strip()

        df_d["Ehliyet Durumu"] = df_d["License Expiry"].apply(lambda d: check_driver_expiry(d)[0])
        df_d["Ehliyet İkon"] = df_d["License Expiry"].apply(lambda d: check_driver_expiry(d)[1])
        df_d["Medical Durumu"] = df_d["Next Medical"].apply(lambda d: check_driver_expiry(d)[0])
        df_d["Medical İkon"] = df_d["Next Medical"].apply(lambda d: check_driver_expiry(d)[1])

        c_lic = df_d[df_d["Ehliyet İkon"].isin(["🔴", "🟡"])]
        c_med = df_d[df_d["Medical İkon"].isin(["🔴", "🟡"])]

        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Toplam Şoför", len(df_d))
        d2.metric("Aktif Şoförler", len(df_d[df_d["Status"] == "Active"]))
        d3.metric("Kritik CDL", len(c_lic), delta_color="inverse")
        d4.metric("Kritik Medical Card", len(c_med), delta_color="inverse")

        if len(c_lic) > 0:
            st.error(f"🚨 **DİKKAT:** {len(c_lic)} şoförün CDL lisans süresi dolmuş veya dolmak üzere!")
        if len(c_med) > 0:
            st.warning(f"⚠️ **DİKKAT:** {len(c_med)} şoförün Medical Card süresi kritik seviyede!")

        d_cols = [
            "Name", "Telephone", "E-mail", "License Number", 
            "License Expiry", "Ehliyet İkon", "Ehliyet Durumu", 
            "Next Medical", "Medical İkon", "Medical Durumu"
        ]

        st.dataframe(
            df_d[d_cols].rename(columns={
                "Name": "Şoför Adı Soyadı",
                "Telephone": "Telefon",
                "E-mail": "Kurumsal / Şahsi E-Posta",
                "License Number": "CDL Lisans No",
                "License Expiry": "CDL Bitiş",
                "Ehliyet İkon": "CDL",
                "Next Medical": "Medical Bitiş",
                "Medical İkon": "Med"
            }),
            use_container_width=True,
            hide_index=True
        )

        with st.expander("👤 Yeni Şoför Ekle & Sil"):
            da, db = st.columns(2)
            with da:
                st.markdown("**Yeni Şoför Ekle**")
                with st.form("new_dr_form"):
                    dn = st.text_input("Ad Soyad")
                    dp = st.text_input("Telefon")
                    de = st.text_input("E-Posta")
                    dl = st.text_input("CDL Lisans No")
                    dle = st.date_input("CDL Bitiş Tarihi")
                    dme = st.date_input("Medical Card Bitiş Tarihi")
                    if st.form_submit_button("Şoförü Kaydet") and dn:
                        new_r = {
                            "Status": "Active", "Name": dn.strip(), "Telephone": dp.strip(),
                            "E-mail": de.strip(), "License Number": dl.strip(),
                            "License Expiry": str(dle), "Next Medical": str(dme)
                        }
                        df_d = pd.concat([df_d, pd.DataFrame([new_r])], ignore_index=True)
                        df_d.to_excel(DRIVERS_FILE, index=False)
                        st.success(f"{dn} eklendi!")
                        st.rerun()
            with db:
                st.markdown("**Şoför Sil**")
                all_drs = df_d["Name"].dropna().tolist()
                del_dr = st.selectbox("Silinecek Şoför:", ["Seçiniz..."] + all_drs)
                if st.button("🚨 Şoförü Sil") and del_dr != "Seçiniz...":
                    df_d = df_d[df_d["Name"] != del_dr]
                    df_d.to_excel(DRIVERS_FILE, index=False)
                    st.warning(f"{del_dr} silindi!")
                    st.rerun()

# -------------------------------------------------------------
# 3. BÖLÜM: EKİP İÇİ CANLI CHAT
# -------------------------------------------------------------
elif menu == "💬 Ekip İçi Chat (Operasyon)":
    st.markdown("#### 💬 Moonstar Ekip İçi Operasyon Mesajlaşması")
    with st.form("chat_box", clear_on_submit=True):
        cm1, cm2 = st.columns([5, 1])
        with cm1:
            msg = st.text_input("Mesajınızı yazın...", placeholder="Örn: Unit 12'nin servisi tamamlandı, sefere çıkıyor.", label_visibility="collapsed")
        with cm2:
            if st.form_submit_button("Gönder 🚀", use_container_width=True) and msg.strip():
                cur = conn.cursor()
                now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
                cur.execute("INSERT INTO team_chat (sender, message, timestamp) VALUES (?, ?, ?)", (st.session_state.get("current_user"), msg.strip(), now_str))
                conn.commit()
                st.rerun()

    df_chat = pd.read_sql_query("SELECT * FROM team_chat ORDER BY id DESC LIMIT 50", conn)
    if not df_chat.empty:
        for _, r in df_chat.iterrows():
            st.markdown(f"""
            <div class="chat-card">
                <b>👤 {r['sender']}</b> <span style="color:#64748b; font-size:11px; margin-left:8px;">🕒 {r['timestamp']}</span>
                <div style="margin-top:4px; font-size:14px; color:#1e293b;">{r['message']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Henüz bir mesaj paylaşılmamış.")

# -------------------------------------------------------------
# 4. BÖLÜM: BAKIM & SERVİS GİRİŞİ
# -------------------------------------------------------------
elif menu == "🔧 Bakım & Servis Kaydı Ekle":
    st.markdown("#### 🔧 Servis & Bakım Girişi")
    with st.form("log_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            sel_u = st.selectbox("Unit Seçin", df_v["unit_number"].tolist())
            l_date = st.date_input("İşlem Tarihi")
        with c2:
            l_type = st.selectbox("İşlem Türü", ["Yağ Değişimi", "Lastik / Fren", "DOT Muayene", "Arıza / Onarım", "Periyodik Bakım", "Diğer"])
            l_mil = st.number_input("İşlem Mili", min_value=0, step=1000)
        with c3:
            l_cost = st.number_input("Tutar ($)", min_value=0.0, step=50.0)
            inv_file = st.file_uploader("Fatura / Belge", type=["pdf", "png", "jpg", "jpeg"])
        
        l_notes = st.text_area("Açıklamalar")
        if st.form_submit_button("Servisi Kaydet"):
            s_file = ""
            if inv_file:
                s_file = f"Unit_{sel_u}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{inv_file.name}"
                with open(os.path.join(INVOICE_DIR, s_file), "wb") as f:
                    f.write(inv_file.getbuffer())
            cur = conn.cursor()
            cur.execute("INSERT INTO logs (unit_number, log_date, log_type, mileage, cost, invoice_filename, notes) VALUES (?, ?, ?, ?, ?, ?, ?)", (sel_u, str(l_date), l_type, l_mil, l_cost, s_file, l_notes))
            if l_type == "Yağ Değişimi" and l_mil > 0:
                cur.execute("UPDATE vehicles SET last_oil_mileage = ?, current_mileage = MAX(current_mileage, ?) WHERE unit_number = ?", (l_mil, l_mil, sel_u))
            elif l_mil > 0:
                cur.execute("UPDATE vehicles SET current_mileage = MAX(current_mileage, ?) WHERE unit_number = ?", (l_mil, sel_u))
            conn.commit()
            st.success("Kayıt başarıyla tamamlandı!")
            st.rerun()

# -------------------------------------------------------------
# 5. BÖLÜM: EVRAK & FATURA ARŞİVİ
# -------------------------------------------------------------
elif menu == "📁 Evrak & Fatura Arşivi":
    st.markdown("#### 📁 Fatura & Belge Deposu")
    all_files = os.listdir(INVOICE_DIR) if os.path.exists(INVOICE_DIR) else []
    if all_files:
        for f in all_files:
            st.write(f"📄 `{f}`")
    else:
        st.info("Arşivde yüklü evrak bulunmuyor.")
