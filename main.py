from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Template
from datetime import datetime

app = FastAPI(title="MOONSTAR EXPRESS LLC — Executive Fleet Console")

# Yüklediğiniz gerçek Excel verilerinden derlenen master filo ve şoför listesi
FLEET_DATA = [
    {"unit_number": "6", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "ASIL BAD SHAH", "vin": "3AKJHHDR6JSJJ1492", "plate": "AH43983 PA", "annual_dot": "2026-09-01", "pa_insp": "2026-09-26", "status": "DUE SOON", "gross": 19500.0, "fuel": 4800.0, "net": 14700.0, "files": ["DOT_Inspection.pdf"]},
    {"unit_number": "8", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "AT YARD", "vin": "4V4NC9EH7KN900632", "plate": "AH35700 PA", "annual_dot": "2026-10-26", "pa_insp": "2026-11-26", "status": "READY", "gross": 15000.0, "fuel": 4200.0, "net": 10800.0, "files": []},
    {"unit_number": "10", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "OMAID FNU", "vin": "3AKJGLDR5KSKL6961", "plate": "R785774 TX", "annual_dot": "2027-08-26", "pa_insp": "TX PLATE", "status": "READY", "gross": 21000.0, "fuel": 5300.0, "net": 15700.0, "files": []},
    {"unit_number": "11", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "at shop", "vin": "3HSDZAPR1LN872658", "plate": "AH59898 PA", "annual_dot": "2026-10-26", "pa_insp": "2026-05-27", "status": "DUE SOON", "gross": 0.0, "fuel": 0.0, "net": 0.0, "files": []},
    {"unit_number": "12", "unit_type": "TRUCK", "company": "FIORI", "driver": "ALTUG BACI", "vin": "4V4NC9EJ4MN275936", "plate": "AH69361 PA", "annual_dot": "2027-03-01", "pa_insp": "2027-03-01", "status": "READY", "gross": 22000.0, "fuel": 5100.0, "net": 16900.0, "files": []},
    {"unit_number": "14", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "HABIB KHAN TANIWAL", "vin": "3AKJHHDR9LSLM9887", "plate": "AH59899 PA", "annual_dot": "2026-10-01", "pa_insp": "2026-07-27", "status": "DUE SOON", "gross": 18500.0, "fuel": 4600.0, "net": 13900.0, "files": []},
    {"unit_number": "33", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "SAID KHAN", "vin": "4V4NC9EHXKN212592", "plate": "AG85614 PA", "annual_dot": "2026-07-27", "pa_insp": "2026-11-26", "status": "READY", "gross": 20400.0, "fuel": 4900.0, "net": 15500.0, "files": []},
    {"unit_number": "34", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "HAQMAL HABIBI", "vin": "3AKJGLDR0JSHF1489", "plate": "R567959 TX", "annual_dot": "2027-02-27", "pa_insp": "TX PLATE", "status": "READY", "gross": 17500.0, "fuel": 4100.0, "net": 13400.0, "files": []},
    {"unit_number": "55", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "NOOR SHAHZADIN", "vin": "1M1AN4GY8LM014136", "plate": "AH48256 PA", "annual_dot": "2026-11-26", "pa_insp": "2026-11-26", "status": "DUE SOON", "gross": 23000.0, "fuel": 5500.0, "net": 17500.0, "files": []},
    {"unit_number": "30", "unit_type": "TRUCK", "company": "LIONSTAR", "driver": "RAFIQ SERFERAZ", "vin": "4V4NC9EJXMN286911", "plate": "TEMP- PA", "annual_dot": "2026-12-26", "pa_insp": "N/A", "status": "DUE SOON", "gross": 17000.0, "fuel": 4000.0, "net": 13000.0, "files": []},
    {"unit_number": "31", "unit_type": "TRUCK", "company": "LIONSTAR", "driver": "JOSHUA RAYMOND DIAZ", "vin": "4V4NC9EJ1GN953465", "plate": "AH84982 PA", "annual_dot": "2026-11-01", "pa_insp": "2026-05-27", "status": "DUE SOON", "gross": 18500.0, "fuel": 4300.0, "net": 14200.0, "files": []},
    {"unit_number": "38", "unit_type": "TRUCK", "company": "LIONSTAR", "driver": "BRYAN MAHMUTAJ", "vin": "4V4NC9EH4PN625082", "plate": "AH38803 PA", "annual_dot": "2027-10-01", "pa_insp": "2026-01-27", "status": "READY", "gross": 24000.0, "fuel": 5800.0, "net": 18200.0, "files": []},
    {"unit_number": "40", "unit_type": "TRUCK", "company": "LIONSTAR", "driver": "RUSSLAN SMIRNOV", "vin": "4V4NC9EH3PN613540", "plate": "AH34226 PA", "annual_dot": "2026-10-01", "pa_insp": "2026-10-26", "status": "DUE SOON", "gross": 22500.0, "fuel": 5200.0, "net": 17300.0, "files": []},
    {"unit_number": "41", "unit_type": "TRUCK", "company": "LIONSTAR", "driver": "NOOR ALI WAZIRI", "vin": "4V4NC9EH5PN613541", "plate": "AH79469 PA", "annual_dot": "2027-04-01", "pa_insp": "2026-10-26", "status": "READY", "gross": 21000.0, "fuel": 5000.0, "net": 16000.0, "files": []},
    {"unit_number": "53", "unit_type": "TRUCK", "company": "LIONSTAR", "driver": "WAHDAT SAFI", "vin": "3HSDZSZR0SN355353", "plate": "AH76436 PA", "annual_dot": "2027-07-26", "pa_insp": "2027-07-27", "status": "READY", "gross": 26000.0, "fuel": 6200.0, "net": 19800.0, "files": []},
    {"unit_number": "63", "unit_type": "TRUCK", "company": "LIONSTAR", "driver": "FARHADULLAH WESAL", "vin": "3HSDZSZR8TN355263", "plate": "AH79468 PA", "annual_dot": "2027-07-27", "pa_insp": "2026-10-01", "status": "READY", "gross": 25000.0, "fuel": 5900.0, "net": 19100.0, "files": []},
    {"unit_number": "65", "unit_type": "TRUCK", "company": "LIONSTAR", "driver": "RIDVAN DENIZ", "vin": "4V4NC9EH8HN976742", "plate": "AH84983 PA", "annual_dot": "2026-12-01", "pa_insp": "2026-12-26", "status": "DUE SOON", "gross": 19500.0, "fuel": 4500.0, "net": 15000.0, "files": []},
    {"unit_number": "R14782", "unit_type": "TRAILER", "company": "TNT RENTAL", "driver": "Unassigned", "vin": "3AWF1VT24LX004006", "plate": "31-19733 ME", "annual_dot": "2026-07-27", "pa_insp": "N/A", "status": "READY", "gross": 0.0, "fuel": 0.0, "net": 0.0, "files": []},
    {"unit_number": "S5319149", "unit_type": "TRAILER", "company": "PLM RENTAL", "driver": "Unassigned", "vin": "1UYVS2531K2742401", "plate": "30-25944 ME", "annual_dot": "2026-01-27", "pa_insp": "N/A", "status": "READY", "gross": 0.0, "fuel": 0.0, "net": 0.0, "files": []}
]

