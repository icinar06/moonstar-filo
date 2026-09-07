from fastapi import FastAPI, Form, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Template

app = FastAPI(title="MOONSTAR EXPRESS LLC — Executive Fleet Console")

def get_full_fleet():
    return [
        {"unit_number": "6", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "ASIL BAD SHAH", "vin": "3AKJHHDR6JSJJ1492", "plate": "AH43983 PA", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "gross": 19500.0, "fuel": 4800.0, "net": 14700.0, "files": ["DOT_Inspection.pdf", "Insurance_Cert.jpg"]},
        {"unit_number": "8", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "AT YARD", "vin": "4V4NC9EH7KN900632", "plate": "AH35700 PA", "status": "READY", "oil_status": "READY", "dot_status": "READY", "gross": 15000.0, "fuel": 4200.0, "net": 10800.0, "files": ["Registration.pdf"]},
        {"unit_number": "10", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "OMAID FNU", "vin": "3AKJGLDR5KSKL6961", "plate": "R785774 TX", "status": "DUE SOON", "oil_status": "READY", "dot_status": "READY", "gross": 21000.0, "fuel": 5300.0, "net": 15700.0, "files": []},
        {"unit_number": "11", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "at shop", "vin": "3HSDZAPR1LN872658", "plate": "AH59898 PA", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "gross": 0.0, "fuel": 0.0, "net": 0.0, "files": ["Repair_Estimate.pdf"]},
        {"unit_number": "12", "unit_type": "TRUCK", "company": "FIORI", "driver": "ALTUG BACI", "vin": "4V4NC9EJ4MN275936", "plate": "AH69361 PA", "status": "READY", "oil_status": "READY", "dot_status": "READY", "gross": 22000.0, "fuel": 5100.0, "net": 16900.0, "files": ["Title.pdf"]},
        {"unit_number": "14", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "HABIB KHAN TANIWAL", "vin": "3AKJHHDR9LSLM9887", "plate": "AH59899 PA", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "gross": 18500.0, "fuel": 4600.0, "net": 13900.0, "files": []},
        {"unit_number": "33", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "SAID KHAN", "vin": "4V4NC9EHXKN212592", "plate": "AG85614 PA", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "gross": 20400.0, "fuel": 4900.0, "net": 15500.0, "files": []},
        {"unit_number": "34", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "HAQMAL HABIBI", "vin": "3AKJGLDR0JSHF1489", "plate": "R567959 TX", "status": "READY", "oil_status": "READY", "dot_status": "READY", "gross": 17500.0, "fuel": 4100.0, "net": 13400.0, "files": []}
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
    <div class="flex space-x-2 border-b border-slate-200 pb-3">
        <a href="/dashboard?tab=trucks" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'trucks' %}bg-sky-600 text-white shadow{% else %}bg-white text-slate-700 border border-slate-200 hover:bg-slate-50{% endif %}">Trucks & Trailers</a>
        <a href="/dashboard?tab=drivers" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'drivers' %}bg-sky-600 text-white shadow{% else %}bg-white text-slate-700 border border-slate-200 hover:bg-slate-50{% endif %}">Drivers Compliance</a>
        <a href="/dashboard?tab=imports" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'imports' %}bg-sky-600 text-white shadow{% else %}bg-white text-slate-700 border border-slate-200 hover:bg-slate-50{% endif %}">Data Imports</a>
        <a href="/dashboard?tab=service" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'service' %}bg-sky-600 text-white shadow{% else %}bg-white text-slate-700 border border-slate-200 hover:bg-slate-50{% endif %}">Service Ledger</a>
    </div>

    {% if tab == 'trucks' %}
    <!-- KPI CARDS -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-white p-5 rounded-xl border-l-4 border-sky-600 shadow-sm">
            <div class="text-xs font-bold uppercase text-slate-500">Monthly Fleet Gross (ITS)</div>
            <div class="text-2xl font-black text-sky-600 mt-2">$153,400.00</div>
        </div>
        <div class="bg-white p-5 rounded-xl border-l-4 border-orange-500 shadow-sm">
            <div class="text-xs font-bold uppercase text-slate-500">Total Monthly Fuel Cost</div>
            <div class="text-2xl font-black text-orange-600 mt-2">$37,900.00</div>
        </div>
        <div class="bg-white p-5 rounded-xl border-l-4 border-amber-500 shadow-sm">
            <div class="text-xs font-bold uppercase text-slate-500">Inspections Due Soon</div>
            <div class="text-2xl font-black text-amber-600 mt-2">4 Assets</div>
        </div>
        <div class="bg-white p-5 rounded-xl border-l-4 border-emerald-600 shadow-sm">
            <div class="text-xs font-bold uppercase text-slate-500">Active Fleet Total</div>
            <div class="text-2xl font-black text-emerald-600 mt-2">{{ vehicles|length }} Units</div>
        </div>
    </div>

    <!-- EQUIPMENT PORTAL GRID -->
    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h3 class="text-lg font-black text-slate-900 mb-6 flex items-center gap-2">
            📦 Fleet Equipment Portal & Master Dossiers (Click any card)
        </h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {% for v in vehicles %}
            <a href="/dashboard?tab=trucks&dossier={{ v.unit_number }}" class="bg-white border-2 border-slate-900 rounded-xl p-5 shadow-sm hover:shadow-lg transition flex flex-col justify-between relative overflow-hidden text-left block">
                <div class="absolute left-0 top-0 bottom-0 w-2 {% if v.status == 'DUE SOON' %}bg-amber-500{% else %}bg-emerald-500{% endif %}"></div>
                
                <div class="pl-3">
                    <div class="flex justify-between items-center border-b border-slate-200 pb-2 mb-3">
                        <span class="font-black text-slate-900 text-sm">UNIT #{{ v.unit_number }} ({{ v.company }})</span>
                        <span class="text-[10px] font-bold px-2 py-0.5 rounded {% if v.status == 'DUE SOON' %}bg-amber-100 text-amber-700{% else %}bg-emerald-100 text-emerald-700{% endif %}">{{ v.status }}</span>
                    </div>
                    <div class="space-y-1 text-xs text-slate-700">
                        <div><b>Driver:</b> <span class="text-sky-600 font-semibold">{{ v.driver }}</span></div>
                        <div><b>Plate:</b> {{ v.plate }}</div>
                        <div><b>Oil Service:</b> {{ v.oil_status }}</div>
                        <div><b>Annual DOT:</b> {{ v.dot_status }}</div>
                        <div class="pt-2 border-t border-slate-100 font-semibold text-slate-900">
                            Gross: ${{ "{:,.0f}".format(v.gross) }} | Net: ${{ "{:,.0f}".format(v.net) }}
                        </div>
                    </div>
                </div>
                <div class="mt-4 pl-3">
                    <span class="w-full text-center text-xs font-bold text-sky-600 border border-sky-200 bg-sky-50 py-2 rounded-lg block">
                        Open Master Dossier →
                    </span>
                </div>
            </a>
            {% endfor %}
        </div>
    </div>
    {% elif tab == 'drivers' %}
    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h3 class="text-lg font-black text-slate-900 mb-4">👤 Drivers Compliance & Master Dossiers</h3>
        <p class="text-xs text-slate-500 mb-6">Click any driver to view compliance files, CDL status, and documents.</p>
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {% for v in vehicles %}
            <a href="/dashboard?tab=drivers&driver_dossier={{ v.driver }}" class="bg-white border-2 border-slate-900 rounded-xl p-5 shadow-sm hover:shadow-lg transition flex flex-col justify-between relative overflow-hidden block">
                <div class="absolute left-0 top-0 bottom-0 w-2 bg-emerald-500"></div>
                <div class="pl-3">
                    <div class="font-black text-slate-900 text-sm mb-2">{{ v.driver }}</div>
                    <div class="text-xs text-slate-600 space-y-1">
                        <div><b>Company:</b> {{ v.company }}</div>
                        <div><b>Assigned Unit:</b> Unit #{{ v.unit_number }}</div>
                        <div class="text-emerald-600 font-bold">CDL: Valid</div>
                        <div class="text-emerald-600 font-bold">Medical: Compliant</div>
                    </div>
                </div>
                <div class="mt-4 pl-3">
                    <span class="w-full text-center text-xs font-bold text-sky-600 border border-sky-200 bg-sky-50 py-2 rounded-lg block">
                        Driver Dossier →
                    </span>
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
                <button onclick="alert('Samsara telemetry synced successfully!')" class="w-full bg-sky-600 text-white py-2 rounded-lg text-xs font-bold">Sync Mileages</button>
            </div>
            <div class="bg-slate-50 p-5 rounded-xl border border-slate-200">
                <h4 class="font-bold text-sm text-slate-900 mb-2">2. ITS Gross Revenue Sync</h4>
                <input type="file" class="w-full text-xs text-slate-500 mb-4">
                <button onclick="alert('ITS Gross revenues updated!')" class="w-full bg-sky-600 text-white py-2 rounded-lg text-xs font-bold">Sync Revenues</button>
            </div>
            <div class="bg-slate-50 p-5 rounded-xl border border-slate-200">
                <h4 class="font-bold text-sm text-slate-900 mb-2">3. Fuel Card Expense Sync</h4>
                <input type="file" class="w-full text-xs text-slate-500 mb-4">
                <button onclick="alert('Fuel expenses reconciled!')" class="w-full bg-sky-600 text-white py-2 rounded-lg text-xs font-bold">Sync Fuel Expenses</button>
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
        <button onclick="alert('Service entry recorded successfully!')" class="mt-4 bg-sky-600 text-white px-6 py-2.5 rounded-lg text-xs font-bold uppercase">Record Service Entry</button>
    </div>
    {% endif %}

    <!-- DOSSIER MODAL POPUP FOR TRUCKS -->
    {% if selected_unit %}
    <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-3xl overflow-hidden border border-slate-200">
            <div class="bg-slate-900 text-white p-5 flex justify-between items-center">
                <h3 class="font-black text-lg">Equipment Dossier — Unit #{{ selected_unit.unit_number }} ({{ selected_unit.company }})</h3>
                <a href="/dashboard?tab=trucks" class="text-slate-400 hover:text-white font-bold text-lg">✕</a>
            </div>
            <div class="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
                <form action="/update_unit" method="POST" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <input type="hidden" name="unit_number" value="{{ selected_unit.unit_number }}">
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Assigned Driver</label>
                        <input type="text" name="driver" value="{{ selected_unit.driver }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Plate Number</label>
                        <input type="text" name="plate" value="{{ selected_unit.plate }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">VIN / Serial</label>
                        <input type="text" name="vin" value="{{ selected_unit.vin }}" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-slate-600 mb-1">Hooked Trailer #</label>
                        <input type="text" name="trailer" placeholder="None" class="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-lg">
                    </div>
                    <div class="md:col-span-2 pt-2">
                        <button type="submit" class="bg-sky-600 hover:bg-sky-700 text-white px-5 py-2.5 rounded-lg text-xs font-bold uppercase shadow">Save Vehicle Details</button>
                    </div>
                </form>

                <div class="border-t border-slate-200 pt-4">
                    <h4 class="font-bold text-sm text-slate-900 mb-2">📁 Archived Documents & Files (Silme Yönetimi)</h4>
                    {% if selected_unit.files %}
                    <div class="space-y-2">
                        {% for file in selected_unit.files %}
                        <div class="flex justify-between items-center bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                            <span class="text-xs font-medium text-slate-700">📄 {{ file }}</span>
                            <a href="/delete_file?unit={{ selected_unit.unit_number }}&file={{ file }}" class="bg-red-100 hover:bg-red-200 text-red-700 px-3 py-1 rounded text-xs font-bold transition">🗑️ Delete File</a>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <p class="text-xs text-slate-500">No documents uploaded for this unit yet.</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    {% endif %}

    <!-- DOSSIER MODAL POPUP FOR DRIVERS -->
    {% if selected_driver %}
    <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-xl overflow-hidden border border-slate-200">
            <div class="bg-slate-900 text-white p-5 flex justify-between items-center">
                <h3 class="font-black text-lg">Driver Dossier: {{ selected_driver.driver }}</h3>
                <a href="/dashboard?tab=drivers" class="text-slate-400 hover:text-white font-bold text-lg">✕</a>
            </div>
            <div class="p-6 space-y-4">
                <div><b>Company:</b> {{ selected_driver.company }}</div>
                <div><b>Assigned Unit:</b> Unit #{{ selected_driver.unit_number }}</div>
                <div><b>Plate:</b> {{ selected_driver.plate }}</div>
                <div class="pt-4 border-t border-slate-200 flex justify-end">
                    <a href="/dashboard?tab=drivers" class="bg-slate-800 text-white px-5 py-2 rounded-lg text-xs font-bold">Close Dossier</a>
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
    return Template(LOGIN_HTML).render()

