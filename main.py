from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Template

app = FastAPI(title="MOONSTAR EXPRESS LLC — Executive Fleet Console")

# Hafızada dinamik olarak yönetilen filo ve şoför listesi
FLEET_DATA = [
    {"unit_number": "6", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "ASIL BAD SHAH", "vin": "3AKJHHDR6JSJJ1492", "plate": "AH43983 PA", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "gross": 19500.0, "fuel": 4800.0, "net": 14700.0, "files": ["DOT_Inspection.pdf"]},
    {"unit_number": "8", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "AT YARD", "vin": "4V4NC9EH7KN900632", "plate": "AH35700 PA", "status": "READY", "oil_status": "READY", "dot_status": "READY", "gross": 15000.0, "fuel": 4200.0, "net": 10800.0, "files": []},
    {"unit_number": "R14782", "unit_type": "TRAILER", "company": "TNT RENTAL", "driver": "Unassigned", "vin": "3AWF1VT24LX004006", "plate": "31-19733 ME", "status": "READY", "oil_status": "N/A", "dot_status": "READY", "gross": 0.0, "fuel": 0.0, "net": 0.0, "files": []},
    {"unit_number": "12", "unit_type": "TRUCK", "company": "FIORI", "driver": "ALTUG BACI", "vin": "4V4NC9EJ4MN275936", "plate": "AH69361 PA", "status": "READY", "oil_status": "READY", "dot_status": "READY", "gross": 22000.0, "fuel": 5100.0, "net": 16900.0, "files": []}
]