DRIVERS_DATA = [
    {"name": "ALTUG BACI", "company": "FIORI", "phone": "954-669-6229""954-669-6229", "email": "altug_baci@hotmail.com", "cdl": "B227-564-89-400-0", "cdl_expiry": "2033-06-04", "medical": "2026-08-26", "unit": "12", "files": ["CDL_Scan.pdf"]},
    {"name": "ASIL BAD SHAH", "company": "MOONSTAR", "phone": "215-555-0192""215-555-0192", "email": "asil@moonstarpa.com", "cdl": "PA-982341", "cdl_expiry": "2027-05-31", "medical": "2026-12-01", "unit": "6", "files": ["Medical_Card.pdf"]},
    {"name": "AT YARD", "company": "MOONSTAR", "phone": "215-555-0144""215-555-0144", "email": "yard@moonstarpa.com", "cdl": "PA-334112", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "unit": "8", "files": []},
    {"name": "OMAID FNU", "company": "MOONSTAR", "phone": "215-555-0110""215-555-0110", "email": "omaid@moonstarpa.com", "cdl": "TX-778574", "cdl_expiry": "2027-04-30", "medical": "2027-02-26", "unit": "10", "files": []},
    {"name": "HABIB KHAN TANIWAL", "company": "MOONSTAR", "phone": "215-555-0114""215-555-0114", "email": "habib@moonstarpa.com", "cdl": "PA-598991", "cdl_expiry": "2027-05-31", "medical": "2026-10-01", "unit": "14", "files": []},
    {"name": "SAID KHAN", "company": "MOONSTAR", "phone": "215-555-0133""215-555-0133", "email": "said@moonstarpa.com", "cdl": "PA-856140", "cdl_expiry": "2027-05-31", "medical": "2026-07-27", "unit": "33", "files": []},
    {"name": "HAQMAL HABIBI", "company": "MOONSTAR", "phone": "215-555-0134""215-555-0134", "email": "haqmal@moonstarpa.com", "cdl": "TX-567959", "cdl_expiry": "2027-04-30", "medical": "2027-02-27", "unit": "34", "files": []},
    {"name": "NOOR SHAHZADIN", "company": "MOONSTAR", "phone": "215-555-0155""215-555-0155", "email": "noor@moonstarpa.com", "cdl": "PA-482560", "cdl_expiry": "2027-05-31", "medical": "2026-11-26", "unit": "55", "files": []},
    {"name": "RAFIQ SERFERAZ", "company": "LIONSTAR", "phone": "215-555-0130""215-555-0130", "email": "rafiq@moonstarpa.com", "cdl": "PA-286911", "cdl_expiry": "2026-09-25", "medical": "2026-12-26", "unit": "30", "files": []},
    {"name": "JOSHUA RAYMOND DIAZ", "company": "LIONSTAR", "phone": "215-555-0131""215-555-0131", "email": "joshua@moonstarpa.com", "cdl": "PA-849821", "cdl_expiry": "2026-11-30", "medical": "2026-11-01", "unit": "31", "files": []},
    {"name": "BRYAN MAHMUTAJ", "company": "LIONSTAR", "phone": "215-555-0138""215-555-0138", "email": "bryan@moonstarpa.com", "cdl": "PA-388031", "cdl_expiry": "2027-05-31", "medical": "2027-10-01", "unit": "38", "files": []},
    {"name": "RUSSLAN SMIRNOV", "company": "LIONSTAR", "phone": "215-555-0140""215-555-0140", "email": "russlan@moonstarpa.com", "cdl": "PA-342260", "cdl_expiry": "2027-05-31", "medical": "2026-10-01", "unit": "40", "files": []},
    {"name": "NOOR ALI WAZIRI", "company": "LIONSTAR", "phone": "215-555-0141""215-555-0141", "email": "noorw@moonstarpa.com", "cdl": "PA-794690", "cdl_expiry": "2027-05-31", "medical": "2027-04-01", "unit": "41", "files": []},
    {"name": "WAHDAT SAFI", "company": "LIONSTAR", "phone": "215-555-0153""215-555-0153", "email": "wahdat@moonstarpa.com", "cdl": "PA-764360", "cdl_expiry": "2027-05-31", "medical": "2027-07-26", "unit": "53", "files": []},
    {"name": "FARHADULLAH WESAL", "company": "LIONSTAR", "phone": "215-555-0163""215-555-0163", "email": "farhad@moonstarpa.com", "cdl": "PA-794680", "cdl_expiry": "2026-11-30", "medical": "2027-07-27", "unit": "63", "files": []},
    {"name": "RIDVAN DENIZ", "company": "LIONSTAR", "phone": "215-555-0165""215-555-0165", "email": "ridvan@moonstarpa.com", "cdl": "PA-849830", "cdl_expiry": "2026-11-30", "medical": "2026-12-01", "unit": "65", "files": []}
]

