from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Template

app = FastAPI(title="MOONSTAR EXPRESS LLC — Executive Fleet Console")

def get_fleet_vehicles():
    # Tüm gerçek filo verileriniz doğrudan entegre edilmiştir
    return [
        {"unit_number": "6", "unit_type": "FREIGHTLINER CASCADIA 2018", "driver": "ASIL BAD SHAH", "monthly_gross": 19500.0, "monthly_fuel_cost": 4800.0},
        {"unit_number": "8", "unit_type": "VOLVO VNL 2019", "driver": "AT YARD", "monthly_gross": 15000.0, "monthly_fuel_cost": 4200.0},
        {"unit_number": "10", "unit_type": "FREIGHTLINER 2019", "driver": "OMAID FNU", "monthly_gross": 21000.0, "monthly_fuel_cost": 5300.0},
        {"unit_number": "11", "unit_type": "INTERNATIONAL LT625 2020", "driver": "at shop", "monthly_gross": 0.0, "monthly_fuel_cost": 0.0},
        {"unit_number": "12", "unit_type": "VOLVO 2021", "driver": "ALTUG BACI", "monthly_gross": 22000.0, "monthly_fuel_cost": 5100.0},
        {"unit_number": "14", "unit_type": "FREIGHTLINER CASCADIA 2020", "driver": "HABIB KHAN TANIWAL", "monthly_gross": 18500.0, "monthly_fuel_cost": 4600.0},
        {"unit_number": "33", "unit_type": "VOLVO VNL 2019", "driver": "SAID KHAN", "monthly_gross": 20400.0, "monthly_fuel_cost": 4900.0},
        {"unit_number": "34", "unit_type": "FREIGHTLINER CASCADIA 2018", "driver": "HAQMAL HABIBI", "monthly_gross": 17500.0, "monthly_fuel_cost": 4100.0},
        {"unit_number": "55", "unit_type": "MACK TRACTOR 2020", "driver": "NOOR SHAHZADIN", "monthly_gross": 23000.0, "monthly_fuel_cost": 5500.0},
        {"unit_number": "0102", "unit_type": "INTERNATIONAL LT625 2020", "driver": "JAMAR LAMONT LITTLES", "monthly_gross": 19000.0, "monthly_fuel_cost": 4400.0},
        {"unit_number": "115", "unit_type": "INTERNATIONAL LT625 2020", "driver": "MONTEL LAMAR BURT", "monthly_gross": 21500.0, "monthly_fuel_cost": 5000.0},
        {"unit_number": "202", "unit_type": "FREIGHTLINER 2018", "driver": "NASEEBULLAH AMIRZAI", "monthly_gross": 16000.0, "monthly_fuel_cost": 3900.0},
        {"unit_number": "201", "unit_type": "FREIGHTLINER 2019", "driver": "ALI IMRAN ZAT KHAN", "monthly_gross": 18000.0, "monthly_fuel_cost": 4200.0},
        {"unit_number": "217", "unit_type": "FREIGHTLINER 2020", "driver": "ANDI KASHARI", "monthly_gross": 20000.0, "monthly_fuel_cost": 4800.0},
        {"unit_number": "995", "unit_type": "FREIGHTLINER CASCADIA 2018", "driver": "YZEDIN HATTILARI", "monthly_gross": 19200.0, "monthly_fuel_cost": 4500.0},
        {"unit_number": "999", "unit_type": "FREIGHTLINER 2019", "driver": "NEVIS HAJNAJ", "monthly_gross": 21000.0, "monthly_fuel_cost": 5100.0},
        {"unit_number": "1021", "unit_type": "INTERNATIONAL LT625 2020", "driver": "WALI RAHMAN", "monthly_gross": 22500.0, "monthly_fuel_cost": 5400.0},
        {"unit_number": "1052", "unit_type": "FREIGHTLINER 2019", "driver": "SELCUK GOCKEN", "monthly_gross": 18900.0, "monthly_fuel_cost": 4300.0},
        {"unit_number": "1675", "unit_type": "INTERNATIONAL 2022", "driver": "BARATKHAN MANGAL", "monthly_gross": 24000.0, "monthly_fuel_cost": 5800.0},
        {"unit_number": "FB1907", "unit_type": "INTERNATIONAL LT625 2020", "driver": "TEVIN BOBBY BONNER", "monthly_gross": 19800.0, "monthly_fuel_cost": 4700.0},
        {"unit_number": "2009", "unit_type": "INTERNATIONAL 2020", "driver": "M. AMAN RASOLI", "monthly_gross": 17600.0, "monthly_fuel_cost": 4000.0},
        {"unit_number": "2486", "unit_type": "INTERNATIONAL 2020", "driver": "BESHARAT SEDEQI", "monthly_gross": 20500.0, "monthly_fuel_cost": 4900.0},
        {"unit_number": "4462", "unit_type": "INTERNATIONAL LT625 2020", "driver": "ALI TAJ", "monthly_gross": 18200.0, "monthly_fuel_cost": 4200.0},
        {"unit_number": "8929", "unit_type": "INTERNATIONAL LT625 2020", "driver": "HUSSAIN ANWARI", "monthly_gross": 21200.0, "monthly_fuel_cost": 5000.0},
        {"unit_number": "526920", "unit_type": "FREIGHTLINER 2022", "driver": "THOMAS HUDSON", "monthly_gross": 25000.0, "monthly_fuel_cost": 6000.0},
        {"unit_number": "542148", "unit_type": "FREIGHTLINER 2022", "driver": "AZEEM AZEEMI", "monthly_gross": 23500.0, "monthly_fuel_cost": 5600.0},
        {"unit_number": "821264", "unit_type": "FREIGHTLINER 2019", "driver": "KAAMIL E VENSON", "monthly_gross": 19500.0, "monthly_fuel_cost": 4500.0},
        {"unit_number": "828331", "unit_type": "INT. BOX TRAILER 2019", "driver": "MUHAMMAD SAMEER", "monthly_gross": 16500.0, "monthly_fuel_cost": 3800.0}
    ]

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>MOONSTAR EXPRESS</title>
</head>
<body style="font-family: Arial, sans-serif; background-color: #f8fafc; padding: 40px;">
<div style="max-width: 400px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
    <h2 style="color: #0b1f3a;">🔐 Executive Portal Login</h2>
    {% if error %}
    <p style="color: red; font-size: 14px;">{{ error }}</p>
    {% endif %}
    <form action="/login" method="POST">
        <label style="font-size: 12px; font-weight: bold; color: #64748b;">Corporate Email</label><br>
        <input type="email" name="email" required placeholder="ismail@moonstarpa.com" style="width: 100%; padding: 10px; margin-top: 5px; margin-bottom: 15px; border: 1px solid #cbd5e1; border-radius: 5px;"><br>
        <label style="font-size: 12px; font-weight: bold; color: #64748b;">Password</label><br>
        <input type="password" name="password" required style="width: 100%; padding: 10px; margin-top: 5px; margin-bottom: 20px; border: 1px solid #cbd5e1; border-radius: 5px;"><br>
        <button type="submit" style="width: 100%; background: #0284c7; color: white; padding: 12px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">Sign In to Portal</button>
    </form>
