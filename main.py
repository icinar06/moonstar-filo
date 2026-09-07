import os
import pandas as pd
from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Template
from datetime import datetime

app = FastAPI(title="MOONSTAR EXPRESS LLC — Executive Fleet Console")

def load_master_data():
    trucks, trailers, drivers = [], [], []

    if os.path.exists("Trucks.xlsx"):
        try:
            df = pd.read_excel("Trucks.xlsx", sheet_name=0)
            for _, r in df.iterrows():
                num = str(r.get("Number", "")).strip()
                if num and num.lower() != "nan":
                    trucks.append({
                        "unit": num,
                        "type": str(r.get("Type", "Truck")).strip(),
                        "plate": str(r.get("Plate Number", "-")).strip(),
                        "plate_expiry": str(r.get("Plate Expiry", "-")).strip()[:10],
                        "dot_insp": str(r.get("DOT Inspection Date", "2026-10-26")).strip()[:10],
                        "vin": str(r.get("VIN", "-")).strip(),
                        "driver": "Unassigned",
                        "trailer": "None",
                        "status": "Active",
                        "gross": 21500.0,
                        "fuel": 4800.0,
                        "maintenance": 650.0,
                        "accident_report": "No accidents reported.",
                        "files": []
                    })
        except:
            pass

    if os.path.exists("Trailers.xlsx"):
        try:
            df = pd.read_excel("Trailers.xlsx", sheet_name=0)
            for _, r in df.iterrows():
                num = str(r.get("Number", "")).strip()
                if num and num.lower() != "nan":
                    trailers.append({
                        "unit": num,
                        "type": str(r.get("Type", "Trailer")).strip(),
                        "plate": str(r.get("Plate Number", "-")).strip(),
                        "plate_expiry": str(r.get("Plate Expiry", "-")).strip()[:10],
                        "annual_insp": str(r.get("Annual Inspection Date", "2026-11-26")).strip()[:10],
                        "vin": str(r.get("VIN", "-")).strip(),
                        "assigned_truck": "None",
                        "files": []
                    })
        except:
            pass

    if os.path.exists("Drivers (2).xlsx"):
        try:
            df = pd.read_excel("Drivers (2).xlsx", sheet_name=0)
            for _, r in df.iterrows():
                name = str(r.get("Name", "")).strip()
                if name and name.lower() != "nan":
                    drivers.append({
                        "name": name,
                        "phone": str(r.get("Telephone", "-")).strip(),
                        "email": str(r.get("E-mail", "-")).strip(),
                        "cdl": str(r.get("License Number", "-")).strip(),
                        "cdl_expiry": str(r.get("License Expiry", "2027-05-31")).strip()[:10],
                        "medical": str(r.get("Next Medical", "2027-01-15")).strip()[:10],
                        "truck": "Unassigned",
                        "accident_report": "Clean record.",
                        "files": []
                    })
        except:
            pass

    if not trucks:
        trucks = [{"unit": "8", "type": "VOLVO", "plate": "AH35700 PA", "plate_expiry": "2027-05-31", "dot_insp": "2026-10-26", "vin": "4V4", "driver": "AT YARD", "trailer": "None", "status": "Active", "gross": 18000.0, "fuel": 4000.0, "maintenance": 300.0, "accident_report": "None", "files": []}]
    if not trailers:
        trailers = [{"unit": "R14782", "type": "Dry Van", "plate": "31-19733 ME", "plate_expiry": "2031-02-28", "annual_insp": "2026-07-27", "vin": "3AW", "assigned_truck": "None", "files": []}]
    if not drivers:
        drivers = [{"name": "AT YARD", "phone": "215-555-0144""215-555-0144", "email": "yard@moonstarpa.com", "cdl": "PA-334", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "truck": "8", "accident_report": "None", "files": []}]

    return trucks, trailers, drivers

