import glob
import os
import shutil
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Moonstar Express LLC – Fleet Management",
    page_icon="⭐",
    layout="wide",
)

DB_FILE = "fleet_database.db"
INVOICE_DIR = "faturalar"
DRIVERS_FILE = "Drivers.xlsx"
FLEET_EXCEL = "Başlıksız e-tablo (2) copy 2.xlsx"

os.makedirs(INVOICE_DIR, exist_ok=True)

# --- KURUMSAL GİRİŞ KONTROLÜ ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=220)
    st.markdown("### 🔒 Moonstar Express LLC – Filo Yönetim Paneli")
    st.caption("Bu panele yalnızca yetkili kurumsal personeller erişebilir.")

    with st.form("login_form"):
        email = st.text_input("Kurumsal E-Posta", placeholder="ornek@moonstarpa...")
        password = st.text_input("Şifre", type="password")
        submit = st.form_submit_button("Giriş Yap")

    if submit:
        email_clean = email.strip().lower()
        if "@moonstarpa" in email_clean and password == "Moonstar2026!":
            st.session_state["authenticated"] = True
            st.session_state["current_user"] = email_clean
            st.success("Giriş başarılı, yükleniyor...")
            st.rerun()
        else:
            st.error("Yetkisiz erişim! Geçersiz kurumsal e-posta veya şifre.")

    st.stop()

# Sol menüye çıkış butonu
with st.sidebar:
    st.write(f"👤 Aktif Kullanıcı: **{st.session_state.get('current_user')}**")
    if st.button("Güvenli Çıkış"):
        st.session_state["authenticated"] = False
        st.rerun()

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
            return f"Süresi Doldu ({abs(diff)} gün önce)", "🔴"
        elif diff <= 30:
            return f"Kritik! ({diff} gün kaldı)", "🟡"
        elif diff <= 60:
            return f"Yaklaşıyor ({diff} gün kaldı)", "🟠"
        else:
            return f"Geçerli ({diff} gün var)", "🟢"
    except Exception:
        return "Geçersiz Tarih", "⚪"

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

# LOGO & BAŞLIK
head_col1, head_col2 = st.columns([1, 4])
with head_col1:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=180)
    else:
        st.markdown("## ⭐")

with head_col2:
    st.markdown("""
        <h1 style="color: #0b1f3a; margin-bottom: 0px; font-weight: 800;">MOONSTAR EXPRESS LLC</h1>
        <p style="color: #0284c7; font-size: 16px; margin-top: 2px; font-weight: 600;">Fleet Maintenance, Driver Compliance & Expense Management System</p>
    """, unsafe_allow_html=True)

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

# KPI KARTLARI
total_trucks = len(df_v[df_v["unit_type"] == "TRUCK"])
total_trailers = len(df_v[df_v["unit_type"] == "TRAILER"])
total_expired = len(df_v[df_v["durum"] == "GECİKMİŞ ❌"])
total_warning = len(df_v[df_v["durum"] == "YAKLAŞIYOR ⚠️"])
all_spending = df_logs["cost"].sum() if not df_logs.empty else 0.0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Aktif Truck (Çekici)", f"{total_trucks} Çekici")
k2.metric("Aktif Trailer (Dorse)", f"{total_trailers} Dorse")
k3.metric("Geciken Muayeneler", total_expired, delta_color="inverse")
k4.metric("Yaklaşan Muayeneler", total_warning, delta_color="off")
k5.metric("Toplam Masraf", f"${all_spending:,.2f}")

st.markdown("---")

tab_fleet, tab_drivers, tab_add_log, tab_expenses = st.tabs([
    "📋 Canlı Filo & Araç Yönetimi",
    "👤 Şoförler & Evrak Takibi",
    "➕ Bakım, Yağ & Fatura Ekle",
    "💰 Masraf Raporları & Evrak Deposu",
])

