# DECISIONS.md

Este documento registra las decisiones técnicas tomadas durante el desarrollo del sistema de aprobación de gastos, las alternativas consideradas y por qué se descartaron.

---

## 1. Representación de roles (Empleado / Responsable)

**Decisión:** Dos campos booleanos en un modelo `User` custom, en vez de usar `django.contrib.auth.models.Group`.

```python
class User(AbstractUser):
    is_employee = models.BooleanField(default=True)
    is_responsible = models.BooleanField(default=False)
```

**Por qué:**

- El enunciado exige que una misma persona pueda tener ambos roles a la vez ("nadie puede aprobar ni rechazar su propio gasto, aunque también posea rol de responsable"). Un único campo de tipo choice (`role = CharField(choices=[...])`) es mutuamente excluyente y no permite representar esto — por eso se descartó desde el inicio.
- Se evaluó `Group` de Django (relación many-to-many nativa, pensada justamente para roles). Se descartó porque:
  - Agrega dos tablas intermedias (`auth_group`, `auth_user_groups`) y requiere sembrar los grupos antes de poder asignarlos.
  - El filtrado (`user.groups.filter(name=...).exists()`) implica un JOIN, contra una simple lectura de columna con los booleanos.
  - A la escala de este proyecto (decenas/cientos de usuarios, no millones), la diferencia de performance entre ambas opciones es despreciable — la decisión se tomó por legibilidad y facilidad de testeo (se puede instanciar un `User(is_responsible=True)` en un test sin necesidad de fixtures de grupos), no por rendimiento.
  - Groups aporta valor cuando se necesita el sistema de permisos granular de Django (`add_expense`, `approve_expense`, etc.) o roles dinámicos que se crean en runtime. Ninguno de los dos casos aplica acá: los roles son fijos y conocidos de antemano.

**Nota aparte:** `is_staff` / `is_superuser` (heredados de `AbstractUser`) se usan exclusivamente para acceso administrativo técnico (panel `/admin/`), sin relación con los roles de negocio `empleado`/`responsable`.

---

## 2. Estructura de apps

**Decisión:** Dos apps de dominio (`applications.users`, `applications.expenses`), en vez de una app por rol (`employees`, `responsibles`) o todo en una sola app monolítica.

**Por qué:**

- El modelo mínimo sugerido por el enunciado describe tres entidades: Usuario/rol, Gasto, Decisión/historial — no dos flujos de usuario separados. Modelar `employees` y `responsibles` como apps independientes sugiere (incorrectamente) que son dos tipos de entidad distintos, cuando en realidad son permisos sobre una misma cuenta de usuario.
- `users` concentra identidad y autorización (login, logout, mixins de permiso) — infraestructura transversal, reutilizable independientemente del dominio de negocio.
- `expenses` concentra el modelo `Expense`/`Decision` y toda la lógica de negocio (crear, listar, aprobar, rechazar) — cambia por razones de negocio, no de autenticación.
- Se descartó una única app (`web`) porque, si bien es válida según el enunciado ("una solución monolítica y sencilla es válida"), mezclar autenticación con lógica de negocio en los mismos `models.py`/`views.py` complica la lectura sin ahorrar esfuerzo real de desarrollo.

---

## 3. Servidor: WSGI en vez de ASGI

**Decisión:** `runserver` (desarrollo) y `gunicorn` con `config.wsgi:application` (producción/Docker), eliminando `uvicorn` y las dependencias asociadas (`anyio`, `httptools`, `uvloop`, `watchfiles`).

**Por qué:** El proyecto usa vistas y templates de Django clásicos (síncronos), sin WebSockets ni streaming. ASGI no aporta ningún beneficio funcional acá y agrega superficie de configuración innecesaria. `asgiref` y `sqlparse` se mantienen porque son dependencias internas de Django, independientes de esta elección.

---

## 4. Docker Compose

**Decisión:** Se eliminó el servicio `redis` del `compose.yml`.

**Por qué:** No se usa cache, colas ni Channels en ningún punto del proyecto — era un remanente de una base de proyecto distinta. Mantenerlo agregaba un contenedor sin función real.

**Decisión adicional:** `healthcheck` con `pg_isready` en el servicio `db`, y `depends_on: db: condition: service_healthy` en `web`.

**Por qué:** Evita una condición de carrera donde Django intenta migrar/conectar antes de que Postgres esté realmente listo para aceptar conexiones (no solo "iniciado").

---

## 5. Limitación conocida (fuera de alcance)

Si el sistema tiene un único usuario con rol `responsable` y ese usuario crea un gasto propio, el gasto queda pendiente indefinidamente (nadie más puede aprobarlo, por la regla de que nadie decide sobre su propio gasto). No se implementó ningún mecanismo de escalamiento jerárquico para este caso — no está contemplado en el enunciado y agregar un rol adicional de "super-aprobador" excede el alcance definido. Se resuelve operativamente garantizando al menos dos usuarios con rol `responsable` en los datos demo.

---

## 6. Ciclos TDD

*(Completar a medida que se implementen — mínimo dos ciclos documentados, cada uno con: comportamiento, fallo inicial, implementación, refactor.)*

### Ciclo 1: [nombre de la regla, ej. "Nadie puede aprobar su propio gasto"]

- **Comportamiento esperado:** 
- **Test (Red):** nombre del test y por qué falló inicialmente
- **Implementación mínima (Green):** 
- **Refactor:** 

### Ciclo 2: [nombre de la regla]

- **Comportamiento esperado:** 
- **Test (Red):** 
- **Implementación mínima (Green):** 
- **Refactor:**