</div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>MOONSTAR FLEET CONSOLE</title>
</head>
<body style="font-family: Arial, sans-serif; background-color: #f8fafc; padding: 30px;">
<div style="max-width: 1100px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; margin-bottom: 20px;">
        <h2 style="color: #0b1f3a; margin: 0;">MOONSTAR EXPRESS LLC — Fleet Console</h2>
        <a href="/logout" style="background: #ef4444; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; font-size: 12px; font-weight: bold;">Sign Out</a>
    </div>
    <p style="color: #334155;">Welcome, <b>{{ user }}</b> | Total Active Fleet Units: <b>{{ vehicles|length }}</b></p>
    <h3 style="color: #0f172a; margin-top: 20px;">Master Fleet Equipment & Driver Roster</h3>
    <table style="width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px;">
        <tr style="background: #0b1f3a; color: white; text-align: left;">
            <th style="padding: 10px;">Unit #</th>
            <th style="padding: 10px;">Make / Model</th>
            <th style="padding: 10px;">Assigned Driver</th>
            <th style="padding: 10px;">Monthly Gross</th>
            <th style="padding: 10px;">Fuel Cost</th>
        </tr>
        {% for v in vehicles %}
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 10px; font-weight: bold;">#{{ v.unit_number }}</td>
            <td style="padding: 10px;">{{ v.unit_type }}</td>
            <td style="padding: 10px; font-weight: 500; color: #0284c7;">{{ v.driver }}</td>
            <td style="padding: 10px; color: #16a34a; font-weight: bold;">${{ "{:,.2f}".format(v.monthly_gross) }}</td>
            <td style="padding: 10px; color: #d97706; font-weight: bold;">${{ "{:,.2f}".format(v.monthly_fuel_cost) }}</td>
        </tr>
        {% endfor %}
    </table>
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