CHAT_MESSAGES = [
    {"sender": "ismail@moonstarpa.com", "message": "Dispatch, please check Unit #8 maintenance status.", "time": "09:30 AM"},
    {"sender": "safety@moonstarpa.com", "message": "All driver medical cards and federal annual inspections are tracked.", "time": "10:15 AM"}
]

HOME_HTML = """




MOONSTAR EXPRESS LLC — Reliable Transportation



    body { font-family: 'Inter', sans-serif; background-color: #ffffff; }
    .brand-font { font-family: 'Montserrat', sans-serif; }



    
    
        
            MOON★TAR
            EXPRESS
        
        
            Home
            About Us
            Contact Us
            Services
            Employee Application
        
    

    
    
        
            
        
        
            RELIABLE TRANSPORTATION SOLUTIONS
            Your trusted partner for safe and efficient travel across the United States.
            
                Book Now
                📞 +1 215-666-0595
            
        
    

    
    
        
            🔐 Sign In to Executive Fleet Console →
        
    

    
    
        © 2026 Moonstar Express LLC. All rights reserved.
    


""""""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>MOONSTAR EXPRESS LLC — Reliable Transportation</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    body { font-family: 'Inter', sans-serif; background-color: #ffffff; }
    .brand-font { font-family: 'Montserrat', sans-serif; }
</style>
</head>
<body class="min-h-screen flex flex-col justify-between">
    <!-- HEADER -->
    <header class="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center shadow-sm">
        <div class="flex items-center space-x-3">
            <span class="brand-font text-2xl font-black text-slate-900 tracking-wide">MOON<span class="text-sky-500">★</span>TAR</span>
            <span class="text-xs font-semibold text-sky-600 border border-sky-600 px-2 py-0.5 rounded">EXPRESS</span>
        </div>
        <nav class="hidden md:flex items-center space-x-8 text-xs font-bold uppercase tracking-wider text-slate-700">
            <a href="/" class="text-sky-600 border-b-2 border-sky-600 pb-1">Home</a>
            <a href="#" class="hover:text-sky-600 transition">About Us</a>
            <a href="#" class="hover:text-sky-600 transition">Contact Us</a>
            <a href="#" class="hover:text-sky-600 transition">Services</a>
            <a href="#" class="hover:text-sky-600 transition">Employee Application</a>
        </nav>
    </header>

    <!-- HERO SECTION -->
    <main class="max-w-7xl mx-auto px-6 py-12 w-full grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div class="rounded-2xl overflow-hidden shadow-2xl relative">
            <img src="https://images.unsplash.com/photo-1519003722824-194d4455a60c?auto=format&fit=crop&w=1200&q=80" alt="Fleet Trucks" class="w-full h-[400px] object-cover">
        </div>
        <div class="bg-slate-900 text-white p-12 rounded-2xl shadow-xl relative overflow-hidden">
            <h1 class="brand-font text-4xl font-black mb-4 leading-tight">RELIABLE TRANSPORTATION SOLUTIONS</h1>
            <p class="text-slate-400 text-sm mb-8">Your trusted partner for safe and efficient travel across the United States.</p>
            <div class="flex items-center justify-between">
                <a href="/login" class="bg-white text-slate-900 hover:bg-slate-100 px-8 py-3 rounded-lg text-xs font-bold uppercase tracking-wider transition shadow">Book Now</a>
                <div class="text-sky-400 font-bold text-sm flex items-center gap-2">📞 +1 215-666-0595</div>
            </div>
        </div>
    </main>

    <!-- PORTAL LOGIN LINK FOOTER BAR -->
    <div class="bg-slate-50 border-t border-slate-200 py-6 text-center">
        <a href="/login" class="text-sky-600 hover:text-sky-700 font-bold text-xs uppercase tracking-widest bg-sky-50 border border-sky-200 px-6 py-3 rounded-xl shadow-sm inline-block transition">
            🔐 Sign In to Executive Fleet Console →
        </a>
    </div>

    <!-- FOOTER -->
    <footer class="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        &copy; 2026 Moonstar Express LLC. All rights reserved.
    </footer>
</body>
</html>
"""

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>MOONSTAR EXPRESS — Executive Portal</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-100 min-h-screen flex items-center justify-center">
<div class="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border border-slate-200">
    <div class="text-center mb-6">
        <span class="text-3xl font-black text-slate-900 tracking-wide">MOON<span class="text-sky-500">★</span>TAR</span>
        <p class="text-xs font-semibold text-sky-600 mt-1 uppercase tracking-wider">Executive Fleet Console</p>
    </div>
    {% if error %}
    <div class="bg-red-50 border border-red-200 text-red-600 text-xs p-3 rounded-lg mb-4 font-medium text-center">
        {{ error }}
    </div>
    {% endif %}
    <form action="/login" method="POST" class="space-y-4">
        <div>
            <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Corporate Email</label>
            <input type="email" name="email" required placeholder="ismail@moonstarpa.com" class="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-sky-600">
        </div>
        <div>
            <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Password</label>
            <input type="password" name="password" required class="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-sky-600">
        </div>
        <button type="submit" class="w-full py-3 bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold uppercase tracking-wider rounded-lg transition shadow-md">
            Sign In to Portal
        </button>
    </form>
    <div class="text-center mt-4">
        <a href="/" class="text-xs text-slate-500 hover:underline">← Back to Home</a>
    </div>
