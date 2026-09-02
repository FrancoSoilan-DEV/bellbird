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

- El enunciado exige que una misma persona pueda tener ambos roles a la vez ("nadie puede aprobar ni rechazar su propio gasto, aunque también posea rol de responsable"). Un único campo de tipo choice (`role = CharField(choices=[...])`) es mutuamente excluyente y no permite representar esto.
- Se evaluó `Group` de Django. Se descartó porque agrega tablas intermedias many-to-many y requiere sembrar los grupos antes de poder asignarlos, contra columnas directas de lectura simple. A esta escala la diferencia de performance es despreciable; la decisión se tomó por legibilidad y facilidad de testeo (se puede instanciar un `User(is_responsible=True)` en un test sin fixtures de grupos).
- Groups aporta valor cuando se necesita el sistema de permisos granular de Django o roles dinámicos. Ninguno de los dos casos aplica acá.

**Nota:** `is_staff` / `is_superuser` (heredados de `AbstractUser`) se reservan para acceso administrativo técnico, sin relación con los roles de negocio.

---

## 2. Estructura de apps

**Decisión:** `applications.users` (identidad, autenticación, permisos) y `applications.expenses` (modelo de negocio y vistas de gastos), en vez de una app por rol (`employees`, `responsibles`).

**Por qué:** El modelo mínimo sugerido describe tres entidades (Usuario/rol, Gasto, Decisión/historial), no dos flujos de usuario separados. Modelar `employees`/`responsibles` como apps independientes sugiere que son dos tipos de entidad distintos, cuando en realidad son permisos sobre una misma cuenta. `users` concentra identidad y autorización; `expenses` concentra el modelo y la lógica de negocio — cada una cambia por razones distintas.

**Corolario aplicado en la práctica:** el dashboard de empleado (`EmployeeDashboardView`) inicialmente se ubicó por error dentro de `users`; se corrigió moviéndolo a `expenses`, ya que es contenido de negocio (una vista sobre gastos), no de identidad.

---

## 3. Mixins de permiso: dos clases explícitas en vez de un mixin genérico parametrizable

**Decisión final:**

```python
class EmployeeRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_employee


class ResponsibleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_responsible
```

**Alternativa descartada:** un único `RoleRequiredMixin` con un atributo `required_role = 'is_employee'` configurable por vista, que centralizaba la lógica en una sola clase parametrizada.

**Por qué se descartó:** aunque evitaba una pequeña duplicación (`LoginRequiredMixin, UserPassesTestMixin` repetido en ambas clases), agregaba una capa de indirección (`getattr(self.request.user, self.required_role, False)`) que hacía menos directo de leer qué rol exige cada vista. Con solo dos roles fijos y conocidos de antemano, dos clases explícitas y cortas son más legibles y más fáciles de verificar en la defensa técnica que una única clase genérica con configuración por atributo — se prefirió explicitud sobre reducción de líneas.

---

## 4. Servidor: WSGI en vez de ASGI

**Decisión:** `runserver` (desarrollo) y `gunicorn` con `config.wsgi:application` (producción/Docker), eliminando `uvicorn` y dependencias asociadas.

**Por qué:** El proyecto usa vistas y templates de Django clásicos, sin WebSockets ni streaming. ASGI no aporta beneficio funcional y agrega superficie de configuración innecesaria. `asgiref` y `sqlparse` se mantienen por ser dependencias internas de Django.

---

## 5. Docker Compose

**Decisión:** se eliminó el servicio `redis` (sin uso real en el proyecto) y se agregó `healthcheck` con `pg_isready` en `db` + `depends_on: condition: service_healthy` en `web`, para evitar condiciones de carrera donde Django intenta migrar antes de que Postgres acepte conexiones.

---

## 6. Limitación conocida (fuera de alcance)

Si el sistema tiene un único usuario con rol `responsable` y ese usuario crea un gasto propio, el gasto queda pendiente indefinidamente. No se implementó escalamiento jerárquico de aprobaciones — excede el alcance del enunciado. Se resuelve operativamente garantizando al menos dos usuarios con rol `responsable` en los datos demo.

---

## 7. Ciclos TDD

### Ciclo 1: `EmployeeRequiredMixin` (aislado)

- **Comportamiento esperado:** un usuario con `is_employee=True` puede acceder a una vista protegida; uno sin ese rol es rechazado (`PermissionDenied`); un usuario anónimo es redirigido a login.
- **Test (Red):** tests contra una vista mínima construida solo para el test, usando `RequestFactory`. Falló primero por `ImportError` (el mixin no existía), y luego —tras crearlo— dos casos fallaron con `PermissionDenied` no capturada, porque al invocar la vista directamente (sin pasar por el resolver de URLs) la excepción no se traduce automáticamente a una respuesta 403.
- **Implementación mínima (Green):** se ajustaron esos dos tests para usar `self.assertRaises(PermissionDenied)` en lugar de verificar `status_code == 403`, reflejando el comportamiento real del mixin en ese contexto de test aislado.
- **Refactor:** se documentó con un docstring por qué el mixin lanza `PermissionDenied` en vez de devolver 403 directamente.

### Ciclo 2: Login con redirección por rol + dashboard de empleado protegido (extremo a extremo)

- **Comportamiento esperado:** un empleado que envía credenciales válidas al login es redirigido a `e-dash`; un usuario anónimo que intenta acceder a `e-dash` es redirigido a login.
- **Test (Red):** dos tests usando `self.client` (flujo HTTP real, a través de `urls.py`) fallaron con `NoReverseMatch`, porque ni la ruta `login` ni `e-dash` existían todavía.
- **Implementación mínima (Green):** se crearon `CustomLoginView` (con `get_success_url` según `is_responsible`), `EmployeeDashboardView` (usando `EmployeeRequiredMixin`) y las rutas correspondientes en `users/urls.py` y `expenses/urls.py`. En el camino aparecieron tres errores intermedios que no eran del comportamiento en sí sino de piezas de soporte faltantes: un `ImportError` por una URL que importaba una vista de `expenses` antes de que existiera, y dos `TemplateDoesNotExist` (login y dashboard) por templates no creados aún. Cada uno se resolvió antes de continuar, y la suite se corrió después de cada corrección.
- **Refactor:** pendiente — el código actual es corto y no presenta duplicación evidente que amerite extracción.

*(Falta un tercer ciclo formal para completar el mínimo de tres requerido — candidatos naturales: login de responsable → `r-dash`, y rechazo cruzado de rol en cada dashboard.)*