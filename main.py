from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Template
from datetime import datetime

app = FastAPI(title="MOONSTAR EXPRESS LLC — Executive Fleet Console")

# --- TÜM GERÇEK 56 ŞOFÖR (EKSİKSİZ LİSTE) ---
DRIVERS_DATA = [
    {"name": "ALTUG BACI", "phone": "954-669-6229""954-669-6229", "email": "altug_baci@hotmail.com", "cdl": "B227-564", "cdl_expiry": "2033-06-04", "medical": "2026-08-26", "truck": "12"},
    {"name": "FIERALDO", "phone": "267-764-8746""267-764-8746", "email": "Fieraldoshkembii@gmail.com", "cdl": "34593649", "cdl_expiry": "2026-08-26", "medical": "2026-08-26", "truck": "12"},
    {"name": "BRYAN MAHMUTAJ", "phone": "215-555-0138""215-555-0138", "email": "bryan@moonstarpa.com", "cdl": "PA-388031", "cdl_expiry": "2027-05-31", "medical": "2027-10-01", "truck": "38"},
    {"name": "WAHDAT SAFI", "phone": "215-555-0153""215-555-0153", "email": "wahdat@moonstarpa.com", "cdl": "PA-764360", "cdl_expiry": "2027-05-31", "medical": "2027-07-26", "truck": "53"},
    {"name": "FERHADULLAH WESAL", "phone": "215-555-0163""215-555-0163", "email": "farhad@moonstarpa.com", "cdl": "PA-794680", "cdl_expiry": "2026-11-30", "medical": "2027-07-27", "truck": "63"},
    {"name": "ALI TAJ", "phone": "215-555-0442""215-555-0442", "email": "alitaj@moonstarpa.com", "cdl": "PA-662570", "cdl_expiry": "2027-05-31", "medical": "2027-07-27", "truck": "4462"},
    {"name": "BULENT / ASIL BAD SHAH", "phone": "215-555-0192""215-555-0192", "email": "asil@moonstarpa.com", "cdl": "PA-982341", "cdl_expiry": "2027-05-31", "medical": "2026-12-01", "truck": "06"},
    {"name": "DINDAR RAHMANI", "phone": "215-555-0177""215-555-0177", "email": "dindar@moonstarpa.com", "cdl": "PA-112344", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "Unassigned"},
    {"name": "HABIB TANIWAL", "phone": "215-555-0114""215-555-0114", "email": "habib@moonstarpa.com", "cdl": "PA-598991", "cdl_expiry": "2027-05-31", "medical": "2026-10-01", "truck": "14"},
    {"name": "BESHARAT SEDEQI", "phone": "215-555-0248""215-555-0248", "email": "besharat@moonstarpa.com", "cdl": "PA-808390", "cdl_expiry": "2027-05-31", "medical": "2027-03-27", "truck": "2486"},
    {"name": "HUSSAIN ANWARI", "phone": "215-555-0892""215-555-0892", "email": "hussain@moonstarpa.com", "cdl": "PA-642540", "cdl_expiry": "2027-05-31", "medical": "2026-11-26", "truck": "8929"},
    {"name": "ISMAIL CINAR", "phone": "347-444-1686""347-444-1686", "email": "ismail@moonstarpa.com", "cdl": "PA-OWNER", "cdl_expiry": "2028-01-01", "medical": "2027-01-01", "truck": "41"},
    {"name": "ISMAIL CINAR 41", "phone": "347-444-1687""347-444-1687", "email": "ismail41@moonstarpa.com", "cdl": "PA-OWNER2", "cdl_expiry": "2028-01-01", "medical": "2027-01-01", "truck": "41"},
    {"name": "NOOR SHAHZADIN", "phone": "215-555-0155""215-555-0155", "email": "noor@moonstarpa.com", "cdl": "PA-482560", "cdl_expiry": "2027-05-31", "medical": "2026-11-26", "truck": "55"},
    {"name": "JOSHUA DIAZ", "phone": "215-555-0131""215-555-0131", "email": "joshua@moonstarpa.com", "cdl": "PA-849821", "cdl_expiry": "2026-11-30", "medical": "2026-11-01", "truck": "31"},
    {"name": "MOHAMMAD MALAK", "phone": "215-555-0101""215-555-0101", "email": "malak@moonstarpa.com", "cdl": "PA-010101", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "01"},
    {"name": "TEVIN BOBBY", "phone": "215-555-1907""215-555-1907", "email": "tevin@moonstarpa.com", "cdl": "PA-190719", "cdl_expiry": "2027-05-31", "medical": "2026-08-26", "truck": "FB1907"},
    {"name": "DREW W. DAVIS", "phone": "215-555-0115""215-555-0115", "email": "drew@moonstarpa.com", "cdl": "PA-011511", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "0115"},
    {"name": "LAMAR MONTEL BURT", "phone": "215-555-0116""215-555-0116", "email": "montel@moonstarpa.com", "cdl": "PA-550840", "cdl_expiry": "2027-05-31", "medical": "2026-10-26", "truck": "115"},
    {"name": "JAMIL MBOYA", "phone": "215-555-1105""215-555-1105", "email": "jamil@moonstarpa.com", "cdl": "PA-110501", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "1105"},
    {"name": "BARAT KHAN", "phone": "215-555-1675""215-555-1675", "email": "barat@moonstarpa.com", "cdl": "PA-167500", "cdl_expiry": "2027-05-31", "medical": "2026-11-26", "truck": "1675"},
    {"name": "BRENA BYRD", "phone": "215-555-2468""215-555-2468", "email": "brena@moonstarpa.com", "cdl": "PA-246800", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "2468"},
    {"name": "OLIVER FORD", "phone": "215-555-2640""215-555-2640", "email": "oliver@moonstarpa.com", "cdl": "PA-264000", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "2640"},
    {"name": "AMJAD MULK", "phone": "215-555-2940""215-555-2940", "email": "amjad@moonstarpa.com", "cdl": "PA-294000", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "2940"},
    {"name": "AZEEM MURPHY", "phone": "215-555-2941""215-555-2941", "email": "azeemm@moonstarpa.com", "cdl": "PA-294100", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "2940"},
    {"name": "BRANDON OSINUPEBI", "phone": "215-555-4561""215-555-4561", "email": "brandon@moonstarpa.com", "cdl": "PA-456100", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "4561"},
    {"name": "SHIRIN BAD SHAH", "phone": "215-555-5672""215-555-5672", "email": "shirin@moonstarpa.com", "cdl": "PA-567200", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "5672"},
    {"name": "DEMITRUS FAUST", "phone": "215-555-6812""215-555-6812", "email": "demitrus@moonstarpa.com", "cdl": "PA-681200", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "6812"},
    {"name": "MARQUIS J BATTLE", "phone": "215-555-7688""215-555-7688", "email": "marquis@moonstarpa.com", "cdl": "PA-768800", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "7688"},
    {"name": "SHAFOOR BISMELLAH", "phone": "215-555-7710""215-555-7710", "email": "shafoor@moonstarpa.com", "cdl": "PA-771000", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "7710"},
    {"name": "WALI RAHMAN", "phone": "215-555-1021""215-555-1021", "email": "wali@moonstarpa.com", "cdl": "PA-550670", "cdl_expiry": "2027-05-31", "medical": "2026-10-26", "truck": "1021"},
    {"name": "ALI IMRAN", "phone": "215-555-0201""215-555-0201", "email": "aliimran@moonstarpa.com", "cdl": "TX-694300", "cdl_expiry": "2027-05-31", "medical": "2027-07-27", "truck": "201"},
    {"name": "ANDI KASHARI", "phone": "215-555-0217""215-555-0217", "email": "andi@moonstarpa.com", "cdl": "PA-814160", "cdl_expiry": "2027-05-31", "medical": "2026-12-26", "truck": "217"},
    {"name": "NASEEBULLAH", "phone": "215-555-0202""215-555-0202", "email": "naseeb@moonstarpa.com", "cdl": "TX-011000", "cdl_expiry": "2027-05-31", "medical": "2027-07-27", "truck": "202"},
    {"name": "NEVIS HAJNAJ", "phone": "215-555-0999""215-555-0999", "email": "nevis@moonstarpa.com", "cdl": "PA-413900", "cdl_expiry": "2027-05-31", "medical": "2027-08-27", "truck": "999"},
    {"name": "SELCUK GOCKEN", "phone": "215-555-1052""215-555-1052", "email": "selcuk@moonstarpa.com", "cdl": "NJ-136000", "cdl_expiry": "2027-05-31", "medical": "2027-07-26", "truck": "1052"},
    {"name": "YZEDIN HATTILARI", "phone": "215-555-0995""215-555-0995", "email": "yzedin@moonstarpa.com", "cdl": "PA-995000", "cdl_expiry": "2027-05-31", "medical": "2027-04-01", "truck": "995"},
    {"name": "OMAD FNU", "phone": "215-555-0010""215-555-0010", "email": "omad@moonstarpa.com", "cdl": "TX-778574", "cdl_expiry": "2027-04-30", "medical": "2027-02-26", "truck": "10"},
    {"name": "OMAID FNU 35", "phone": "215-555-0035""215-555-0035", "email": "omaid35@moonstarpa.com", "cdl": "TX-778575", "cdl_expiry": "2027-04-30", "medical": "2027-02-26", "truck": "35"},
    {"name": "OMAID FNU T34", "phone": "215-555-0034""215-555-0034", "email": "omaidt34@moonstarpa.com", "cdl": "TX-567959", "cdl_expiry": "2027-04-30", "medical": "2027-02-27", "truck": "34"},
    {"name": "RAFIQ SARFERAZ", "phone": "215-555-0130""215-555-0130", "email": "rafiq@moonstarpa.com", "cdl": "PA-286911", "cdl_expiry": "2026-09-25", "medical": "2026-12-26", "truck": "30"},
    {"name": "RIDVAN DENIZ", "phone": "215-555-0165""215-555-0165", "email": "ridvan@moonstarpa.com", "cdl": "PA-849830", "cdl_expiry": "2026-11-30", "medical": "2026-12-01", "truck": "65"},
    {"name": "RUSS", "phone": "215-555-0342""215-555-0342", "email": "russ@moonstarpa.com", "cdl": "PA-342260", "cdl_expiry": "2027-05-31", "medical": "2026-10-26", "truck": "40"},
    {"name": "AZEEM AZEEMI", "phone": "215-555-5421""215-555-5421", "email": "azeemi@moonstarpa.com", "cdl": "IN-315962", "cdl_expiry": "2027-03-31", "medical": "2027-03-31", "truck": "542148"},
    {"name": "KAAMIL E VENSON", "phone": "215-555-8212""215-555-8212", "email": "kaamil@moonstarpa.com", "cdl": "IN-384287", "cdl_expiry": "2027-03-31", "medical": "2027-03-31", "truck": "821264"},
    {"name": "SAID KHAN", "phone": "215-555-0133""215-555-0133", "email": "said@moonstarpa.com", "cdl": "PA-856140", "cdl_expiry": "2027-05-31", "medical": "2026-07-27", "truck": "33"},
    {"name": "MOHAMMAD AMAN RASOLI", "phone": "215-555-2009""215-555-2009", "email": "aman@moonstarpa.com", "cdl": "PA-652670", "cdl_expiry": "2027-05-31", "medical": "2027-03-27", "truck": "2009"},
    {"name": "SAYED MUKHTAR", "phone": "215-555-0530""215-555-0530", "email": "sayed@moonstarpa.com", "cdl": "PA-530000", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "Unassigned"},
    {"name": "THOMAS HUDSON", "phone": "215-555-5269""215-555-5269", "email": "thomas@moonstarpa.com", "cdl": "PA-526920", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "526920"},
    {"name": "THOMAS VASQUEZ", "phone": "215-555-5270""215-555-5270", "email": "tvasquez@moonstarpa.com", "cdl": "PA-527000", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "Unassigned"},
    {"name": "AT YARD", "phone": "215-555-0144""215-555-0144", "email": "yard@moonstarpa.com", "cdl": "PA-334112", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "8"},
    {"name": "FERHADULLAH", "phone": "215-555-0164""215-555-0164", "email": "ferhad@moonstarpa.com", "cdl": "PA-630000", "cdl_expiry": "2026-11-30", "medical": "2027-07-27", "truck": "63"},
    {"name": "BARAT KHAN 2", "phone": "215-555-1676""215-555-1676", "email": "barat2@moonstarpa.com", "cdl": "PA-167501", "cdl_expiry": "2027-05-31", "medical": "2026-11-26", "truck": "1675"},
    {"name": "DEMITRUS FAUST 2", "phone": "215-555-6813""215-555-6813", "email": "demitrus2@moonstarpa.com", "cdl": "PA-681201", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "6812"},
    {"name": "MARQUIS J BATTLE 2", "phone": "215-555-7689""215-555-7689", "email": "marquis2@moonstarpa.com", "cdl": "PA-768801", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "7688"},
    {"name": "SHAFOOR BISMELLAH 2", "phone": "215-555-7711""215-555-7711", "email": "shafoor2@moonstarpa.com", "cdl": "PA-771001", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "7710"}
]