TRUCKS_LIST, TRAILERS_LIST, DRIVERS_LIST = load_master_data()
CHAT_MESSAGES = [{"sender": "ismail@moonstarpa.com", "message": "Executive Fleet Console synchronized successfully.", "time": "10:00 AM"}]

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
            <a href="/dashboard?tab=home" title="Home" class="p-3 rounded-xl {% if tab == 'home' %}bg-sky-600 text-white{% else %}hover:bg-slate-800{% endif %} transition">🏠</a>
            <a href="/dashboard?tab=trucks" title="Trucks & Trailers" class="p-3 rounded-xl {% if tab == 'trucks' or tab == 'trailers' %}bg-sky-600 text-white{% else %}hover:bg-slate-800{% endif %} transition">🚛</a>
            <a href="/dashboard?tab=drivers" title="Drivers Compliance" class="p-3 rounded-xl {% if tab == 'drivers' %}bg-sky-600 text-white{% else %}hover:bg-slate-800{% endif %} transition">👤</a>
            <a href="/dashboard?tab=chat" title="Dispatch Chat" class="p-3 rounded-xl {% if tab == 'chat' %}bg-sky-600 text-white{% else %}hover:bg-slate-800{% endif %} transition">💬</a>
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

        <div class="bg-white border-b border-slate-200 px-8 py-3 flex justify-between items-center shadow-sm">
            <div class="flex space-x-3">
                <a href="/dashboard?tab=home" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'home' %}bg-slate-900 text-white shadow{% else %}text-slate-600 hover:bg-slate-100{% endif %}">Home / Analytics</a>
                <a href="/dashboard?tab=trucks" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'trucks' %}bg-slate-900 text-white shadow{% else %}text-slate-600 hover:bg-slate-100{% endif %}">Trucks & Trailers ({{ trucks|length }}/{{ trailers|length }})</a>
                <a href="/dashboard?tab=drivers" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'drivers' %}bg-slate-900 text-white shadow{% else %}text-slate-600 hover:bg-slate-100{% endif %}">Drivers Compliance ({{ drivers|length }})</a>
                <a href="/dashboard?tab=chat" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'chat' %}bg-slate-900 text-white shadow{% else %}text-slate-600 hover:bg-slate-100{% endif %}">Dispatch Team Chat</a>
            </div>
            <div>
                {% if tab == 'trucks' %}
                <a href="/dashboard?tab=trucks&action=add_truck" class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-xs font-bold uppercase shadow">+ Add Truck</a>
                {% elif tab == 'trailers' %}
                <a href="/dashboard?tab=trailers&action=add_trailer" class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-xs font-bold uppercase shadow">+ Add Trailer</a>
                {% elif tab == 'drivers' %}
                <a href="/dashboard?tab=drivers&action=add_driver" class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-xs font-bold uppercase shadow">+ Add Driver</a>
                {% endif %}
            </div>
        </div>

        <main class="p-8 space-y-6 flex-1">
            {% if tab == 'home' %}
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
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
                <div class="bg-white p-5 rounded-xl border-l-4 border-indigo-600 shadow-sm">
                    <div class="text-xs font-bold uppercase text-slate-500">Filo Net Kar (Est.)</div>
                    <div class="text-3xl font-black text-indigo-600 mt-2">
                        ${{ "{:,.0f}".format(trucks | sum(attribute='gross') - trucks | sum(attribute='fuel') - trucks | sum(attribute='maintenance')) }}
                    </div>
                </div>
            </div>
            <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200 space-y-4">
                <h3 class="text-lg font-black text-slate-900">🚨 Fleet Compliance & Inspection Watch</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div class="bg-amber-50 p-4 rounded-xl border border-amber-200 space-y-2">
                        <h4 class="font-bold text-amber-900 text-sm">🚚 Trucks Inspection Watch</h4>
                        {% for t in trucks[:6] %}
                        <div class="flex justify-between bg-white p-2.5 rounded border border-amber-100">
                            <span><b>Unit #{{ t.unit }}</b> ({{ t.type }})</span>
                            <span class="text-amber-700 font-bold">DOT: {{ t.dot_insp }}</span>
                        </div>
                        {% endfor %}
                    </div>
                    <div class="bg-sky-50 p-4 rounded-xl border border-sky-200 space-y-2">
                        <h4 class="font-bold text-sky-900 text-sm">👤 Drivers CDL & Medical Watch</h4>
                        {% for d in drivers[:6] %}
                        <div class="flex justify-between bg-white p-2.5 rounded border border-sky-100">
                            <span><b>{{ d.name }}</b></span>
                            <span class="text-sky-700 font-bold">Medical: {{ d.medical }}</span>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            {% elif tab == 'trucks' %}
            <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div class="p-5 border-b border-slate-200 flex justify-between items-center bg-slate-50">
                    <h3 class="font-black text-slate-900 text-base">🚛 Master Trucks Inventory & P&L Ledger ({{ trucks|length }} Units)</h3>
                    <form method="GET" action="/dashboard" class="flex gap-2">
                        <input type="hidden" name="tab" value="trucks">
                        <input type="text" name="search" value="{{ search or '' }}" placeholder="Search unit, driver, plate..." class="px-3 py-1.5 text-xs border rounded-lg bg-white">
                        <button type="submit" class="bg-slate-900 text-white px-3 py-1.5 rounded-lg text-xs font-bold">Search</button>
                    </form>
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
                        {% if not search or search.lower() in t.unit.lower() or search.lower() in t.driver.lower() or search.lower() in t.plate.lower() %}
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
                        {% endif %}
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% elif tab == 'trailers' %}
            <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div class="p-5 border-b border-slate-200 flex justify-between items-center bg-slate-50">
                    <h3 class="font-black text-slate-900 text-base">📦 Master Trailers Inventory ({{ trailers|length }} Units)</h3>
                    <a href="/dashboard?tab=trailers&action=add_trailer" class="bg-emerald-600 text-white px-3 py-1.5 rounded-lg text-xs font-bold">+ Add Trailer</a>
                </div>
                <table class="w-full text-left border-collapse text-xs">
                    <thead>
                        <tr class="bg-slate-900 text-white">
                            <th class="p-3">Unit #</th>
                            <th class="p-3">Trailer Type</th>
                            <th class="p-3">Plate & Expiry</th>
                            <th class="p-3">Annual Inspection</th>
                            <th class="p-3">Assigned Truck</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-200">
                        {% for tr in trailers %}
                        <tr class="hover:bg-slate-50 cursor-pointer" onclick="window.location='/dashboard?tab=trailers&trailer_dossier={{ tr.unit }}'">
                            <td class="p-3 font-black text-slate-900">#{{ tr.unit }}</td>
                            <td class="p-3 text-slate-700">{{ tr.type }}</td>
                            <td class="p-3 text-slate-600">{{ tr.plate }} <br><span class="text-[10px] text-slate-400">Exp: {{ tr.plate_expiry }}</span></td>
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
                    <h3 class="font-black text-slate-900 text-base">👤 Master Drivers Compliance & Roster ({{ drivers|length }} Active Drivers)</h3>
                    <span class="text-xs text-slate-500">Click any driver to view full dossier (CDL, Medical, Phone, Accident Report).</span>
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
                        <tr class="hover:bg-slate-50 cursor-pointer" onclick="window.location='/dashboard?tab=drivers&driver_dossier={{ d.name }}'">
                            <td class="p-3 font-black text-slate-900">{{ d.name }}</td>
                            <td class="p-3 text-slate-600">
                                <a href="tel:{{ d.phone }}" class="text-sky-600 font-bold hover:underline" onclick="event.stopPropagation();">📞 {{ d.phone }}</a>
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
        </main>
    </div>

    <!-- TRUCK DOSSIER MODAL -->
    {% if selected_unit %}
    <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden border border-slate-200">
            <div class="bg-slate-900 text-white p-5 flex justify-between items-center">
                <h3 class="font-black text-lg">Truck Dossier & Financial Ledger — Unit #{{ selected_unit.unit }}</h3>
                <a href="/dashboard?tab=trucks" class="text-slate-400 hover:text-white font-bold text-lg">✕</a>
            </div>
            <form action="/update_truck" method="POST" class="p-6 space-y-4">
                <input type="hidden" name="unit" value="{{ selected_unit.unit }}">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Gross Revenue ($)</label>
                        <input type="number" step="0.01" name="gross" value="{{ selected_unit.gross }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Fuel Expense ($)</label>
                        <input type="number" step="0.01" name="fuel" value="{{ selected_unit.fuel }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Maintenance Expense ($)</label>
                        <input type="number" step="0.01" name="maintenance" value="{{ selected_unit.maintenance }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Accident / Incident Report</label>
                        <input type="text" name="accident_report" value="{{ selected_unit.accident_report }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                </div>
                <div class="flex justify-between pt-2">
                    <button type="submit" class="bg-sky-600 text-white px-5 py-2 rounded-lg text-xs font-bold uppercase shadow">💾 Save Truck Info</button>
                    <a href="/delete_truck?unit={{ selected_unit.unit }}" class="bg-red-600 text-white px-5 py-2 rounded-lg text-xs font-bold uppercase shadow">🗑️ Delete Truck</a>
                </div>
            </form>
        </div>
    </div>
    {% endif %}

    <!-- DRIVER DOSSIER MODAL -->
    {% if selected_driver %}
    <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden border border-slate-200">
            <div class="bg-slate-900 text-white p-5 flex justify-between items-center">
                <h3 class="font-black text-lg">Driver Dossier & Compliance: {{ selected_driver.name }}</h3>
                <a href="/dashboard?tab=drivers" class="text-slate-400 hover:text-white font-bold text-lg">✕</a>
            </div>
            <form action="/update_driver" method="POST" class="p-6 space-y-4">
                <input type="hidden" name="original_name" value="{{ selected_driver.name }}">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Full Name</label>
                        <input type="text" name="name" value="{{ selected_driver.name }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Phone Number</label>
                        <input type="text" name="phone" value="{{ selected_driver.phone }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">CDL License Number</label>
                        <input type="text" name="cdl" value="{{ selected_driver.cdl }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">DOT Medical Expiry</label>
                        <input type="text" name="medical" value="{{ selected_driver.medical }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div class="col-span-2">
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Accident / Violation Record</label>
                        <input type="text" name="accident_report" value="{{ selected_driver.accident_report or 'Clean' }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                </div>
                <div class="flex justify-between pt-2">
                    <button type="submit" class="bg-sky-600 text-white px-5 py-2 rounded-lg text-xs font-bold uppercase shadow">💾 Save Driver Compliance</button>
                    <a href="/delete_driver?name={{ selected_driver.name }}" class="bg-red-600 text-white px-5 py-2 rounded-lg text-xs font-bold uppercase shadow">🗑️ Delete Driver</a>
                </div>
            </form>
        </div>
    </div>
    {% endif %}

    <!-- ADD TRUCK MODAL -->
    {% if action == 'add_truck' %}
    <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden border border-slate-200">
            <div class="bg-slate-900 text-white p-5 flex justify-between items-center">
                <h3 class="font-black text-lg">➕ Add New Truck</h3>
                <a href="/dashboard?tab=trucks" class="text-slate-400 hover:text-white font-bold text-lg">✕</a>
            </div>
            <form action="/add_truck" method="POST" class="p-6 space-y-4">
                <div>
                    <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Unit Number (e.g., 95)</label>
                    <input type="text" name="unit" required class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                </div>
                <div>
                    <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Make / Model</label>
                    <input type="text" name="type" value="VOLVO VNL" required class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                </div>
                <div class="flex justify-end pt-2">
                    <button type="submit" class="bg-emerald-600 text-white px-5 py-2 rounded-lg text-xs font-bold uppercase shadow">Save Truck</button>
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
                <h3 class="font-black text-lg">➕ Add New Driver</h3>
                <a href="/dashboard?tab=drivers" class="text-slate-400 hover:text-white font-bold text-lg">✕</a>
            </div>
            <form action="/add_driver" method="POST" class="p-6 space-y-4">
                <div>
                    <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Full Name</label>
                    <input type="text" name="name" required class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                </div>
                <div>
                    <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Phone Number</label>
                    <input type="text" name="phone" required class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                </div>
                <div class="flex justify-end pt-2">
                    <button type="submit" class="bg-emerald-600 text-white px-5 py-2 rounded-lg text-xs font-bold uppercase shadow">Save Driver</button>
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
        response = RedirectResponse(url="/dashboard?tab=home", status_code=303)
        response.set_cookie(key="user", value=email.strip().lower())
        return response
    return Template(LOGIN_HTML).render(error="Invalid credentials!")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, tab: str = "home", dossier: str = None, trailer_dossier: str = None, driver_dossier: str = None, search: str = None, action: str = None):
    user = request.cookies.get("user")
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    selected_unit = next((t for t in TRUCKS_LIST if t["unit"] == dossier), None) if dossier else None
    selected_driver = next((d for d in DRIVERS_LIST if d["name"] == driver_dossier), None) if driver_dossier else None

    return Template(DASHBOARD_HTML).render(
        user=user, 
        trucks=TRUCKS_LIST, 
        trailers=TRAILERS_LIST,
        drivers=DRIVERS_LIST,
        chat_messages=CHAT_MESSAGES, 
        tab=tab,
        search=search,
        action=action, 
        selected_unit=selected_unit,
        selected_driver=selected_driver
    )

