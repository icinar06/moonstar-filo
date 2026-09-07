import os
import pandas as pd
from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Template
from datetime import datetime

app = FastAPI(title="MOONSTAR EXPRESS LLC — Executive Fleet Console")

# --- EXCEL DOSYALARINDAN TÜM VERİLERİ OTOMATİK OKUYAN FONKSİYONLAR ---
def load_all_data():
    trucks = []
    trailers = []
    drivers = []

    # 1. Trucks.xlsx
    if os.path.exists("Trucks.xlsx"):
        try:
            df_t = pd.read_excel("Trucks.xlsx", sheet_name=0)
            for _, r in df_t.iterrows():
                num = str(r.get("Number", "")).strip()
                if num and num.lower() != "nan":
                    trucks.append({
                        "unit": num,
                        "type": str(r.get("Type", "Truck")).strip(),
                        "plate": str(r.get("Plate Number", "-")).strip(),
                        "plate_expiry": str(r.get("Plate Expiry", "-")).strip()[:10],
                        "dot_insp": str(r.get("DOT Inspection Date", "-")).strip()[:10],
                        "annual_insp": str(r.get("Truck Annual Inspection Date", "-")).strip()[:10],
                        "vin": str(r.get("VIN", "-")).strip(),
                        "driver": "Unassigned",
                        "trailer": "None",
                        "files": []
                    })
        except Exception as e:
            print("Error reading Trucks.xlsx:", e)

    # 2. Trailers.xlsx
    if os.path.exists("Trailers.xlsx"):
        try:
            df_tr = pd.read_excel("Trailers.xlsx", sheet_name=0)
            for _, r in df_tr.iterrows():
                num = str(r.get("Number", "")).strip()
                if num and num.lower() != "nan":
                    trailers.append({
                        "unit": num,
                        "type": str(r.get("Type", "Trailer")).strip(),
                        "plate": str(r.get("Plate Number", "-")).strip(),
                        "plate_expiry": str(r.get("Plate Expiry", "-")).strip()[:10],
                        "annual_insp": str(r.get("Annual Inspection Date", "-")).strip()[:10],
                        "vin": str(r.get("VIN", "-")).strip(),
                        "assigned_truck": "None",
                        "files": []
                    })
        except Exception as e:
            print("Error reading Trailers.xlsx:", e)

    # 3. Drivers (2).xlsx
    if os.path.exists("Drivers (2).xlsx"):
        try:
            df_d = pd.read_excel("Drivers (2).xlsx", sheet_name=0)
            for _, r in df_d.iterrows():
                name = str(r.get("Name", "")).strip()
                if name and name.lower() != "nan":
                    drivers.append({
                        "name": name,
                        "phone": str(r.get("Telephone", "-")).strip(),
                        "email": str(r.get("E-mail", "-")).strip(),
                        "cdl": str(r.get("License Number", "-")).strip(),
                        "cdl_expiry": str(r.get("License Expiry", "-")).strip()[:10],
                        "medical": str(r.get("Next Medical", "-")).strip()[:10],
                        "truck": "Unassigned",
                        "trailer": "None",
                        "files": []
                    })
        except Exception as e:
            print("Error reading Drivers (2).xlsx:", e)

    # Eğer dosyalar boşsa varsayılan test verisi
    if not trucks:
        trucks = [{"unit": "8", "type": "VOLVO", "plate": "AH35700 PA", "plate_expiry": "2027-05-31", "dot_insp": "2026-10-26", "annual_insp": "2026-10-26", "vin": "4V4NC9EH", "driver": "AT YARD", "trailer": "None", "files": []}]
    if not drivers:
        drivers = [{"name": "AT YARD", "phone": "215-555-0144""215-555-0144", "email": "yard@moonstarpa.com", "cdl": "PA-334112", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "8", "trailer": "None", "files": []}]
    if not trailers:
        trailers = [{"unit": "R14782", "type": "Dry Van", "plate": "31-19733 ME", "plate_expiry": "2031-02-28", "annual_insp": "2026-07-27", "vin": "3AWF1VT", "assigned_truck": "8", "files": []}]

    return trucks, trailers, drivers

TRUCKS_DATA, TRAILERS_DATA, DRIVERS_DATA = load_all_data()
CHAT_MESSAGES = [{"sender": "ismail@moonstarpa.com", "message": "All Master Excel data successfully synchronized into the console.", "time": "10:00 AM"}]