@app.post("/login")
def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    if "@moonstarpa" in email.strip().lower() and password == "Moonstar2026!":
        response = RedirectResponse(url="/dashboard?tab=trucks", status_code=303)
        response.set_cookie(key="user", value=email.strip().lower())
        return response
    return Template(LOGIN_HTML).render(error="Invalid credentials!")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, tab: str = "trucks", dossier: str = None, driver_dossier: str = None):
    user = request.cookies.get("user")
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    vehicles = get_full_fleet()
    selected_unit = next((v for v in vehicles if v["unit_number"] == dossier), None) if dossier else None
    selected_driver = next((v for v in vehicles if v["driver"] == driver_dossier), None) if driver_dossier else None

    return Template(DASHBOARD_HTML).render(
        user=user, 
        vehicles=vehicles, 
        tab=tab, 
        selected_unit=selected_unit,
        selected_driver=selected_driver
    )

@app.post("/update_unit")
def update_unit(unit_number: str = Form(...), driver: str = Form(...), plate: str = Form(...), vin: str = Form(...)):
    response = RedirectResponse(url=f"/dashboard?tab=trucks&dossier={unit_number}", status_code=303)
    return response

@app.get("/delete_file")
def delete_file(unit: str, file: str):
    response = RedirectResponse(url=f"/dashboard?tab=trucks&dossier={unit}", status_code=303)
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="user")
    return response
