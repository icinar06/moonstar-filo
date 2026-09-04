import glob
import os
import shutil
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="MOONSTAR EXPRESS LLC - TMS Portal",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Kurumsal TMS Teması & Özel CSS
st.markdown("""
<style>
    /* Üst Bar Stili */
    .top-header {
        background: linear-gradient(90deg, #0b1f3a 0%, #1a365d 60%, #0284c7 100%);
        padding: 12px 24px;
        border-radius: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    }
    .top-title {
        font-size: 22px;
        font-weight: 800;
        letter-spacing: 1px;
        margin: 0;
    }
    .top-sub {
        font-size: 13px;
        color: #93c5fd;
        margin: 0;
    }
    .account-badge {
        background: rgba(255, 255, 255, 0.15);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    /* Durum Rozetleri */
    .badge-open { background-color: #fef08a; color: #854d0e; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .badge-route { background-color: #bbf7d0; color: #166534; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .badge-alert { background-color: #fecaca; color: #991b1b; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

DB_FILE = "fleet_database.db"
INVOICE_DIR = "faturalar"
DRIVERS_FILE = "Drivers.xlsx"
FLEET_EXCEL = "Başlıksız e-tablo (2) copy 2.xlsx"

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
        st.caption("Corporate Operations, Fleet & Driver Compliance Management")
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
        return "Tarih Yok / Eksik", "⚪"
    try:
        dt = datetime.strptime(str(date_str).strip()[:10], "%Y-%m-%d").date()
        today = datetime.now().date()
        diff = (dt - today).days
        if diff < 0:
            return f"Süresi Doldu ({abs(diff)}g)", "🔴"
        elif diff <= 30:
            return f"Kritik ({diff}g)", "🟡"
        elif diff <= 60:
            return f"Yaklaşıyor ({diff}g)", "🟠"
        else:
            return f"Geçerli ({diff}g)", "🟢"
    except Exception:
        return "Geçersiz", "⚪"

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

        driver = str(row.get("DRIVER", "")).strip() if pd.notna(row.get("DRIVER")) else ""
        vin = str(row.get("VIN", "")).strip() if pd.notna(row.get("VIN")) else ""
        plate = str(row.get("PLATE", "")).strip() if pd.notna(row.get("PLATE")) else ""
        reg = str(row.get("REGISTRATION", "")).split(" ")[0].replace("0000-00-00", "") if pd.notna(row.get("REGISTRATION")) else ""
        model = str(row.get("MAKE-MODEL-YEAR", "")).strip() if pd.notna(row.get("MAKE-MODEL-YEAR")) else ""
        ann = str(row.get("ANNUAL INSPECTION", "")).split(" ")[0].replace("0000-00-00", "") if pd.notna(row.get("ANNUAL INSPECTION")) else ""
        pa_insp = str(row.get("PA INSPECTION", "")).split(" ")[0].replace("0000-00-00", "") if pd.notna(row.get("PA INSPECTION")) else ""

        records.append({
            "company": curr_company,
            "unit_type": curr_type,
            "unit_number": u_val,
            "driver": driver,
            "vin": vin,
            "plate_number": plate,
            "make_model": model,
            "plate_expiry": reg,
            "dot_inspection": ann,
            "state_inspection": pa_insp,
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
    try:
        c_m = int(row.get("current_mileage") or 0)
        l_o = int(row.get("last_oil_mileage") or 0)
        o_i = int(row.get("oil_interval") or 0)
        if o_i > 0:
            miles_run = c_m - l_o
            if miles_run >= o_i:
                return "GECİKMİŞ ❌"
            elif (o_i - miles_run) <= 3000:
                status = "YAKLAŞIYOR ⚠️"
    except:
        pass
    return status

conn = get_connection()
df_v = pd.read_sql_query("SELECT * FROM vehicles ORDER BY unit_number ASC", conn)
df_logs = pd.read_sql_query("SELECT * FROM logs ORDER BY log_date DESC", conn)

cost_totals = df_logs.groupby("unit_number")["cost"].sum().to_dict() if not df_logs.empty else {}
df_v["total_spent"] = df_v["unit_number"].map(cost_totals).fillna(0.0).apply(lambda x: f"${x:,.2f}")
df_v["durum"] = df_v.apply(evaluate_status, axis=1)
df_v["kalan_yag_mili"] = df_v.apply(
    lambda r: "-" if r["unit_type"] == "TRAILER" or int(r["oil_interval"] or 0) == 0 else str(int(r["oil_interval"] or 0) - (int(r["current_mileage"] or 0) - int(r["last_oil_mileage"] or 0))),
    axis=1
)

total_trucks = len(df_v[df_v["unit_type"] == "TRUCK"])
total_trailers = len(df_v[df_v["unit_type"] == "TRAILER"])
total_expired = len(df_v[df_v["durum"] == "GECİKMİŞ ❌"])
total_warning = len(df_v[df_v["durum"] == "YAKLAŞIYOR ⚠️"])
all_spending = df_logs["cost"].sum() if not df_logs.empty else 0.0

# -------------------------------------------------------------
# YAN MENÜ (PROFESYONEL TMS SOL PANEL)
# -------------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=190)
    st.markdown("### 🏢 MOONSTAR TMS")
    st.caption(f"Aktif Kullanıcı: **{st.session_state.get('current_user')}**")
    
    st.markdown("---")
    menu = st.radio(
        "NAVİGASYON",
        [
            "📊 Dispatch & Filo Yönetimi",
            "👤 Şoförler & Compliance (CDL/Medical)",
            "🔧 Bakım & Servis Kayıtları",
            "🧾 Muhasebe, Faturalar & Evrak Arşivi"
        ],
        index=0
    )
    st.markdown("---")
    st.markdown("**Hızlı İstatistikler**")
    st.write(f"🚛 **Trucks:** {total_trucks}")
    st.write(f"🚚 **Trailers:** {total_trailers}")
    st.write(f"🔴 **Geciken:** {total_expired}")
    st.write(f"🟡 **Yaklaşan:** {total_warning}")
    st.write(f"💵 **Harcama:** ${all_spending:,.2f}")
    
    st.markdown("---")
    if st.button("🚪 Güvenli Çıkış Yap"):
        st.session_state["authenticated"] = False
        st.rerun()

# -------------------------------------------------------------
# ÜST BİLGİ ŞERİDİ (TOP HEADER BAR)
# -------------------------------------------------------------
st.markdown(f"""
<div class="top-header">
    <div>
        <div class="top-title">MOONSTAR EXPRESS LLC — FLEET & DISPATCH MANAGEMENT</div>
        <div class="top-sub">PA55290 • Operations Live Console • Bensalem, PA</div>
    </div>
    <div class="account-badge">
        🟢 Account Status: Active | <b>{st.session_state.get('current_user')}</b>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. SAYFA: DISPATCH & FİLO YÖNETİMİ
# -------------------------------------------------------------
if menu == "📊 Dispatch & Filo Yönetimi":
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Aktif Çekici (Truck)", f"{total_trucks}")
    k2.metric("Aktif Dorse (Trailer)", f"{total_trailers}")
    k3.metric("Kritik / Geciken Muayene", total_expired, delta_color="inverse")
    k4.metric("Yaklaşan Muayene (30g)", total_warning, delta_color="off")
    k5.metric("Toplam Filo Masrafı", f"${all_spending:,.2f}")

    st.markdown("#### 📋 Canlı Araç & Ekipman Takip Listesi")

    c_filter, t_filter, s_box = st.columns([1, 1, 2])
    with c_filter:
        f_comp = st.selectbox("Şirket:", ["HEPSİ", "MOONSTAR", "LIONSTAR"])
    with t_filter:
        f_type = st.selectbox("Ekipman Türü:", ["HEPSİ", "TRUCK", "TRAILER", "ACİL / GECİKENLER"])
    with s_box:
        f_search = st.text_input("Arama (Unit, Şoför, Plaka, VIN):")

    df_show = df_v.copy()
    if f_comp != "HEPSİ":
        df_show = df_show[df_show["company"] == f_comp]
    if f_type == "TRUCK":
        df_show = df_show[df_show["unit_type"] == "TRUCK"]
    elif f_type == "TRAILER":
        df_show = df_show[df_show["unit_type"] == "TRAILER"]
    elif f_type == "ACİL / GECİKENLER":
        df_show = df_show[df_show["durum"].str.contains("❌|⚠️")]
    if f_search:
        s = f_search.strip().lower()
        df_show = df_show[
            df_show["unit_number"].str.lower().str.contains(s) |
            df_show["driver"].str.lower().str.contains(s) |
            df_show["plate_number"].str.lower().str.contains(s) |
            df_show["vin"].str.lower().str.contains(s)
        ]

    cols = [
        "id", "company", "unit_type", "unit_number", "driver", "vin", "make_model",
        "plate_number", "plate_expiry", "dot_inspection", "state_inspection",
        "current_mileage", "last_oil_mileage", "kalan_yag_mili", "total_spent", "durum"
    ]

    edited_df = st.data_editor(
        df_show[cols],
        column_config={
            "id": st.column_config.TextColumn("ID", disabled=True),
            "total_spent": st.column_config.TextColumn("Toplam Masraf", disabled=True),
            "durum": st.column_config.TextColumn("Durum", disabled=True),
            "kalan_yag_mili": st.column_config.TextColumn("Kalan Yağ Mili", disabled=True),
            "company": st.column_config.SelectboxColumn("Firma", options=["MOONSTAR", "LIONSTAR"]),
            "unit_type": st.column_config.SelectboxColumn("Tür", options=["TRUCK", "TRAILER"]),
        },
        use_container_width=True,
        height=480,
        key="live_tms_grid"
    )

    if st.button("💾 Değişiklikleri Veritabanına Kaydet", type="primary"):
        c = conn.cursor()
        for _, row in edited_df.iterrows():
            try:
                c_mil = int(float(str(row["current_mileage"]).replace(",", "") or 0))
                l_oil = int(float(str(row["last_oil_mileage"]).replace(",", "") or 0))
                r_id = int(float(str(row["id"])))
                c.execute("""
                    UPDATE vehicles 
                    SET company=?, unit_type=?, driver=?, vin=?, make_model=?, plate_number=?, 
                        plate_expiry=?, dot_inspection=?, state_inspection=?, current_mileage=?, last_oil_mileage=?
                    WHERE id=?
                """, (
                    str(row["company"]), str(row["unit_type"]), str(row["driver"]), str(row["vin"]),
                    str(row["make_model"]), str(row["plate_number"]), str(row["plate_expiry"]),
                    str(row["dot_inspection"]), str(row["state_inspection"]), c_mil, l_oil, r_id
                ))
            except Exception:
                pass
        conn.commit()
        st.success("Tüm değişiklikler kaydedildi!")
        st.rerun()

    st.markdown("---")
    with st.expander("➕ Sisteme Yeni Çekici / Dorse Ekle  |  ❌ Araç Sil"):
        va, vb = st.columns(2)
        with va:
            st.markdown("**Yeni Araç Ekle (Truck veya Trailer)**")
            with st.form("add_veh"):
                new_c = st.selectbox("Firma", ["MOONSTAR", "LIONSTAR"])
                new_t = st.selectbox("Araç Tipi", ["TRUCK", "TRAILER"])
                new_u = st.text_input("Unit No (Örn: 95)")
                new_dr = st.text_input("Atanan Şoför")
                new_vn = st.text_input("VIN")
                new_pl = st.text_input("Plaka")
                new_mo = st.text_input("Model / Yıl")
                new_rg = st.date_input("Registration Bitiş")
                new_dt = st.date_input("DOT / Annual Muayene")
                new_st = st.date_input("State / PA Muayene")
                if st.form_submit_button("Aracı Kaydet"):
                    if new_u:
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO vehicles (company, unit_type, unit_number, driver, vin, plate_number, make_model, plate_expiry, dot_inspection, state_inspection)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (new_c, new_t, new_u.strip(), new_dr.strip(), new_vn.strip(), new_pl.strip(), new_mo.strip(), str(new_rg), str(new_dt), str(new_st)))
                        conn.commit()
                        st.success(f"{new_t} #{new_u} eklendi!")
                        st.rerun()
                    else:
                        st.error("Unit No girilmelidir.")

        with vb:
            st.markdown("**Sistemden Araç Sil**")
            all_u = df_v["unit_number"].dropna().tolist()
            u_del = st.selectbox("Silinecek Araç:", ["Seçiniz..."] + all_u)
            if st.button("🚨 Aracı Tamamen Sil", type="secondary"):
                if u_del != "Seçiniz...":
                    cur = conn.cursor()
                    cur.execute("DELETE FROM vehicles WHERE unit_number = ?", (u_del,))
                    conn.commit()
                    st.warning(f"Unit #{u_del} silindi!")
                    st.rerun()