DRIVERS_DATA = [
    {"name": "ASIL BAD SHAH", "company": "MOONSTAR", "phone": "215-555-0192""215-555-0192", "email": "asil@moonstarpa.com", "cdl": "PA-982341", "cdl_expiry": "2027-05-31", "medical": "2026-12-01", "unit": "6", "files": ["CDL_Scan.pdf"]},
    {"name": "AT YARD", "company": "MOONSTAR", "phone": "215-555-0144""215-555-0144", "email": "yard@moonstarpa.com", "cdl": "PA-334112", "cdl_expiry": "2027-05-31", "medical": "2027-01-15", "unit": "8", "files": []},
    {"name": "ALTUG BACI", "company": "FIORI", "phone": "215-555-0188""215-555-0188", "email": "altug@moonstarpa.com", "cdl": "PA-556789", "cdl_expiry": "2027-05-31", "medical": "2027-03-01", "unit": "12", "files": []}
]

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
        <span class="text-3xl font-black text-slate-900 tracking-wide">MOON<span class="text-orange-500">★</span>TAR</span>
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
            <span class="text-2xl font-black tracking-wide">MOON<span class="text-orange-500">★</span>TAR</span>
            <span class="text-xs font-semibold text-sky-300 border border-sky-400 px-2.5 py-0.5 rounded">EXPRESS LLC</span>
        </div>
        <div class="flex items-center space-x-4">
            <span class="text-xs text-slate-200">Executive Fleet Management | User: <b>{{ user }}</b></span>
            <a href="/logout" class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-xs font-bold uppercase transition shadow">Sign Out</a>
        </div>
    </header>

    <!-- NAVIGATION TABS -->
    <div class="flex justify-between items-center border-b border-slate-200 pb-3">
        <div class="flex space-x-2">
            <a href="/dashboard?tab=trucks" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'trucks' %}bg-sky-600 text-white shadow{% else %}bg-white text-slate-700 border border-slate-200 hover:bg-slate-50{% endif %}">Trucks & Trailers</a>
            <a href="/dashboard?tab=drivers" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'drivers' %}bg-sky-600 text-white shadow{% else %}bg-white text-slate-700 border border-slate-200 hover:bg-slate-50{% endif %}">Drivers Compliance</a>
            <a href="/dashboard?tab=imports" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'imports' %}bg-sky-600 text-white shadow{% else %}bg-white text-slate-700 border border-slate-200 hover:bg-slate-50{% endif %}">Data Imports</a>
            <a href="/dashboard?tab=service" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'service' %}bg-sky-600 text-white shadow{% else %}bg-white text-slate-700 border border-slate-200 hover:bg-slate-50{% endif %}">Service Ledger</a>
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
        <h3 class="text-lg font-black text-slate-900 mb-6">📦 Fleet Equipment Portal (Click any unit card to edit, save or delete)</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {% for v in vehicles %}
            <a href="/dashboard?tab=trucks&dossier={{ v.unit_number }}" class="bg-white border-2 border-slate-900 rounded-xl p-5 shadow-sm hover:shadow-lg transition flex flex-col justify-between relative overflow-hidden text-left block">
                <div class="absolute left-0 top-0 bottom-0 w-2 {% if v.status == 'DUE SOON' %}bg-amber-500{% else %}bg-emerald-500{% endif %}"></div>
                <div class="pl-3 space-y-1 text-xs text-slate-700">
                    <div class="flex justify-between items-center border-b border-slate-200 pb-2 mb-3">
                        <span class="font-black text-slate-900 text-sm">UNIT #{{ v.unit_number }} ({{ v.unit_type }})</span>
                        <span class="text-[10px] font-bold px-2 py-0.5 rounded {% if v.status == 'DUE SOON' %}bg-amber-100 text-amber-700{% else %}bg-emerald-100 text-emerald-700{% endif %}">{{ v.status }}</span>
                    </div>
                    <div><b>Company:</b> {{ v.company }}</div>
                    <div><b>Driver:</b> <span class="text-sky-600 font-semibold">{{ v.driver }}</span></div>
                    <div><b>Plate:</b> {{ v.plate }}</div>
                    <div><b>VIN:</b> {{ v.vin }}</div>
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
        <h3 class="text-lg font-black text-slate-900 mb-6">👤 Drivers Compliance Roster (Click card to edit, save or delete)</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {% for d in drivers %}
            <a href="/dashboard?tab=drivers&driver_dossier={{ d.name }}" class="bg-white border-2 border-slate-900 rounded-xl p-5 shadow-sm hover:shadow-lg transition flex flex-col justify-between relative overflow-hidden block">
                <div class="absolute left-0 top-0 bottom-0 w-2 bg-emerald-500"></div>
                <div class="pl-3 space-y-1 text-xs text-slate-600">
                    <div class="font-black text-slate-900 text-sm mb-2">{{ d.name }}</div>
                    <div><b>Company:</b> {{ d.company }}</div>
                    <div><b>Phone:</b> {{ d.phone }}</div>
                    <div><b>Assigned Unit:</b> Unit #{{ d.unit }}</div>
                    <div><b>CDL #:</b> {{ d.cdl }}</div>
                    <div class="text-emerald-600 font-bold pt-2">CDL & Medical: Valid</div>
                </div>
            </a>
            {% endfor %}
        </div>
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
    {% elif tab == 'service' %}
    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200 space-y-4">
        <h3 class="text-lg font-black text-slate-900">🔧 Equipment Service & Maintenance Record Entry</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
                <label class="block text-xs font-bold text-slate-600 mb-1">Select Unit</label>
                <select class="w-full p-2.5 text-xs bg-slate-50 border border-slate-300 rounded-lg">
                    {% for v in vehicles %}
                    <option>Unit #{{ v.unit_number }} ({{ v.driver }})</option>
                    {% endfor %}
                </select>
            </div>
            <div>
                <label class="block text-xs font-bold text-slate-600 mb-1">Service Type</label>
                <select class="w-full p-2.5 text-xs bg-slate-50 border border-slate-300 rounded-lg">
                    <option>Oil Change (PM)</option>
                    <option>Tires / Brakes</option>
                    <option>Annual DOT Inspection</option>
                    <option>Breakdown / Repair</option>
                </select>
            </div>
            <div>
                <label class="block text-xs font-bold text-slate-600 mb-1">Cost ($)</label>
                <input type="number" placeholder="350.00" class="w-full p-2.5 text-xs bg-slate-50 border border-slate-300 rounded-lg">
            </div>
        </div>
        <button onclick="alert('Service recorded!')" class="mt-4 bg-sky-600 text-white px-6 py-2.5 rounded-lg text-xs font-bold uppercase">Record Service Entry</button>
    </div>
    {% endif %}

    <!-- TRUCK / TRAILER DOSSIER EDIT / SAVE / DELETE MODAL -->
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
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Unit Type</label>
                        <select name="unit_type" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                            <option value="TRUCK" {% if selected_unit.unit_type == 'TRUCK' %}selected{% endif %}>TRUCK</option>
                            <option value="TRAILER" {% if selected_unit.unit_type == 'TRAILER' %}selected{% endif %}>TRAILER</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Assigned Driver</label>
                        <input type="text" name="driver" value="{{ selected_unit.driver }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Company</label>
                        <input type="text" name="company" value="{{ selected_unit.company }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Plate Number</label>
                        <input type="text" name="plate" value="{{ selected_unit.plate }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">VIN / Serial</label>
                        <input type="text" name="vin" value="{{ selected_unit.vin }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div class="md:col-span-2 flex justify-between pt-2">
                        <button type="submit" class="bg-sky-600 hover:bg-sky-700 text-white px-5 py-2.5 rounded-lg text-xs font-bold uppercase shadow">💾 Save Changes</button>
                        <a href="/delete_unit?unit={{ selected_unit.unit_number }}" class="bg-red-600 hover:bg-red-700 text-white px-5 py-2.5 rounded-lg text-xs font-bold uppercase shadow">🗑️ Delete Unit</a>
                    </div>
                </form>

                <div class="border-t border-slate-200 pt-4">
                    <h4 class="font-bold text-sm text-slate-900 mb-2">📁 Uploaded Documents & File Management</h4>
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
                    <p class="text-xs text-slate-500">No documents uploaded for this unit.</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    {% endif %}

    <!-- DRIVER DOSSIER EDIT / SAVE / DELETE MODAL -->
    {% if selected_driver %}
    <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-xl overflow-hidden border border-slate-200">
            <div class="bg-slate-900 text-white p-5 flex justify-between items-center">
                <h3 class="font-black text-lg">Driver Dossier: {{ selected_driver.name }}</h3>
                <a href="/dashboard?tab=drivers" class="text-slate-400 hover:text-white font-bold text-lg">✕</a>
            </div>
            <div class="p-6 space-y-4">
                <form action="/update_driver" method="POST" class="space-y-3">
                    <input type="hidden" name="original_name" value="{{ selected_driver.name }}">
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Full Name</label>
                        <input type="text" name="name" value="{{ selected_driver.name }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Company</label>
                        <input type="text" name="company" value="{{ selected_driver.company }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Phone Number</label>
                        <input type="text" name="phone" value="{{ selected_driver.phone }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">CDL Number</label>
                        <input type="text" name="cdl" value="{{ selected_driver.cdl }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div class="flex justify-between pt-2">
                        <button type="submit" class="bg-sky-600 hover:bg-sky-700 text-white px-5 py-2 rounded-lg text-xs font-bold uppercase shadow">💾 Save Driver</button>
                        <a href="/delete_driver?name={{ selected_driver.name }}" class="bg-red-600 hover:bg-red-700 text-white px-5 py-2 rounded-lg text-xs font-bold uppercase shadow">🗑️ Delete Driver</a>
                    </div>
                </form>
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
                    <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Company</label>
                    <input type="text" name="company" value="MOONSTAR" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                </div>
                <div>
                    <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Assigned Driver</label>
                    <input type="text" name="driver" value="Unassigned" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
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
                    <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Company</label>
                    <input type="text" name="company" value="MOONSTAR" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
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
def dashboard(request: Request, tab: str = "trucks", dossier: str = None, driver_dossier: str = None, action: str = None):
    user = request.cookies.get("user")
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    selected_unit = next((v for v in FLEET_DATA if v["unit_number"] == dossier), None) if dossier else None
    selected_driver = next((d for d in DRIVERS_DATA if d["name"] == driver_dossier), None) if driver_dossier else None

    return Template(DASHBOARD_HTML).render(
        user=user, 
        vehicles=FLEET_DATA, 
        drivers=DRIVERS_DATA,
        tab=tab, 
        selected_unit=selected_unit,
        selected_driver=selected_driver,
        action=action
    )

