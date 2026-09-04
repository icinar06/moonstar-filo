import glob
import os
import re
import shutil
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="MOONSTAR EXPRESS LLC — Enterprise Portal",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# SCHNEIDER & SWIFT KURUMSAL TASARIM SİSTEMİ
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #f4f5f7 !important;
        color: #1e293b;
    }
    
    /* Üst Kurumsal Header */
    .corp-header {
        background: #ffffff;
        border-bottom: 3px solid #ea580c;
        padding: 16px 28px;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 24px;
    }
    .corp-brand {
        font-family: 'Montserrat', sans-serif;
        font-size: 26px;
        font-weight: 900;
        color: #0b1f3a;
        letter-spacing: -0.5px;
    }
    .corp-tag {
        color: #ea580c;
        font-weight: 800;
    }
    
    /* Schneider Tarzı Modüler Kartlar */
    .schneider-card {
        background: #ffffff;
        border-radius: 8px;
        padding: 24px 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        margin-bottom: 16px;
        border-top: 4px solid #0b1f3a;
        transition: transform 0.15s ease;
    }
    .schneider-card-accent {
        border-top: 4px solid #ea580c !important;
    }
    .card-kicker {
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #ea580c;
        margin-bottom: 4px;
    }
    .card-title-lg {
        font-family: 'Montserrat', sans-serif;
        font-size: 20px;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 8px;
    }
    
    /* Durum Rozetleri */
    .badge-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 700;
    }
    .badge-crit { background: #fee2e2; color: #991b1b; }
    .badge-warn { background: #fef3c7; color: #92400e; }
    .badge-good { background: #dcfce7; color: #166534; }
    
    /* Form Butonları */
    .stButton>button {
        background-color: #0b1f3a !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
        border: none !important;
        padding: 8px 20px !important;
    }
    .stButton>button:hover {
        background-color: #ea580c !important;
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
        st.markdown("<br><br>", unsafe_allow_html=True)
        if os.path.exists("logo.jpg"):
            st.image("logo.jpg", width=220)
        st.markdown("### 🔒 MOONSTAR ENTERPRISE PORTAL")
        st.caption("Fleet Management, Compliance & Operations Control")
        with st.form("login_box"):
            email = st.text_input("Kurumsal E-Posta", placeholder="ismail@moonstarpa.com")
            pwd = st.text_input("Şifre", type="password")
            if st.form_submit_button("Sisteme Giriş Yap"):
                if "@moonstarpa" in email.strip().lower() and pwd == "Moonstar2026!":
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = email.strip().lower()
                    st.rerun()
                else:
                    st.error("Hatalı e-posta veya şifre!")
    st.stop()

# ---------------------------------------------
def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def check_driver_expiry(date_str):
    if not date_str or str(date_str).strip() in ["0000-00-00", "nan", "None", "-", ""]:
        return "Tarih Yok", "⚪"
    try:
        dt = datetime.strptime(str(date_str).strip()[:10], "%Y-%m-%d").date()
        diff = (dt - datetime.now().date()).days
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
df_logs = pd.read_sql_query("SELECT * FROM logs ORDER BY log_date DESC", conn)

def evaluate_insp(row):
    today = datetime.now().date()
    for col in ["plate_expiry", "dot_inspection", "state_inspection"]:
        d_str = str(row.get(col, "")).strip()
        if d_str and d_str not in ["nan", "None", "", "-"]:
            try:
                diff = (datetime.strptime(d_str[:10], "%Y-%m-%d").date() - today).days
                if diff < 0:
                    return "GECİKMİŞ ❌"
                elif diff <= 30:
                    return "YAKLAŞIYOR ⚠️"
            except:
                pass
    return "GEÇERLİ"

df_v["muayene_durum"] = df_v.apply(evaluate_insp, axis=1)
oil_res = df_v.apply(check_oil_status, axis=1)
df_v["yag_durumu"] = [r[0] for r in oil_res]
df_v["yag_ikon"] = [r[1] for r in oil_res]
df_v["kalan_yag_mili"] = [r[2] for r in oil_res]

total_trucks = len(df_v[df_v["unit_type"] == "TRUCK"])
total_trailers = len(df_v[df_v["unit_type"] == "TRAILER"])
crit_oil = df_v[df_v["yag_ikon"].isin(["🔴", "🟡"])]
crit_insp = df_v[df_v["muayene_durum"].str.contains("❌|⚠️")]

# -------------------------------------------------------------
# SCHNEIDER / SWIFT TARZI YAN PANEL
# -------------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=180)
    st.markdown("### MOONSTAR **TMS**")
    st.caption(f"👤 {st.session_state.get('current_user')}")
    
    st.markdown("---")
    menu = st.radio(
        "MENÜ",
        [
            "🏢 Operasyon Merkezi",
            "🚛 Çekici & Dorse Masası",
            "👤 Şoförler & Compliance",
            "💬 Ekip İçi Chat",
            "🔧 Bakım & Fatura Girişi"
        ]
    )
    st.markdown("---")
    if st.button("🚪 Çıkış Yap"):
        st.session_state["authenticated"] = False
        st.rerun()

# -------------------------------------------------------------
# ÜST KURUMSAL ŞERİT
# -------------------------------------------------------------
st.markdown(f"""
<div class="corp-header">
    <div>
        <span class="corp-brand">MOONSTAR <span class="corp-tag">EXPRESS</span></span>
        <div style="font-size:12px; color:#64748b; font-weight:600;">FLEET MANAGEMENT & TRANSPORTATION SOLUTIONS • BENSALEM, PA</div>
    </div>
    <div style="text-align:right;">
        <span style="font-size:13px; font-weight:700; color:#0b1f3a;">DOT Active</span> | 
        <span style="font-size:12px; color:#ea580c; font-weight:700;">{st.session_state.get('current_user')}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. MODÜL: OPERASYON MERKEZİ (SCHNEIDER KARTLARI)
# -------------------------------------------------------------
if menu == "🏢 Operasyon Merkezi":
    st.markdown("#### 📌 Filo Durum Özeti")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="schneider-card">
            <div class="card-kicker">Kayıtlı Ekipman</div>
            <div class="card-title-lg">{total_trucks} Çekici</div>
            <div style="color:#64748b; font-size:13px;">{total_trailers} Aktif Dorse</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""
        <div class="schneider-card schneider-card-accent">
            <div class="card-kicker">Yağ Değişimi Alarmı</div>
            <div class="card-title-lg" style="color:#b91c1c;">{len(crit_oil)} Çekici</div>
            <div style="color:#64748b; font-size:13px;">Acil / 3,000 mil altı</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="schneider-card">
            <div class="card-kicker">Muayene / DOT Alarmı</div>
            <div class="card-title-lg" style="color:#b45309;">{len(crit_insp)} Araç</div>
            <div style="color:#64748b; font-size:13px;">Günü geçen veya 30 gün altı</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="schneider-card">
            <div class="card-kicker">Compliance Güvenlik</div>
            <div class="card-title-lg" style="color:#15803d;">%98.4</div>
            <div style="color:#64748b; font-size:13px;">Yola elverişlilik oranı</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🚨 Müdahale Gerektiren Kritik Araçlar")
    if len(crit_oil) > 0:
        st.dataframe(
            crit_oil[["unit_number", "driver", "current_mileage", "last_oil_mileage", "yag_ikon", "yag_durumu"]].rename(columns={
                "unit_number": "Unit", "driver": "Şoför", "current_mileage": "Güncel Mil", "last_oil_mileage": "Son Yağ Mili", "yag_ikon": "İkon", "yag_durumu": "Yağ Durumu"
            }),
            use_container_width=True, hide_index=True
        )
    else:
        st.success("Tüm araçların bakımları güncel!")

# -------------------------------------------------------------
# 2. MODÜL: ÇEKİCİ & DORSE MASASI
# -------------------------------------------------------------
elif menu == "🚛 Çekici & Dorse Masası":
    st.markdown("#### 🚛 Ekipman & Filo Listesi")

    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        s_comp = st.selectbox("Şirket:", ["HEPSİ", "MOONSTAR", "LIONSTAR"])
    with f2:
        s_type = st.selectbox("Tür:", ["HEPSİ", "TRUCK", "TRAILER", "🚨 Sadece Yağ Alarmları"])
    with f3:
        s_srch = st.text_input("Unit, Şoför veya Plaka ile Ara:")

    df_show = df_v.copy()
    if s_comp != "HEPSİ":
        df_show = df_show[df_show["company"] == s_comp]
    if s_type == "TRUCK":
        df_show = df_show[df_show["unit_type"] == "TRUCK"]
    elif s_type == "TRAILER":
        df_show = df_show[df_show["unit_type"] == "TRAILER"]
    elif s_type == "🚨 Sadece Yağ Alarmları":
        df_show = df_show[df_show["yag_ikon"].isin(["🔴", "🟡"])]

    if s_srch:
        s = s_srch.strip().lower()
        df_show = df_show[
            df_show["unit_number"].str.lower().str.contains(s) |
            df_show["driver"].str.lower().str.contains(s) |
            df_show["plate_number"].str.lower().str.contains(s)
        ]

    st.dataframe(
        df_show[[
            "unit_number", "company", "unit_type", "driver", "make_model",
            "current_mileage", "last_oil_mileage", "yag_ikon", "yag_durumu",
            "plate_number", "plate_expiry", "dot_inspection", "muayene_durum"
        ]].rename(columns={
            "unit_number": "Unit", "company": "Şirket", "unit_type": "Tür", "driver": "Şoför",
            "make_model": "Model", "current_mileage": "Güncel Mil", "last_oil_mileage": "Son Yağ",
            "yag_ikon": "Yağ", "yag_durumu": "Yağ Detay", "plate_number": "Plaka",
            "plate_expiry": "Reg Bitiş", "dot_inspection": "DOT Insp", "muayene_durum": "Muayene"
        }),
        use_container_width=True, height=450, hide_index=True
    )

    with st.expander("➕ Sisteme Yeni Çekici / Dorse Ekle & Sil"):
        ea, eb = st.columns(2)
        with ea:
            st.markdown("**Yeni Araç Ekle**")
            with st.form("veh_add_box"):
                nc = st.selectbox("Firma", ["MOONSTAR", "LIONSTAR"])
                nt = st.selectbox("Tür", ["TRUCK", "TRAILER"])
                nu = st.text_input("Unit No")
                nd = st.text_input("Şoför")
                nv = st.text_input("VIN")
                np = st.text_input("Plaka")
                nm = st.text_input("Model / Yıl")
                n_reg = st.date_input("Registration Bitiş")
                n_dot = st.date_input("Annual / DOT")
                n_sta = st.date_input("PA / State Muayene")
                if st.form_submit_button("Aracı Kaydet") and nu:
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO vehicles (company, unit_type, unit_number, driver, vin, plate_number, make_model, plate_expiry, dot_inspection, state_inspection)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (nc, nt, nu.strip(), nd.strip(), nv.strip(), np.strip(), nm.strip(), str(n_reg), str(n_dot), str(n_sta)))
                    conn.commit()
                    st.success(f"{nt} #{nu} kaydedildi!")
                    st.rerun()

        with eb:
            st.markdown("**Sistemden Araç Sil**")
            all_units = df_v["unit_number"].dropna().tolist()
            u_del = st.selectbox("Silinecek Araç:", ["Seçiniz..."] + all_units)
            if st.button("🚨 Aracı Tamamen Sil") and u_del != "Seçiniz...":
                cur = conn.cursor()
                cur.execute("DELETE FROM vehicles WHERE unit_number = ?", (u_del,))
                conn.commit()
                st.warning(f"Unit #{u_del} silindi!")
                st.rerun()

# -------------------------------------------------------------
# 3. MODÜL: ŞOFÖRLER & COMPLIANCE
# -------------------------------------------------------------
elif menu == "👤 Şoförler & Compliance":
    st.markdown("#### 👤 Şoför Masası (CDL & Medical Compliance)")

    if os.path.exists(DRIVERS_FILE):
        df_d = pd.read_excel(DRIVERS_FILE)
        df_d = df_d[df_d["Name"].notna()].copy()
        df_d["License Expiry"] = df_d["License Expiry"].astype(str).str.strip()
        df_d["Next Medical"] = df_d["Next Medical"].astype(str).str.strip()
        df_d["Telephone"] = df_d["Telephone"].fillna("-").astype(str).str.strip()
        df_d["License Number"] = df_d["License Number"].fillna("-").astype(str).str.strip()

        df_d["Ehliyet Durumu"] = df_d["License Expiry"].apply(lambda d: check_driver_expiry(d)[0])
        df_d["Ehliyet İkon"] = df_d["License Expiry"].apply(lambda d: check_driver_expiry(d)[1])
        df_d["Medical Durumu"] = df_d["Next Medical"].apply(lambda d: check_driver_expiry(d)[0])
        df_d["Medical İkon"] = df_d["Next Medical"].apply(lambda d: check_driver_expiry(d)[1])

        st.dataframe(
            df_d[[
                "Name", "Telephone", "License Number", "License Expiry", 
                "Ehliyet İkon", "Ehliyet Durumu", "Next Medical", "Medical İkon", "Medical Durumu"
            ]].rename(columns={
                "Name": "Şoför", "Telephone": "Telefon", "License Number": "CDL No",
                "License Expiry": "CDL Bitiş", "Ehliyet İkon": "CDL", "Next Medical": "Med Bitiş", "Medical İkon": "Med"
            }),
            use_container_width=True, hide_index=True
        )

# -------------------------------------------------------------
# 4. MODÜL: EKİP İÇİ CHAT
# -------------------------------------------------------------
elif menu == "💬 Ekip İçi Chat":
    st.markdown("#### 💬 Ekip İçi Operasyon Chat")
    with st.form("chat_b", clear_on_submit=True):
        col_m1, col_m2 = st.columns([5, 1])
        with col_m1:
            msg = st.text_input("Mesajınızı yazın...", placeholder="Örn: Unit 12 yola çıktı.")
        with col_m2:
            if st.form_submit_button("Gönder 🚀") and msg.strip():
                cur = conn.cursor()
                now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
                cur.execute("INSERT INTO team_chat (sender, message, timestamp) VALUES (?, ?, ?)", (st.session_state.get("current_user"), msg.strip(), now_str))
                conn.commit()
                st.rerun()

    df_chat = pd.read_sql_query("SELECT * FROM team_chat ORDER BY id DESC LIMIT 40", conn)
    for _, r in df_chat.iterrows():
        st.markdown(f"""
        <div style="background:#ffffff; border-left:4px solid #ea580c; padding:10px 14px; border-radius:6px; margin-bottom:8px; border:1px solid #e2e8f0;">
            <b style="color:#0b1f3a;">👤 {r['sender']}</b> <span style="font-size:11px; color:#64748b; margin-left:8px;">🕒 {r['timestamp']}</span>
            <div style="margin-top:4px; font-size:14px;">{r['message']}</div>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# 5. MODÜL: BAKIM & FATURA GİRİŞİ
# -------------------------------------------------------------
elif menu == "🔧 Bakım & Fatura Girişi":
    st.markdown("#### 🔧 Yeni Bakım & Servis Kaydı")
    with st.form("serv_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            sel_u = st.selectbox("Unit Seçin", df_v["unit_number"].tolist())
            l_date = st.date_input("Servis Tarihi")
        with c2:
            l_type = st.selectbox("İşlem Türü", ["Yağ Değişimi", "Lastik / Fren", "DOT Muayene", "Arıza / Onarım", "Periyodik Bakım", "Diğer"])
            l_mil = st.number_input("İşlem Mili", min_value=0, step=1000)
        with c3:
            l_cost = st.number_input("Tutar ($)", min_value=0.0, step=50.0)
            inv_file = st.file_uploader("Fatura / Belge", type=["pdf", "png", "jpg", "jpeg"])
        
        notes = st.text_area("Açıklama")
        if st.form_submit_button("Servisi Kaydet"):
            s_file = ""
            if inv_file:
                s_file = f"Unit_{sel_u}_{inv_file.name}"
                with open(os.path.join(INVOICE_DIR, s_file), "wb") as f:
                    f.write(inv_file.getbuffer())
            cur = conn.cursor()
            cur.execute("INSERT INTO logs (unit_number, log_date, log_type, mileage, cost, invoice_filename, notes) VALUES (?, ?, ?, ?, ?, ?, ?)", (sel_u, str(l_date), l_type, l_mil, l_cost, s_file, notes))
            if l_type == "Yağ Değişimi" and l_mil > 0:
                cur.execute("UPDATE vehicles SET last_oil_mileage = ?, current_mileage = MAX(current_mileage, ?) WHERE unit_number = ?", (l_mil, l_mil, sel_u))
            elif l_mil > 0:
                cur.execute("UPDATE vehicles SET current_mileage = MAX(current_mileage, ?) WHERE unit_number = ?", (l_mil, sel_u))
            conn.commit()
            st.success("Servis kaydı başarıyla eklendi!")
            st.rerun()
