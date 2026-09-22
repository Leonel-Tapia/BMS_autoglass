# BMS Autoglass — Base de Datos

Referencia del schema de PostgreSQL.
**Última actualización:** 2026-09-19

## Índice de tablas (27 en total)

### Company / Users
- `company` — Datos del taller (nombre, dirección, costos default)
- `users` — Usuarios del sistema (admin, manager, sales, technician)

### Clientes
- `customers` — Clientes con contacto, vehículos y coordenadas GPS
- `zipcodes` — Catálogo de CP → ciudad/estado

### Vehículos (catálogos)
- `vehicle_makes` — Marcas (Toyota, Honda...)
- `vehicle_models` — Modelos por marca
- `vehicle_trims` — Trims por modelo
- `vehicle_years` — Años
- `time_catalog` — Catálogo de horas para citas (08:00, 08:05...)

### Estimates
- `estimates` — Cotizaciones
- `estimate_details` — Items de cotización
- `estimates_history` — Historial de cambios

### Invoices
- `invoices` — Facturas
- `invoice_items` — Items de factura (partes + labor + materiales)
- `invoice_payments` — Pagos registrados
- `invoice_activities` — Actividades/notas de la factura
- `invoice_glasses` — Vidrios comprados por factura (módulo InvoiceGlass)

### Inventario
- `inventory_parts` — Partes físicas en inventario
- `inventory_movements` — Movimientos entrada/salida
- `windshield_catalog` — Catálogo de vidrios (NAGS codes)
- `windshield_catalog_vendor_prices` — Precios por proveedor

### Compras
- `purchase_orders` — Órdenes de compra
- `purchase_order_details` — Items de la OC
- `purchase_order_receiving` — Recepciones (parciales y completas)
- `purchase_price_variances` — Diferencias de precio facturado vs OC

### Otros
- `vendors` — Proveedores (Mygrant, Pilkington...)
- `concepts` — Conceptos para actividades

---

## Tablas críticas en detalle

### `company` (25 columnas)

Registro único del taller. Se usa en PDFs de invoice y rutas.

**Campos principales:**
| Campo | Tipo | Uso |
|---|---|---|
| `id` | int | PK |
| `trade_name` | varchar | Nombre comercial (para PDFs) |
| `legal_name` | varchar | Razón social |
| `tax_id` | varchar | RFC / EIN |
| `address`, `neighborhood`, `city`, `state`, `postal_code` | varchar | Dirección completa |
| `main_phone`, `main_email` | varchar | Contacto principal |
| `invoice_notice` | text | Texto al pie de la factura |
| `general_sales_tax` | numeric | % tax por default |
| `mobile_fee` | numeric | Cargo móvil por default |
| `labor_cost`, `materials_cost`, `misc_cost` | numeric | Costos base |
| `origin_address` | text | Punto de partida para rutas |

---

### `users`

Empleados del sistema.

| Campo | Tipo | Uso |
|---|---|---|
| `id` | int | PK |
| `full_name` | text | Nombre completo |
| `username` | text | Login |
| `password` | text | ⚠️ ACTUALMENTE EN TEXTO PLANO (pendiente bcrypt) |
| `email` | text | Correo |
| `role` | text | ADMIN / MANAGER / SALES / TECHNICIAN |
| `is_active` | boolean | Login habilitado |

---

### `customers` (~40 columnas)

Cliente con datos extendidos.

**Campos clave:**
| Campo | Tipo | Uso |
|---|---|---|
| `id` | int | PK |
| `name` | varchar | Nombre |
| `business_name` | varchar | Nombre de negocio (flotas) |
| `phone`, `phone2` | varchar | Teléfonos |
| `email` | varchar | Email |
| `address`, `city`, `state`, `zip_code` | varchar/text | Dirección |
| `language` | varchar | ENGLISH / SPANISH |
| `mood` | varchar | HAPPY / NEUTRAL / ANGRY |
| `allow_sms` | boolean | Permite SMS |
| `latitude`, `longitude` | double | Coordenadas GPS (para rutas) |
| `status` | varchar | ACTIVE / INACTIVE |

**Nota:** `latitude` y `longitude` se llenan automáticamente al optimizar rutas (Nominatim).

---

### `invoices` (~50 columnas)

Factura generada desde un estimate.

**Estados (`status`):**
- `PENDING` — Pendiente de cobro
- `PAID` — Cobrada completamente
- `PARTIALLY_PAID` — Cobro parcial
- `VOID` — Anulada
- `CANCELLED` — Cancelada
- `NO_SHOW` — Cliente no llegó

**Estados (`payment_status`):**
- `PENDING` — No confirmado en banco
- (vacío) — Sin uso activo actualmente