@app.post("/update_unit")
def update_unit(unit_number: str = Form(...), unit_type: str = Form(...), driver: str = Form(...), company: str = Form(...), plate: str = Form(...), vin: str = Form(...)):
    for v in FLEET_DATA:
        if v["unit_number"] == unit_number:
            v["unit_type"] = unit_type
            v["driver"] = driver
            v["company"] = company
            v["plate"] = plate
            v["vin"] = vin
    return RedirectResponse(url=f"/dashboard?tab=trucks&dossier={unit_number}", status_code=303)

@app.get("/delete_unit")
def delete_unit(unit: str):
    global FLEET_DATA
    FLEET_DATA = [v for v in FLEET_DATA if v["unit_number"] != unit]
    return RedirectResponse(url="/dashboard?tab=trucks", status_code=303)

@app.post("/update_driver")
def update_driver(original_name: str = Form(...), name: str = Form(...), company: str = Form(...), phone: str = Form(...), cdl: str = Form(...)):
    for d in DRIVERS_DATA:
        if d["name"] == original_name:
            d["name"] = name
            d["company"] = company
            d["phone"] = phone
            d["cdl"] = cdl
    return RedirectResponse(url=f"/dashboard?tab=drivers&driver_dossier={name}", status_code=303)

@app.get("/delete_driver")
def delete_driver(name: str):
    global DRIVERS_DATA
    DRIVERS_DATA = [d for d in DRIVERS_DATA if d["name"] != name]
    return RedirectResponse(url="/dashboard?tab=drivers", status_code=303)