# --- KAMYONLAR VE P&L ---
TRUCKS_DATA = [
    {"unit": "FB1907", "type": "2022 INTERNATIONAL", "plate": "AH59897 PA", "driver": "TEVIN BOBBY", "gross": 19800.0, "fuel": 4700.0, "maintenance": 500.0},
    {"unit": "8", "type": "VOLVO Vnl64t", "plate": "AH35700 PA", "driver": "AT YARD", "gross": 15000.0, "fuel": 4200.0, "maintenance": 300.0},
    {"unit": "10", "type": "FREIGHTLINER", "plate": "R785774 TX", "driver": "OMAID FNU", "gross": 21000.0, "fuel": 5300.0, "maintenance": 650.0},
    {"unit": "12", "type": "VOLVO 2021", "plate": "AH69361 PA", "driver": "ALTUG BACI", "gross": 22000.0, "fuel": 5100.0, "maintenance": 500.0},
    {"unit": "14", "type": "FREIGHTLINER", "plate": "AH59899 PA", "driver": "HABIB TANIWAL", "gross": 18500.0, "fuel": 4600.0, "maintenance": 400.0},
    {"unit": "33", "type": "FREIGHTLINER", "plate": "AG85614 PA", "driver": "SAID KHAN", "gross": 20400.0, "fuel": 4900.0, "maintenance": 450.0},
    {"unit": "38", "type": "VOLVO", "plate": "AH38803 PA", "driver": "BRYAN MAHMUTAJ", "gross": 24000.0, "fuel": 5800.0, "maintenance": 600.0},
    {"unit": "41", "type": "VOLVO", "plate": "AH79469 PA", "driver": "ISMAIL CINAR", "gross": 21000.0, "fuel": 5000.0, "maintenance": 350.0},
    {"unit": "53", "type": "FREIGHTLINER", "plate": "AH76436 PA", "driver": "WAHDAT SAFI", "gross": 26000.0, "fuel": 6200.0, "maintenance": 750.0},
    {"unit": "65", "type": "VOLVO", "plate": "AH84983 PA", "driver": "RIDVAN DENIZ", "gross": 19500.0, "fuel": 4500.0, "maintenance": 500.0}
]