@app.post("/update_truck")
def update_truck(unit: str = Form(...), gross: float = Form(0.0), fuel: float = Form(0.0), maintenance: float = Form(0.0), accident_report: str = Form("None")):
    for t in TRUCKS_LIST:
        if t["unit"] == unit:
            t["gross"] = gross
            t["fuel"] = fuel
            t["maintenance"] = maintenance
            t["accident_report"] = accident_report
    return RedirectResponse(url=f"/dashboard?tab=trucks&dossier={unit}", status_code=303)

@app.post("/update_driver")
def update_driver(original_name: str = Form(...), name: str = Form(...), phone: str = Form(...), cdl: str = Form(...), medical: str = Form(...), accident_report: str = Form("Clean")):
    for d in DRIVERS_LIST:
        if d["name"] == original_name:
            d["name"] = name
            d["phone"] = phone
            d["cdl"] = cdl
            d["medical"] = medical
            d["accident_report"] = accident_report
    return RedirectResponse(url=f"/dashboard?tab=drivers&driver_dossier={name}", status_code=303)

@app.post("/add_truck")
def add_truck(unit: str = Form(...), type: str = Form(...)):
    TRUCKS_LIST.append({
        "unit": unit, "type": type, "plate": "TEMP-PA", "plate_expiry": "2027-05-31",
        "dot_insp": "2027-01-01", "vin": "NEW", "driver": "Unassigned", "trailer": "None",
        "status": "Active", "gross": 15000.0, "fuel": 3500.0, "maintenance": 500.0, "accident_report": "None", "files": []
    })
    return RedirectResponse(url="/dashboard?tab=trucks", status_code=303)

@app.get("/delete_truck")
def delete_truck(unit: str):
    global TRUCKS_LIST
    TRUCKS_LIST = [t for t in TRUCKS_LIST if t["unit"] != unit]
    return RedirectResponse(url="/dashboard?tab=trucks", status_code=303)

@app.post("/add_driver")
def add_driver(name: str = Form(...), phone: str = Form(...)):
    DRIVERS_LIST.append({
        "name": name, "phone": phone, "email": f"{name.lower().replace(' ', '')}@moonstarpa.com",
        "cdl": "CDL-NEW", "cdl_expiry": "2028-01-01", "medical": "2027-01-01", "truck": "Unassigned", "accident_report": "Clean", "files": []
    })
    return RedirectResponse(url="/dashboard?tab=drivers", status_code=303)

@app.get("/delete_driver")
def delete_driver(name: str):
    global DRIVERS_LIST
    DRIVERS_LIST = [d for d in DRIVERS_LIST if d["name"] != name]
    return RedirectResponse(url="/dashboard?tab=drivers", status_code=303)

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="user")
    return response
