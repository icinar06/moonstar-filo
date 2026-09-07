from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Template

app = FastAPI(title="MOONSTAR EXPRESS LLC — Executive Fleet Console")

def get_fleet_vehicles():
    return [
        {"unit_number": "6", "unit_type": "TRUCK", "driver": "ASIL BAD SHAH", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "monthly_gross": 19500.0, "monthly_fuel_cost": 4800.0, "net_profit": 14700.0},
        {"unit_number": "8", "unit_type": "TRUCK", "driver": "AT YARD", "status": "READY", "oil_status": "READY", "dot_status": "READY", "monthly_gross": 15000.0, "monthly_fuel_cost": 4200.0, "net_profit": 10800.0},
        {"unit_number": "10", "unit_type": "TRUCK", "driver": "OMAID FNU", "status": "DUE SOON", "oil_status": "READY", "dot_status": "READY", "monthly_gross": 21000.0, "monthly_fuel_cost": 5300.0, "net_profit": 15700.0},
        {"unit_number": "11", "unit_type": "TRUCK", "driver": "at shop", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "monthly_gross": 0.0, "monthly_fuel_cost": 0.0, "net_profit": 0.0},
        {"unit_number": "12", "unit_type": "TRUCK", "driver": "ALTUG BACI", "status": "READY", "oil_status": "READY", "dot_status": "READY", "monthly_gross": 22000.0, "monthly_fuel_cost": 5100.0, "net_profit": 16900.0},
        {"unit_number": "14", "unit_type": "TRUCK", "driver": "HABIB KHAN TANIWAL", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "monthly_gross": 18500.0, "monthly_fuel_cost": 4600.0, "net_profit": 13900.0},
        {"unit_number": "33", "unit_type": "TRUCK", "driver": "SAID KHAN", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "monthly_gross": 20400.0, "monthly_fuel_cost": 4900.0, "net_profit": 15500.0},
        {"unit_number": "34", "unit_type": "TRUCK", "driver": "HAQMAL HABIBI", "status": "READY", "oil_status": "READY", "dot_status": "READY", "monthly_gross": 17500.0, "monthly_fuel_cost": 4100.0, "net_profit": 13400.0},
        {"unit_number": "55", "unit_type": "TRUCK", "driver": "NOOR SHAHZADIN", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "monthly_gross": 23000.0, "monthly_fuel_cost": 5500.0, "net_profit": 17500.0},
        {"unit_number": "0102", "unit_type": "TRUCK", "driver": "JAMAR LAMONT LITTLES", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "monthly_gross": 19000.0, "monthly_fuel_cost": 4400.0, "net_profit": 14600.0},
        {"unit_number": "115", "unit_type": "TRUCK", "driver": "MONTEL LAMAR BURT", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "monthly_gross": 21500.0, "monthly_fuel_cost": 5000.0, "net_profit": 16500.0},
        {"unit_number": "202", "unit_type": "TRUCK", "driver": "NASEEBULLAH AMIRZAI", "status": "READY", "oil_status": "READY", "dot_status": "READY", "monthly_gross": 16000.0, "monthly_fuel_cost": 3900.0, "net_profit": 12100.0},
        {"unit_number": "201", "unit_type": "TRUCK", "driver": "ALI IMRAN ZAT KHAN", "status": "READY", "oil_status": "READY", "dot_status": "READY", "monthly_gross": 18000.0, "monthly_fuel_cost": 4200.0, "net_profit": 13800.0},
        {"unit_number": "217", "unit_type": "TRUCK", "driver": "ANDI KASHARI", "status": "DUE SOON", "oil_status": "READY", "dot_status": "DUE SOON", "monthly_gross": 20000.0, "monthly_fuel_cost": 4800.0, "net_profit": 15200.0},
        {"unit_number": "995", "unit_type": "TRUCK", "driver": "YZEDIN HATTILARI", "status": "READY", "oil_status": "READY", "dot_status": "READY", "monthly_gross": 19200.0, "monthly_fuel_cost": 4500.0, "net_profit": 14700.0},
        {"unit_number": "999", "unit_type": "TRUCK", "driver": "NEVIS HAJNAJ", "status": "DUE SOON", "oil_status": "READY", "dot_status": "READY", "monthly_gross": 21000.0, "monthly_fuel_cost": 5100.0, "net_profit": 15900.0}
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
        <span class="text-3xl font-black text-slate-900 tracking-wide font-sans">MOON<span class="text-orange-500">★</span>TAR</span>
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
            <span class="text-xs text-slate-200">User: <b>{{ user }}</b></span>
            <a href="/logout" class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-xs font-bold uppercase transition shadow">Sign Out</a>
        </div>
    </header>

    <!-- KPI CARDS -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-white p-5 rounded-xl border-l-4 border-sky-600 shadow-sm">
            <div class="text-xs font-bold uppercase text-slate-500">Monthly Fleet Gross (ITS)</div>
            <div class="text-2xl font-black text-sky-600 mt-2">$305,100.00</div>
        </div>
        <div class="bg-white p-5 rounded-xl border-l-4 border-orange-500 shadow-sm">
            <div class="text-xs font-bold uppercase text-slate-500">Total Monthly Fuel Cost</div>
            <div class="text-2xl font-black text-orange-600 mt-2">$73,400.00</div>
        </div>
        <div class="bg-white p-5 rounded-xl border-l-4 border-amber-500 shadow-sm">
            <div class="text-xs font-bold uppercase text-slate-500">Inspections Due Soon</div>
            <div class="text-2xl font-black text-amber-600 mt-2">10 Assets</div>
        </div>
        <div class="bg-white p-5 rounded-xl border-l-4 border-emerald-600 shadow-sm">
            <div class="text-xs font-bold uppercase text-slate-500">Active Fleet Total</div>
            <div class="text-2xl font-black text-emerald-600 mt-2">{{ vehicles|length }} Trucks</div>
        </div>
    </div>

    <!-- EQUIPMENT PORTAL GRID (KUTUCUKLAR) -->
    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h3 class="text-lg font-black text-slate-900 mb-6 flex items-center gap-2">
            📦 Fleet Equipment Portal (Click unit for dossier)
        </h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {% for v in vehicles %}
            <div class="bg-white border-2 border-slate-900 rounded-xl p-5 shadow-sm hover:shadow-md transition flex flex-col justify-between relative overflow-hidden">
                <!-- Sol Kenar Şeridi (Duruma Göre Renk) -->
                <div class="absolute left-0 top-0 bottom-0 w-2 {% if v.status == 'DUE SOON' %}bg-amber-500{% else %}bg-emerald-500{% endif %}"></div>
                
                <div class="pl-3">
                    <div class="flex justify-between items-center border-b border-slate-200 pb-2 mb-3">
                        <span class="font-black text-slate-900 text-sm">UNIT #{{ v.unit_number }} ({{ v.unit_type }})</span>
                        <span class="text-[10px] font-bold px-2 py-0.5 rounded {% if v.status == 'DUE SOON' %}bg-amber-100 text-amber-700{% else %}bg-emerald-100 text-emerald-700{% endif %}">{{ v.status }}</span>
                    </div>
                    <div class="space-y-1 text-xs text-slate-700">
                        <div><b>Driver:</b> <span class="text-sky-600 font-semibold">{{ v.driver }}</span></div>
                        <div><b>Oil Service:</b> {{ v.oil_status }}</div>
                        <div><b>Annual DOT:</b> {{ v.dot_status }}</div>
                        <div class="pt-2 border-t border-slate-100 font-semibold text-slate-900">
                            Gross: ${{ "{:,.0f}".format(v.monthly_gross) }} | Net: ${{ "{:,.0f}".format(v.net_profit) }}
                        </div>
                    </div>
                </div>
                <div class="mt-4 pl-3">
                    <button class="w-full text-center text-xs font-bold text-sky-600 hover:text-sky-700 border border-sky-200 bg-sky-50 py-2 rounded-lg transition">
                        Open Master Dossier →
                    </button>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
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
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="user", value=email.strip().lower())
        return response
    return Template(LOGIN_HTML).render(error="Invalid credentials!")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = request.cookies.get("user")
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    vehicles = get_fleet_vehicles()
    return Template(DASHBOARD_HTML).render(user=user, vehicles=vehicles)

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="user")
    return response