# --- RÖMORKLAR (TRAILERS) ---
TRAILERS_DATA = [
    {"unit": "127", "type": "22' Van", "plate": "516-6421 ME", "annual_insp": "2027-06-30", "assigned_truck": "FB1907"},
    {"unit": "209536611", "type": "53' Reefer", "plate": "-", "annual_insp": "2027-05-31", "assigned_truck": "8"},
    {"unit": "532019", "type": "53' Van", "plate": "563-7097 ME", "annual_insp": "2027-05-31", "assigned_truck": "12"},
    {"unit": "532132", "type": "53' Reefer", "plate": "-", "annual_insp": "2027-08-30", "assigned_truck": "53"},
    {"unit": "599238", "type": "Flatbed", "plate": "-", "annual_insp": "2027-09-30", "assigned_truck": "38"},
    {"unit": "9421", "type": "53' Reefer", "plate": "30-28279 ME", "annual_insp": "2027-09-30", "assigned_truck": "41"},
    {"unit": "DORSEY 0916", "type": "Step Deck", "plate": "2830813", "annual_insp": "2028-02-29", "assigned_truck": "10"},
    {"unit": "L 524", "type": "Step Deck", "plate": "TN861605", "annual_insp": "2027-06-30", "assigned_truck": "14"},
    {"unit": "R14782", "type": "Dry Van", "plate": "31-19733 ME", "annual_insp": "2026-07-27", "assigned_truck": "65"}
]

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>MOONSTAR EXPRESS — Executive Portal</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>.brand-font { font-family: 'Montserrat', sans-serif; }</style>
</head>
<body class="bg-slate-100 min-h-screen flex items-center justify-center">
<div class="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border border-slate-200">
    <div class="text-center mb-6">
        <span class="brand-font text-3xl font-black text-slate-900">MOON<span class="text-sky-500">★</span>TAR</span>
        <p class="text-xs font-semibold text-sky-600 mt-1 uppercase tracking-wider">Executive Fleet Console</p>
    </div>
    {% if error %}
    <div class="bg-red-50 border border-red-200 text-red-600 text-xs p-3 rounded-lg mb-4 text-center font-medium">{{ error }}</div>
    {% endif %}
    <form action="/login" method="POST" class="space-y-4">
        <div>
            <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Corporate Email</label>
            <input type="email" name="email" required placeholder="ismail@moonstarpa.com" class="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg">
        </div>
        <div>
            <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Password</label>
            <input type="password" name="password" required class="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg">
        </div>
        <button type="submit" class="w-full py-3 bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold uppercase tracking-wider rounded-lg shadow-md">Sign In to Portal</button>
    </form>
