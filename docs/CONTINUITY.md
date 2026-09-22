# BMS Autoglass — Continuidad

Referencias de accesos y contactos para continuidad del proyecto.
**Última actualización:** 2026-09-19

⚠️ IMPORTANTE: Este documento NO contiene credenciales reales.
Las credenciales están en la bóveda de contraseñas (o donde se indique).
Este archivo es solo un MAPA de dónde está cada cosa.

---

## Bóveda de contraseñas

Estado actual: ❌ NO EXISTE
Pendiente: Crear cuenta en 1Password o Bitwarden

Cuando exista, aquí va la referencia:
- Servicio: ____________________
- Cuenta: _____________________
- Master password: (en papel físico / caja fuerte)

---

## Repositorio y código

| Servicio | URL / Ubicación | Credenciales |
|---|---|---|
| GitHub | https://github.com/Leonel-Tapia/BMS Autoglass | En bóveda / navegador |
| Repo local | C:\BMS Autoglass | (no aplica) |
| Backup del código | Disco externo (físico) | (no aplica) |

---

## Servidores / Hosting

| Servicio | URL | Credenciales |
|---|---|---|
| Railway (dashboard) | railway.app | En bóveda / navegador |
| Railway (proyecto) | ____________________ | En bóveda |
| Demo público | ____________________ | (no aplica) |

---

## Base de datos

### LOCAL (desarrollo)
- Host: localhost
- Puerto: 5432
- DB: (ver .env)
- User/Pass: (ver .env)

### PRODUCCIÓN (Railway)
- Host: (ver variables en Railway)
- Puerto: (ver Railway)
- DB: (ver Railway)
- User/Pass: (ver Railway → Variables)

**Para acceder desde pgAdmin:**
- Conexión: BMS Autoglass_Railway
- Credenciales en: Railway → Settings → Variables + bóveda

---

## Correo y servicios externos

| Servicio | Estado | Credenciales |
|---|---|---|
| Gmail / Email empresa | ⏳ por definir | — |
| SendGrid (email transaccional) | ⏳ pendiente | — |
| Twilio (SMS/MMS) | ⏳ pendiente | — |
| Google Cloud (Geocoding) | ⏳ pendiente | — |

---

## Dominio y DNS

Estado: ❌ No comprado aún
Pendiente: Comprar dominio (ej. BMS Autoglass-erp.com)

- Dominio: ____________________
- Registrador: ____________________
- DNS / SSL: ____________________

---

## Personas y roles

### Socios
| Nombre / Iniciales | Rol | Email | Teléfono |
|---|---|---|---|
| (Yo) | Socio técnico | ____________________ | ____________________ |
| ____________________ | Socio | ____________________ | ____________________ |
| ____________________ | Socio | ____________________ | ____________________ |

### Desarrollador externo (futuro)
| Nombre | Rol | Contacto |
|---|---|---|
| ____________________ | Mantenimiento | ____________________ |

---

## Servicios gratuitos en uso (no requieren pago)

| Servicio | Uso | Límite |
|---|---|---|
| Nominatim (OSM) | Geocoding | Uso justo |
| OSRM | Routing | Uso justo |
| Bootstrap CDN | Frontend | Ilimitado |
| Font Awesome CDN | Iconos | Ilimitado |

---

## Riesgos pendientes

| Riesgo | Impacto | Mitigación pendiente |
|---|---|---|
| Contraseña PostgreSQL expuesta | Alto | Cambiar pass + limpiar historial Git |
| `.env` en historial Git | Alto | git filter-repo |
| Sin backup automático BD | Alto | Cron diario en Railway |
| Sin bóveda de contraseñas | Medio | Crear cuenta 1Password/Bitwarden |
| Contraseñas de usuarios en texto plano | Alto | Migrar a bcrypt |
| `.gitignore` con BOM | Bajo | Reescribir sin BOM |
| Sin dominio propio | Bajo | Comprar cuando haya cliente |

---

## Plan de recuperación ante desastres

### Escenario A — Railway cae / deja de funcionar

1. **Datos:** Restaurar desde backup de BD (si existe) o desde Railway
2. **Código:** Clonar desde GitHub
3. **Hosting alternativo:** Render, Fly.io, Heroku, VPS propio

### Escenario B — GitHub se vuelve inaccesible

1. **Código:** Restaurar desde disco externo (último ZIP)
2. **Repo nuevo:** Crear en GitLab / Bitbucket / Gitea
3. **Railway:** Reconectar al repo nuevo

### Escenario C — PostgreSQL Railway corrupto

1. **Backup:** Restaurar de pg_dump más reciente
2. **Nueva BD:** Crear en Railway, importar dump
3. **Código:** No requiere cambio (solo reconectar .env de Railway)

### Escenario D — Sin acceso al desarrollador principal (yo)

1. **Documentación:** Los 4 archivos de docs/ son la fuente
2. **Contratar:** Desarrollador freelance con perfil Python/FastAPI
3. **Alternativa IA:** Claude, ChatGPT, Copilot pueden ayudar

---

## Checklist antes del primer cliente real

- [ ] Cambiar contraseña PostgreSQL (local + Railway)
- [ ] Verificar/purgar `.env` del historial Git
- [ ] Crear backup automático diario de BD
- [ ] Migrar contraseñas a bcrypt
- [ ] Crear bóveda de contraseñas
- [ ] Blindar endpoint `/invoices/void/{id}` con rol admin
- [ ] Comprar dominio propio
- [ ] Probar restauración en máquina limpia (seguir README)
- [ ] Configurar SendGrid (email de invoice)
- [ ] Configurar Twilio (SMS de invoice)
- [ ] Migrar a Google Geocoding

---

**Fin del documento.**