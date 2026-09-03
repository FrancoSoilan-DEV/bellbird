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

## 6. Organización de templates: por rol, no por app

**Decisión:** `applications/expenses/templates/employee/` (y su futura contraparte `responsible/`), en vez de `applications/expenses/templates/expenses/`.

**Por qué:** surgió en la práctica al crear las plantillas — se agrupó por rol de usuario (quién ve la pantalla) en vez de por app de Django (dónde vive el código). Es una decisión de organización válida siempre que el `template_name` de cada vista se mantenga consistente con la carpeta real; se corrigió un desajuste inicial donde las vistas apuntaban a `expenses/` mientras los archivos físicos estaban en `employee/`.

---

## 7. Mensajes de validación en tests: comportamiento, no texto exacto

**Decisión:** los tests que verifican errores de formulario comprueban `form.errors.get('campo')` (que el campo tiene un error), no el texto literal del mensaje.

**Por qué:** el proyecto tiene `LANGUAGE_CODE = 'es'`, por lo que Django traduce automáticamente los mensajes de validación de sus propios validadores (ej. `MinValueValidator`). Un test que compara el texto exacto en inglés falla no porque la regla de negocio esté mal, sino porque el mensaje real viene en español — un falso negativo que no dice nada sobre la corrección del código. Verificar la presencia del error (sin atarse a la redacción) prueba el comportamiento real sin depender de un detalle de implementación de terceros.

---

## 8. Limitación conocida (fuera de alcance)

Si el sistema tiene un único usuario con rol `responsable` y ese usuario crea un gasto propio, el gasto queda pendiente indefinidamente. No se implementó escalamiento jerárquico de aprobaciones — excede el alcance del enunciado. Se resuelve operativamente garantizando al menos dos usuarios con rol `responsable` en los datos demo.

---

## 9. Ciclos TDD

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

### Ciclo 3: Creación de gasto — camino feliz y validación de importe

- **Comportamiento esperado:** un empleado logueado puede crear un gasto con datos válidos, que queda en estado `PENDING`; un importe igual o menor a cero es rechazado sin crear el registro.
- **Test (Red):** `test_employee_can_create_expense_with_valid_data` falló primero con `NoReverseMatch` (la ruta `expense-create` no existía). Luego, al agregar `test_amount_zero_is_rejected` y `test_negative_amount_is_rejected`, ambos fallaron con `TemplateDoesNotExist`, por un desajuste entre el `template_name` configurado en la vista y la carpeta real de templates (ver decisión 6).
- **Implementación mínima (Green):** se creó `ExpenseForm` (ModelForm sobre `Expense`), `ExpenseCreateView` (asigna `owner` al usuario logueado en `form_valid`), la ruta correspondiente y el template. Tras corregir la ruta del template, uno de los dos tests de validación seguía fallando — no por un bug de la regla de negocio (el campo `amount` sí registraba el error), sino porque el test comparaba el mensaje de error en inglés contra el mensaje real en español (ver decisión 7). Se ajustó el test para verificar la presencia del error en el campo en vez del texto exacto.
- **Refactor:** se evaluó unificar los dos tests de importe inválido (cero y negativo) en uno solo parametrizado; se decidió no hacerlo por ahora — con dos casos, la duplicación es mínima y el código actual es más legible que la abstracción.

Con este ciclo se completa el mínimo de tres ciclos TDD documentados que pide el enunciado.



---

## 10. Filtro de estado en el listado de responsable: reinterpretación del criterio

**Contexto:** el enunciado pide que el responsable pueda *"listar gastos pendientes y filtrarlos, como mínimo, por estado y empleado."* La vista `PendingExpenseListView` por diseño ya muestra solo pendientes — el filtro por "estado" sobre una lista que ya es monoestado parecía redundante.

**Decisión:** en vez de crear una vista separada para historial, se extendió la misma vista para que el parámetro `?status=` sea configurable, con `PENDING` como valor por defecto. Esto permite que la misma URL sirva tanto para el caso de uso principal (ver pendientes) como para consultar el historial (`?status=APPROVED` o `?status=REJECTED`), cubriendo también la capacidad de "consultar el historial" que el enunciado exige al responsable en la misma tabla de roles.

**Por qué:** no hay jerarquía de aprobación en el sistema (cualquier responsable puede decidir sobre cualquier empleado, según lo definido en la decisión 1 y confirmado por el criterio 10). Con esa premisa, agregar una vista nueva solo para historial hubiera sido duplicar filtrado y permisos ya resueltos en `PendingExpenseListView`. Un único endpoint parametrizable es más simple y coherente con el principio de "no exigimos arquitectura específica" del enunciado.

---

## 11. Mensajes de confirmación: `django.contrib.messages` sobre alternativas

**Decisión:** se usa el framework de mensajes de Django (ya declarado en `MIDDLEWARE`/`INSTALLED_APPS` por defecto) para las confirmaciones tras crear, editar y decidir un gasto (criterio 15), en vez de mensajes ad-hoc en cada template o parámetros en la URL de redirección.

