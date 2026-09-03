# Sistema de aprobación de gastos — Bellbird

Aplicación Django para que empleados registren gastos y responsables los aprueben o rechacen. Prueba técnica de selección — ver `DECISIONS.md`, `DELIVERY.md` y `AI_USAGE.md` para contexto adicional.

## Prerrequisitos

- Docker y Docker Compose
- (Alternativa sin Docker) Python 3.13, PostgreSQL 16 o SQLite

## Puesta en marcha (Docker — recomendado)

1. Copiá `.env.example` a `.env` y completá las variables (sin secretos reales, valores de desarrollo alcanzan):

```bash
   cp .env.example .env
```

2. Levantá el stack:

```bash
   docker compose up --build
```

   Esto aplica migraciones automáticamente y levanta el servidor de desarrollo en `http://localhost:8000/`.

3. **[PENDIENTE]** Cargar datos demo — ver sección siguiente.

## Datos demo

> **[PENDIENTE — a completar]**
> Falta el comando/fixture para cargar usuarios demo. Una vez implementado, documentar acá:
> - Comando exacto (`python manage.py loaddata ...` o management command custom)
> - Al menos un usuario empleado y un usuario responsable, con sus credenciales
> - Un caso de gasto ya rechazado, para poder recorrer ese flujo sin crear datos manualmente

## URLs principales

| Ruta | Descripción |
|---|---|
| `/` | Login |
| `/employee/dashboard/` | Panel de empleado |
| `/expenses/` | Mis gastos (empleado) |
| `/expenses/new/` | Crear gasto |
| `/expenses/<id>/` | Detalle de un gasto |
| `/expenses/<id>/edit/` | Editar gasto (solo propio y pendiente) |
| `/responsible/dashboard/` | Panel de responsable |
| `/responsible/pending/` | Gastos pendientes (filtrable por `?owner=` y `?status=`) |

## Comandos

Ejecutar la suite de tests:

```bash
docker compose exec web python manage.py test applications
```

Ejecutar tests con cobertura de ramas:

```bash
docker compose exec web coverage run --branch --source='applications' manage.py test
docker compose exec web coverage report -m
```

> **[PENDIENTE]** Reemplazar por `./run.sh` y `./test.sh` como entrada única, según pide el enunciado (sección 6).

## Arquitectura

Ver `DECISIONS.md` para el detalle de decisiones técnicas (representación de roles, estructura de apps, atomicidad de decisiones, etc.).

## Uso de IA

Ver `AI_USAGE.md` para el registro completo de interacciones con IA que influyeron en la solución.