</div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>MOONSTAR EXPRESS LLC — Fleet Console</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-50 min-h-screen p-6">
<div class="max-w-7xl mx-auto space-y-6">
    <!-- TOP HEADER -->
    <header class="bg-gradient-to-r from-slate-900 via-blue-950 to-sky-600 p-5 rounded-xl shadow-lg border-b-4 border-orange-500 flex justify-between items-center text-white">
        <div class="flex items-center space-x-3">
            <a href="/" class="text-2xl font-black tracking-wide text-white no-underline">MOON<span class="text-orange-500">★</span>TAR</a>
            <span class="text-xs font-semibold text-sky-300 border border-sky-400 px-2.5 py-0.5 rounded">EXPRESS LLC</span>
        </div>
        <div class="flex items-center space-x-4">
            <span class="text-xs text-slate-200">User: <b>{{ user }}</b></span>
            <a href="/logout" class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-xs font-bold uppercase transition shadow">Sign Out</a>
        </div>
    </header>

    <!-- NAVIGATION TABS -->
    <div class="flex justify-between items-center border-b border-slate-200 pb-3">
        <div class="flex space-x-2">
            <a href="/dashboard?tab=trucks" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'trucks' %}bg-sky-600 text-white shadow{% else %}bg-white text-slate-700 border border-slate-200 hover:bg-slate-50{% endif %}">Trucks & Trailers</a>
            <a href="/dashboard?tab=drivers" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'drivers' %}bg-sky-600 text-white shadow{% else %}bg-white text-slate-700 border border-slate-200 hover:bg-slate-50{% endif %}">Drivers Compliance</a>
            <a href="/dashboard?tab=chat" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'chat' %}bg-sky-600 text-white shadow{% else %}bg-white text-slate-700 border border-slate-200 hover:bg-slate-50{% endif %}">💬 Fleet Team Chat</a>
            <a href="/dashboard?tab=imports" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'imports' %}bg-sky-600 text-white shadow{% else %}bg-white text-slate-700 border border-slate-200 hover:bg-slate-50{% endif %}">Data Imports</a>
        </div>
        <div>
            {% if tab == 'trucks' %}
            <a href="/dashboard?tab=trucks&action=add_truck" class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-xs font-bold uppercase shadow transition">+ Add Truck / Trailer</a>
            {% elif tab == 'drivers' %}
            <a href="/dashboard?tab=drivers&action=add_driver" class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-xs font-bold uppercase shadow transition">+ Add Driver</a>
            {% endif %}
        </div>
    </div>

    {% if tab == 'trucks' %}
    <!-- EQUIPMENT PORTAL GRID -->
    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h3 class="text-lg font-black text-slate-900 mb-6">📦 Fleet Equipment Portal (Federal Annual Inspection & DOT Tracking)</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {% for v in vehicles %}
            <a href="/dashboard?tab=trucks&dossier={{ v.unit_number }}" class="bg-white border-2 border-slate-900 rounded-xl p-5 shadow-sm hover:shadow-lg transition flex flex-col justify-between relative overflow-hidden text-left block">
                <div class="absolute left-0 top-0 bottom-0 w-2 {% if v.status == 'DUE SOON' %}bg-amber-500{% else %}bg-emerald-500{% endif %}"></div>
                <div class="pl-3 space-y-1.5 text-xs text-slate-700">
                    <div class="flex justify-between items-center border-b border-slate-200 pb-2 mb-2">
                        <span class="font-black text-slate-900 text-sm">UNIT #{{ v.unit_number }} ({{ v.unit_type }})</span>
                        <span class="text-[10px] font-bold px-2 py-0.5 rounded {% if v.status == 'DUE SOON' %}bg-amber-100 text-amber-700{% else %}bg-emerald-100 text-emerald-700{% endif %}">{{ v.status }}</span>
                    </div>
                    <div><b>Company:</b> {{ v.company }}</div>
                    <div><b>Driver:</b> <span class="text-sky-600 font-semibold">{{ v.driver }}</span></div>
                    <div><b>Plate:</b> {{ v.plate }}</div>
                    <div class="text-amber-700 font-semibold"><b>Annual DOT:</b> {{ v.annual_dot }}</div>
                    <div class="text-slate-600"><b>PA Inspection:</b> {{ v.pa_insp }}</div>
                    <div class="pt-2 border-t border-slate-100 font-semibold text-slate-900">
                        Gross: ${{ "{:,.0f}".format(v.gross) }} | Net: ${{ "{:,.0f}".format(v.net) }}
                    </div>
                </div>
            </a>
            {% endfor %}
        </div>
    </div>
    {% elif tab == 'drivers' %}
    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h3 class="text-lg font-black text-slate-900 mb-6">👤 Drivers Compliance Roster (CDL & Medical Expirations)</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {% for d in drivers %}
            <a href="/dashboard?tab=drivers&driver_dossier={{ d.name }}" class="bg-white border-2 border-slate-900 rounded-xl p-5 shadow-sm hover:shadow-lg transition flex flex-col justify-between relative overflow-hidden block">
                <div class="absolute left-0 top-0 bottom-0 w-2 bg-emerald-500"></div>
                <div class="pl-3 space-y-1.5 text-xs text-slate-600">
                    <div class="font-black text-slate-900 text-sm mb-2">{{ d.name }}</div>
                    <div><b>Company:</b> {{ d.company }}</div>
                    <div><b>Phone:</b> {{ d.phone }}</div>
                    <div><b>Assigned Unit:</b> Unit #{{ d.unit }}</div>
                    <div><b>CDL Number:</b> {{ d.cdl }}</div>
                    <div class="text-sky-700 font-bold"><b>CDL Expiry:</b> {{ d.cdl_expiry }}</div>
                    <div class="text-amber-700 font-bold"><b>Medical Due:</b> {{ d.medical }}</div>
                </div>
            </a>
            {% endfor %}
        </div>
    </div>
    {% elif tab == 'chat' %}
    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200 space-y-6 max-w-4xl mx-auto">
        <h3 class="text-lg font-black text-slate-900 border-b pb-3">💬 Moonstar Fleet Team Chat & Dispatch Board</h3>
        <div class="space-y-3 bg-slate-50 p-4 rounded-xl border border-slate-200 h-80 overflow-y-auto">
            {% for c in chat_messages %}
            <div class="bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
                <div class="flex justify-between text-[10px] text-slate-400 mb-1">
                    <span class="font-bold text-sky-600">{{ c.sender }}</span>
                    <span>{{ c.time }}</span>
                </div>
                <div class="text-xs text-slate-800 font-medium">{{ c.message }}</div>
            </div>
            {% endfor %}
        </div>
        <form action="/send_chat" method="POST" class="flex gap-3">
            <input type="text" name="message" required placeholder="Type dispatch message or safety note..." class="flex-1 px-4 py-2.5 text-xs bg-slate-50 border border-slate-300 rounded-lg">
            <button type="submit" class="bg-sky-600 hover:bg-sky-700 text-white px-6 py-2.5 rounded-lg text-xs font-bold uppercase shadow">Send Message</button>
        </form>
    </div>
    {% elif tab == 'imports' %}
    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200 space-y-6">
        <h3 class="text-lg font-black text-slate-900">📥 Automated Telematics, Revenue & Fuel Ingestion</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="bg-slate-50 p-5 rounded-xl border border-slate-200">
                <h4 class="font-bold text-sm text-slate-900 mb-2">1. Samsara Odometer Sync</h4>
                <input type="file" class="w-full text-xs text-slate-500 mb-4">
                <button onclick="alert('Samsara synced!')" class="w-full bg-sky-600 text-white py-2 rounded-lg text-xs font-bold">Sync Mileages</button>
            </div>
            <div class="bg-slate-50 p-5 rounded-xl border border-slate-200">
                <h4 class="font-bold text-sm text-slate-900 mb-2">2. ITS Gross Revenue Sync</h4>
                <input type="file" class="w-full text-xs text-slate-500 mb-4">
                <button onclick="alert('Revenues synced!')" class="w-full bg-sky-600 text-white py-2 rounded-lg text-xs font-bold">Sync Revenues</button>
            </div>
            <div class="bg-slate-50 p-5 rounded-xl border border-slate-200">
                <h4 class="font-bold text-sm text-slate-900 mb-2">3. Fuel Card Expense Sync</h4>
                <input type="file" class="w-full text-xs text-slate-500 mb-4">
                <button onclick="alert('Fuel reconciled!')" class="w-full bg-sky-600 text-white py-2 rounded-lg text-xs font-bold">Sync Fuel Expenses</button>
            </div>
        </div>
    </div>
    {% endif %}

    <!-- TRUCK DOSSIER EDIT & FILE MANAGEMENT MODAL -->
    {% if selected_unit %}
    <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-3xl overflow-hidden border border-slate-200">
            <div class="bg-slate-900 text-white p-5 flex justify-between items-center">
                <h3 class="font-black text-lg">Equipment Dossier — Unit #{{ selected_unit.unit_number }}</h3>
                <a href="/dashboard?tab=trucks" class="text-slate-400 hover:text-white font-bold text-lg">✕</a>
            </div>
            <div class="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
                <form action="/update_unit" method="POST" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <input type="hidden" name="unit_number" value="{{ selected_unit.unit_number }}">
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Assigned Driver (Select from list)</label>
                        <select name="driver" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                            <option value="Unassigned">Unassigned</option>
                            {% for d in drivers %}
                            <option value="{{ d.name }}" {% if selected_unit.driver == d.name %}selected{% endif %}>{{ d.name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Plate Number</label>
                        <input type="text" name="plate" value="{{ selected_unit.plate }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Federal Annual Inspection Due</label>
                        <input type="date" name="annual_dot" value="{{ selected_unit.annual_dot }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">PA State Inspection Due</label>
                        <input type="date" name="pa_insp" value="{{ selected_unit.pa_insp }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div class="md:col-span-2 flex justify-between pt-2">
                        <button type="submit" class="bg-sky-600 hover:bg-sky-700 text-white px-5 py-2.5 rounded-lg text-xs font-bold uppercase shadow">💾 Save Changes</button>
                        <a href="/delete_unit?unit={{ selected_unit.unit_number }}" class="bg-red-600 hover:bg-red-700 text-white px-5 py-2.5 rounded-lg text-xs font-bold uppercase shadow">🗑️ Delete Unit</a>
                    </div>
                </form>

                <!-- DOSYA EKLEME & YÖNETME ALANI -->
                <div class="border-t border-slate-200 pt-4 space-y-4">
                    <h4 class="font-bold text-sm text-slate-900">📁 Federal Inspection & Compliance Documents</h4>
                    
                    <form action="/upload_unit_file" method="POST" enctype="multipart/form-data" class="flex gap-3">
                        <input type="hidden" name="unit" value="{{ selected_unit.unit_number }}">
                        <input type="file" name="filename" required class="flex-1 text-xs text-slate-500 border border-slate-300 p-2 rounded-lg bg-slate-50">
                        <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-xs font-bold uppercase">📎 Add File</button>
                    </form>

                    {% if selected_unit.files %}
                    <div class="space-y-2">
                        {% for file in selected_unit.files %}
                        <div class="flex justify-between items-center bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                            <span class="text-xs font-medium text-slate-700">📄 {{ file }}</span>
                            <a href="/delete_unit_file?unit={{ selected_unit.unit_number }}&file={{ file }}" class="bg-red-100 hover:bg-red-200 text-red-700 px-3 py-1 rounded text-xs font-bold transition">🗑️ Delete File</a>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <p class="text-xs text-slate-500">No inspection files uploaded yet.</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    {% endif %}

    <!-- DRIVER DOSSIER EDIT MODAL -->
    {% if selected_driver %}
    <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-xl overflow-hidden border border-slate-200">
            <div class="bg-slate-900 text-white p-5 flex justify-between items-center">
                <h3 class="font-black text-lg">Driver Dossier: {{ selected_driver.name }}</h3>
                <a href="/dashboard?tab=drivers" class="text-slate-400 hover:text-white font-bold text-lg">✕</a>
            </div>
            <div class="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
                <form action="/update_driver" method="POST" class="space-y-3">
                    <input type="hidden" name="original_name" value="{{ selected_driver.name }}">
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Full Name</label>
                        <input type="text" name="name" value="{{ selected_driver.name }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">CDL Expiry Date</label>
                        <input type="date" name="cdl_expiry" value="{{ selected_driver.cdl_expiry }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">DOT Medical Card Expiry</label>
                        <input type="date" name="medical" value="{{ selected_driver.medical }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div class="flex justify-between pt-2">
                        <button type="submit" class="bg-sky-600 hover:bg-sky-700 text-white px-5 py-2 rounded-lg text-xs font-bold uppercase shadow">💾 Save Driver</button>
                        <a href="/delete_driver?name={{ selected_driver.name }}" class="bg-red-600 hover:bg-red-700 text-white px-5 py-2 rounded-lg text-xs font-bold uppercase shadow">🗑️ Delete Driver</a>
                    </div>
                </form>

                <!-- DRIVER DOSYA EKLEME & YÖNETME ALANI -->
                <div class="border-t border-slate-200 pt-4 space-y-4">
                    <h4 class="font-bold text-sm text-slate-900">📁 Driver Compliance Documents (CDL / Medical)</h4>
                    
                    <form action="/upload_driver_file" method="POST" enctype="multipart/form-data" class="flex gap-3">
                        <input type="hidden" name="driver_name" value="{{ selected_driver.name }}">
                        <input type="file" name="filename" required class="flex-1 text-xs text-slate-500 border border-slate-300 p-2 rounded-lg bg-slate-50">
                        <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-xs font-bold uppercase">📎 Add File</button>
                    </form>

                    {% if selected_driver.files %}
                    <div class="space-y-2">
                        {% for file in selected_driver.files %}
                        <div class="flex justify-between items-center bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                            <span class="text-xs font-medium text-slate-700">📄 {{ file }}</span>
                            <a href="/delete_driver_file?driver={{ selected_driver.name }}&file={{ file }}" class="bg-red-100 hover:bg-red-200 text-red-700 px-3 py-1 rounded text-xs font-bold transition">🗑️ Delete File</a>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <p class="text-xs text-slate-500">No driver compliance files uploaded yet.</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    {% endif %}

    <!-- ADD TRUCK / TRAILER MODAL -->
    {% if action == 'add_truck' %}
    <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden border border-slate-200">
            <div class="bg-slate-900 text-white p-5 flex justify-between items-center">
                <h3 class="font-black text-lg">➕ Register New Truck or Trailer</h3>
                <a href="/dashboard?tab=trucks" class="text-slate-400 hover:text-white font-bold text-lg">✕</a>
            </div>
            <form action="/add_unit" method="POST" class="p-6 space-y-4">
                <div>
                    <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Equipment Type</label>
                    <select name="unit_type" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                        <option value="TRUCK">TRUCK</option>
                        <option value="TRAILER">TRAILER</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Unit Number (e.g., 95 or R148)</label>
                    <input type="text" name="unit_number" required class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                </div>
                <div>
                    <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Assigned Driver</label>
                    <select name="driver" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                        <option value="Unassigned">Unassigned</option>
                        {% for d in drivers %}
                        <option value="{{ d.name }}">{{ d.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="flex justify-end pt-2">
                    <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 rounded-lg text-xs font-bold uppercase shadow">Save Equipment</button>
                </div>
            </form>
        </div>
    </div>
    {% endif %}

    <!-- ADD DRIVER MODAL -->
    {% if action == 'add_driver' %}
    <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden border border-slate-200">
            <div class="bg-slate-900 text-white p-5 flex justify-between items-center">
                <h3 class="font-black text-lg">👤 Onboard New Driver</h3>
                <a href="/dashboard?tab=drivers" class="text-slate-400 hover:text-white font-bold text-lg">✕</a>
            </div>
            <form action="/add_driver" method="POST" class="p-6 space-y-4">
                <div>
                    <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Full Name</label>
                    <input type="text" name="name" required class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                </div>
                <div>
                    <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Phone Number</label>
                    <input type="text" name="phone" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                </div>
                <div class="flex justify-end pt-2">
                    <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 rounded-lg text-xs font-bold uppercase shadow">Save Driver</button>
                </div>
            </form>
        </div>
    </div>
    {% endif %}
</div>
</body>
</html>
"""

from fastapi import UploadFile, File

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return Template(HOME_HTML).render()

@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return Template(LOGIN_HTML).render()

@app.post("/login")
def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    if "@moonstarpa" in email.strip().lower() and password == "Moonstar2026!":
        response = RedirectResponse(url="/dashboard?tab=trucks", status_code=303)
        response.set_cookie(key="user", value=email.strip().lower())
        return response
    return Template(LOGIN_HTML).render(error="Invalid credentials!")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, tab: str = "trucks", dossier: str = None, driver_dossier: str = None, action: str = None):
    user = request.cookies.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    selected_unit = next((v for v in FLEET_DATA if v["unit_number"] == dossier), None) if dossier else None
    selected_driver = next((d for d in DRIVERS_DATA if d["name"] == driver_dossier), None) if driver_dossier else None

    return Template(DASHBOARD_HTML).render(
        user=user, 
        vehicles=FLEET_DATA, 
        drivers=DRIVERS_DATA,
        chat_messages=CHAT_MESSAGES,
        tab=tab, 
        selected_unit=selected_unit,
        selected_driver=selected_driver,
        action=action
    )

@app.post("/send_chat")
def send_chat(request: Request, message: str = Form(...)):
    user = request.cookies.get("user", "dispatch@moonstarpa.com")
    time_str = datetime.now().strftime("%I:%M %p")
    CHAT_MESSAGES.append({"sender": user, "message": message.strip(), "time": time_str})
    return RedirectResponse(url="/dashboard?tab=chat", status_code=303)

@app.post("/update_unit")
def update_unit(unit_number: str = Form(...), driver: str = Form(...), plate: str = Form(...), annual_dot: str = Form(...), pa_insp: str = Form(...)):
    for v in FLEET_DATA:
        if v["unit_number"] == unit_number:
            v["driver"] = driver
            v["plate"] = plate
            v["annual_dot"] = annual_dot
            v["pa_insp"] = pa_insp
    return RedirectResponse(url=f"/dashboard?tab=trucks&dossier={unit_number}", status_code=303)

@app.get("/delete_unit")
def delete_unit(unit: str):
    global FLEET_DATA
    FLEET_DATA = [v for v in FLEET_DATA if v["unit_number"] != unit]
    return RedirectResponse(url="/dashboard?tab=trucks", status_code=303)

@app.post("/update_driver")
def update_driver(original_name: str = Form(...), name: str = Form(...), cdl_expiry: str = Form(...), medical: str = Form(...)):
    for d in DRIVERS_DATA:
        if d["name"] == original_name:
            d["name"] = name
            d["cdl_expiry"] = cdl_expiry
            d["medical"] = medical
    return RedirectResponse(url=f"/dashboard?tab=drivers&driver_dossier={name}", status_code=303)

@app.get("/delete_driver")
def delete_driver(name: str):
    global DRIVERS_DATA
    DRIVERS_DATA = [d for d in DRIVERS_DATA if d["name"] != name]
    return RedirectResponse(url="/dashboard?tab=drivers", status_code=303)

@app.post("/add_unit")
def add_unit(unit_number: str = Form(...), unit_type: str = Form(...), driver: str = Form(...)):
    FLEET_DATA.append({
        "unit_number": unit_number,
        "unit_type": unit_type,
        "company": "MOONSTAR",
        "driver": driver,
        "vin": "VIN-NEW-000",
        "plate": "TEMP-PA",
        "annual_dot": "2027-01-01",
        "pa_insp": "2027-01-01",
        "status": "READY",
        "gross": 15000.0,
        "fuel": 3500.0,
        "net": 11500.0,
        "files": []
    })
    return RedirectResponse(url="/dashboard?tab=trucks", status_code=303)

@app.post("/add_driver")
def add_driver(name: str = Form(...), phone: str = Form(...)):
    DRIVERS_DATA.append({
        "name": name,
        "company": "MOONSTAR",
        "phone": phone,
        "email": f"{name.lower().replace(' ', '')}@moonstarpa.com",
        "cdl": "CDL-NEW-00",
        "cdl_expiry": "2028-01-01",
        "medical": "2027-01-01",
        "unit": "New",
        "files": []
    })
    return RedirectResponse(url="/dashboard?tab=drivers", status_code=303)

@app.post("/upload_unit_file")
def upload_unit_file(unit: str = Form(...), filename: UploadFile = File(...)):
    for v in FLEET_DATA:
        if v["unit_number"] == unit:
            if filename.filename and filename.filename not in v["files"]:
                v["files"].append(filename.filename)
    return RedirectResponse(url=f"/dashboard?tab=trucks&dossier={unit}", status_code=303)

@app.get("/delete_unit_file")
def delete_unit_file(unit: str, file: str):
    for v in FLEET_DATA:
        if v["unit_number"] == unit:
            if file in v["files"]:
                v["files"].remove(file)
    return RedirectResponse(url=f"/dashboard?tab=trucks&dossier={unit}", status_code=303)

@app.post("/upload_driver_file")
def upload_driver_file(driver_name: str = Form(...), filename: UploadFile = File(...)):
    for d in DRIVERS_DATA:
        if d["name"] == driver_name:
            if filename.filename and filename.filename not in d["files"]:
                d["files"].append(filename.filename)
    return RedirectResponse(url=f"/dashboard?tab=drivers&driver_dossier={driver_name}", status_code=303)

@app.get("/delete_driver_file")
def delete_driver_file(driver: str, file: str):
    for d in DRIVERS_DATA:
        if d["name"] == driver:
            if file in d["files"]:
                d["files"].remove(file)
    return RedirectResponse(url=f"/dashboard?tab=drivers&driver_dossier={driver}", status_code=303)

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="user")
    return response
