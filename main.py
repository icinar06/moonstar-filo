from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="MOONSTAR EXPRESS LLC — Executive Fleet Console")

SPA_HTML = """



MOONSTAR EXPRESS LLC — Master Fleet Console



.brand-font { font-family: 'Montserrat', sans-serif; } body { font-family: 'Inter', sans-serif; }


    
    
        ★
        
            🏠
            🚛
            📦
            👤
        
    

    
        
            
                MOON★TAR
                EXPRESS LLC
            
            
                User: ismail@moonstarpa.com
                System Online
            
        

        
            
                Home / Analytics
                Trucks Master ()
                Trailers Master ()
                Drivers Roster ()
            
            
                
            
        

        
            

            

            

            
        
    

    
        function fleetApp() {
            return {
                tab: 'home',
                drivers: [
                    { name: "ALTUG BACI", phone: "954-669-6229", cdl: "B227-564", medical: "2026-08-26", truck: "12" },
                    { name: "FIERALDO", phone: "267-764-8746", cdl: "34593649", medical: "2026-08-26", truck: "12" },
                    { name: "BRYAN MAHMUTAJ", phone: "215-555-0138", cdl: "PA-388031", medical: "2027-10-01", truck: "38" },
                    { name: "WAHDAT SAFI", phone: "215-555-0153", cdl: "PA-764360", medical: "2027-07-26", truck: "53" },
                    { name: "FERHADULLAH WESAL", phone: "215-555-0163", cdl: "PA-794680", medical: "2027-07-27", truck: "63" },
                    { name: "ALI TAJ", phone: "215-555-0442", cdl: "PA-662570", medical: "2027-07-27", truck: "4462" },
                    { name: "BULENT / ASIL BAD SHAH", phone: "215-555-0192", cdl: "PA-982341", medical: "2026-12-01", truck: "06" },
                    { name: "DINDAR RAHMANI", phone: "215-555-0177", cdl: "PA-112344", medical: "2027-01-15", truck: "Unassigned" },
                    { name: "HABIB TANIWAL", phone: "215-555-0114", cdl: "PA-598991", medical: "2026-10-01", truck: "14" },
                    { name: "BESHARAT SEDEQI", phone: "215-555-0248", cdl: "PA-808390", medical: "2027-03-27", truck: "2486" },
                    { name: "HUSSAIN ANWARI", phone: "215-555-0892", cdl: "PA-642540", medical: "2026-11-26", truck: "8929" },
                    { name: "ISMAIL CINAR", phone: "347-444-1686", cdl: "PA-OWNER", medical: "2027-01-01", truck: "41" },
                    { name: "NOOR SHAHZADIN", phone: "215-555-0155", cdl: "PA-482560", medical: "2026-11-26", truck: "55" },
                    { name: "JOSHUA DIAZ", phone: "215-555-0131", cdl: "PA-849821", medical: "2026-11-01", truck: "31" },
                    { name: "MOHAMMAD MALAK", phone: "215-555-0101", cdl: "PA-010101", medical: "2027-01-15", truck: "01" },
                    { name: "TEVIN BOBBY", phone: "215-555-1907", cdl: "PA-190719", medical: "2026-08-26", truck: "FB1907" },
                    { name: "AT YARD", phone: "215-555-0144", cdl: "PA-334", medical: "2027-01-15", truck: "8" }
                ],
                trucks: [
                    { unit: "FB1907", type: "2022 INTERNATIONAL", driver: "TEVIN BOBBY", gross: 19800.0, fuel: 4700.0, maintenance: 500.0 },
                    { unit: "8", type: "VOLVO Vnl64t", driver: "AT YARD", gross: 15000.0, fuel: 4200.0, maintenance: 300.0 },
                    { unit: "10", type: "FREIGHTLINER", driver: "OMAID FNU", gross: 21000.0, fuel: 5300.0, maintenance: 650.0 },
                    { unit: "12", type: "VOLVO 2021", driver: "ALTUG BACI", gross: 22000.0, fuel: 5100.0, maintenance: 500.0 }
                ],
                trailers: [
                    { unit: "127", type: "22' Van", plate: "516-6421 ME", assigned_truck: "FB1907" },
                    { unit: "209536611", type: "53' Reefer", plate: "-", assigned_truck: "8" }
                ],
                get totalNetProfit() {
                    let net = this.trucks.reduce((acc, t) => acc + (t.gross - t.fuel - t.maintenance), 0);
                    return '$' + net.toLocaleString('en-US', {maximumFractionDigits: 0});
                },
                formatMoney(val) {
                    return '$' + val.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
                }
            }
        }
    


""""""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>MOONSTAR EXPRESS LLC — Master Fleet Console</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
<style>.brand-font { font-family: 'Montserrat', sans-serif; } body { font-family: 'Inter', sans-serif; }</style>
</head>
<body class="bg-slate-50 min-h-screen flex" x-data="fleetApp()">
    
    <aside class="w-20 bg-slate-900 flex flex-col items-center py-6 space-y-8 border-r border-slate-800">
        <div class="brand-font text-sky-400 font-black text-xl">★</div>
        <div class="flex flex-col space-y-6 text-slate-400">
            <button @click="tab = 'home'" :class="tab === 'home' ? 'bg-sky-600 text-white' : 'hover:bg-slate-800'" class="p-3 rounded-xl transition" title="Home">🏠</button>
            <button @click="tab = 'trucks'" :class="tab === 'trucks' ? 'bg-sky-600 text-white' : 'hover:bg-slate-800'" class="p-3 rounded-xl transition" title="Trucks">🚛</button>
            <button @click="tab = 'trailers'" :class="tab === 'trailers' ? 'bg-sky-600 text-white' : 'hover:bg-slate-800'" class="p-3 rounded-xl transition" title="Trailers">📦</button>
            <button @click="tab = 'drivers'" :class="tab === 'drivers' ? 'bg-sky-600 text-white' : 'hover:bg-slate-800'" class="p-3 rounded-xl transition" title="Drivers">👤</button>
        </div>
    </aside>

    <div class="flex-1 flex flex-col min-w-0">
        <header class="bg-gradient-to-r from-slate-900 via-blue-950 to-sky-600 px-8 py-4 shadow-md border-b-4 border-orange-500 flex justify-between items-center text-white">
            <div class="flex items-center space-x-3">
                <span class="brand-font text-2xl font-black tracking-wide">MOON<span class="text-orange-500">★</span>TAR</span>
                <span class="text-xs font-semibold text-sky-300 border border-sky-400 px-2 py-0.5 rounded">EXPRESS LLC</span>
            </div>
            <div class="flex items-center space-x-4 text-xs">
                <span>User: <b>ismail@moonstarpa.com</b></span>
                <span class="bg-emerald-600 px-3 py-1.5 rounded-lg font-bold uppercase shadow">System Online</span>
            </div>
        </header>

        <div class="bg-white border-b border-slate-200 px-8 py-3 flex justify-between items-center shadow-sm">
            <div class="flex space-x-3">
                <button @click="tab = 'home'" :class="tab === 'home' ? 'bg-slate-900 text-white shadow' : 'text-slate-600 hover:bg-slate-100'" class="px-4 py-2 text-xs font-bold uppercase rounded-lg transition">Home / Analytics</button>
                <button @click="tab = 'trucks'" :class="tab === 'trucks' ? 'bg-slate-900 text-white shadow' : 'text-slate-600 hover:bg-slate-100'" class="px-4 py-2 text-xs font-bold uppercase rounded-lg transition">Trucks Master (<span x-text="trucks.length"></span>)</button>
                <button @click="tab = 'trailers'" :class="tab === 'trailers' ? 'bg-slate-900 text-white shadow' : 'text-slate-600 hover:bg-slate-100'" class="px-4 py-2 text-xs font-bold uppercase rounded-lg transition">Trailers Master (<span x-text="trailers.length"></span>)</button>
                <button @click="tab = 'drivers'" :class="tab === 'drivers' ? 'bg-slate-900 text-white shadow' : 'text-slate-600 hover:bg-slate-100'" class="px-4 py-2 text-xs font-bold uppercase rounded-lg transition">Drivers Roster (<span x-text="drivers.length"></span>)</button>
            </div>
            <div>
                <template x-if="tab === 'drivers'">
                    <button @click="openAddDriver = true" class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-xs font-bold uppercase shadow">+ Add Driver</button>
                </template>
            </div>
        </div>

        <main class="p-8 space-y-6 flex-1">
            <template x-if="tab === 'home'">
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div class="bg-white p-5 rounded-xl border-l-4 border-sky-600 shadow-sm">
                        <div class="text-xs font-bold uppercase text-slate-500">Total Trucks</div>
                        <div class="text-3xl font-black text-sky-600 mt-2" x-text="trucks.length"></div>
                    </div>
                    <div class="bg-white p-5 rounded-xl border-l-4 border-orange-500 shadow-sm">
                        <div class="text-xs font-bold uppercase text-slate-500">Total Trailers</div>
                        <div class="text-3xl font-black text-orange-600 mt-2" x-text="trailers.length"></div>
                    </div>
                    <div class="bg-white p-5 rounded-xl border-l-4 border-emerald-600 shadow-sm">
                        <div class="text-xs font-bold uppercase text-slate-500">Active Drivers</div>
                        <div class="text-3xl font-black text-emerald-600 mt-2" x-text="drivers.length"></div>
                    </div>
                    <div class="bg-white p-5 rounded-xl border-l-4 border-indigo-600 shadow-sm">
                        <div class="text-xs font-bold uppercase text-slate-500">Filo Net Kar</div>
                        <div class="text-3xl font-black text-indigo-600 mt-2" x-text="totalNetProfit"></div>
                    </div>
                </div>
            </template>

            <template x-if="tab === 'trucks'">
                <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                    <div class="p-5 border-b border-slate-200 bg-slate-50"><h3 class="font-black text-slate-900 text-base">🚛 Master Trucks Inventory</h3></div>
                    <table class="w-full text-left border-collapse text-xs">
                        <thead>
                            <tr class="bg-slate-900 text-white">
                                <th class="p-3">Unit #</th>
                                <th class="p-3">Make / Model</th>
                                <th class="p-3">Assigned Driver</th>
                                <th class="p-3">Gross Revenue</th>
                                <th class="p-3">Net Profit</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-200">
                            <template x-for="t in trucks" :key="t.unit">
                                <tr class="hover:bg-slate-50">
                                    <td class="p-3 font-black text-slate-900" x-text="'#' + t.unit"></td>
                                    <td class="p-3 text-slate-700" x-text="t.type"></td>
                                    <td class="p-3 font-bold text-sky-600" x-text="t.driver"></td>
                                    <td class="p-3 text-emerald-600 font-bold" x-text="formatMoney(t.gross)"></td>
                                    <td class="p-3 font-black text-emerald-700" x-text="formatMoney(t.gross - t.fuel - t.maintenance)"></td>
                                </tr>
                            </template>
                        </tbody>
                    </table>
                </div>
            </template>

            <template x-if="tab === 'trailers'">
                <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                    <div class="p-5 border-b border-slate-200 bg-slate-50"><h3 class="font-black text-slate-900 text-base">📦 Master Trailers Inventory</h3></div>
                    <table class="w-full text-left border-collapse text-xs">
                        <thead>
                            <tr class="bg-slate-900 text-white">
                                <th class="p-3">Unit #</th>
                                <th class="p-3">Trailer Type</th>
                                <th class="p-3">Plate Number</th>
                                <th class="p-3">Assigned Truck</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-200">
                            <template x-for="tr in trailers" :key="tr.unit">
                                <tr class="hover:bg-slate-50">
                                    <td class="p-3 font-black text-slate-900" x-text="'#' + tr.unit"></td>
                                    <td class="p-3 text-slate-700" x-text="tr.type"></td>
                                    <td class="p-3 text-slate-600" x-text="tr.plate"></td>
                                    <td class="p-3 font-bold text-sky-600" x-text="'Truck #' + tr.assigned_truck"></td>
                                </tr>
                            </template>
                        </tbody>
                    </table>
                </div>
            </template>

            <template x-if="tab === 'drivers'">
                <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                    <div class="p-5 border-b border-slate-200 bg-slate-50"><h3 class="font-black text-slate-900 text-base">👤 Master Drivers Roster (<span x-text="drivers.length"></span> Active)</h3></div>
                    <table class="w-full text-left border-collapse text-xs">
                        <thead>
                            <tr class="bg-slate-900 text-white">
                                <th class="p-3">Driver Name</th>
                                <th class="p-3">Phone</th>
                                <th class="p-3">CDL & Expiry</th>
                                <th class="p-3">Medical Due</th>
                                <th class="p-3">Truck</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-200">
                            <template x-for="d in drivers" :key="d.name">
                                <tr class="hover:bg-slate-50">
                                    <td class="p-3 font-black text-slate-900" x-text="d.name"></td>
                                    <td class="p-3 text-slate-600"><a :href="'tel:' + d.phone" class="text-sky-600 font-bold" x-text="d.phone"></a></td>
                                    <td class="p-3 text-slate-700" x-text="d.cdl"></td>
                                    <td class="p-3 font-bold text-amber-700" x-text="d.medical"></td>
                                    <td class="p-3 font-bold text-sky-600" x-text="'Truck #' + d.truck"></td>
                                </tr>
                            </template>
                        </tbody>
                    </table>
                </div>
            </template>
        </main>
    </div>

    <script>
        function fleetApp() {
            return {
                tab: 'home',
                drivers: [
                    { name: "ALTUG BACI", phone: "954-669-6229", cdl: "B227-564", medical: "2026-08-26", truck: "12" },
                    { name: "FIERALDO", phone: "267-764-8746", cdl: "34593649", medical: "2026-08-26", truck: "12" },
                    { name: "BRYAN MAHMUTAJ", phone: "215-555-0138", cdl: "PA-388031", medical: "2027-10-01", truck: "38" },
                    { name: "WAHDAT SAFI", phone: "215-555-0153", cdl: "PA-764360", medical: "2027-07-26", truck: "53" },
                    { name: "FERHADULLAH WESAL", phone: "215-555-0163", cdl: "PA-794680", medical: "2027-07-27", truck: "63" },
                    { name: "ALI TAJ", phone: "215-555-0442", cdl: "PA-662570", medical: "2027-07-27", truck: "4462" },
                    { name: "BULENT / ASIL BAD SHAH", phone: "215-555-0192", cdl: "PA-982341", medical: "2026-12-01", truck: "06" },
                    { name: "DINDAR RAHMANI", phone: "215-555-0177", cdl: "PA-112344", medical: "2027-01-15", truck: "Unassigned" },
                    { name: "HABIB TANIWAL", phone: "215-555-0114", cdl: "PA-598991", medical: "2026-10-01", truck: "14" },
                    { name: "BESHARAT SEDEQI", phone: "215-555-0248", cdl: "PA-808390", medical: "2027-03-27", truck: "2486" },
                    { name: "HUSSAIN ANWARI", phone: "215-555-0892", cdl: "PA-642540", medical: "2026-11-26", truck: "8929" },
                    { name: "ISMAIL CINAR", phone: "347-444-1686", cdl: "PA-OWNER", medical: "2027-01-01", truck: "41" },
                    { name: "NOOR SHAHZADIN", phone: "215-555-0155", cdl: "PA-482560", medical: "2026-11-26", truck: "55" },
                    { name: "JOSHUA DIAZ", phone: "215-555-0131", cdl: "PA-849821", medical: "2026-11-01", truck: "31" },
                    { name: "MOHAMMAD MALAK", phone: "215-555-0101", cdl: "PA-010101", medical: "2027-01-15", truck: "01" },
                    { name: "TEVIN BOBBY", phone: "215-555-1907", cdl: "PA-190719", medical: "2026-08-26", truck: "FB1907" },
                    { name: "AT YARD", phone: "215-555-0144", cdl: "PA-334", medical: "2027-01-15", truck: "8" }
                ],
                trucks: [
                    { unit: "FB1907", type: "2022 INTERNATIONAL", driver: "TEVIN BOBBY", gross: 19800.0, fuel: 4700.0, maintenance: 500.0 },
                    { unit: "8", type: "VOLVO Vnl64t", driver: "AT YARD", gross: 15000.0, fuel: 4200.0, maintenance: 300.0 },
                    { unit: "10", type: "FREIGHTLINER", driver: "OMAID FNU", gross: 21000.0, fuel: 5300.0, maintenance: 650.0 },
                    { unit: "12", type: "VOLVO 2021", driver: "ALTUG BACI", gross: 22000.0, fuel: 5100.0, maintenance: 500.0 }
                ],
                trailers: [
                    { unit: "127", type: "22' Van", plate: "516-6421 ME", assigned_truck: "FB1907" },
                    { unit: "209536611", type: "53' Reefer", plate: "-", assigned_truck: "8" }
                ],
                get totalNetProfit() {
                    let net = this.trucks.reduce((acc, t) => acc + (t.gross - t.fuel - t.maintenance), 0);
                    return '$' + net.toLocaleString('en-US', {maximumFractionDigits: 0});
                },
                formatMoney(val) {
                    return '$' + val.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
                }
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def read_root():
    return HTMLResponse(content=SPA_HTML, status_code=200)

@app.get("/dashboard", response_class=HTMLResponse)
def read_dashboard():
    return HTMLResponse(content=SPA_HTML, status_code=200)