# -------------------------------------------------------------
# 1. SEKME: CANLI FİLO & ARAÇ YÖNETİMİ (TRUCK & TRAILER)
# -------------------------------------------------------------
with tab_fleet:
    st.markdown("💡 *Hücrelere çift tıklayarak düzenleyebilir, en alttan yeni Çekici/Dorse ekleyip silebilirsiniz.*")
    
    f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
    with f_col1:
        comp_filter = st.selectbox("Firma Filtresi:", ["HEPSİ", "MOONSTAR", "LIONSTAR"], key="f_comp")
    with f_col2:
        type_filter = st.selectbox("Araç Türü Filtresi:", ["HEPSİ", "TRUCK", "TRAILER", "ACİL / GECİKENLER"], key="f_type")
    with f_col3:
        search_txt = st.text_input("Hızlı Arama (Unit, Şoför, Plaka, Model):", key="f_search")

    filtered_df = df_v.copy()
    if comp_filter != "HEPSİ":
        filtered_df = filtered_df[filtered_df["company"] == comp_filter]
    if type_filter == "TRUCK":
        filtered_df = filtered_df[filtered_df["unit_type"] == "TRUCK"]
    elif type_filter == "TRAILER":
        filtered_df = filtered_df[filtered_df["unit_type"] == "TRAILER"]
    elif type_filter == "ACİL / GECİKENLER":
        filtered_df = filtered_df[filtered_df["durum"].str.contains("❌|⚠️")]
    if search_txt:
        s = search_txt.strip().lower()
        filtered_df = filtered_df[
            filtered_df["unit_number"].str.lower().str.contains(s) |
            filtered_df["driver"].str.lower().str.contains(s) |
            filtered_df["plate_number"].str.lower().str.contains(s) |
            filtered_df["make_model"].str.lower().str.contains(s)
        ]

    editable_cols = [
        "id", "company", "unit_type", "unit_number", "driver", "vin", "make_model", 
        "plate_number", "plate_expiry", "dot_inspection", "state_inspection", 
        "current_mileage", "last_oil_mileage", "kalan_yag_mili", "total_spent", "durum"
    ]

    edited_data = st.data_editor(
        filtered_df[editable_cols],
        column_config={
            "id": st.column_config.TextColumn("ID", disabled=True),
            "total_spent": st.column_config.TextColumn("Toplam Masraf", disabled=True),
            "durum": st.column_config.TextColumn("Durum", disabled=True),
            "kalan_yag_mili": st.column_config.TextColumn("Kalan Yağ Mili", disabled=True),
            "company": st.column_config.SelectboxColumn("Firma", options=["MOONSTAR", "LIONSTAR"]),
            "unit_type": st.column_config.SelectboxColumn("Tür", options=["TRUCK", "TRAILER"]),
        },
        use_container_width=True,
        height=450,
        key="fleet_editor"
    )

    if st.button("💾 Değişiklikleri Veritabanına Kaydet", type="primary"):
        c = conn.cursor()
        for _, row in edited_data.iterrows():
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
        st.success("Tablodaki tüm değişiklikler veritabanına başarıyla işlendi!")
        st.rerun()

    st.markdown("---")
    # TRUCK & TRAILER EKLEME VE ÇIKARMA FORMU
    with st.expander("➕ Yeni Çekici / Dorse Ekle  |  ❌ Araç Sil"):
        v_col1, v_col2 = st.columns(2)
        with v_col1:
            st.markdown("##### ➕ Yeni Araç (Truck / Trailer) Ekle")
            with st.form("add_vehicle_modal"):
                v_comp = st.selectbox("Firma", ["MOONSTAR", "LIONSTAR"])
                v_type = st.selectbox("Araç Türü", ["TRUCK", "TRAILER"])
                v_unit = st.text_input("Unit Numarası (Örn: 95 veya 5312)")
                v_driver = st.text_input("Atanan Şoför")
                v_vin = st.text_input("VIN / Şase Numarası")
                v_plate = st.text_input("Plaka No")
                v_model = st.text_input("Marka / Model / Yıl")
                v_reg = st.date_input("Registration Bitiş")
                v_dot = st.date_input("Annual / DOT Muayene")
                v_state = st.date_input("State / PA Muayene")
                
                if st.form_submit_button("Aracı Kaydet"):
                    if v_unit:
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO vehicles (company, unit_type, unit_number, driver, vin, plate_number, make_model, plate_expiry, dot_inspection, state_inspection)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (v_comp, v_type, v_unit.strip(), v_driver.strip(), v_vin.strip(), v_plate.strip(), v_model.strip(), str(v_reg), str(v_dot), str(v_state)))
                        conn.commit()
                        st.success(f"{v_type} #{v_unit} sisteme eklendi!")
                        st.rerun()
                    else:
                        st.error("Unit Numarası zorunludur!")

        with v_col2:
            st.markdown("##### ❌ Sistemden Araç (Truck / Trailer) Sil")
            all_v_units = df_v["unit_number"].dropna().tolist()
            unit_to_del = st.selectbox("Silinecek Aracı Seçin:", ["Seçiniz..."] + all_v_units)
            if st.button("🚨 Seçili Aracı Tamamen Sil", type="secondary"):
                if unit_to_del != "Seçiniz...":
                    cur = conn.cursor()
                    cur.execute("DELETE FROM vehicles WHERE unit_number = ?", (unit_to_del,))
                    conn.commit()
                    st.warning(f"Unit #{unit_to_del} veritabanından silindi!")
                    st.rerun()