HOME_HTML = """




MOONSTAR EXPRESS LLC — Reliable Transportation


body { font-family: 'Inter', sans-serif; } .brand-font { font-family: 'Montserrat', sans-serif; }


    
        
            MOON★TAR
            EXPRESS LLC
        
        
            Home
            About Us
            Contact Us
            Services
        
    
    
        
            
        
        
            RELIABLE TRANSPORTATION SOLUTIONS
            Your trusted partner for safe and efficient travel across the United States.
            
                Sign In
                📞 +1 215-666-0595
            
        
    
    
        
            🔐 Launch Executive Fleet Console →
        
    
    © 2026 Moonstar Express LLC.


""""""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>MOONSTAR EXPRESS LLC — Reliable Transportation</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>body { font-family: 'Inter', sans-serif; } .brand-font { font-family: 'Montserrat', sans-serif; }</style>
</head>
<body class="min-h-screen flex flex-col justify-between bg-white">
    <header class="border-b border-slate-200 px-8 py-4 flex justify-between items-center shadow-sm">
        <div class="flex items-center space-x-3">
            <span class="brand-font text-2xl font-black text-slate-900">MOON<span class="text-sky-500">★</span>TAR</span>
            <span class="text-xs font-semibold text-sky-600 border border-sky-600 px-2 py-0.5 rounded">EXPRESS LLC</span>
        </div>
        <nav class="hidden md:flex items-center space-x-8 text-xs font-bold uppercase tracking-wider text-slate-700">
            <a href="/" class="text-sky-600 border-b-2 border-sky-600 pb-1">Home</a>
            <a href="#" class="hover:text-sky-600 transition">About Us</a>
            <a href="#" class="hover:text-sky-600 transition">Contact Us</a>
            <a href="#" class="hover:text-sky-600 transition">Services</a>
        </nav>
    </header>
    <main class="max-w-7xl mx-auto px-6 py-12 w-full grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div class="rounded-2xl overflow-hidden shadow-2xl">
            <img src="https://images.unsplash.com/photo-1519003722824-194d4455a60c?auto=format&fit=crop&w=1200&q=80" alt="Fleet" class="w-full h-[400px] object-cover">
        </div>
        <div class="bg-slate-900 text-white p-12 rounded-2xl shadow-xl">
            <h1 class="brand-font text-4xl font-black mb-4 leading-tight">RELIABLE TRANSPORTATION SOLUTIONS</h1>
            <p class="text-slate-400 text-sm mb-8">Your trusted partner for safe and efficient travel across the United States.</p>
            <div class="flex items-center justify-between">
                <a href="/login" class="bg-white text-slate-900 hover:bg-slate-100 px-8 py-3 rounded-lg text-xs font-bold uppercase tracking-wider transition shadow">Sign In</a>
                <div class="text-sky-400 font-bold text-sm">📞 +1 215-666-0595</div>
            </div>
        </div>
    </main>
    <div class="bg-slate-50 border-t border-slate-200 py-6 text-center">
        <a href="/login" class="text-sky-600 font-bold text-xs uppercase tracking-widest bg-sky-50 border border-sky-200 px-6 py-3 rounded-xl inline-block shadow-sm">
            🔐 Launch Executive Fleet Console →
        </a>
    </div>
    <footer class="border-t border-slate-200 py-6 text-center text-xs text-slate-500">&copy; 2026 Moonstar Express LLC.</footer>
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
        <span class="text-3xl font-black text-slate-900">MOON<span class="text-sky-500">★</span>TAR</span>
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
    <div class="text-center mt-4"><a href="/" class="text-xs text-slate-500 hover:underline">← Back to Home</a></div>
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
<body class="bg-slate-50 min-h-screen p-6">
<div class="max-w-7xl mx-auto space-y-6">
    <!-- TOP HEADER WITH LOGO -->
    <header class="bg-gradient-to-r from-slate-900 via-blue-950 to-sky-600 p-5 rounded-xl shadow-lg border-b-4 border-orange-500 flex justify-between items-center text-white">
        <div class="flex items-center space-x-3">
            <a href="/dashboard?tab=home" class="brand-font text-2xl font-black tracking-wide text-white no-underline">MOON<span class="text-orange-500">★</span>TAR</a>
            <span class="text-xs font-semibold text-sky-300 border border-sky-400 px-2.5 py-0.5 rounded">EXPRESS LLC</span>
        </div>
        <div class="flex items-center space-x-4">
            <span class="text-xs text-slate-200">User: <b>{{ user }}</b></span>
            <a href="/logout" class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-xs font-bold uppercase shadow">Sign Out</a>
        </div>
    </header>

    <!-- NAVIGATION TABS -->
    <div class="flex space-x-2 border-b border-slate-200 pb-3">
        <a href="/dashboard?tab=home" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'home' %}bg-sky-600 text-white shadow{% else %}bg-white text-slate-700 border border-slate-200{% endif %}">🏠 Home / Alerts</a>
        <a href="/dashboard?tab=trucks" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'trucks' %}bg-sky-600 text-white shadow{% else %}bg-white text-slate-700 border border-slate-200{% endif %}">🚛 Trucks Master</a>
        <a href="/dashboard?tab=trailers" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'trailers' %}bg-sky-600 text-white shadow{% else %}bg-white text-slate-700 border border-slate-200{% endif %}">📦 Trailers Master</a>
        <a href="/dashboard?tab=drivers" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'drivers' %}bg-sky-600 text-white shadow{% else %}bg-white text-slate-700 border border-slate-200{% endif %}">👤 Drivers Roster</a>
        <a href="/dashboard?tab=chat" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'chat' %}bg-sky-600 text-white shadow{% else %}bg-white text-slate-700 border border-slate-200{% endif %}">💬 Fleet Team Chat</a>
    </div>

    {% if tab == 'home' %}
    <!-- HOME / ALERTS DASHBOARD -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-white p-5 rounded-xl border-l-4 border-sky-600 shadow-sm">
            <div class="text-xs font-bold uppercase text-slate-500">Total Registered Trucks</div>
            <div class="text-3xl font-black text-sky-600 mt-2">{{ trucks|length }}</div>
        </div>
        <div class="bg-white p-5 rounded-xl border-l-4 border-orange-500 shadow-sm">
            <div class="text-xs font-bold uppercase text-slate-500">Total Active Trailers</div>
            <div class="text-3xl font-black text-orange-600 mt-2">{{ trailers|length }}</div>
        </div>
        <div class="bg-white p-5 rounded-xl border-l-4 border-emerald-600 shadow-sm">
            <div class="text-xs font-bold uppercase text-slate-500">Total Active Drivers</div>
            <div class="text-3xl font-black text-emerald-600 mt-2">{{ drivers|length }}</div>
        </div>
    </div>
    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200 space-y-4">
        <h3 class="text-lg font-black text-slate-900">🚨 Fleet Compliance & Expiration Alerts</h3>
        <p class="text-xs text-slate-500">Overview of trucks, trailers, and drivers requiring attention.</p>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div class="bg-amber-50 p-4 rounded-xl border border-amber-200 space-y-2">
                <h4 class="font-bold text-amber-900 text-sm">🚚 Trucks / Trailers Inspection Watch</h4>
                {% for t in trucks[:6] %}
                <div class="flex justify-between bg-white p-2 rounded border border-amber-100">
                    <span><b>Unit #{{ t.unit }}</b> ({{ t.type }})</span>
                    <span class="text-amber-700 font-bold">DOT: {{ t.dot_insp }}</span>
                </div>
                {% endfor %}
            </div>
            <div class="bg-sky-50 p-4 rounded-xl border border-sky-200 space-y-2">
                <h4 class="font-bold text-sky-900 text-sm">👤 Drivers CDL & Medical Watch</h4>
                {% for d in drivers[:6] %}
                <div class="flex justify-between bg-white p-2 rounded border border-sky-100">
                    <span><b>{{ d.name }}</b></span>
                    <span class="text-sky-700 font-bold">Medical: {{ d.medical }}</span>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    {% elif tab == 'trucks' %}
    <!-- TRUCKS TABLE (ŞIK TABLO YAPISI) -->
    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200 space-y-4">
        <div class="flex justify-between items-center">
            <h3 class="text-lg font-black text-slate-900">🚛 Master Trucks Inventory ({{ trucks|length }} Units)</h3>
            <span class="text-xs text-slate-500">Click any unit row to assign driver, trailer, or manage files.</span>
        </div>
        <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse text-xs">
                <thead>
                    <tr class="bg-slate-900 text-white">
                        <th class="p-3">Unit #</th>
                        <th class="p-3">Make / Model</th>
                        <th class="p-3">Plate & Expiry</th>
                        <th class="p-3">Annual DOT</th>
                        <th class="p-3">Assigned Driver</th>
                        <th class="p-3">Hooked Trailer</th>
                        <th class="p-3 text-right">Action</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-200">
                    {% for t in trucks %}
                    <tr class="hover:bg-slate-50">
                        <td class="p-3 font-black text-slate-900">#{{ t.unit }}</td>
                        <td class="p-3 text-slate-700">{{ t.type }}</td>
                        <td class="p-3 text-slate-600">{{ t.plate }} <br><span class="text-[10px] text-slate-400">Exp: {{ t.plate_expiry }}</span></td>
                        <td class="p-3 font-semibold text-amber-700">{{ t.dot_insp }}</td>
                        <td class="p-3 font-bold text-sky-600">{{ t.driver }}</td>
                        <td class="p-3 font-bold text-orange-600">{{ t.trailer }}</td>
                        <td class="p-3 text-right">
                            <a href="/dashboard?tab=trucks&dossier={{ t.unit }}" class="bg-sky-50 text-sky-600 border border-sky-200 px-3 py-1.5 rounded-lg font-bold hover:bg-sky-600 hover:text-white transition">Manage Dossier →</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% elif tab == 'trailers' %}
    <!-- TRAILERS TABLE -->
    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200 space-y-4">
        <div class="flex justify-between items-center">
            <h3 class="text-lg font-black text-slate-900">📦 Master Trailers Inventory ({{ trailers|length }} Units)</h3>
            <span class="text-xs text-slate-500">Click unit to view assigned truck and inspection info.</span>
        </div>
        <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse text-xs">
                <thead>
                    <tr class="bg-slate-900 text-white">
                        <th class="p-3">Unit #</th>
                        <th class="p-3">Trailer Type</th>
                        <th class="p-3">Plate & Expiry</th>
                        <th class="p-3">Annual Inspection</th>
                        <th class="p-3">Assigned Truck</th>
                        <th class="p-3 text-right">Action</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-200">
                    {% for tr in trailers %}
                    <tr class="hover:bg-slate-50">
                        <td class="p-3 font-black text-slate-900">#{{ tr.unit }}</td>
                        <td class="p-3 text-slate-700">{{ tr.type }}</td>
                        <td class="p-3 text-slate-600">{{ tr.plate }} <br><span class="text-[10px] text-slate-400">Exp: {{ tr.plate_expiry }}</span></td>
                        <td class="p-3 font-semibold text-amber-700">{{ tr.annual_insp }}</td>
                        <td class="p-3 font-bold text-sky-600">Truck #{{ tr.assigned_truck }}</td>
                        <td class="p-3 text-right">
                            <a href="/dashboard?tab=trailers&trailer_dossier={{ tr.unit }}" class="bg-orange-50 text-orange-600 border border-orange-200 px-3 py-1.5 rounded-lg font-bold hover:bg-orange-600 hover:text-white transition">Manage Unit →</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% elif tab == 'drivers' %}
    <!-- DRIVERS TABLE -->
    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200 space-y-4">
        <div class="flex justify-between items-center">
            <h3 class="text-lg font-black text-slate-900">👤 Master Drivers Roster ({{ drivers|length }} Active Drivers)</h3>
            <span class="text-xs text-slate-500">Click driver row for CDL, medical records, and truck/trailer assignment.</span>
        </div>
        <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse text-xs">
                <thead>
                    <tr class="bg-slate-900 text-white">
                        <th class="p-3">Driver Name</th>
                        <th class="p-3">Phone & Email</th>
                        <th class="p-3">CDL Number & Expiry</th>
                        <th class="p-3">DOT Medical Due</th>
                        <th class="p-3">Assigned Truck</th>
                        <th class="p-3 text-right">Action</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-200">
                    {% for d in drivers %}
                    <tr class="hover:bg-slate-50">
                        <td class="p-3 font-black text-slate-900">{{ d.name }}</td>
                        <td class="p-3 text-slate-600">{{ d.phone }} <br><span class="text-[10px] text-slate-400">{{ d.email }}</span></td>
                        <td class="p-3 text-slate-700">{{ d.cdl }} <br><span class="text-[10px] text-sky-600 font-bold">Exp: {{ d.cdl_expiry }}</span></td>
                        <td class="p-3 font-bold text-amber-700">{{ d.medical }}</td>
                        <td class="p-3 font-bold text-sky-600">Truck #{{ d.truck }}</td>
                        <td class="p-3 text-right">
                            <a href="/dashboard?tab=drivers&driver_dossier={{ d.name }}" class="bg-emerald-50 text-emerald-600 border border-emerald-200 px-3 py-1.5 rounded-lg font-bold hover:bg-emerald-600 hover:text-white transition">Driver Dossier →</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
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
            <input type="text" name="message" required placeholder="Type dispatch message..." class="flex-1 px-4 py-2.5 text-xs bg-slate-50 border border-slate-300 rounded-lg">
            <button type="submit" class="bg-sky-600 text-white px-6 py-2.5 rounded-lg text-xs font-bold uppercase shadow">Send</button>
        </form>
    </div>
    {% endif %}

    <!-- TRUCK DOSSIER MODAL WITH DRIVER & TRAILER ASSIGNMENT -->
    {% if selected_unit %}
    <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden border border-slate-200">
            <div class="bg-slate-900 text-white p-5 flex justify-between items-center">
                <h3 class="font-black text-lg">Truck Dossier — Unit #{{ selected_unit.unit }}</h3>
                <a href="/dashboard?tab=trucks" class="text-slate-400 hover:text-white font-bold text-lg">✕</a>
            </div>
            <div class="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
                <form action="/update_truck" method="POST" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <input type="hidden" name="unit" value="{{ selected_unit.unit }}">
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Assign Driver</label>
                        <select name="driver" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                            <option value="Unassigned">Unassigned</option>
                            {% for d in drivers %}
                            <option value="{{ d.name }}" {% if selected_unit.driver == d.name %}selected{% endif %}>{{ d.name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Hook Trailer</label>
                        <select name="trailer" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                            <option value="None">None</option>
                            {% for tr in trailers %}
                            <option value="{{ tr.unit }}" {% if selected_unit.trailer == tr.unit %}selected{% endif %}>Trailer #{{ tr.unit }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Plate Number</label>
                        <input type="text" name="plate" value="{{ selected_unit.plate }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Federal Annual DOT</label>
                        <input type="text" name="dot_insp" value="{{ selected_unit.dot_insp }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div class="md:col-span-2 flex justify-between pt-2">
                        <button type="submit" class="bg-sky-600 text-white px-5 py-2.5 rounded-lg text-xs font-bold uppercase shadow">💾 Save Truck</button>
                        <a href="/delete_truck?unit={{ selected_unit.unit }}" class="bg-red-600 text-white px-5 py-2.5 rounded-lg text-xs font-bold uppercase shadow">🗑️ Delete</a>
                    </div>
                </form>
                <div class="border-t pt-4 space-y-3">
                    <h4 class="font-bold text-sm text-slate-900">📁 Truck Documents & Compliance Files</h4>
                    <form action="/upload_truck_file" method="POST" enctype="multipart/form-data" class="flex gap-3">
                        <input type="hidden" name="unit" value="{{ selected_unit.unit }}">
                        <input type="file" name="filename" required class="flex-1 text-xs border p-2 rounded-lg bg-slate-50">
                        <button type="submit" class="bg-emerald-600 text-white px-4 py-2 rounded-lg text-xs font-bold">📎 Add File</button>
                    </form>
                    {% for f in selected_unit.files %}
                    <div class="flex justify-between items-center bg-slate-50 p-2 rounded border text-xs">
                        <span>📄 {{ f }}</span>
                        <a href="/delete_truck_file?unit={{ selected_unit.unit }}&file={{ f }}" class="text-red-600 font-bold">Delete</a>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    {% endif %}

    <!-- DRIVER DOSSIER MODAL WITH TRUCK ASSIGNMENT -->
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
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Assign Truck</label>
                        <select name="truck" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                            <option value="Unassigned">Unassigned</option>
                            {% for t in trucks %}
                            <option value="{{ t.unit }}" {% if selected_driver.truck == t.unit %}selected{% endif %}>Truck #{{ t.unit }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">CDL Expiry Date</label>
                        <input type="text" name="cdl_expiry" value="{{ selected_driver.cdl_expiry }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">DOT Medical Card Expiry</label>
                        <input type="text" name="medical" value="{{ selected_driver.medical }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div class="flex justify-between pt-2">
                        <button type="submit" class="bg-sky-600 text-white px-5 py-2 rounded-lg text-xs font-bold uppercase shadow">💾 Save Driver</button>
                        <a href="/delete_driver?name={{ selected_driver.name }}" class="bg-red-600 text-white px-5 py-2 rounded-lg text-xs font-bold uppercase shadow">🗑️ Delete</a>
                    </div>
                </form>
                <div class="border-t pt-4 space-y-3">
                    <h4 class="font-bold text-sm text-slate-900">📁 Driver Compliance Files</h4>
                    <form action="/upload_driver_file" method="POST" enctype="multipart/form-data" class="flex gap-3">
                        <input type="hidden" name="driver_name" value="{{ selected_driver.name }}">
                        <input type="file" name="filename" required class="flex-1 text-xs border p-2 rounded-lg bg-slate-50">
                        <button type="submit" class="bg-emerald-600 text-white px-4 py-2 rounded-lg text-xs font-bold">📎 Add File</button>
                    </form>
                    {% for f in selected_driver.files %}
                    <div class="flex justify-between items-center bg-slate-50 p-2 rounded border text-xs">
                        <span>📄 {{ f }}</span>
                        <a href="/delete_driver_file?driver={{ selected_driver.name }}&file={{ f }}" class="text-red-600 font-bold">Delete</a>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    {% endif %}
</div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return Template(HOME_HTML).render()

@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return Template(LOGIN_HTML).render()

@app.post("/login")
def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    if "@moonstarpa" in email.strip().lower() and password == "Moonstar2026!":
        response = RedirectResponse(url="/dashboard?tab=home", status_code=303)
        response.set_cookie(key="user", value=email.strip().lower())
        return response
    return Template(LOGIN_HTML).render(error="Invalid credentials!")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, tab: str = "home", dossier: str = None, driver_dossier: str = None):
    user = request.cookies.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    selected_unit = next((t for t in TRUCKS_DATA if t["unit"] == dossier), None) if dossier else None
    selected_driver = next((d for d in DRIVERS_DATA if d["name"] == driver_dossier), None) if driver_dossier else None

    return Template(DASHBOARD_HTML).render(
        user=user,
        trucks=TRUCKS_DATA,
        trailers=TRAILERS_DATA,
        drivers=DRIVERS_DATA,
        chat_messages=CHAT_MESSAGES,
        tab=tab,
        selected_unit=selected_unit,
        selected_driver=selected_driver
    )

@app.post("/send_chat")
def send_chat(request: Request, message: str = Form(...)):
    user = request.cookies.get("user", "dispatch@moonstarpa.com")
    time_str = datetime.now().strftime("%I:%M %p")
    CHAT_MESSAGES.append({"sender": user, "message": message.strip(), "time": time_str})
    return RedirectResponse(url="/dashboard?tab=chat", status_code=303)

@app.post("/update_truck")
def update_truck(unit: str = Form(...), driver: str = Form(...), trailer: str = Form(...), plate: str = Form(...), dot_insp: str = Form(...)):
    for t in TRUCKS_DATA:
        if t["unit"] == unit:
            t["driver"] = driver
            t["trailer"] = trailer
            t["plate"] = plate
            t["dot_insp"] = dot_insp
    return RedirectResponse(url=f"/dashboard?tab=trucks&dossier={unit}", status_code=303)

@app.post("/update_driver")
def update_driver(original_name: str = Form(...), name: str = Form(...), truck: str = Form(...), cdl_expiry: str = Form(...), medical: str = Form(...)):
    for d in DRIVERS_DATA:
        if d["name"] == original_name:
            d["name"] = name
            d["truck"] = truck
            d["cdl_expiry"] = cdl_expiry
            d["medical"] = medical
    return RedirectResponse(url=f"/dashboard?tab=drivers&driver_dossier={name}", status_code=303)

@app.post("/upload_truck_file")
def upload_truck_file(unit: str = Form(...), filename: UploadFile = File(...)):
    for t in TRUCKS_DATA:
        if t["unit"] == unit:
            if filename.filename and filename.filename not in t["files"]:
                t["files"].append(filename.filename)
    return RedirectResponse(url=f"/dashboard?tab=trucks&dossier={unit}", status_code=303)

@app.get("/delete_truck_file")
def delete_truck_file(unit: str, file: str):
    for t in TRUCKS_DATA:
        if t["unit"] == unit:
            if file in t["files"]:
                t["files"].remove(file)
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
