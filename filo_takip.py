import glob
import os
import shutil
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Moonstar Express LLC - Fleet Management",
    page_icon="⭐",
    layout="wide",
)

DB_FILE = "fleet_database.db"

INVOICE_DIR = "faturalar"
os.makedirs(INVOICE_DIR, exist_ok=True)

# --- KURUMSAL GİRİŞ KONTROLÜ ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.image("logo.jpg", width=220) if os.path.exists("logo.jpg") else None
    st.markdown("### 🔒 Moonstar Express LLC — Filo Yönetim Paneli")
    st.caption("Bu panele yalnızca yetkili kurumsal personeller erişebilir.")
    
    with st.form("login_form"):
        email = st.text_input("Kurumsal E-Posta", placeholder="ornek@moonstarpa...")
        password = st.text_input("Şifre", type="password")
        submit = st.form_submit_button("Giriş Yap")
        
        if submit:
            email_clean = email.strip().lower()
            # @moonstarpa kontrolü ve şifre doğrulaması:
            if "@moonstarpa" in email_clean and password == "Moonstar2026!":
                st.session_state["authenticated"] = True
                st.session_state["current_user"] = email_clean
                st.success("Giriş başarılı, yükleniyor...")
                st.rerun()
            else:
                st.error("Yetkisiz erişim! Geçersiz kurumsal e-posta veya şifre.")
    
    # Giriş yapılmadığı sürece aşağıdaki hiçbir kod çalışmaz ve hiçbir veri gösterilmez:
    st.stop()

# Sol menüye çıkış butonu
with st.sidebar:
    st.write(f"👤 Aktif Kullanıcı: **{st.session_state.get('current_user')}**")
    if st.button("Güvenli Çıkış"):
        st.session_state["authenticated"] = False
        st.rerun()
# -------------------------------
def get_connection():
  return sqlite3.connect(DB_FILE, check_same_thread=False)