**Campos clave:**
| Campo | Tipo | Uso |
|---|---|---|
| `id` | int | PK |
| `estimate_id` | int | FK → estimates (opcional) |
| `customer_id` | int | FK → customers |
| `vehicle_year_id`, `vehicle_make`, `vehicle_model`, `vehicle_vin` | varios | Datos del vehículo |
| `estimated_appointment_date`, `estimated_appointment_time` | date/time | Cita |
| `technician_id` | int | FK → users (técnico asignado) |
| `tentative_time` | timestamp | Hora sugerida por Optimize Route (temporal) |
| `status` | varchar | Estado del cobro |
| `subtotal`, `tax`, `total` | numeric | Cálculos |
| `labor_cost`, `materials_cost`, `misc_cost` | numeric | Costos por línea |
| `service_type` | varchar | SHOP / MOVIL |
| `created_by`, `created_at` | varchar/timestamp | Auditoría |

**Estados que usa el módulo de rutas:**
- `technician_id` es **obligatorio** para optimizar ruta
- Si falta → el botón "Optimize" se bloquea

---

### `invoice_items`

Items de la factura (partes, labor, materiales, misc).

| Campo | Tipo | Uso |
|---|---|---|
| `id` | int | PK |
| `invoice_id` | int | FK → invoices |
| `product_name` | varchar | NAGS code o nombre |
| `description` | varchar | Descripción |
| `quantity` | int | Cantidad |
| `cost` | numeric | Costo |
| `price` | numeric | Precio venta |
| `is_taxable`, `tax_amount` | boolean/numeric | IVA |
| `part_number` | varchar | Part number |

**Nota:** Al actualizar un invoice, los items viejos se borran y se recrean.

---

### `invoice_payments`

Pagos registrados contra una factura.

| Campo | Tipo | Uso |
|---|---|---|
| `id` | int | PK |
| `invoice_id` | int | FK → invoices |
| `payment_type` | varchar | CASH / CREDIT_CARD / CHECK / TRANSFER / ZELLE / OTHER |
| `amount` | numeric | Monto |
| `payment_date` | date | Fecha del pago |
| `reference` | varchar | # check, autorización |
| `payment_status` | varchar | PENDING / DEPOSITED / BOUNCED / REJECTED / VOID / REFUNDED |
| `deposited_at`, `deposited_by` | timestamp/varchar | Confirmación bancaria |
| `rejection_reason`, `fee_amount` | text/numeric | Si rebotó |

**Lógica:** al crear pago → recalcula `invoice.status`.

---

### `invoice_glasses` (23 columnas)

Módulo InvoiceGlass. Vidrio comprado por factura.

| Campo | Tipo | Uso |
|---|---|---|
| `id` | int | PK |
| `invoice_id` | int | FK → invoices |
| `vendor` | varchar | Mygrant, Pilkington... |
| `nags_code` | varchar | Código NAGS |
| `description` | varchar | Descripción |
| `glass_type`, `position` | varchar | Tipo y posición |
| `purchase_price`, `sales_price` | numeric | Precios |
| `purchase_date`, `vendor_invoice_date` | date | Fechas |
| `status` | varchar | ORDERED / RECEIVED / INSTALLED / DAMAGED / RETURNED / CANCELLED |
| `payment_status` | varchar | PAID / CREDIT / PENDING |
| `received_at`, `received_by` | timestamp/varchar | Recepción por técnico |
| `return_date`, `return_reason` | date/varchar | Devolución |
| `storage_location` | varchar | Ubicación física |

---

## Otras tablas (uso rápido)

### `estimates` / `estimate_details`
Mismos campos que invoices pero para cotización previa.
Cuando el cliente acepta → se genera invoice.

### `vendors`
Proveedores de vidrios y partes.

### `windshield_catalog` / `windshield_catalog_vendor_prices`
Catálogo de vidrios con NAGS + precios por proveedor.

### `purchase_orders` y derivadas
Órdenes de compra a proveedores (con recepciones parciales).

### `inventory_parts` / `inventory_movements`
Inventario físico de partes y movimientos.

### `concepts`
Conceptos para las actividades del invoice (ej. "Cliente llamó", "Vidrio dañado").

### `zipcodes`
Catálogo CP → ciudad/estado (búsqueda rápida).

### `time_catalog`
Catálogo de horas válidas para citas (08:00 a 19:00 en intervalos de 5 min).

### `vehicle_makes`, `vehicle_models`, `vehicle_trims`, `vehicle_years`
Catálogos de vehículos. Se usan en el selector del invoice.

---

## Relaciones principales