# -------------------------------------------------------------
# 2. SEKME: ŞOFÖRLER, CDL & MEDICAL TAKİBİ + EKLE/ÇIKAR
# -------------------------------------------------------------
with tab_drivers:
    st.markdown("### 👤 Şoför Bilgileri, CDL & Medical Card Takibi")
    
    if os.path.exists(DRIVERS_FILE):
        try:
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

            crit_lic = df_d[df_d["Ehliyet İkon"].isin(["🔴", "🟡"])]
            crit_med = df_d[df_d["Medical İkon"].isin(["🔴", "🟡"])]

            dc1, dc2, dc3, dc4 = st.columns(4)
            dc1.metric("Toplam Kayıtlı Şoför", len(df_d))
            dc2.metric("Aktif Şoförler", len(df_d[df_d["Status"] == "Active"]))
            dc3.metric("Kritik / Biten CDL", len(crit_lic), delta_color="inverse")
            dc4.metric("Kritik / Biten Medical", len(crit_med), delta_color="inverse")

            if len(crit_lic) > 0:
                st.error(f"⚠️ **DİKKAT:** {len(crit_lic)} şoförün ehliyet (CDL) süresi dolmuş veya 30 günden az kalmış!")
            if len(crit_med) > 0:
                st.warning(f"⚠️ **DİKKAT:** {len(crit_med)} şoförün Medical Card süresi dolmuş veya 30 günden az kalmış!")

            disp_d = [
                "Name", "Telephone", "E-mail", "License Number", 
                "License Expiry", "Ehliyet İkon", "Ehliyet Durumu", 
                "Next Medical", "Medical İkon", "Medical Durumu"
            ]

            st.dataframe(
                df_d[disp_d].rename(columns={
                    "Name": "Şoför Adı",
                    "Telephone": "Telefon",
                    "E-mail": "E-Posta",
                    "License Number": "Ehliyet (CDL) No",
                    "License Expiry": "CDL Bitiş Tarihi",
                    "Next Medical": "Medical Card Bitiş"
                }),
                use_container_width=True,
                hide_index=True
            )
        except Exception as ex:
            st.error(f"Drivers.xlsx okunurken hata oluştu: {ex}")
    else:
        st.info("Drivers.xlsx dosyası bulunamadı. Lütfen GitHub deposuna yükleyin.")
        df_d = pd.DataFrame(columns=["Name", "Status", "Telephone", "E-mail", "License Number", "License Expiry", "Next Medical"])

    st.markdown("---")
    # ŞOFÖR EKLEME VE ÇIKARMA FORMU
    with st.expander("👤 Yeni Şoför Ekle  |  ❌ Şoför Çıkar"):
        d_sub1, d_sub2 = st.columns(2)
        with d_sub1:
            st.markdown("##### ➕ Yeni Şoför Kaydet")
            with st.form("new_driver_form"):
                dr_name = st.text_input("Şoför Adı Soyadı")
                dr_phone = st.text_input("Telefon")
                dr_mail = st.text_input("E-Posta")
                dr_lic = st.text_input("CDL Lisans No")
                dr_lic_exp = st.date_input("CDL Bitiş Tarihi")
                dr_med_exp = st.date_input("Medical Card Bitiş Tarihi")

                if st.form_submit_button("Şoförü Sisteme Ekle"):
                    if dr_name:
                        new_row = {
                            "Status": "Active",
                            "Name": dr_name.strip(),
                            "Telephone": dr_phone.strip(),
                            "E-mail": dr_mail.strip(),
                            "License Number": dr_lic.strip(),
                            "License Expiry": str(dr_lic_exp),
                            "Next Medical": str(dr_med_exp)
                        }
                        df_d = pd.concat([df_d, pd.DataFrame([new_row])], ignore_index=True)
                        df_d.to_excel(DRIVERS_FILE, index=False)
                        st.success(f"{dr_name} başarıyla eklendi!")
                        st.rerun()
                    else:
                        st.error("Şoför ismi zorunludur!")

        with d_sub2:
            st.markdown("##### ❌ Şoförü Sistemden Çıkar")
            all_drivers = df_d["Name"].dropna().tolist() if not df_d.empty else []
            dr_to_del = st.selectbox("Silinecek Şoförü Seçin:", ["Seçiniz..."] + all_drivers)
            if st.button("🚨 Şoförü Sil", type="secondary"):
                if dr_to_del != "Seçiniz...":
                    df_d = df_d[df_d["Name"] != dr_to_del]
                    df_d.to_excel(DRIVERS_FILE, index=False)
                    st.warning(f"{dr_to_del} sistemden silindi!")
                    st.rerun()