def parse_updated_sheet(filepath):
  records = []
  try:
    xls = pd.ExcelFile(filepath)
    sheet_name = next(
        (
            s
            for s in xls.sheet_names
            if "drivers" in s.lower() or "unit" in s.lower()
        ),
        xls.sheet_names[0],
    )
    df = pd.read_excel(filepath, sheet_name=sheet_name)
    curr_company, curr_type = "MOONSTAR", "TRUCK"

    for _, row in df.iterrows():
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

      driver = (
          str(row.get("DRIVER", "")).strip()
          if pd.notna(row.get("DRIVER"))
          else ""
      )
      vin = str(row.get("VIN", "")).strip() if pd.notna(row.get("VIN")) else ""
      plate = (
          str(row.get("PLATE", "")).strip() if pd.notna(row.get("PLATE")) else ""
      )
      reg = (
          str(row.get("REGISTRATION", ""))
          .split(" ")[0]
          .replace("0000-00-00", "")
          if pd.notna(row.get("REGISTRATION"))
          else ""
      )
      make = (
          str(row.get("MAKE-MODEL-YEAR", "")).strip()
          if pd.notna(row.get("MAKE-MODEL-YEAR"))
          else ""
      )
      ann = (
          str(row.get("ANNUAL INSPECTION", ""))
          .split(" ")[0]
          .replace("0000-00-00", "")
          if pd.notna(row.get("ANNUAL INSPECTION"))
          else ""
      )
      pa_insp = (
          str(row.get("PA INSPECTION", ""))
          .split(" ")[0]
          .replace("0000-00-00", "")
          if pd.notna(row.get("PA INSPECTION"))
          else ""
      )
      insurance = (
          str(row.get("INSURANCE", "")).strip()
          if pd.notna(row.get("INSURANCE"))
          else ""
      )

      records.append({
          "company": curr_company,
          "type": curr_type,
          "unit": u_val,
          "driver": driver,
          "vin": vin,
          "plate": plate,
          "reg": reg,
          "make_model": make,
          "ann": ann,
          "pa_insp": pa_insp,
          "insurance": insurance,
      })
  except Exception as e:
    st.error(f"Excel okuma hatası: {e}")
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
        make_model TEXT,
        plate_number TEXT,
        plate_expiry TEXT,
        dot_inspection TEXT,
        state_inspection TEXT,
        current_mileage INTEGER DEFAULT 0,
        last_oil_mileage INTEGER DEFAULT 0,
        oil_interval INTEGER DEFAULT 25000,
        notes TEXT
    )
    """)
  c.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unit_number TEXT,
        log_date TEXT,
        service_type TEXT,
        mileage INTEGER,
        cost REAL,
        vendor TEXT,
        invoice_file TEXT,
        notes TEXT
    )
    """)
  conn.commit()

  c.execute("SELECT COUNT(*) FROM vehicles")
  if c.fetchone()[0] == 0:
    new_files = (
        glob.glob("*copy 2*.xlsx")
        + glob.glob("*tablo*.xlsx")
        + glob.glob("*drivers*.xlsx")
    )
    if new_files:
      for r in parse_updated_sheet(new_files[0]):
        c.execute(
            """
                INSERT OR REPLACE INTO vehicles 
                (company, unit_type, unit_number, driver, vin, make_model, plate_number, plate_expiry, dot_inspection, state_inspection, current_mileage, last_oil_mileage, oil_interval, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
            """,
            (
                r["company"],
                r["type"],
                r["unit"],
                r["driver"],
                r["vin"],
                r["make_model"],
                r["plate"],
                r["reg"],
                r["ann"],
                r["pa_insp"],
                25000 if r["type"] == "TRUCK" else 0,
                f"Ins: {r['insurance']}" if r["insurance"] else "",
            ),
        )

    if os.path.exists("Trucks.xlsx"):
      try:
        df_trucks = pd.read_excel("Trucks.xlsx")
        for _, row in df_trucks.iterrows():
          u_num = str(row.get("Number", "")).strip()
          if not u_num or u_num.lower() == "nan":
            continue
          c.execute("SELECT id FROM vehicles WHERE unit_number = ?", (u_num,))
          if not c.fetchone():
            make = (
                str(row.get("Type", ""))
                if str(row.get("Type", "")).lower() != "nan"
                else ""
            )
            plate = (
                str(row.get("Plate Number", ""))
                if str(row.get("Plate Number", "")).lower() != "nan"
                else ""
            )
            plate_exp = (
                str(row.get("Plate Expiry", ""))
                .split(" ")[0]
                .replace("0000-00-00", "")
            )
            dot_exp = (
                str(row.get("DOT Inspection Date", ""))
                .split(" ")[0]
                .replace("0000-00-00", "")
            )
            ann_exp = (
                str(row.get("Annual Inspection Date", ""))
                .split(" ")[0]
                .replace("0000-00-00", "")
            )
            notes = (
                str(row.get("Notes", ""))
                if str(row.get("Notes", "")).lower() != "nan"
                else ""
            )
            c.execute(
                """
                    INSERT INTO vehicles 
                    (company, unit_type, unit_number, driver, vin, make_model, plate_number, plate_expiry, dot_inspection, state_inspection, current_mileage, last_oil_mileage, oil_interval, notes)
                    VALUES ('MOONSTAR', 'TRUCK', ?, '', '', ?, ?, ?, ?, '', 0, 0, 25000, ?)
                """,
                (u_num, make, plate, plate_exp, dot_exp or ann_exp, notes),
            )
      except Exception:
        pass

    if os.path.exists("Trailers.xlsx"):
      try:
        df_trailers = pd.read_excel("Trailers.xlsx")
        for _, row in df_trailers.iterrows():
          u_num = str(row.get("Number", "")).strip()
          if not u_num or u_num.lower() == "nan":
            continue
          c.execute("SELECT id FROM vehicles WHERE unit_number = ?", (u_num,))
          if not c.fetchone():
            make = (
                str(row.get("Type", ""))
                if str(row.get("Type", "")).lower() != "nan"
                else ""
            )
            plate = (
                str(row.get("Plate Number", ""))
                if str(row.get("Plate Number", "")).lower() != "nan"
                else ""
            )
            plate_exp = (
                str(row.get("Plate Expiry", ""))
                .split(" ")[0]
                .replace("0000-00-00", "")
            )
            dot_exp = (
                str(row.get("DOT Inspection Date", ""))
                .split(" ")[0]
                .replace("0000-00-00", "")
            )
            ann_exp = (
                str(row.get("Annual Inspection Date", ""))
                .split(" ")[0]
                .replace("0000-00-00", "")
            )
            notes = (
                str(row.get("Notes", ""))
                if str(row.get("Notes", "")).lower() != "nan"
                else ""
            )
            c.execute(
                """
                    INSERT INTO vehicles 
                    (company, unit_type, unit_number, driver, vin, make_model, plate_number, plate_expiry, dot_inspection, state_inspection, current_mileage, last_oil_mileage, oil_interval, notes)
                    VALUES ('MOONSTAR', 'TRAILER', ?, '', '', ?, ?, ?, ?, '', 0, 0, 0, ?)
                """,
                (u_num, make, plate, plate_exp, dot_exp or ann_exp, notes),
            )
      except Exception:
        pass

    conn.commit()
  conn.close()


