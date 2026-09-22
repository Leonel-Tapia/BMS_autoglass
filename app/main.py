# RUTA: app/main.py | ACTUALIZADO: 2026-09-16 (invoice_glass_router registered)
# DESCRIPCIÓN: Punto de entrada principal de BMS Autoglass - Registro de módulos

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware   # 🔥 AGREGADO

# Importaciones de routers existentes
from app.routers.users import users_routers, auth_login
from app.routers.manager import manager_menu
from app.routers.company import main_menu
from app.routers.company import company_router
from app.routers.inventory import inventory, makes_router, models_router

# NUEVO: Módulo Call Center
from app.routers.call_center.callcenter_menu import router as callcenter_menu_router
from app.routers.call_center.callcenter_search import router as callcenter_search_router
from app.routers.call_center.callcenter_lookup import router as callcenter_lookup_router

# NUEVO: Call Center Estimates / Daily Appointments
from app.routers.estimates.estimates_callcenter import router as estimates_callcenter_router

# NUEVO: Menú de Inventario
from app.routers.inventory.inventory_menu_router import router as inventory_menu_router

# NUEVO: Movimientos de Inventario
from app.routers.inventory.inventory_movements_router import router as inventory_movements_router

# NUEVO: Stock Report
from app.routers.inventory.inventory_stock_report_router import router as inventory_stock_report_router

# NUEVO: Windshield Catalog Router
from app.routers.inventory.windshield_router import router as windshield_router

# NUEVO: Years Router (Movido a inventory)
from app.routers.inventory.years_router import router as years_router

# NUEVO: Makes & Models Manager Router (Gestión unificada de marcas, modelos y trims)
from app.routers.inventory.makes_models_router import router as makes_models_router

# Vendors
from app.routers.vendors import vendor_router

# Purchases
from app.routers.purchases import purchase_router
from app.routers.purchases.purchase_receiving_router import router as receiving_router

# Customers
from app.routers.customers.customers_router import router as customers_router
from app.routers.customers.customers_edit_router import router as customers_edit_router

# Estimates (Módulo nuevo)
from app.routers.estimates.estimates_router import router as estimates_router

# Zip Codes
from app.routers.zipcodes.zipcodes_router import router as zipcodes_router

# INVOICES (NUEVO — NECESARIO PARA EL MODAL)
from app.routers.invoices.invoices_router import router as invoices_router

# TÉCNICO - Ruta del día
from app.routers.invoices.technician_routes import router as technician_router

# INVOICE GLASSES (InvoiceGlass Module)
from app.routers.invoices.invoice_glass_router import router as invoice_glass_router


app = FastAPI(title="BMS Autoglass System")

# 🔥 ACTIVAR SESIONES
app.add_middleware(SessionMiddleware, secret_key="BMSAutoglassSecretKey2026")

# ✅ MONTAJE DE ARCHIVOS ESTÁTICOS (logos, imágenes, CSS, etc.)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ---------------------------------------------------------
# REGISTRO DE ROUTERS (Ordenado por flujo de usuario)
# ---------------------------------------------------------

# 1. Auth/Login
app.include_router(auth_login.router)

# 2. Users
app.include_router(users_routers.router)

# 3. Manager
app.include_router(manager_menu.router)

# 4. Company Main Menu
app.include_router(main_menu.router)

# 5. Company CRUD
app.include_router(company_router.router)

# 6. Call Center System
app.include_router(callcenter_menu_router)
app.include_router(callcenter_search_router)
app.include_router(callcenter_lookup_router)
app.include_router(estimates_callcenter_router)  # 🔥 NUEVA RUTA INTEGRADA

# 6. Inventory System
app.include_router(inventory.router)

# 6.1 Inventory Menu
app.include_router(inventory_menu_router)

# 6.2 Inventory Movements
app.include_router(inventory_movements_router)

# 6.3 Stock Report
app.include_router(inventory_stock_report_router)

# 6.4 Makes Router
app.include_router(makes_router.router)

# 6.5 Models Router
app.include_router(models_router.router)

# 6.6 Windshield Catalog Router
app.include_router(windshield_router)

# 6.7 Years Router
app.include_router(years_router)

# 6.8 Makes & Models Manager Router (Gestión unificada de marcas, modelos y trims)
app.include_router(makes_models_router)

# 7. Vendors System
app.include_router(vendor_router.router)

# 7.1 Customers System
app.include_router(customers_router)

# 7.1.1 Customers Edit System
app.include_router(customers_edit_router)

# 7.1.2 Estimates System (Nuevo)
app.include_router(estimates_router)

# 7.3 Invoices System (NUEVO — ACTIVADO)
app.include_router(invoices_router)

# 7.4 Technician Dashboard
app.include_router(technician_router)

# 7.5 Invoice Glasses Module (NUEVO)
app.include_router(invoice_glass_router)

# 7.2 Zip Codes System
app.include_router(zipcodes_router)

# 8. Purchases System
app.include_router(purchase_router.router)

# 9. Receiving System
app.include_router(receiving_router)


@app.get("/")
async def root():
    return {
        "status": "online",
        "system": "BMS Autoglass",
        "version": "1.0.9",
        "date": "07-27-2026",
        "message": "BMS Autoglass System is online and running"
    }