import glob
import os
import re
import shutil
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="MOONSTAR EXPRESS LLC - Enterprise TMS",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Kurumsal TMS & Ekip Chat Teması
st.markdown("""
<style>
    .top-header {
        background: linear-gradient(90deg, #0b1f3a 0%, #1a365d 60%, #0284c7 100%);
        padding: 12px 24px;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
        margin-bottom: 18px;
        box-shadow: 0 3px 8px rgba(0,0,0,0.15);
    }
    .top-title { font-size: 21px; font-weight: 800; letter-spacing: 0.5px; margin: 0; }
    .top-sub { font-size: 13px; color: #93c5fd; margin: 0; }
    .account-badge {
        background: rgba(255, 255, 255, 0.15);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        border: 1px solid rgba(255, 255, 255, 0.25);
    }
    .chat-bubble {
        background-color: #f8fafc;
        border-left: 4px solid #0284c7;
        padding: 10px 14px;
        border-radius: 4px;
        margin-bottom: 8px;
    }
    .chat-user { font-weight: 700; color: #0b1f3a; font-size: 13px; }
    .chat-time { color: #64748b; font-size: 11px; margin-left: 8px; }
    .chat-text { margin-top: 4px; font-size: 14px; color: #1e293b; }
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
            st.image("logo.jpg", width=240)
        st.markdown("### 🔒 MOONSTAR EXPRESS LLC — TMS PORTAL")
        st.caption("Fleet Management, Compliance & Internal Dispatch Communications")
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
    # Ekip Mesajlaşma Tablosu
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
        "NAVİGASYON",
        [
            "📊 Yönetici Kokpiti & Filo",
            "💬 Ekip İçi Mesajlaşma (Chat)",
            "👤 Şoförler & Evrak (Compliance)",
            "🔧 Bakım & Servis Kayıtları",
            "📁 Belgeler & Masraf Raporları"
        ],
        index=0
    )
    st.markdown("---")
    st.markdown("**Hızlı Filo Durumu**")
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
<div class="top-header">
    <div>
        <div class="top-title">MOONSTAR EXPRESS LLC — ENTERPRISE FLEET PORTAL</div>
        <div class="top-sub">PA55290 • Live Operations Console • Bensalem, PA</div>
    </div>
    <div class="account-badge">
        🟢 Canlı Oturum: <b>{st.session_state.get('current_user')}</b>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. BÖLÜM: YÖNETİCİ KOKPİTİ & FİLO (SADELEŞTİRİLMİŞ AKILLI TABLO)
# -------------------------------------------------------------
if menu == "📊 Yönetici Kokpiti & Filo":
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Toplam Ekipman", f"{total_trucks} Çekici / {total_trailers} Dorse")
    k2.metric("Yağ Değişimi Kritik", f"{len(crit_oil_df)} Çekici", delta_color="inverse")
    k3.metric("Muayenesi Yaklaşan / Dolan", f"{len(crit_insp_df)} Araç", delta_color="inverse")
    k4.metric("Toplam Bakım Masrafı", f"${all_spending:,.2f}")

    # SADECE ACİL OLANLARI GÖSTEREN YÖNETİCİ BİLGİLENDİRME PANELİ
    if len(crit_oil_df) > 0 or len(crit_insp_df) > 0:
        with st.expander("🚨 ACİL MÜDAHALE GEREKTİREN ARAÇLAR (Özet Bildirim)", expanded=True):
            alert_c1, alert_c2 = st.columns(2)
            with alert_c1:
                st.markdown("**🔴 / 🟡 Yağ Değişimi Yaklaşan / Dolan Çekiciler**")
                if not crit_oil_df.empty:
                    st.dataframe(
                        crit_oil_df[["unit_number", "driver", "current_mileage", "last_oil_mileage", "yag_ikon", "yag_durumu"]].rename(columns={
                            "unit_number": "Unit", "driver": "Şoför", "current_mileage": "Güncel Mil", "last_oil_mileage": "Son Yağ", "yag_durumu": "Durum"
                        }),
                        use_container_width=True, hide_index=True
                    )
                else:
                    st.success("Tüm çekicilerin yağ durumu güvenli!")
            with alert_c2:
                st.markdown("**⚠️ DOT / Registration Muayenesi Yaklaşanlar**")
                if not crit_insp_df.empty:
                    st.dataframe(
                        crit_insp_df[["unit_number", "unit_type", "plate_number", "dot_inspection", "muayene_durum"]].rename(columns={
                            "unit_number": "Unit", "unit_type": "Tür", "plate_number": "Plaka", "dot_inspection": "DOT Bitiş", "muayene_durum": "Durum"
                        }),
                        use_container_width=True, hide_index=True
                    )
                else:
                    st.success("Tüm muayeneler güncel!")

    st.markdown("---")
    st.markdown("#### 📋 Filo Ekipman Masası")

    # AKILLI GÖRÜNÜM MODLARI
    view_mode = st.radio(
        "Görünüm Modu Seçin:",
        ["🔹 Genel Bakış (Ferah)", "🔧 Yağ & Bakım Masası", "📋 Muayene & Evrak Masası", "🔍 Tüm Detaylar (Genişletilmiş)"],
        horizontal=True
    )

    f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
    with f_col1:
        f_comp = st.selectbox("Şirket:", ["HEPSİ", "MOONSTAR", "LIONSTAR"])
    with f_col2:
        f_type = st.selectbox("Tür:", ["HEPSİ", "TRUCK", "TRAILER"])
    with f_col3:
        f_search = st.text_input("Filtrele (Unit, Şoför, Plaka):")

    df_filtered = df_v.copy()
    if f_comp != "HEPSİ":
        df_filtered = df_filtered[df_filtered["company"] == f_comp]
    if f_type == "TRUCK":
        df_filtered = df_filtered[df_filtered["unit_type"] == "TRUCK"]
    elif f_type == "TRAILER":
        df_filtered = df_filtered[df_filtered["unit_type"] == "TRAILER"]
    if f_search:
        s = f_search.strip().lower()
        df_filtered = df_filtered[
            df_filtered["unit_number"].str.lower().str.contains(s) |
            df_filtered["driver"].str.lower().str.contains(s) |
            df_filtered["plate_number"].str.lower().str.contains(s)
        ]

    # SEÇİLEN GÖRÜNÜME GÖRE SÜTUNLARI AZALTIP SADELEŞTİRME
    if view_mode == "🔹 Genel Bakış (Ferah)":
        display_cols = ["id", "unit_number", "company", "unit_type", "driver", "make_model", "plate_number", "yag_ikon", "muayene_durum"]
    elif view_mode == "🔧 Yağ & Bakım Masası":
        display_cols = ["id", "unit_number", "driver", "current_mileage", "last_oil_mileage", "yag_ikon", "yag_durumu", "kalan_yag_mili"]
    elif view_mode == "📋 Muayene & Evrak Masası":
        display_cols = ["id", "unit_number", "unit_type", "plate_number", "plate_expiry", "dot_inspection", "state_inspection", "muayene_durum"]
    else:
        display_cols = [
            "id", "company", "unit_type", "unit_number", "driver", "vin", "make_model",
            "plate_number", "plate_expiry", "dot_inspection", "state_inspection",
            "current_mileage", "last_oil_mileage", "kalan_yag_mili", "yag_ikon", "muayene_durum"
        ]

    edited_df = st.data_editor(
        df_filtered[display_cols],
        column_config={
            "id": st.column_config.TextColumn("ID", disabled=True),
            "yag_ikon": st.column_config.TextColumn("Yağ", disabled=True),
            "muayene_durum": st.column_config.TextColumn("Muayene", disabled=True),
            "kalan_yag_mili": st.column_config.TextColumn("Kalan Yağ Mili", disabled=True),
            "company": st.column_config.SelectboxColumn("Firma", options=["MOONSTAR", "LIONSTAR"]),
            "unit_type": st.column_config.SelectboxColumn("Tür", options=["TRUCK", "TRAILER"]),
        },
        use_container_width=True,
        height=450,
        key="cockpit_table"
    )

    if st.button("💾 Değişiklikleri Kaydet", type="primary"):
        c = conn.cursor()
        for _, row in edited_df.iterrows():
            try:
                r_id = int(float(str(row["id"])))
                # Var olan sütunları dinamik güncelle
                updates = []
                params = []
                for col in ["company", "unit_type", "driver", "plate_number", "make_model", "current_mileage", "last_oil_mileage", "plate_expiry", "dot_inspection", "state_inspection"]:
                    if col in row:
                        updates.append(f"{col} = ?")
                        params.append(row[col])
                params.append(r_id)
                c.execute(f"UPDATE vehicles SET {', '.join(updates)} WHERE id = ?", tuple(params))
            except Exception:
                pass
        conn.commit()
        st.success("Tüm değişiklikler başarıyla işlendi!")
        st.rerun()

    st.markdown("---")
    with st.expander("➕ Yeni Çekici / Dorse Ekle  |  ❌ Araç Sil"):
        va, vb = st.columns(2)
        with va:
            st.markdown("**Yeni Araç Ekle**")
            with st.form("veh_add_form"):
                new_c = st.selectbox("Firma", ["MOONSTAR", "LIONSTAR"])
                new_t = st.selectbox("Araç Tipi", ["TRUCK", "TRAILER"])
                new_u = st.text_input("Unit No (Örn: 95)")
                new_dr = st.text_input("Şoför")
                new_vn = st.text_input("VIN")
                new_pl = st.text_input("Plaka")
                new_mo = st.text_input("Model / Yıl")
                new_rg = st.date_input("Registration Bitiş")
                new_dt = st.date_input("DOT Muayene")
                new_st = st.date_input("State Muayene")
                if st.form_submit_button("Kaydet"):
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
            st.markdown("**Araç Sil**")
            all_u = df_v["unit_number"].dropna().tolist()
            u_del = st.selectbox("Silinecek Araç:", ["Seçiniz..."] + all_u)
            if st.button("🚨 Tamamen Sil", type="secondary"):
                if u_del != "Seçiniz...":
                    cur = conn.cursor()
                    cur.execute("DELETE FROM vehicles WHERE unit_number = ?", (u_del,))
                    conn.commit()
                    st.warning(f"Unit #{u_del} silindi!")
                    st.rerun()

# -------------------------------------------------------------
# 2. BÖLÜM: EKİP İÇİ CANLI MESAJLAŞMA (DISPATCH CHAT)
# -------------------------------------------------------------
elif menu == "💬 Ekip İçi Mesajlaşma (Chat)":
    st.markdown("#### 💬 Moonstar Ekip İçi Operasyon & Dispatch Mesajlaşması")
    st.caption("Filo takibi, araç durumları ve günlük operasyonel notları buradan ekip arkadaşlarınızla paylaşabilirsiniz.")

    # Mesaj Gönderme Alanı
    with st.form("chat_form", clear_on_submit=True):
        col_m1, col_m2 = st.columns([5, 1])
        with col_m1:
            msg_input = st.text_input("Mesajınızı yazın...", placeholder="Örn: Unit 12'nin servisi tamamlandı, yola çıkmaya hazır.", label_visibility="collapsed")
        with col_m2:
            send_btn = st.form_submit_button("Gönder 🚀", use_container_width=True)
            
        if send_btn and msg_input.strip():
            cur = conn.cursor()
            now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
            cur.execute("""
                INSERT INTO team_chat (sender, message, timestamp)
                VALUES (?, ?, ?)
            """, (st.session_state.get("current_user"), msg_input.strip(), now_str))
            conn.commit()
            st.rerun()

    st.markdown("---")
    # Geçmiş Mesajlar
    df_chat = pd.read_sql_query("SELECT * FROM team_chat ORDER BY id DESC LIMIT 50", conn)
    if not df_chat.empty:
        for _, c_row in df_chat.iterrows():
            st.markdown(f"""
            <div class="chat-bubble">
                <span class="chat-user">👤 {c_row['sender']}</span>
                <span class="chat-time">🕒 {c_row['timestamp']}</span>
                <div class="chat-text">{c_row['message']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Henüz bir mesaj paylaşılmamış. İlk notu siz bırakın!")

# -------------------------------------------------------------
# 3. BÖLÜM: ŞOFÖRLER & COMPLIANCE
# -------------------------------------------------------------
elif menu == "👤 Şoförler & Evrak (Compliance)":
    st.markdown("#### 👤 Şoför İletişim, CDL & Medical Card Takibi")

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
        d1.metric("Kayıtlı Şoför", len(df_d))
        d2.metric("Aktif Şoför", len(df_d[df_d["Status"] == "Active"]))
        d3.metric("Kritik CDL", len(c_lic), delta_color="inverse")
        d4.metric("Kritik Medical", len(c_med), delta_color="inverse")

        if len(c_lic) > 0:
            st.error(f"🚨 **DİKKAT:** {len(c_lic)} şoförün CDL lisans süresi kritik seviyede!")
        if len(c_med) > 0:
            st.warning(f"⚠️ **DİKKAT:** {len(c_med)} şoförün Medical Card süresi yaklaşıyor veya doldu!")

        d_cols = [
            "Name", "Telephone", "E-mail", "License Number", 
            "License Expiry", "Ehliyet İkon", "Ehliyet Durumu", 
            "Next Medical", "Medical İkon", "Medical Durumu"
        ]

        st.dataframe(
            df_d[d_cols].rename(columns={
                "Name": "Şoför Adı Soyadı",
                "Telephone": "Telefon",
                "E-mail": "E-Posta",
                "License Number": "CDL No",
                "License Expiry": "CDL Bitiş",
                "Next Medical": "Medical Bitiş"
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
            st.markdown("**Yeni Şoför Bilgileri**")
            with st.form("dr_form"):
                dn = st.text_input("Ad Soyad")
                dp = st.text_input("Telefon")
                de = st.text_input("E-Posta")
                dl = st.text_input("CDL No")
                dle = st.date_input("CDL Bitiş Tarihi")
                dme = st.date_input("Medical Card Bitiş Tarihi")
                if st.form_submit_button("Şoförü Kaydet"):
                    if dn:
                        new_r = {
                            "Status": "Active", "Name": dn.strip(), "Telephone": dp.strip(),
                            "E-mail": de.strip(), "License Number": dl.strip(),
                            "License Expiry": str(dle), "Next Medical": str(dme)
                        }
                        df_d = pd.concat([df_d, pd.DataFrame([new_r])], ignore_index=True)
                        df_d.to_excel(DRIVERS_FILE, index=False)
                        st.success(f"{dn} eklendi!")
                        st.rerun()
                    else:
                        st.error("İsim giriniz.")

        with db:
            st.markdown("**Şoför Sil**")
            all_drs = df_d["Name"].dropna().tolist() if not df_d.empty else []
            d_del = st.selectbox("Silinecek Şoför:", ["Seçiniz..."] + all_drs)
            if st.button("🚨 Şoförü Sil", type="secondary"):
                if d_del != "Seçiniz...":
                    df_d = df_d[df_d["Name"] != d_del]
                    df_d.to_excel(DRIVERS_FILE, index=False)
                    st.warning(f"{d_del} silindi!")
                    st.rerun()

# -------------------------------------------------------------
# 4. BÖLÜM: BAKIM & SERVİS KAYITLARI
# -------------------------------------------------------------
elif menu == "🔧 Bakım & Servis Kayıtları":
    st.markdown("#### 🔧 Araç Bakım & Yağ Değişimi Girişi")

    if os.path.exists(SERVICE_LOGS_CSV):
        with st.expander("📜 Service logs.csv Geçmiş Kayıtları", expanded=False):
            df_s_csv = pd.read_csv(SERVICE_LOGS_CSV)
            st.dataframe(df_s_csv, use_container_width=True, height=250)

    st.markdown("##### ➕ Yeni Servis / Yağ Girişi")
    with st.form("service_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            all_units = df_v["unit_number"].tolist()
            sel_unit = st.selectbox("Unit Seçin", all_units if all_units else ["Yok"])
            log_date = st.date_input("Servis Tarihi")
        with col2:
            log_type = st.selectbox("İşlem Türü", ["Yağ Değişimi", "Lastik / Fren", "DOT Muayene", "Arıza / Onarım", "Periyodik Bakım", "Diğer"])
            curr_mil = st.number_input("İşlem Mili (Odometer)", min_value=0, step=1000)
        with col3:
            cost_val = st.number_input("Tutar ($)", min_value=0.0, step=50.0)
            inv_file = st.file_uploader("Fatura / Fiş (PDF/JPG)", type=["pdf", "png", "jpg", "jpeg"])
        
        notes_val = st.text_area("İşlem Notları")
        if st.form_submit_button("Servisi Kaydet"):
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
            st.success("Servis kaydı başarıyla oluşturuldu!")
            st.rerun()

# -------------------------------------------------------------
# 5. BÖLÜM: BELGELER & MASRAF RAPORLARI
# -------------------------------------------------------------
elif menu == "📁 Belgeler & Masraf Raporları":
    st.markdown("#### 📁 Fatura Geçmişi & Evrak Arşivi")
    if not df_logs.empty:
        st.dataframe(df_logs, use_container_width=True, hide_index=True)
    else:
        st.info("Kayıtlı harcama bulunmuyor.")

    st.markdown("---")
    with st.expander("📁 Belge & Fatura Yükle / Sil"):
        ba, bb = st.columns(2)
        with ba:
            st.markdown("**Yeni Belge / Poliçe Yükle**")
            up_doc = st.file_uploader("Dosya Seç", type=["pdf", "png", "jpg", "jpeg"], key="doc_up")
            doc_label = st.text_input("Belge Tanımı (Örn: Unit95_Sigorta)")
            if st.button("Arşive Kaydet"):
                if up_doc is not None:
                    ext = up_doc.name.split(".")[-1]
                    s_name = f"{doc_label.strip().replace(' ', '_')}.{ext}" if doc_label else up_doc.name
                    with open(os.path.join(INVOICE_DIR, s_name), "wb") as f:
                        f.write(up_doc.getbuffer())
                    st.success(f"'{s_name}' kaydedildi!")
                    st.rerun()
                else:
                    st.error("Dosya seçiniz.")

        with bb:
            st.markdown("**Belge Sil**")
            existing_files = os.listdir(INVOICE_DIR) if os.path.exists(INVOICE_DIR) else []
            f_del = st.selectbox("Silinecek Belge:", ["Seçiniz..."] + existing_files)
            if st.button("🚨 Belgeyi Sil", type="secondary"):
                if f_del != "Seçiniz...":
                    del_p = os.path.join(INVOICE_DIR, f_del)
                    if os.path.exists(del_p):
                        os.remove(del_p)
                    st.warning(f"'{f_del}' silindi!")
                    st.rerun()