# -------------------------------------------------------------
# 2. SAYFA: ŞOFÖRLER & COMPLIANCE
# -------------------------------------------------------------
elif menu == "👤 Şoförler & Compliance (CDL/Medical)":
    st.markdown("#### 👤 Şoförler, CDL Lisans & Medical Card Uyarı Masası")

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
        d1.metric("Kayıtlı Şoför Sayısı", len(df_d))
        d2.metric("Aktif Şoförler", len(df_d[df_d["Status"] == "Active"]))
        d3.metric("Kritik / Biten CDL", len(c_lic), delta_color="inverse")
        d4.metric("Kritik / Biten Medical", len(c_med), delta_color="inverse")

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
                "License Expiry": "CDL Bitiş Tarihi",
                "Next Medical": "Medical Card Bitiş"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Drivers.xlsx dosyası bulunamadı.")
        df_d = pd.DataFrame()

    st.markdown("---")
    with st.expander("👤 Yeni Şoför Ekle  |  ❌ Şoför Çıkar"):
        da, db = st.columns(2)
        with da:
            st.markdown("**Yeni Şoför Bilgilerini Girin**")
            with st.form("dr_add_form"):
                dn = st.text_input("Adı Soyadı")
                dp = st.text_input("Telefon")
                de = st.text_input("E-Posta")
                dl = st.text_input("CDL Numarası")
                dle = st.date_input("CDL Bitiş Tarihi")
                dme = st.date_input("Medical Card Bitiş Tarihi")
                if st.form_submit_button("Şoförü Kaydet"):
                    if dn:
                        new_r = {
                            "Status": "Active",
                            "Name": dn.strip(),
                            "Telephone": dp.strip(),
                            "E-mail": de.strip(),
                            "License Number": dl.strip(),
                            "License Expiry": str(dle),
                            "Next Medical": str(dme)
                        }
                        df_d = pd.concat([df_d, pd.DataFrame([new_r])], ignore_index=True)
                        df_d.to_excel(DRIVERS_FILE, index=False)
                        st.success(f"{dn} sisteme kaydedildi!")
                        st.rerun()
                    else:
                        st.error("Şoför adı zorunludur.")

        with db:
            st.markdown("**Şoför Kaydını Sil**")
            all_drs = df_d["Name"].dropna().tolist() if not df_d.empty else []
            d_del = st.selectbox("Silinecek Şoför:", ["Seçiniz..."] + all_drs)
            if st.button("🚨 Şoförü Sistemden Sil", type="secondary"):
                if d_del != "Seçiniz...":
                    df_d = df_d[df_d["Name"] != d_del]
                    df_d.to_excel(DRIVERS_FILE, index=False)
                    st.warning(f"{d_del} silindi!")
                    st.rerun()