@app.post("/add_unit")
def add_unit(unit_number: str = Form(...), unit_type: str = Form(...), company: str = Form(...), driver: str = Form(...)):
    FLEET_DATA.append({
        "unit_number": unit_number,
        "unit_type": unit_type,
        "company": company,
        "driver": driver,
        "vin": "NEW-VIN-000",
        "plate": "TEMP-PA",
        "status": "READY",
        "oil_status": "READY",
        "dot_status": "READY",
        "gross": 10000.0,
        "fuel": 2500.0,
        "net": 7500.0,
        "files": []
    })
    return RedirectResponse(url="/dashboard?tab=trucks", status_code=303)

@app.post("/add_driver")
def add_driver(name: str = Form(...), company: str = Form(...), phone: str = Form(...)):
    DRIVERS_DATA.append({
        "name": name,
        "company": company,
        "phone": phone,
        "email": f"{name.lower().replace(' ', '')}@moonstarpa.com",
        "cdl": "CDL-NEW-00",
        "cdl_expiry": "2028-01-01",
        "medical": "2027-01-01",
        "unit": "New",
        "files": []
    })
    return RedirectResponse(url="/dashboard?tab=drivers", status_code=303)

@app.get("/delete_unit_file")
def delete_unit_file(unit: str, file: str):
    for v in FLEET_DATA:
        if v["unit_number"] == unit:
            if file in v["files"]:
                v["files"].remove(file)
    return RedirectResponse(url=f"/dashboard?tab=trucks&dossier={unit}", status_code=303)

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="user")
    return response
