# Sistema de aprobación de gastos — Bellbird

Aplicación Django para que empleados registren gastos y responsables los aprueben o rechacen. Prueba técnica de selección — ver `DECISIONS.md`, `DELIVERY.md` y `AI_USAGE.md` para contexto adicional.

## Prerrequisitos

- Docker y Docker Compose
- En Windows: Git Bash (para correr los scripts `.sh`) — viene incluido con [Git para Windows](https://git-scm.com/download/win)

## Puesta en marcha

1. Copiá `.env.example` a `.env` y completá las variables (valores de desarrollo alcanzan, sin secretos reales):

```bash
   cp .env.example .env
```

2. Ejecutá:

```bash
   bash run.sh
```

   Esto verifica prerrequisitos, levanta los contenedores, aplica migraciones y carga datos demo automáticamente. La aplicación queda disponible en `http://localhost:8000/`.

## Datos demo

El comando `seed_demo_data` (ejecutado automáticamente por `run.sh`) crea los siguientes usuarios, con contraseña `demo1234` para todos:

| Usuario | Rol | Notas |
|---|---|---|
| `empleado1` | Empleado | Tiene un gasto pendiente, uno aprobado y uno rechazado — permite recorrer los tres estados sin cargar datos a mano |
| `responsable1` | Responsable | Decidió los gastos aprobado/rechazado de `empleado1` en el seed |
| `dual1` | Empleado + Responsable | Para probar en vivo la regla de "nadie aprueba su propio gasto" |

Podés volver a correr el comando en cualquier momento sin duplicar datos (es idempotente):

```bash
docker compose exec web python manage.py seed_demo_data
```

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
| `/responsible/pending/` | Gastos pendientes (filtrable por `?owner=<id>` y `?status=PENDING\|APPROVED\|REJECTED`) |

## Comandos

Correr la suite de tests con cobertura de ramas:

```bash
bash test.sh
```

Requiere que los servicios ya estén levantados (`bash run.sh` primero).

## Arquitectura

Ver `DECISIONS.md` para el detalle de decisiones técnicas (representación de roles, estructura de apps, atomicidad de decisiones, filtros del listado de responsable, etc.).

## Uso de IA

Ver `AI_USAGE.md` para el registro completo de interacciones con IA que influyeron en la solución.