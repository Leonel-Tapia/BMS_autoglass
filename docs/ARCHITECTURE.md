# BMS Autoglass — Arquitectura

Documento técnico de referencia rápida.
**Última actualización:** 2026-09-19

## Stack

- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Frontend: Jinja2 + Bootstrap 5
- PDFs: xhtml2pdf
- Geocoding: Nominatim
- Rutas: OSRM

## Estructura de carpetas

app/
├── main.py            → Punto de entrada, registra routers
├── core/              → template_loader.py (Jinja2)
├── database/          → database.py (get_db, Base)
├── models/            → Tablas SQLAlchemy (por módulo)
├── routers/           → Endpoints FastAPI (por módulo)
├── services/          → Lógica de negocio (poco uso)
├── templates/         → HTML Jinja2 (por módulo)
├── static/images/     → Imágenes
└── utils/             → geocoding.py, routing.py

## Routers principales

| Prefix | Archivo | Rol |
|---|---|---|
| /auth | users/auth_login.py | Login/logout |
| /users | users/users_routers.py | CRUD usuarios |
| /manager | manager/manager_menu.py | Panel manager |
| /company | company/main_menu.py + company_router.py | Empresa |
| /call_center | call_center/* | Búsqueda, menú |
| /estimates | estimates/* | Cotizaciones |
| /inventory | inventory/* | Inventario |
| /invoices | invoices/invoices_router.py | Facturas, pagos, rutas |
| /invoices | invoices/invoice_glass_router.py | InvoiceGlass |
| /technician | invoices/technician_routes.py | Dashboard técnico |
| /customers | customers/* | Clientes |
| /purchases | purchases/* | Compras |
| /vendors | vendors/* | Proveedores |
| /zipcodes | zipcodes/zipcodes_router.py | CP |

## Convenciones

- Modelos: `nombre_model.py` → clase `Nombre`
- Routers: `nombre_router.py` → objeto `router`
- Templates: `nombre.html`
- Cada modelo tiene método `to_dict()`
- Cada router se registra en `main.py`
- Cada template es HTML completo (no usa `{% extends %}`)

## Flujos clave

**Invoice desde Estimate:**
- POST /invoices/generate/{estimate_id} → crea Invoice + copia InvoiceItems

**Registrar pago:**
- POST /invoices/{id}/payments → crea InvoicePayment, recalcula status

**InvoiceGlass:**
- Oficina: POST /invoices/{id}/glasses → crea vidrio ORDERED
- Técnico: POST /technician/glass/{id}/received → cambia a RECEIVED

**Optimizar ruta:**
- POST /invoices/workshop/optimize-route → geocodifica + llama OSRM
- PATCH /invoices/{id}/apply-tentative-time → aplica hora sugerida

**Daily Closing:**
- GET /technician/daily-closing → agrupa pagos del día por método

## Zonas de riesgo (cuidado)

- `app/main.py` → si rompes un import, toda la app cae
- `app/database/database.py` → afecta todas las conexiones
- `app/routers/invoices/invoices_router.py` → dinero
- `app/templates/users/login.html` → nadie puede entrar si se rompe

## Cómo agregar un módulo

1. Crear modelo: `app/models/X/X_model.py`
2. Crear tabla en Railway + local (Railway primero)
3. Crear router: `app/routers/X/X_router.py`
4. Crear template: `app/templates/X/X.html`
5. Registrar router en `app/main.py`
6. Botón en menú correspondiente
7. Commit + push

**Fin.**