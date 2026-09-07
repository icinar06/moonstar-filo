import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="MOONSTAR EXPRESS LLC — Executive Fleet Console")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    if "@moonstarpa" in email.strip().lower() and password == "Moonstar2026!":
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="user", value=email.strip().lower())
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials!"})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = request.cookies.get("user")
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    # Örnek filo verileri (dosya bağımlılığı yok)
    vehicles = [
        {"unit_number": "8", "unit_type": "TRUCK", "driver": "AT YARD", "hooked_trailer": "None", "monthly_gross": 15000, "monthly_fuel_cost": 4200},
        {"unit_number": "12", "unit_type": "TRUCK", "driver": "ALTUG BACI", "hooked_trailer": "None", "monthly_gross": 22000, "monthly_fuel_cost": 5100}
    ]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "vehicles": vehicles
    })

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="user")
    return response