# -------------------------------------------------------------
# 3. SEKME: BAKIM & FATURA GİRİŞİ
# -------------------------------------------------------------
with tab_add_log:
    st.subheader("Yeni Bakım, Onarım veya Fatura Girişi")
    with st.form("log_form", clear_on_submit=True):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            all_units = df_v["unit_number"].tolist()
            sel_unit = st.selectbox("Unit Seçin", all_units if all_units else ["Yok"])
            log_date = st.date_input("İşlem Tarihi")
        with col_b:
            log_type = st.selectbox("İşlem Türü", ["Yağ Değişimi", "Lastik / Fren", "Periyodik Bakım", "DOT Muayene", "Arıza / Onarım", "Diğer"])
            curr_mil = st.number_input("İşlem Mili", min_value=0, step=1000)
        with col_c:
            cost_val = st.number_input("Tutar ($)", min_value=0.0, step=50.0)
            inv_file = st.file_uploader("Fatura / Belge Yükle (PDF / Resim)", type=["pdf", "png", "jpg", "jpeg"])
        
        notes_val = st.text_area("Açıklama / Notlar")
        log_submit = st.form_submit_button("Kaydı Tamamla")

    if log_submit:
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
        st.success("Kayıt başarıyla eklendi!")
        st.rerun()

# -------------------------------------------------------------
# 4. SEKME: MASRAF RAPORLARI & BELGE YÖNETİCİSİ (EKLE/SİL)
# -------------------------------------------------------------
with tab_expenses:
    st.subheader("Masraf Raporları & Kayıtlı Belgeler")
    if not df_logs.empty:
        st.dataframe(df_logs, use_container_width=True, hide_index=True)
    else:
        st.info("Henüz harcama veya bakım kaydı girilmemiş.")

    st.markdown("---")
    # BELGE / DOSYA YÜKLEME VE SİLME FORMU
    with st.expander("📁 Belge & Dosya Deposu (Ruhsat, Sigorta, Fatura Yükle / Sil)"):
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            st.markdown("##### 📤 Yeni Belge / Fatura Yükle")
            doc_file = st.file_uploader("Belge Seç (PDF, JPG, PNG)", type=["pdf", "png", "jpg", "jpeg"], key="gen_doc")
            doc_custom = st.text_input("Belge Açıklaması / Adı (Örn: Unit_95_Sigorta_2026)")
            if st.button("Belgeyi Arşive Kaydet"):
                if doc_file is not None:
                    ext = doc_file.name.split(".")[-1]
                    s_name = f"{doc_custom.strip().replace(' ', '_')}.{ext}" if doc_custom else doc_file.name
                    with open(os.path.join(INVOICE_DIR, s_name), "wb") as f:
                        f.write(doc_file.getbuffer())
                    st.success(f"'{s_name}' başarıyla arşive yüklendi!")
                    st.rerun()
                else:
                    st.error("Lütfen bir dosya seçin.")

        with b_col2:
            st.markdown("##### 🗑️ Arşivden Belge Sil")
            all_docs = os.listdir(INVOICE_DIR) if os.path.exists(INVOICE_DIR) else []
            doc_to_del = st.selectbox("Silinecek Dosyayı Seçin:", ["Seçiniz..."] + all_docs)
            if st.button("🚨 Dosyayı Tamamen Sil", type="secondary"):
                if doc_to_del != "Seçiniz...":
                    del_p = os.path.join(INVOICE_DIR, doc_to_del)
                    if os.path.exists(del_p):
                        os.remove(del_p)
                    st.warning(f"'{doc_to_del}' arşivden silindi!")
                    st.rerun()