# -------------------------------------------------------------
# 3. SAYFA: BAKIM & SERVİS KAYITLARI
# -------------------------------------------------------------
elif menu == "🔧 Bakım & Servis Kayıtları":
    st.markdown("#### 🔧 Araç Bakım, Yağ Değişimi & Servis Girişi")
    with st.form("log_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            all_units = df_v["unit_number"].tolist()
            sel_unit = st.selectbox("Unit Seçin", all_units if all_units else ["Yok"])
            log_date = st.date_input("Servis Tarihi")
        with col2:
            log_type = st.selectbox("İşlem Türü", ["Yağ Değişimi", "Lastik / Fren", "DOT Muayene", "Arıza / Onarım", "Periyodik Bakım", "Diğer"])
            curr_mil = st.number_input("İşlem Mili (Odometer)", min_value=0, step=1000)
        with col3:
            cost_val = st.number_input("İşlem Tutarı ($)", min_value=0.0, step=50.0)
            inv_file = st.file_uploader("Fatura / Servis Fişi (PDF/JPG)", type=["pdf", "png", "jpg", "jpeg"])
        
        notes_val = st.text_area("Yapılan İşlemler / Parça Açıklamaları")
        if st.form_submit_button("Servis Kaydını Tamamla"):
            saved_file = ""
            if inv_file is not None:
                saved_file = f"{sel_unit}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{inv_file.name}"
                with open(os.path.join(INVOICE_DIR, saved_file), "wb") as f:
                    f.write(inv_file.getbuffer())
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO logs (unit_number, log_date, log_type, mileage, cost, invoice_filename, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (sel_unit, str(log_date), log_type, curr_mil, cost_val, saved_file, notes_val))
            if log_type == "Yağ Değişimi" and curr_mil > 0:
                cur.execute("UPDATE vehicles SET last_oil_mileage = ?, current_mileage = MAX(current_mileage, ?) WHERE unit_number = ?", (curr_mil, curr_mil, sel_unit))
            elif curr_mil > 0:
                cur.execute("UPDATE vehicles SET current_mileage = MAX(current_mileage, ?) WHERE unit_number = ?", (curr_mil, sel_unit))
            conn.commit()
            st.success("Servis ve bakım kaydı başarıyla oluşturuldu!")
            st.rerun()

# -------------------------------------------------------------
# 4. SAYFA: MUHASEBE & EVRAK ARŞİVİ
# -------------------------------------------------------------
elif menu == "🧾 Muhasebe, Faturalar & Evrak Arşivi":
    st.markdown("#### 🧾 Fatura Geçmişi, Masraf Dökümleri & Evrak Deposu")
    if not df_logs.empty:
        st.dataframe(df_logs, use_container_width=True, hide_index=True)
    else:
        st.info("Kayıtlı harcama bulunmuyor.")

    st.markdown("---")
    with st.expander("📁 Belge & Dosya Deposu (Ruhsat, Sigorta, Fatura Yükle / Sil)"):
        ba, bb = st.columns(2)
        with ba:
            st.markdown("**Arşive Yeni Dosya / Belge Yükle**")
            up_doc = st.file_uploader("Belge Seç (PDF, JPG, PNG)", type=["pdf", "png", "jpg", "jpeg"], key="doc_up")
            doc_label = st.text_input("Açıklama / Belge Adı (Örn: Unit_95_Sigorta_2026)")
            if st.button("Belgeyi Kaydet"):
                if up_doc is not None:
                    ext = up_doc.name.split(".")[-1]
                    s_name = f"{doc_label.strip().replace(' ', '_')}.{ext}" if doc_label else up_doc.name
                    with open(os.path.join(INVOICE_DIR, s_name), "wb") as f:
                        f.write(up_doc.getbuffer())
                    st.success(f"'{s_name}' yüklendi!")
                    st.rerun()
                else:
                    st.error("Lütfen bir dosya seçin.")

        with bb:
            st.markdown("**Arşivdeki Belgeler & Silme**")
            existing_files = os.listdir(INVOICE_DIR) if os.path.exists(INVOICE_DIR) else []
            f_del = st.selectbox("Silinecek Dosyayı Seçin:", ["Seçiniz..."] + existing_files)
            if st.button("🗑️ Dosyayı Sil", type="secondary"):
                if f_del != "Seçiniz...":
                    del_p = os.path.join(INVOICE_DIR, f_del)
                    if os.path.exists(del_p):
                        os.remove(del_p)
                    st.warning(f"'{f_del}' silindi!")
                    st.rerun()
