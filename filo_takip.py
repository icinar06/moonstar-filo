import glob
import os
import re
import shutil
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="MOONSTAR EXPRESS LLC - Enterprise Fleet Portal",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Kurumsal Tema ve Modern Kart Stilleri
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main-header {
        background: linear-gradient(135deg, #0b1f3a 0%, #172554 50%, #1e40af 100%);
        padding: 18px 26px;
        border-radius: 10px;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(11, 31, 58, 0.15);
    }
    .header-title { font-size: 24px; font-weight: 800; letter-spacing: 0.5px; margin: 0; }
    .header-sub { font-size: 13px; color: #93c5fd; margin-top: 3px; }
    .user-badge {
        background: rgba(255, 255, 255, 0.12);
        padding: 8px 16px;
        border-radius: 30px;
        font-size: 13px;
        border: 1px solid rgba(255, 255, 255, 0.25);
    }
    .profile-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        margin-bottom: 16px;
    }
    .card-title {
        font-size: 16px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 12px;
        border-bottom: 2px solid #f1f5f9;
        padding-bottom: 6px;
    }
    .badge-tag {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-green { background: #dcfce7; color: #15803d; }
    .badge-yellow { background: #fef9c3; color: #a16207; }
    .badge-red { background: #fee2e2; color: #b91c1c; }
    .chat-bubble {
        background-color: #f8fafc;
        border-left: 4px solid #1e40af;
        padding: 10px 14px;
        border-radius: 6px;
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

# --- KURUMSAL GİRİŞ ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("logo.jpg"):
            st.image("logo.jpg", width=240)
        st.markdown("### 🔒 MOONSTAR EXPRESS LLC — TMS PORTAL")
        st.caption("Enterprise Fleet, Driver Compliance & Document Management")
        with st.form("login_form"):
            email = st.text_input("Kurumsal E-Posta", placeholder="ismail@moonstarpa.com")
            password = st.text_input("Şifre", type="password")
            submit = st.form_submit_button("Giriş Yap")
        if submit:
            if "@moonstarpa" in email.strip().lower() and password == "Moonstar2026!":
                st.session_state["authenticated"] = True
                st.session_state["current_user"] = email.strip().lower()
                st.rerun()
            else:
                st.error("Yetkisiz erişim! Geçersiz e-posta veya şifre.")
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
            return f"Geçti ({abs(rem):,} mil)", "🔴", f"{rem:,}"
        elif rem <= 3000:
            return f"Yaklaşıyor ({rem:,} mil)", "🟡", f"{rem:,}"
        else:
            return f"Geçerli ({rem:,} mil)", "🟢", f"{rem:,}"
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
# YAN MENÜ (SOL NAVİGASYON)
# -------------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=190)
    st.markdown("### 🏢 MOONSTAR TMS")
    st.caption(f"👤 Aktif: **{st.session_state.get('current_user')}**")
    
    st.markdown("---")
    menu = st.radio(
        "MODÜLLER",
        [
            "🚛 Araç Dosyaları & Filo",
            "👤 Şoför Dosyaları & Compliance",
            "💬 Ekip İçi Mesajlaşma (Chat)",
            "🔧 Bakım, Yağ & Fatura Girişi",
            "📁 Şirket Evrak Arşivi"
        ],
        index=0
    )
    st.markdown("---")
    st.markdown("**Hızlı İstatistikler**")
    st.write(f"🚛 **Truck:** {total_trucks}  |  🚚 **Trailer:** {total_trailers}")
    st.write(f"🚨 **Yağ Alarmı:** {len(crit_oil_df)} araç")
    st.write(f"⚠️ **Muayene Alarmı:** {len(crit_insp_df)} araç")
    
    st.markdown("---")
    if st.button("🚪 Güvenli Çıkış"):
        st.session_state["authenticated"] = False
        st.rerun()

# -------------------------------------------------------------
# ÜST ŞERİT (TOP BAR)
# -------------------------------------------------------------
st.markdown(f"""
<div class="main-header">
    <div>
        <div class="header-title">MOONSTAR EXPRESS LLC — FLEET & ASSET DOSSIER</div>
        <div class="header-sub">USDOT • Operations Live Console • Bensalem, PA</div>
    </div>
    <div class="user-badge">
        🟢 Oturum: <b>{st.session_state.get('current_user')}</b>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. BÖLÜM: ARAÇ DOSYALARI & FİLO YÖNETİMİ
# -------------------------------------------------------------
if menu == "🚛 Araç Dosyaları & Filo":
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Toplam Ekipman", f"{total_trucks} Çekici / {total_trailers} Dorse")
    k2.metric("Kritik Yağ Değişimi", f"{len(crit_oil_df)} Çekici", delta_color="inverse")
    k3.metric("Kritik / Yaklaşan Muayene", f"{len(crit_insp_df)} Araç", delta_color="inverse")
    k4.metric("Toplam Masraf", f"${all_spending:,.2f}")

    st.markdown("---")

    # ARAÇ DOSYASI (ASSET DOSSIER) SEÇİM ÇEKMECESİ
    st.markdown("#### 📂 Dijital Araç Dosyası İnceleme")
    all_unit_list = df_v["unit_number"].dropna().tolist()
    
    col_sel1, col_sel2 = st.columns([2, 3])
    with col_sel1:
        selected_unit = st.selectbox("İncelemek istediğiniz Çekici veya Dorseyi seçin:", ["Seçiniz..."] + all_unit_list)
    
    if selected_unit != "Seçiniz...":
        veh_row = df_v[df_v["unit_number"] == selected_unit].iloc[0]
        
        # KURUMSAL ARAÇ KÜNYESİ (DOSYA GÖRÜNÜMÜ)
        st.markdown(f"""
        <div class="profile-card">
            <div class="card-title">🚛 EKİPMAN DOSYASI: UNIT #{veh_row['unit_number']} ({veh_row['company']})</div>
        </div>
        """, unsafe_allow_html=True)
        
        d_c1, d_c2, d_c3 = st.columns(3)
        with d_c1:
            st.markdown("**Temel Künye & Kimlik**")
            st.write(f"• **Araç Türü:** `{veh_row['unit_type']}`")
            st.write(f"• **Model / Yıl:** {veh_row['make_model'] or '-'}")
            st.write(f"• **VIN (Şase):** `{veh_row['vin'] or '-'}`")
            st.write(f"• **Plaka:** `{veh_row['plate_number'] or '-'}`")
            st.write(f"• **Atanan Şoför:** **{veh_row['driver'] or 'Atama Yok'}**")
            
        with d_c2:
            st.markdown("**Mekanik & Yağ Durumu**")
            st.write(f"• **Güncel Kilometre / Mil:** {int(veh_row['current_mileage']):,} mi")
            st.write(f"• **Son Yağ Değişim Mili:** {int(veh_row['last_oil_mileage']):,} mi")
            st.write(f"• **Kalan Yağ Mili:** `{veh_row['kalan_yag_mili']}`")
            st.write(f"• **Yağ Alarmı:** {veh_row['yag_ikon']} {veh_row['yag_durumu']}")
            
        with d_c3:
            st.markdown("**Muayene & İzin Geçerlilikleri**")
            st.write(f"• **Registration:** {veh_row['plate_expiry'] or '-'}")
            st.write(f"• **Annual / DOT:** {veh_row['dot_inspection'] or '-'}")
            st.write(f"• **State / PA:** {veh_row['state_inspection'] or '-'}")
            st.write(f"• **Genel Muayene Durumu:** {veh_row['muayene_durum']}")
            st.write(f"• **Toplam Bakım Masrafı:** `{veh_row['total_spent']}`")

        # Bu araca ait geçmiş faturalar ve servis kayıtları
        sub_tab1, sub_tab2, sub_tab3 = st.tabs(["📜 Bu Aracın Servis Geçmişi", "📎 Yüklü Evraklar / Faturalar", "⚙️ Dosyayı Güncelle"])
        with sub_tab1:
            unit_logs = df_logs[df_logs["unit_number"] == selected_unit]
            if not unit_logs.empty:
                st.dataframe(unit_logs[["log_date", "log_type", "mileage", "cost", "notes"]], use_container_width=True, hide_index=True)
            else:
                st.info("Bu araç için kayıtlı servis geçmişi bulunmamaktadır.")

        with sub_tab2:
            st.markdown(f"**Unit #{selected_unit} ile İlgili Dosyalar**")
            found_docs = [f for f in os.listdir(INVOICE_DIR) if str(selected_unit) in f]
            if found_docs:
                for doc in found_docs:
                    st.write(f"📄 `{doc}`")
            else:
                st.caption("Bu araca özel arşivlenmiş bir dosya bulunamadı.")
            
            # Araca doğrudan evrak yükleme
            up_f = st.file_uploader(f"Unit #{selected_unit} için Evrak / Ruhsat Yükle", type=["pdf", "png", "jpg", "jpeg"], key=f"up_{selected_unit}")
            if up_f and st.button(f"Unit #{selected_unit} Dosyasına Kaydet"):
                save_n = f"Unit_{selected_unit}_{up_f.name}"
                with open(os.path.join(INVOICE_DIR, save_n), "wb") as f:
                    f.write(up_f.getbuffer())
                st.success(f"'{save_n}' başarıyla yüklendi!")
                st.rerun()

        with sub_tab3:
            st.markdown("**Araç Bilgilerini Düzenle**")
            with st.form(f"edit_veh_{selected_unit}"):
                eu_driver = st.text_input("Atanan Şoför", value=veh_row['driver'])
                eu_plate = st.text_input("Plaka", value=veh_row['plate_number'])
                eu_vin = st.text_input("VIN", value=veh_row['vin'])
                eu_mil = st.number_input("Güncel Mil", value=int(veh_row['current_mileage']))
                eu_oil = st.number_input("Son Yağ Mili", value=int(veh_row['last_oil_mileage']))
                if st.form_submit_button("Değişiklikleri Bu Araç İçin Kaydet"):
                    c = conn.cursor()
                    c.execute("""
                        UPDATE vehicles 
                        SET driver=?, plate_number=?, vin=?, current_mileage=?, last_oil_mileage=?
                        WHERE unit_number=?
                    """, (eu_driver, eu_plate, eu_vin, eu_mil, eu_oil, selected_unit))
                    conn.commit()
                    st.success("Araç dosyası güncellendi!")
                    st.rerun()

    st.markdown("---")
    st.markdown("#### 📋 Tüm Filo Tablosu (Hızlı Görünüm)")
    v_mode = st.radio("Tablo Modu:", ["🔹 Ferah Görünüm", "🔧 Yağ Durumu", "📋 Muayene & Evrak", "🔍 Tüm Detaylar"], horizontal=True)

    if v_mode == "🔹 Ferah Görünüm":
        cols_show = ["unit_number", "company", "unit_type", "driver", "make_model", "plate_number", "yag_ikon", "muayene_durum"]
    elif v_mode == "🔧 Yağ Durumu":
        cols_show = ["unit_number", "driver", "current_mileage", "last_oil_mileage", "yag_ikon", "yag_durumu", "kalan_yag_mili"]
    elif v_mode == "📋 Muayene & Evrak":
        cols_show = ["unit_number", "unit_type", "plate_number", "plate_expiry", "dot_inspection", "state_inspection", "muayene_durum"]
    else:
        cols_show = ["id", "company", "unit_type", "unit_number", "driver", "vin", "make_model", "plate_number", "plate_expiry", "dot_inspection", "current_mileage", "last_oil_mileage", "yag_ikon", "muayene_durum"]

    st.dataframe(df_v[cols_show], use_container_width=True, height=380, hide_index=True)

    with st.expander("➕ Yeni Araç Ekle / ❌ Araç Sil"):
        va, vb = st.columns(2)
        with va:
            with st.form("new_veh_f"):
                st.markdown("**Yeni Ekipman Ekle**")
                nc = st.selectbox("Firma", ["MOONSTAR", "LIONSTAR"])
                nt = st.selectbox("Tür", ["TRUCK", "TRAILER"])
                nu = st.text_input("Unit No")
                nd = st.text_input("Şoför")
                nv = st.text_input("VIN")
                np = st.text_input("Plaka")
                nm = st.text_input("Model / Yıl")
                n_reg = st.date_input("Registration Bitiş")
                n_dot = st.date_input("DOT Muayene")
                n_sta = st.date_input("State Muayene")
                if st.form_submit_button("Aracı Kaydet") and nu:
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO vehicles (company, unit_type, unit_number, driver, vin, plate_number, make_model, plate_expiry, dot_inspection, state_inspection)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (nc, nt, nu.strip(), nd.strip(), nv.strip(), np.strip(), nm.strip(), str(n_reg), str(n_dot), str(n_sta)))
                    conn.commit()
                    st.success(f"{nt} #{nu} eklendi!")
                    st.rerun()
        with vb:
            st.markdown("**Sistemden Araç Sil**")
            u_del = st.selectbox("Silinecek Unit:", ["Seçiniz..."] + all_unit_list)
            if st.button("🚨 Aracı Tamamen Sil") and u_del != "Seçiniz...":
                cur = conn.cursor()
                cur.execute("DELETE FROM vehicles WHERE unit_number = ?", (u_del,))
                conn.commit()
                st.warning(f"Unit #{u_del} silindi!")
                st.rerun()

# -------------------------------------------------------------
# 2. BÖLÜM: ŞOFÖR DOSYALARI & COMPLIANCE
# -------------------------------------------------------------
elif menu == "👤 Şoför Dosyaları & Compliance":
    st.markdown("#### 👤 Şoför Dosyaları, CDL & Medical Card Masası")

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

        driver_names = df_d["Name"].dropna().tolist()

        col_dr1, _ = st.columns([2, 3])
        with col_dr1:
            sel_dr = st.selectbox("İncelemek istediğiniz şoförün dosyasını seçin:", ["Seçiniz..."] + driver_names)

        if sel_dr != "Seçiniz...":
            dr_data = df_d[df_d["Name"] == sel_dr].iloc[0]

            st.markdown(f"""
            <div class="profile-card">
                <div class="card-title">👤 PERSONEL & COMPLIANCE DOSYASI: {dr_data['Name']}</div>
            </div>
            """, unsafe_allow_html=True)

            dc1, dc2, dc3 = st.columns(3)
            with dc1:
                st.markdown("**İletişim Bilgileri**")
                st.write(f"• **Telefon:** `{dr_data['Telephone']}`")
                st.write(f"• **E-Posta:** `{dr_data['E-mail']}`")
                st.write(f"• **Durum:** `{dr_data.get('Status', 'Active')}`")
            with dc2:
                st.markdown("**CDL Ehliyet Bilgileri**")
                st.write(f"• **CDL Lisans No:** `{dr_data['License Number']}`")
                st.write(f"• **Bitiş Tarihi:** `{dr_data['License Expiry']}`")
                st.write(f"• **Ehliyet Alarmı:** {dr_data['Ehliyet İkon']} {dr_data['Ehliyet Durumu']}")
            with dc3:
                st.markdown("**Medical Card Bilgileri**")
                st.write(f"• **Next Medical Tarihi:** `{dr_data['Next Medical']}`")
                st.write(f"• **Medical Alarmı:** {dr_data['Medical İkon']} {dr_data['Medical Durumu']}")

            # Şoför evrakları
            st.markdown(f"**{dr_data['Name']} - Yüklü Evraklar**")
            found_dr_docs = [f for f in os.listdir(INVOICE_DIR) if str(sel_dr).replace(" ", "_") in f]
            if found_dr_docs:
                for d_doc in found_dr_docs:
                    st.write(f"📄 `{d_doc}`")
            else:
                st.caption("Bu şoföre ait sistemde kayıtlı evrak bulunmuyor.")

            up_dr_f = st.file_uploader(f"{dr_data['Name']} için Evrak (CDL/Medical PDF) Yükle", type=["pdf", "png", "jpg", "jpeg"], key=f"dr_up_{sel_dr}")
            if up_dr_f and st.button(f"{dr_data['Name']} Dosyasına Ekle"):
                s_name = f"Driver_{sel_dr.replace(' ', '_')}_{up_dr_f.name}"
                with open(os.path.join(INVOICE_DIR, s_name), "wb") as f:
                    f.write(up_dr_f.getbuffer())
                st.success(f"'{s_name}' dosyaya eklendi!")
                st.rerun()

        st.markdown("---")
        st.markdown("#### 📋 Tüm Şoförlerin Compliance Listesi")
        disp_cols = ["Name", "Telephone", "E-mail", "License Number", "License Expiry", "Ehliyet İkon", "Ehliyet Durumu", "Next Medical", "Medical İkon", "Medical Durumu"]
        st.dataframe(df_d[disp_cols].rename(columns={"Name": "Şoför Adı", "License Number": "CDL No", "License Expiry": "CDL Bitiş", "Next Medical": "Medical Bitiş"}), use_container_width=True, hide_index=True)

    with st.expander("➕ Yeni Şoför Ekle / ❌ Şoför Sil"):
        da, db = st.columns(2)
        with da:
            with st.form("dr_new_form"):
                st.markdown("**Yeni Şoför Kaydı**")
                dn = st.text_input("Adı Soyadı")
                dp = st.text_input("Telefon")
                de = st.text_input("E-Posta")
                dl = st.text_input("CDL Numarası")
                dle = st.date_input("CDL Bitiş")
                dme = st.date_input("Medical Card Bitiş")
                if st.form_submit_button("Kaydet") and dn:
                    new_r = {"Status": "Active", "Name": dn.strip(), "Telephone": dp.strip(), "E-mail": de.strip(), "License Number": dl.strip(), "License Expiry": str(dle), "Next Medical": str(dme)}
                    df_d = pd.concat([df_d, pd.DataFrame([new_r])], ignore_index=True)
                    df_d.to_excel(DRIVERS_FILE, index=False)
                    st.success(f"{dn} eklendi!")
                    st.rerun()
        with db:
            st.markdown("**Şoför Sil**")
            d_to_del = st.selectbox("Silinecek Şoför:", ["Seçiniz..."] + driver_names)
            if st.button("🚨 Şoförü Sil") and d_to_del != "Seçiniz...":
                df_d = df_d[df_d["Name"] != d_to_del]
                df_d.to_excel(DRIVERS_FILE, index=False)
                st.warning(f"{d_to_del} silindi!")
                st.rerun()

# -------------------------------------------------------------
# 3. BÖLÜM: EKİP İÇİ CANLI MESAJLAŞMA (DISPATCH CHAT)
# -------------------------------------------------------------
elif menu == "💬 Ekip İçi Mesajlaşma (Chat)":
    st.markdown("#### 💬 Ekip İçi Canlı Operasyon & Not Defteri")
    with st.form("chat_form", clear_on_submit=True):
        cm1, cm2 = st.columns([5, 1])
        with cm1:
            msg = st.text_input("Mesajınızı yazın...", placeholder="Örn: Unit 63 için Laredo yükü alındı, yola çıkıyor.", label_visibility="collapsed")
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
            <div class="chat-bubble">
                <b>👤 {r['sender']}</b> <span style="color:#64748b; font-size:11px; margin-left:8px;">🕒 {r['timestamp']}</span>
                <div style="margin-top:4px; font-size:14px; color:#1e293b;">{r['message']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Henüz bir mesaj paylaşılmamış.")

# -------------------------------------------------------------
# 4. BÖLÜM: BAKIM, YAĞ & FATURA GİRİŞİ
# -------------------------------------------------------------
elif menu == "🔧 Bakım, Yağ & Fatura Girişi":
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
# 5. BÖLÜM: ŞİRKET EVRAK ARŞİVİ
# -------------------------------------------------------------
elif menu == "📁 Şirket Evrak Arşivi":
    st.markdown("#### 📁 Genel Evrak, Poliçe & Belge Kasası")
    all_files = os.listdir(INVOICE_DIR) if os.path.exists(INVOICE_DIR) else []
    if all_files:
        for f in all_files:
            st.write(f"📄 `{f}`")
    else:
        st.info("Arşivde yüklü belge bulunmuyor.")
