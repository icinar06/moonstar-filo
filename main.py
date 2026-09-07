from fastapi import FastAPI, Form, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Template

app = FastAPI(title="MOONSTAR EXPRESS LLC — Executive Fleet Console")

def get_full_fleet():
    return [
        {"unit_number": "6", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "ASIL BAD SHAH", "vin": "3AKJHHDR6JSJJ1492", "plate": "AH43983 PA", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "gross": 19500.0, "fuel": 4800.0, "net": 14700.0},
        {"unit_number": "8", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "AT YARD", "vin": "4V4NC9EH7KN900632", "plate": "AH35700 PA", "status": "READY", "oil_status": "READY", "dot_status": "READY", "gross": 15000.0, "fuel": 4200.0, "net": 10800.0},
        {"unit_number": "10", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "OMAID FNU", "vin": "3AKJGLDR5KSKL6961", "plate": "R785774 TX", "status": "DUE SOON", "oil_status": "READY", "dot_status": "READY", "gross": 21000.0, "fuel": 5300.0, "net": 15700.0},
        {"unit_number": "11", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "at shop", "vin": "3HSDZAPR1LN872658", "plate": "AH59898 PA", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "gross": 0.0, "fuel": 0.0, "net": 0.0},
        {"unit_number": "12", "unit_type": "TRUCK", "company": "FIORI", "driver": "ALTUG BACI", "vin": "4V4NC9EJ4MN275936", "plate": "AH69361 PA", "status": "READY", "oil_status": "READY", "dot_status": "READY", "gross": 22000.0, "fuel": 5100.0, "net": 16900.0},
        {"unit_number": "14", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "HABIB KHAN TANIWAL", "vin": "3AKJHHDR9LSLM9887", "plate": "AH59899 PA", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "gross": 18500.0, "fuel": 4600.0, "net": 13900.0},
        {"unit_number": "33", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "SAID KHAN", "vin": "4V4NC9EHXKN212592", "plate": "AG85614 PA", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "gross": 20400.0, "fuel": 4900.0, "net": 15500.0},
        {"unit_number": "34", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "HAQMAL HABIBI", "vin": "3AKJGLDR0JSHF1489", "plate": "R567959 TX", "status": "READY", "oil_status": "READY", "dot_status": "READY", "gross": 17500.0, "fuel": 4100.0, "net": 13400.0},
        {"unit_number": "55", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "NOOR SHAHZADIN", "vin": "1M1AN4GY8LM014136", "plate": "AH48256 PA", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "gross": 23000.0, "fuel": 5500.0, "net": 17500.0},
        {"unit_number": "0102", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "JAMAR LAMONT LITTLES", "vin": "3HSDZAPR6LN400102", "plate": "AH67146 PA", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "gross": 19000.0, "fuel": 4400.0, "net": 14600.0},
        {"unit_number": "115", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "MONTEL LAMAR BURT", "vin": "3HSDZAPR4KN610115", "plate": "AH55084 PA", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "gross": 21500.0, "fuel": 5000.0, "net": 16500.0},
        {"unit_number": "202", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "NASEEBULLAH AMIRZAI", "vin": "3ALACWFC3JDJH5531", "plate": "XXJ0110 TX", "status": "READY", "oil_status": "READY", "dot_status": "READY", "gross": 16000.0, "fuel": 3900.0, "net": 12100.0},
        {"unit_number": "201", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "ALI IMRAN ZAT KHAN", "vin": "3ALACWFB0KDKM5838", "plate": "YGL6943 TX", "status": "READY", "oil_status": "READY", "dot_status": "READY", "gross": 18000.0, "fuel": 4200.0, "net": 13800.0},
        {"unit_number": "217", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "ANDI KASHARI", "vin": "3AKJHHDV4LSMC8375", "plate": "AH81416 PA", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "gross": 20000.0, "fuel": 4800.0, "net": 15200.0},
        {"unit_number": "995", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "YZEDIN HATTILARI", "vin": "3AKJHHDR3JSGC5847", "plate": "TEMP PA", "status": "READY", "oil_status": "READY", "dot_status": "READY", "gross": 19200.0, "fuel": 4500.0, "net": 14700.0},
        {"unit_number": "999", "unit_type": "TRUCK", "company": "MOONSTAR", "driver": "NEVIS HAJNAJ", "vin": "3AKJHHDR3KSKF5143", "plate": "AH41390 PA", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "gross": 21000.0, "fuel": 5100.0, "net": 15900.0},
        {"unit_number": "30", "unit_type": "TRUCK", "company": "LIONSTAR", "driver": "RAFIQ SERFERAZ", "vin": "4V4NC9EJXMN286911", "plate": "TEMP- PA", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "gross": 17000.0, "fuel": 4000.0, "net": 13000.0},
        {"unit_number": "31", "unit_type": "TRUCK", "company": "LIONSTAR", "driver": "JOSHUA RAYMOND DIAZ", "vin": "4V4NC9EJ1GN953465", "plate": "AH84982 PA", "status": "READY", "oil_status": "READY", "dot_status": "READY", "gross": 18500.0, "fuel": 4300.0, "net": 14200.0},
        {"unit_number": "38", "unit_type": "TRUCK", "company": "LIONSTAR", "driver": "BRYAN MAHMUTAJ", "vin": "4V4NC9EH4PN625082", "plate": "AH38803 PA", "status": "READY", "oil_status": "READY", "dot_status": "READY", "gross": 24000.0, "fuel": 5800.0, "net": 18200.0},
        {"unit_number": "40", "unit_type": "TRUCK", "company": "LIONSTAR", "driver": "RUSSLAN SMIRNOV", "vin": "4V4NC9EH3PN613540", "plate": "AH34226 PA", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "gross": 22500.0, "fuel": 5200.0, "net": 17300.0},
        {"unit_number": "41", "unit_type": "TRUCK", "company": "LIONSTAR", "driver": "NOOR ALI WAZIRI", "vin": "4V4NC9EH5PN613541", "plate": "AH79469 PA", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "gross": 21000.0, "fuel": 5000.0, "net": 16000.0},
        {"unit_number": "53", "unit_type": "TRUCK", "company": "LIONSTAR", "driver": "WAHDAT SAFI", "vin": "3HSDZSZR0SN355353", "plate": "AH76436 PA", "status": "READY", "oil_status": "READY", "dot_status": "READY", "gross": 26000.0, "fuel": 6200.0, "net": 19800.0},
        {"unit_number": "63", "unit_type": "TRUCK", "company": "LIONSTAR", "driver": "FARHADULLAH WESAL", "vin": "3HSDZSZR8TN355263", "plate": "AH79468 PA", "status": "READY", "oil_status": "READY", "dot_status": "READY", "gross": 25000.0, "fuel": 5900.0, "net": 19100.0},
        {"unit_number": "65", "unit_type": "TRUCK", "company": "LIONSTAR", "driver": "RIDVAN DENIZ", "vin": "4V4NC9EH8HN976742", "plate": "AH84983 PA", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "gross": 19500.0, "fuel": 4500.0, "net": 15000.0}
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
        <a href="/dashboard?tab=imports" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'imports' %}bg-sky-600 text-white shadow{% else %}bg-white text-slate-700 border border-slate-200 hover:bg-slate-50{% endif %}">Data Imports (Samsara/ITS/Fuel)</a>
        <a href="/dashboard?tab=service" class="px-4 py-2 text-xs font-bold uppercase rounded-lg {% if tab == 'service' %}bg-sky-600 text-white shadow{% else %}bg-white text-slate-700 border border-slate-200 hover:bg-slate-50{% endif %}">Service Ledger</a>
    </div>

    {% if tab == 'trucks' %}
    <!-- KPI CARDS -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-white p-5 rounded-xl border-l-4 border-sky-600 shadow-sm">
            <div class="text-xs font-bold uppercase text-slate-500">Monthly Fleet Gross (ITS)</div>
            <div class="text-2xl font-black text-sky-600 mt-2">$489,400.00</div>
        </div>
        <div class="bg-white p-5 rounded-xl border-l-4 border-orange-500 shadow-sm">
            <div class="text-xs font-bold uppercase text-slate-500">Total Monthly Fuel Cost</div>
            <div class="text-2xl font-black text-orange-600 mt-2">$118,200.00</div>
        </div>
        <div class="bg-white p-5 rounded-xl border-l-4 border-amber-500 shadow-sm">
            <div class="text-xs font-bold uppercase text-slate-500">Inspections Due Soon</div>
            <div class="text-2xl font-black text-amber-600 mt-2">12 Assets</div>
        </div>
        <div class="bg-white p-5 rounded-xl border-l-4 border-emerald-600 shadow-sm">
            <div class="text-xs font-bold uppercase text-slate-500">Active Fleet Total</div>
            <div class="text-2xl font-black text-emerald-600 mt-2">{{ vehicles|length }} Units</div>
        </div>
    </div>

    <!-- EQUIPMENT PORTAL GRID -->
    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h3 class="text-lg font-black text-slate-900 mb-6 flex items-center gap-2">
            📦 Fleet Equipment Portal & Master Dossiers
        </h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {% for v in vehicles %}
            <div class="bg-white border-2 border-slate-900 rounded-xl p-5 shadow-sm hover:shadow-md transition flex flex-col justify-between relative overflow-hidden">
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
                    <button onclick="alert('Dossier for Unit #{{ v.unit_number }} - Driver: {{ v.driver }} | VIN: {{ v.vin }}')" class="w-full text-center text-xs font-bold text-sky-600 hover:text-sky-700 border border-sky-200 bg-sky-50 py-2 rounded-lg transition">
                        Open Master Dossier →
                    </button>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% elif tab == 'drivers' %}
    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h3 class="text-lg font-black text-slate-900 mb-4">👤 Drivers Compliance & Safety Roster</h3>
        <p class="text-xs text-slate-500 mb-6">Manage CDL expirations, medical cards, and driver safety files for Moonstar & Lionstar drivers.</p>
        <table class="w-full text-left border-collapse text-xs">
            <tr class="bg-slate-900 text-white">
                <th class="p-3">Driver Name</th>
                <th class="p-3">Assigned Unit</th>
                <th class="p-3">Company</th>
                <th class="p-3">CDL Status</th>
                <th class="p-3">Medical Status</th>
            </tr>
            {% for v in vehicles %}
            <tr class="border-b border-slate-200 hover:bg-slate-50">
                <td class="p-3 font-bold text-slate-900">{{ v.driver }}</td>
                <td class="p-3 font-semibold text-sky-600">Unit #{{ v.unit_number }}</td>
                <td class="p-3">{{ v.company }}</td>
                <td class="p-3 text-emerald-600 font-bold">Valid (2027)</td>
                <td class="p-3 text-emerald-600 font-bold">Compliant</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% elif tab == 'imports' %}
    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200 space-y-6">
        <h3 class="text-lg font-black text-slate-900">📥 Automated Telematics, Revenue & Fuel Ingestion</h3>
        <p class="text-xs text-slate-500">Upload export files to sync live mileage, monthly settlement revenue, and fuel card expenses.</p>
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
</div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return Template(LOGIN_HTML).render()

@app.post("/login")
def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    if "@moonstarpa" in email.string.lower() if hasattr(email, 'string') else "@moonstarpa" in email.strip().lower() and password == "Moonstar2026!":
        response = RedirectResponse(url="/dashboard?tab=trucks", status_code=303)
        response.set_cookie(key="user", value=email.strip().lower())
        return response
    return Template(LOGIN_HTML).render(error="Invalid credentials!")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, tab: str = "trucks"):
    user = request.cookies.get("user")
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    vehicles = get_full_fleet()
    return Template(DASHBOARD_HTML).render(user=user, vehicles=vehicles, tab=tab)

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="user")
    return response