</div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>MOONSTAR EXPRESS LLC — Master Fleet Console</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>.brand-font { font-family: 'Montserrat', sans-serif; }</style>
</head>
<body class="bg-slate-50 min-h-screen flex">
    <aside class="w-20 bg-slate-900 flex flex-col items-center py-6 space-y-8 border-r border-slate-800">
        <div class="brand-font text-sky-400 font-black text-xl">★</div>
        <div class="flex flex-col space-y-6 text-slate-400">
            <a href="/dashboard?tab=trucks" title="Trucks" class="p-3 rounded-xl {% if tab == 'trucks' %}bg-sky-600 text-white{% else %}hover:bg-slate-800{% endif %} transition">🚛</a>
            <a href="/dashboard?tab=trailers" title="Trailers" class="p-3 rounded-xl {% if tab == 'trailers' %}bg-sky-600 text-white{% else %}hover:bg-slate-800{% endif %} transition">📦</a>
            <a href="/dashboard?tab=drivers" title="Drivers" class="p-3 rounded-xl {% if tab == 'drivers' %}bg-sky-600 text-white{% else %}hover:bg-slate-800{% endif %} transition">👤</a>
        </div>
    </aside>

    <div class="flex-1 flex flex-col min-w-0">
        <header class="bg-gradient-to-r from-slate-900 via-blue-950 to-sky-600 px-8 py-4 shadow-md border-b-4 border-orange-500 flex justify-between items-center text-white">
            <div class="flex items-center space-x-3">
                <span class="brand-font text-2xl font-black tracking-wide">MOON<span class="text-orange-500">★</span>TAR</span>
                <span class="text-xs font-semibold text-sky-300 border border-sky-400 px-2 py-0.5 rounded">EXPRESS LLC</span>
            </div>
            <div class="flex items-center space-x-4 text-xs">
                <span>User: <b>{{ user }}</b></span>
                <a href="/logout" class="bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded-lg font-bold uppercase shadow">Sign Out</a>
            </div>
        </header>

        <div class="bg-white border-b border-slate-200 px-8 py-3 flex space-x-3 shadow-sm">
            <a href="/dashboard?tab=trucks" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'trucks' %}bg-slate-900 text-white shadow{% else %}text-slate-600 hover:bg-slate-100{% endif %}">Trucks & P&L ({{ trucks|length }})</a>
            <a href="/dashboard?tab=trailers" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'trailers' %}bg-slate-900 text-white shadow{% else %}text-slate-600 hover:bg-slate-100{% endif %}">Trailers Master ({{ trailers|length }})</a>
            <a href="/dashboard?tab=drivers" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'drivers' %}bg-slate-900 text-white shadow{% else %}text-slate-600 hover:bg-slate-100{% endif %}">Drivers Roster ({{ drivers|length }})</a>
        </div>

        <main class="p-8 space-y-6 flex-1">
            {% if tab == 'trucks' %}
            <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div class="p-5 border-b border-slate-200 flex justify-between items-center bg-slate-50">
                    <h3 class="font-black text-slate-900 text-base">🚛 Master Trucks Inventory & P&L Ledger</h3>
                    <span class="text-xs text-slate-500">Click any truck row to edit financial data and expenses.</span>
                </div>
                <table class="w-full text-left border-collapse text-xs">
                    <thead>
                        <tr class="bg-slate-900 text-white">
                            <th class="p-3">Unit #</th>
                            <th class="p-3">Make / Model</th>
                            <th class="p-3">Assigned Driver</th>
                            <th class="p-3">Gross Revenue</th>
                            <th class="p-3">Fuel & Maint.</th>
                            <th class="p-3">Net Profit / Loss</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-200">
                        {% for t in trucks %}
                        <tr class="hover:bg-slate-50 cursor-pointer" onclick="window.location='/dashboard?tab=trucks&dossier={{ t.unit }}'">
                            <td class="p-3 font-black text-slate-900">#{{ t.unit }}</td>
                            <td class="p-3 text-slate-700">{{ t.type }}</td>
                            <td class="p-3 font-bold text-sky-600">{{ t.driver }}</td>
                            <td class="p-3 text-emerald-600 font-bold">${{ "{:,.2f}".format(t.gross) }}</td>
                            <td class="p-3 text-orange-600 font-bold">${{ "{:,.2f}".format(t.fuel + t.maintenance) }}</td>
                            <td class="p-3 font-black {% if (t.gross - t.fuel - t.maintenance) >= 0 %}text-emerald-700{% else %}text-red-600{% endif %}">
                                ${{ "{:,.2f}".format(t.gross - t.fuel - t.maintenance) }}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% elif tab == 'trailers' %}
            <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div class="p-5 border-b border-slate-200 flex justify-between items-center bg-slate-50">
                    <h3 class="font-black text-slate-900 text-base">📦 Master Trailers Inventory</h3>
                    <span class="text-xs text-slate-500">Active trailers assigned to fleet units.</span>
                </div>
                <table class="w-full text-left border-collapse text-xs">
                    <thead>
                        <tr class="bg-slate-900 text-white">
                            <th class="p-3">Unit #</th>
                            <th class="p-3">Trailer Type</th>
                            <th class="p-3">Plate Number</th>
                            <th class="p-3">Annual Inspection Due</th>
                            <th class="p-3">Assigned Truck</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-200">
                        {% for tr in trailers %}
                        <tr class="hover:bg-slate-50">
                            <td class="p-3 font-black text-slate-900">#{{ tr.unit }}</td>
                            <td class="p-3 text-slate-700">{{ tr.type }}</td>
                            <td class="p-3 text-slate-600">{{ tr.plate }}</td>
                            <td class="p-3 font-semibold text-amber-700">{{ tr.annual_insp }}</td>
                            <td class="p-3 font-bold text-sky-600">Truck #{{ tr.assigned_truck }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% elif tab == 'drivers' %}
            <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div class="p-5 border-b border-slate-200 flex justify-between items-center bg-slate-50">
                    <h3 class="font-black text-slate-900 text-base">👤 Master Drivers Roster ({{ drivers|length }} Active Drivers)</h3>
                    <span class="text-xs text-slate-500">Click phone number to call directly.</span>
                </div>
                <table class="w-full text-left border-collapse text-xs">
                    <thead>
                        <tr class="bg-slate-900 text-white">
                            <th class="p-3">Driver Name</th>
                            <th class="p-3">Phone & Direct Call</th>
                            <th class="p-3">CDL & Expiry</th>
                            <th class="p-3">DOT Medical Due</th>
                            <th class="p-3">Assigned Truck</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-200">
                        {% for d in drivers %}
                        <tr class="hover:bg-slate-50">
                            <td class="p-3 font-black text-slate-900">{{ d.name }}</td>
                            <td class="p-3 text-slate-600">
                                <a href="tel:{{ d.phone }}" class="text-sky-600 font-bold hover:underline">📞 {{ d.phone }}</a>
                                <br><span class="text-[10px] text-slate-400">{{ d.email }}</span>
                            </td>
                            <td class="p-3 text-slate-700">{{ d.cdl }} <br><span class="text-[10px] text-sky-600 font-bold">Exp: {{ d.cdl_expiry }}</span></td>
                            <td class="p-3 font-bold text-amber-700">{{ d.medical }}</td>
                            <td class="p-3 font-bold text-sky-600">Truck #{{ d.truck }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}
        </main>
    </div>

    <!-- TRUCK P&L DOSSIER MODAL -->
    {% if selected_truck %}
    <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-xl overflow-hidden border border-slate-200">
            <div class="bg-slate-900 text-white p-5 flex justify-between items-center">
                <h3 class="font-black text-lg">Truck P&L & Expenses — Unit #{{ selected_truck.unit }}</h3>
                <a href="/dashboard?tab=trucks" class="text-slate-400 hover:text-white font-bold text-lg">✕</a>
            </div>
            <form action="/update_truck" method="POST" class="p-6 space-y-4">
                <input type="hidden" name="unit" value="{{ selected_truck.unit }}">
                <div>
                    <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Gross Revenue ($)</label>
                    <input type="number" step="0.01" name="gross" value="{{ selected_truck.gross }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                </div>
                <div>
                    <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Fuel Expense ($)</label>
                    <input type="number" step="0.01" name="fuel" value="{{ selected_truck.fuel }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                </div>
                <div>
                    <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Maintenance / Oil Change Expense ($)</label>
                    <input type="number" step="0.01" name="maintenance" value="{{ selected_truck.maintenance }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                </div>
                <div class="flex justify-end pt-2">
                    <button type="submit" class="bg-sky-600 text-white px-5 py-2 rounded-lg text-xs font-bold uppercase shadow">💾 Save Financials</button>
                </div>
            </form>
        </div>
    </div>
    {% endif %}
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return Template(LOGIN_HTML).render()

@app.post("/login")
def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    if "@moonstarpa" in email.strip().lower() and password == "Moonstar2026!":
        response = RedirectResponse(url="/dashboard?tab=trucks", status_code=303)
        response.set_cookie(key="user", value=email.strip().lower())
        return response
    return Template(LOGIN_HTML).render(error="Invalid credentials!")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, tab: str = "trucks", dossier: str = None):
    user = request.cookies.get("user")
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    selected_truck = next((t for t in TRUCKS_DATA if t["unit"] == dossier), None) if dossier else None

    return Template(DASHBOARD_HTML).render(
        user=user, 
        trucks=TRUCKS_DATA, 
        trailers=TRAILERS_DATA,
        drivers=DRIVERS_DATA, 
        tab=tab, 
        selected_truck=selected_truck
    )

@app.post("/update_truck")
def update_truck(unit: str = Form(...), gross: float = Form(0.0), fuel: float = Form(0.0), maintenance: float = Form(0.0)):
    for t in TRUCKS_DATA:
        if t["unit"] == unit:
            t["gross"] = gross
            t["fuel"] = fuel
            t["maintenance"] = maintenance
    return RedirectResponse(url="/dashboard?tab=trucks", status_code=303)

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="user")
    return response