init_db()


def evaluate_status(row):
  today = datetime.now().date()
  status = "GEÇERLİ"

  for col in ["plate_expiry", "dot_inspection", "state_inspection"]:
    d_str = str(row[col])
    if d_str and d_str != "None" and d_str != "nan" and len(d_str) >= 10:
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
    c_m = int(row["current_mileage"] or 0)
    l_o = int(row["last_oil_mileage"] or 0)
    o_i = int(row["oil_interval"] or 0)
    if o_i > 0:
      miles_run = c_m - l_o
      if miles_run >= o_i:
        return "GECİKMİŞ ❌"
      elif (o_i - miles_run) <= 3000:
        status = "YAKLAŞIYOR ⚠️"
  except:
    pass

  return status


# ----------------- LOGO & BAŞLIK -----------------
logo_path = None
for p in ["logo.png", "logo.jpg", "logo.jpeg"]:
  if os.path.exists(p):
    logo_path = p
    break

head_col1, head_col2 = st.columns([1, 4])
with head_col1:
  if logo_path:
    st.image(logo_path, width=180)
  else:
    st.markdown("## ⭐")

with head_col2:
  st.markdown("""
        <h1 style="color: #0b1f3a; margin-bottom: 0px; font-weight: 800;">
            MOONSTAR EXPRESS LLC
        </h1>
        <p style="color: #0284c7; font-size: 16px; margin-top: 2px; font-weight: 600;">
            Fleet Maintenance, Inspections & Expense Management System
        </p>
    """, unsafe_allow_html=True)

conn = get_connection()
df_v = pd.read_sql_query("SELECT * FROM vehicles ORDER BY unit_number ASC", conn)
df_logs = pd.read_sql_query(
    "SELECT * FROM logs ORDER BY log_date DESC", conn
)

cost_totals = df_logs.groupby("unit_number")["cost"].sum().to_dict()
df_v["total_spent"] = (
    df_v["unit_number"]
    .map(cost_totals)
    .fillna(0.0)
    .apply(lambda x: f"${x:,.2f}")
)
df_v["durum"] = df_v.apply(evaluate_status, axis=1)
df_v["kalan_yag_mili"] = df_v.apply(
    lambda r: (
        "-"
        if r["unit_type"] == "TRAILER" or int(r["oil_interval"] or 0) == 0
        else str(
            int(r["oil_interval"] or 0)
            - (int(r["current_mileage"] or 0) - int(r["last_oil_mileage"] or 0))
        )
    ),
    axis=1,
)

