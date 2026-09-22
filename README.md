# BMS Autoglass

ERP para negocio de vidrios automotrices (servicio móvil + shop).

Sistema web que gestiona clientes, vehículos, estimates, invoices, pagos,
inventario de vidrios, rutas optimizadas, y control de compras de vidrios
por invoice (InvoiceGlass).

---

## Stack

- **Backend:** FastAPI (Python 3.11) + SQLAlchemy + PostgreSQL
- **Frontend:** Jinja2 + Bootstrap 5 + Font Awesome + JavaScript vanilla
- **PDFs:** xhtml2pdf
- **Geocoding:** Nominatim (gratis)
- **Rutas:** OSRM (gratis)
- **Deploy:** Railway
- **Repositorio:** GitHub

---

## Requisitos previos

Antes de empezar, asegúrate de tener instalado:

- **Python 3.11** ([descargar](https://www.python.org/downloads/))
- **PostgreSQL** (local para desarrollo)
- **pgAdmin** (opcional, para administrar la BD)
- **Git** ([descargar](https://git-scm.com/))
- **VS Code** (recomendado)

Verifica que Python y Git funcionan:

```powershell
python --version   # Debe decir Python 3.11.x
git --version