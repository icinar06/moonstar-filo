import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, Form, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import pandas as pd

app = FastAPI(title="MOONSTAR EXPRESS LLC — Executive Fleet Console")

# HTML şablonları için 'templates' klasörünü tanıtıyoruz
templates = Jinja2Templates(directory="templates")

DB_FILE = "fleet_database.db"
DRIVERS_FILE = "Drivers.xlsx"

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# 1. SAYFA: GİRİŞ EKRANI (MOONSTAR ORİJİNAL WEB SİTESİ)
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 2. İŞLEM: GİRİŞ YAPMA KONTROLÜ
@app.post("/login")
def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    if "@moonstarpa" in email.strip().lower() and password == "Moonstar2026!":
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="user", value=email.strip().lower())
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials!"})

# 3. SAYFA: ANA FİLO YÖNETİM PANELİ (DASHBOARD)
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = request.cookies.get("user")
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    conn = get_db()
    vehicles = conn.execute("SELECT * FROM vehicles ORDER BY unit_number ASC").fetchall()
    conn.close()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "vehicles": vehicles
    })

# 4. İŞLEM: ÇIKIŞ YAP (SIGN OUT)
@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="user")
    return response
