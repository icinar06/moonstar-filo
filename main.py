import os
import pandas as pd
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Template

app = FastAPI(title="MOONSTAR EXPRESS LLC — Executive Fleet Console")

EXCEL_FILE = "Başlıksız e-tablo (2) copy 2 (1).xlsx"

def get_fleet_vehicles():
    if not os.path.exists(EXCEL_FILE):
        return [
            {"unit_number": "8", "unit_type": "TRUCK", "driver": "AT YARD", "monthly_gross": 15000.0, "monthly_fuel_cost": 4200.0},
            {"unit_number": "12", "unit_type": "TRUCK", "driver": "ALTUG BACI", "monthly_gross": 22000.0, "monthly_fuel_cost": 5100.0}
        ]
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=0)
        vehicles = []
        for _, r in df.iterrows():
            unit_val = str(r.get("UNIT", "")).strip()
            if unit_val and unit_val.lower() != "nan":
                drv = str(r.get("DRIVER", "Unassigned")).strip()
                if not drv or drv.lower() == "nan":
                    drv = "Unassigned"
                
                # Make model
                make_model = str(r.get("MAKE-MODEL-YEAR", "TRUCK")).strip()
                if not make_model or make_model.lower() == "nan":
                    make_model = "TRUCK"
                
                vehicles.append({
                    "unit_number": unit_val,
                    "unit_type": make_model,
                    "driver": drv,
                    "monthly_gross": 18500.0,  # Varsayılan örnek aylık ciro
                    "monthly_fuel_cost": 4500.0 # Varsayılan örnek yakıt maliyeti
                })
        return vehicles if vehicles else [{
            "unit_number": "8", "unit_type": "VOLVO", "driver": "AT YARD", "monthly_gross": 15000.0, "monthly_fuel_cost": 4200.0
        }]
    except Exception as e:
        return [{
            "unit_number": "8", "unit_type": "VOLVO", "driver": "AT YARD", "monthly_gross": 15000.0, "monthly_fuel_cost": 4200.0
        }]

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
<div style="max-width: 1000px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
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