**Por qué:** es la solución estándar de Django para este patrón (POST → redirect → mensaje de una sola vez), evita reinventar el mecanismo, y se integra directamente con el flujo `form_valid()`/`redirect()` que ya usan las vistas existentes.

**Nota de verificación importante:** el test que confirma el mensaje (`response.context['messages']`) pasa incluso si el template de destino no renderiza ningún HTML visible — el context processor de Django agrega `messages` al contexto de cualquier respuesta, se muestre o no. Esto se detectó como una diferencia entre "el test pasa" y "el criterio 15 está cumplido de verdad" (confirmación *visible*): fue necesario agregar explícitamente el bloque `{% if messages %}` en los templates de destino (`employee/dashboard.html`, `responsible/pending_list.html`) para que la confirmación apareciera en pantalla, no solo en el contexto de test.

---

## 12. Ciclos TDD adicionales (continuación de la sección 9)

### Ciclo 4: `ExpenseDetailView` — consulta con control de acceso por id

- **Comportamiento esperado:** el dueño de un gasto puede ver su detalle; otro empleado que intente acceder por id a un gasto ajeno recibe 404.
- **Test (Red):** ambos tests fallaron con `NoReverseMatch: 'expense-detail'`, porque ni la vista ni la ruta existían.
- **Implementación mínima (Green):** `ExpenseDetailView` (`DetailView`) con `get_queryset()` filtrado por `owner=self.request.user` — mismo patrón que `ExpenseListView`. La diferencia relevante es que acá el filtrado no es solo una optimización de UX (ocultar gastos ajenos de una lista) sino un control de seguridad real: sin el filtro, cualquier usuario autenticado podría ver el detalle de cualquier gasto adivinando su id en la URL.
- **Refactor:** ninguno necesario; el patrón ya estaba establecido por `ExpenseListView`.

### Ciclo 5: `ExpenseUpdateView` — edición restringida a propio y pendiente

- **Comportamiento esperado:** un empleado puede editar su gasto solo si está `PENDING`; ni el dueño puede editar uno ya decidido, y nadie puede editar el gasto de otro.
- **Test (Red):** tres tests (camino feliz, gasto aprobado, gasto ajeno) fallaron con `NoReverseMatch: 'expense-update'`.
- **Implementación mínima (Green):** `ExpenseUpdateView` con `get_queryset()` filtrado por **dos** condiciones simultáneas: `owner=self.request.user` y `status=Expense.Status.PENDING`. Si cualquiera de las dos falla, el gasto no aparece en el queryset y Django devuelve 404 automáticamente — no se necesitó lógica de permisos adicional más allá del filtro.
- **Refactor:** ninguno; reutiliza `ExpenseForm` y `expense_form.html` ya existentes de la creación.

### Ciclo 6: `PendingExpenseListView` y `ExpenseDecisionView` — núcleo del flujo de responsable

- **Comportamiento esperado:** un responsable lista gastos pendientes, filtrables por empleado y estado; puede aprobar o rechazar dejando comentario; no puede decidir su propio gasto aunque tenga ambos roles; no puede decidir un gasto ya decidido; el cambio de estado y la creación del registro de decisión son atómicos.
- **Test (Red):** ocho tests en total repartidos en dos clases, todos fallando inicialmente por `NoReverseMatch` (`'pending-expenses'`, luego `'expense-decide'`).
- **Implementación mínima (Green):** `PendingExpenseListView` filtra por `status` (default `PENDING`) y opcionalmente por `owner`. `ExpenseDecisionView` usa `get_object_or_404(Expense, pk=pk, status=PENDING)` para resolver de una sola vez tanto "no existe" como "ya fue decidido" (criterio 11) sin chequeo aparte; usa el método ya existente `expense.can_be_decided_by(user)` para la regla de no auto-decisión (criterio 10); y envuelve la creación del `Decision` y el cambio de `expense.status` en `transaction.atomic()` (criterio 12).
- **Refactor:** ninguno necesario en esta iteración — el bloque `with transaction.atomic()` es corto y explícito, no amerita extracción a un método de servicio separado a esta escala.

### Ciclo 7 (bugfix vía cobertura): `ResponsibleDashboardView`

- **Comportamiento esperado:** un responsable que se loguea es redirigido a `r-dash`.
- **Test (Red):** el reporte de `coverage --branch` reveló que la rama `is_responsible=True` de `CustomLoginView.get_success_url()` nunca se ejecutaba en tests. Al escribir el test que la ejercitaba, falló con `NoReverseMatch: 'r-dash'` — no un fallo de aserción, sino la confirmación de que la URL de destino literalmente no existía en el proyecto.
- **Implementación mínima (Green):** `ResponsibleDashboardView` (`TemplateView` protegida por `ResponsibleRequiredMixin`) y su ruta.
- **Refactor:** ninguno.

Con estos ciclos documentados, el proyecto supera holgadamente el mínimo de tres ciclos TDD exigido por el enunciado.