# KPI KARTLARI
total_trucks = len(df_v[df_v["unit_type"] == "TRUCK"])
total_trailers = len(df_v[df_v["unit_type"] == "TRAILER"])
total_expired = len(df_v[df_v["durum"] == "GECİKMİŞ ❌"])
total_warning = len(df_v[df_v["durum"] == "YAKLAŞIYOR ⚠️"])
all_spending = df_logs["cost"].sum() if not df_logs.empty else 0.0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Aktif Truck", f"{total_trucks} Çekici")
k2.metric("Aktif Trailer", f"{total_trailers} Dorse")
k3.metric("Geciken Muayeneler", f"{total_expired}", delta_color="inverse")
k4.metric("Yaklaşan Muayeneler", f"{total_warning}", delta_color="off")
k5.metric("Toplam Masraf", f"${all_spending:,.2f}")

st.markdown("---")

tab_fleet, tab_add_log, tab_expenses = st.tabs([
    "📋 Canlı Düzenlenebilir Filo Listesi",
    "➕ Bakım, Yağ & Fatura Ekle",
    "💰 Masraf Raporları & Faturalar",
])

# 1. SEKME: CANLI DÜZENLENEBİLİR FİLO TABLOSU
with tab_fleet:
  st.markdown(
      "💡 *İpucu: Herhangi bir hücreye tıklayıp klavye ile değiştirebilirsiniz."
      " Değişiklikleri kaydetmek için alttaki butona basın.*"
  )

  f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
  with f_col1:
    company_filter = st.selectbox(
        "Firma:", ["HEPSİ", "MOONSTAR", "LIONSTAR"], key="f_comp"
    )
  with f_col2:
    type_filter = st.selectbox(
        "Tür:",
        ["HEPSİ", "TRUCK", "TRAILER", "ACİL / GECİKENLER"],
        key="f_type",
    )
  with f_col3:
    search_txt = st.text_input(
        "Hızlı Arama (Unit No, Şoför, Plaka veya Model):", key="f_search"
    )

  filtered_df = df_v.copy()
  if company_filter != "HEPSİ":
    filtered_df = filtered_df[filtered_df["company"] == company_filter]
  if type_filter in ["TRUCK", "TRAILER"]:
    filtered_df = filtered_df[filtered_df["unit_type"] == type_filter]
  elif type_filter == "ACİL / GECİKENLER":
    filtered_df = filtered_df[filtered_df["durum"] != "GEÇERLİ"]

  if search_txt:
    s = search_txt.lower()
    filtered_df = filtered_df[
        filtered_df["unit_number"].str.lower().str.contains(s, na=False)
        | filtered_df["driver"].str.lower().str.contains(s, na=False)
        | filtered_df["plate_number"].str.lower().str.contains(s, na=False)
        | filtered_df["make_model"].str.lower().str.contains(s, na=False)
    ]

  # Tipleri string formatına çevirerek JS hata riskini sıfırlıyoruz
  for c_name in [
      "id",
      "current_mileage",
      "last_oil_mileage",
      "company",
      "unit_type",
      "unit_number",
      "driver",
      "vin",
      "make_model",
      "plate_number",
      "plate_expiry",
      "dot_inspection",
      "state_inspection",
  ]:
    filtered_df[c_name] = filtered_df[c_name].astype(str).replace("nan", "")

  editable_cols = [
      "id",
      "company",
      "unit_type",
      "unit_number",
      "driver",
      "vin",
      "make_model",
      "plate_number",
      "plate_expiry",
      "dot_inspection",
      "state_inspection",
      "current_mileage",
      "last_oil_mileage",
      "kalan_yag_mili",
      "total_spent",
      "durum",
  ]

  column_config = {
      "id": st.column_config.TextColumn("ID", disabled=True),
      "unit_number": st.column_config.TextColumn("Unit No", disabled=True),
      "kalan_yag_mili": st.column_config.TextColumn(
          "Kalan Yağ Mili", disabled=True
      ),
      "total_spent": st.column_config.TextColumn(
          "Toplam Masraf", disabled=True
      ),
      "durum": st.column_config.TextColumn("Durum", disabled=True),
      "company": st.column_config.SelectboxColumn(
          "Firma", options=["MOONSTAR", "LIONSTAR"]
      ),
      "unit_type": st.column_config.SelectboxColumn(
          "Tür", options=["TRUCK", "TRAILER"]
      ),
      "driver": st.column_config.TextColumn("Şoför"),
      "vin": st.column_config.TextColumn("VIN (Şase)"),
      "make_model": st.column_config.TextColumn("Model / Yıl / Not"),
      "plate_number": st.column_config.TextColumn("Plaka"),
      "plate_expiry": st.column_config.TextColumn("Registration"),
      "dot_inspection": st.column_config.TextColumn("Annual Insp"),
      "state_inspection": st.column_config.TextColumn("State Insp"),
      "current_mileage": st.column_config.TextColumn("Mevcut Mil"),
      "last_oil_mileage": st.column_config.TextColumn("Son Yağ Mili"),
  }

  edited_data = st.data_editor(
      filtered_df[editable_cols],
      column_config=column_config,
      use_container_width=True,
      height=520,
      key="fleet_editor",
  )

  if st.button("💾 Değişiklikleri Veritabanına Kaydet", type="primary"):
    c = conn.cursor()
    for _, row in edited_data.iterrows():
      try:
        c_mil = int(float(str(row["current_mileage"]).replace(",", "") or 0))
        l_oil = int(float(str(row["last_oil_mileage"]).replace(",", "") or 0))
        r_id = int(float(str(row["id"])))
        c.execute(
            """
                    UPDATE vehicles 
                    SET company=?, unit_type=?, driver=?, vin=?, make_model=?, plate_number=?, 
                        plate_expiry=?, dot_inspection=?, state_inspection=?, current_mileage=?, last_oil_mileage=?
                    WHERE id=?
                """,
            (
                str(row["company"]),
                str(row["unit_type"]),
                str(row["driver"]),
                str(row["vin"]),
                str(row["make_model"]),
                str(row["plate_number"]),
                str(row["plate_expiry"]),
                str(row["dot_inspection"]),
                str(row["state_inspection"]),
                c_mil,
                l_oil,
                r_id,
            ),
        )
      except Exception as ex:
        pass
    conn.commit()
    st.success("✅ Tablodaki tüm değişiklikler veritabanına kaydedildi!")
    st.rerun()

# 2. SEKME: BAKIM & FATURA GİRİŞİ
with tab_add_log:
  st.subheader("Yeni Bakım, Onarım veya Fatura Girişi")
  with st.form("log_form", clear_on_submit=True):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
      selected_unit = st.selectbox(
          "Araç Seçin (Unit):", df_v["unit_number"].tolist()
      )
      log_date = st.date_input("İşlem Tarihi:", datetime.now())
      service_type = st.selectbox(
          "Yapılan İşlem:",
          [
              "Oil Change (Motor Yağı)",
              "Annual / DOT Inspection",
              "PA / State Inspection",
              "Fren / Brakes",
              "Lastik / Tires",
              "Motor & Şanzıman",
              "Süspansiyon / Hava Kaçağı",
              "Genel Bakım & Onarım",
              "Parça Alımı",
              "Diğer",
          ],
      )
    with col_b:
      log_mileage = st.number_input("İşlem Mili:", min_value=0, step=1000)
      log_cost = st.number_input(
          "Masraf Tutarı ($):", min_value=0.0, step=50.0, format="%.2f"
      )
      log_vendor = st.text_input(
          "Servis / Dükkan / Parçacı:", placeholder="Örn: TA Truck Stop, Speedco"
      )
    with col_c:
      log_notes = st.text_area(
          "Açıklama / Parça Notları:", placeholder="Örn: Yağ filtreleri değişti"
      )
      uploaded_file = st.file_uploader(
          "Fatura / Invoice Yükle (PDF / Resim):",
          type=["pdf", "png", "jpg", "jpeg"],
      )

    submitted = st.form_submit_button("💾 Masrafı & Faturayı Kaydet")
    if submitted:
      saved_filename = ""
      if uploaded_file is not None:
        ext = os.path.splitext(uploaded_file.name)[1]
        saved_filename = f"{selected_unit}_{log_date}_{datetime.now().strftime('%H%M%S')}{ext}"
        save_path = os.path.join(INVOICE_DIR, saved_filename)
        with open(save_path, "wb") as f:
          f.write(uploaded_file.getbuffer())

      c = conn.cursor()
      c.execute(
          """
                INSERT INTO logs (unit_number, log_date, service_type, mileage, cost, vendor, invoice_file, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
          (
              selected_unit,
              str(log_date),
              service_type,
              log_mileage,
              log_cost,
              log_vendor,
              saved_filename,
              log_notes,
          ),
      )

      if "Oil Change" in service_type:
        c.execute(
            """
                    UPDATE vehicles 
                    SET last_oil_mileage=?, current_mileage=MAX(current_mileage, ?) 
                    WHERE unit_number=?
                """,
            (log_mileage, log_mileage, selected_unit),
        )
      conn.commit()
      st.success(
          f"✅ Unit {selected_unit} için bakım kaydı ve faturası kaydedildi!"
      )
      st.rerun()

# 3. SEKME: MASRAFLAR & FATURALAR
with tab_expenses:
  st.subheader("Harcama Raporları & Arşivlenmiş Faturalar")
  if df_logs.empty:
    st.info("Henüz masraf veya fatura kaydı girilmedi.")
  else:
    c_unit, c_export = st.columns([2, 1])
    with c_unit:
      exp_unit = st.selectbox(
          "Araca Göre Filtrele:",
          ["HEPSİ"] + sorted(df_logs["unit_number"].unique().tolist()),
      )
    with c_export:
      csv_data = df_logs.to_csv(index=False).encode("utf-8")
      st.download_button(
          "📥 Masrafları İndir (CSV)",
          csv_data,
          "moonstar_masraflar.csv",
          "text/csv",
      )

    show_logs = (
        df_logs.copy()
        if exp_unit == "HEPSİ"
        else df_logs[df_logs["unit_number"] == exp_unit].copy()
    )
    st.markdown(
        f"**Filtrelenen Toplam Harcama:** `${show_logs['cost'].sum():,.2f}`"
    )

    st.dataframe(
        show_logs[[
            "unit_number",
            "log_date",
            "service_type",
            "mileage",
            "cost",
            "vendor",
            "invoice_file",
            "notes",
        ]].rename(
            columns={
                "unit_number": "Unit",
                "log_date": "Tarih",
                "service_type": "İşlem",
                "mileage": "Mil",
                "cost": "Tutar ($)",
                "vendor": "Dükkan",
                "invoice_file": "Fatura",
                "notes": "Not",
            }
        ),
        use_container_width=True,
    )

    st.markdown("### 📄 Ekli Faturayı İncele")
    inv_options = show_logs[
        show_logs["invoice_file"].str.len() > 0
    ]["invoice_file"].tolist()
    if inv_options:
      target_inv = st.selectbox("Görüntülenecek faturayı seçin:", inv_options)
      inv_path = os.path.join(INVOICE_DIR, target_inv)
      if os.path.exists(inv_path):
        with open(inv_path, "rb") as f:
          file_bytes = f.read()
          if target_inv.lower().endswith((".png", ".jpg", ".jpeg")):
            st.image(file_bytes, caption=target_inv, width=500)
          else:
            st.download_button(
                f"⬇️ {target_inv} Belgesini Aç / İndir",
                file_bytes,
                file_name=target_inv,)
conn.close()

