# AI_USAGE.md

Registro de interacciones con IA que influyeron materialmente en la solución. Se documentan solo las que produjeron una decisión o cambio real; se omiten consultas triviales de sintaxis.

Herramienta usada en todos los casos: **Claude** (Anthropic, vía claude.ai).

---

### 1. Limpieza de configuración ASGI → WSGI y Docker Compose

- **Objetivo/prompt representativo:** Partía de un esqueleto de proyecto configurado para ASGI/uvicorn con un servicio Redis sin uso. Consulté qué implicaba esa configuración y qué convenía ajustar para una app Django estándar con templates.
- **Resultado obtenido:** Diagnóstico de que ASGI y Redis no aportaban nada funcional al proyecto, y una lista de cambios concretos (Dockerfile a `gunicorn`, healthcheck de Postgres con `pg_isready`, `depends_on: condition: service_healthy`).
- **Qué acepté/rechacé:** Acepté el diagnóstico general. Revisé manualmente cada dependencia del `requirements.txt` original antes de decidir cuáles sacar, en vez de aplicar la lista completa sin revisar.
- **Verificación:** `docker compose up --build` — la app levanta correctamente; se resolvieron además dos errores reales de entorno (condición de carrera con Postgres, y un `TypeError` por un argumento de `CheckConstraint` renombrado entre versiones de Django) confirmando el comportamiento contra la versión real instalada.

---

### 2. Representación de roles: booleanos vs. Django Groups

- **Objetivo/prompt representativo:** Consulté si convenía `Group` de Django o campos propios en `User` para distinguir empleado/responsable.
- **Resultado obtenido:** Comparación de ambas opciones a nivel de esquema de base de datos (Groups implica tablas intermedias many-to-many).
- **Qué acepté/rechacé:** Cuestioné el argumento de performance antes de aceptarlo, pidiendo el detalle de cómo funciona cada opción a nivel de tablas — confirmé que la opción de booleanos, que ya prefería por legibilidad, no tenía además ninguna desventaja real de rendimiento a esta escala. Decidí booleanos.
- **Verificación:** razonamiento validado contra el texto del enunciado (un usuario puede tener ambos roles a la vez) antes de decidir; verificado luego con tests unitarios sobre las vistas protegidas.

---

### 3. Diseño de mixins de permiso: iteración hasta un diseño explícito

- **Objetivo/prompt representativo:** Pedí un mixin que combinara "estar logueado" y "tener el rol correcto" en una sola pieza reutilizable para las vistas protegidas.
- **Resultado obtenido:** La primera propuesta fue un único `RoleRequiredMixin` genérico, configurable con un atributo `required_role`. No me convenció ese nivel de indirección para un caso de solo dos roles fijos.
- **Qué acepté/rechacé:** Rechacé la versión genérica y pedí explícitamente dos mixins separados y directos (`EmployeeRequiredMixin`, `ResponsibleRequiredMixin`). También rechacé código de vistas propuesto antes de tener los tests correspondientes escritos, exigiendo que el ciclo se respetara test-primero en cada paso, y corregí en el camino una inconsistencia donde una sugerencia importaba una clase que ya había sido eliminada del proyecto.
- **Verificación:** suite de tests (`test_user_with_matching_role_can_access`, `test_user_without_matching_role_is_denied`, etc.) corrida en cada paso del ciclo rojo-verde; documentado en `DECISIONS.md`.

---

### 4. Login con redirección por rol y dashboard protegido (flujo completo)

- **Objetivo/prompt representativo:** Construir `CustomLoginView` con redirección según rol y una vista de dashboard de empleado protegida, siguiendo TDD con `self.client` en vez de vistas de prueba aisladas.
- **Resultado obtenido:** Tests que fallaron primero por `NoReverseMatch` (rutas inexistentes), y luego por errores de configuración menores (import de una vista no creada aún, templates faltantes) hasta llegar a la suite en verde.
- **Qué acepté/rechacé:** Acepté la estructura general de vistas y urls una vez que los tests ya estaban escritos y en rojo por el motivo correcto. Corregí manualmente la ubicación de la vista del dashboard (inicialmente ubicada por error en `users` en vez de `expenses`) antes de continuar.
- **Verificación:** `docker compose exec web python manage.py test applications.users` — 2/2 tests en verde tras resolver cada error de configuración de forma incremental.

---

### 5. Estilos CSS del formulario de login

- **Objetivo/prompt representativo:** Pedí estilizar el template de login con CSS embebido en el mismo archivo, sin crear una carpeta de estilos separada.
- **Resultado obtenido:** HTML con `<style>` inline, paleta y tipografía propuestas, layout de panel partido.
- **Qué acepté/rechacé:** Pendiente de revisión visual en navegador antes de aceptar el resultado final.
- **Verificación:** pendiente — validar visualmente en navegador y confirmar que la suite de tests existente sigue en verde tras el cambio (el CSS no debería afectar el comportamiento, pero se re-corre por buena práctica).

---

### 6. Creación de gasto: formulario, vista y validación de importe

- **Objetivo/prompt representativo:** Implementar la funcionalidad de creación de gastos para empleados, siguiendo TDD: primero el camino feliz (importe válido → estado PENDING), luego casos de validación (importe cero o negativo).
- **Resultado obtenido:** Propuesta de `ExpenseForm` (ModelForm), `ExpenseCreateView` (con asignación automática del `owner` en `form_valid`), ruta y template mínimo. Para la validación, propuesta de dos tests separados verificando importe cero y negativo.
- **Qué acepté/rechacé:** Señalé por mi cuenta que el primer test (camino feliz) no cubría ningún caso de validación, antes de que se propusiera continuar con otra funcionalidad — esa observación motivó el segundo ciclo. Además, uno de los tests de validación propuestos comparaba el mensaje de error en inglés; al fallar, se identificó que el proyecto usa `LANGUAGE_CODE='es'` y el mensaje real viene traducido — se optó por reescribir el test para verificar la presencia del error sin atarse al texto exacto, en vez de simplemente traducir el string (decisión más robusta a futuro).
- **Verificación:** `docker compose exec web python manage.py test applications.expenses` — 3/3 tests en verde. Se depuró además un error real de `TemplateDoesNotExist` causado por un desajuste entre el `template_name` de las vistas y la organización real de carpetas de templates (`employee/` en vez de `expenses/`), corregido antes de dar el ciclo por cerrado.



---

### 7. Sesión de continuación: lado responsable, mensajes de confirmación y cobertura

- **Objetivo/prompt representativo:** Retomé el proyecto en una sesión nueva, pegando el estado del código existente para que la IA reconstruyera el contexto. Pedí completar lo que faltaba del lado empleado (detalle, edición) y todo el lado responsable (listar pendientes, aprobar/rechazar), siguiendo TDD estricto en cada paso: test primero, confirmar el fallo, luego implementación mínima.
- **Resultado obtenido:** Se implementaron `ExpenseDetailView`, `ExpenseUpdateView`, `PendingExpenseListView` (con filtros por owner y estado), `ExpenseDecisionView` (con atomicidad vía `transaction.atomic()` y las reglas de no auto-decisión y no doble decisión), y `ResponsibleDashboardView`.
- **Qué acepté/rechacé:** Acepté el diseño de reutilizar `get_queryset()` filtrado (mismo patrón en list/detail/update) para resolver control de acceso vía 404 en vez de chequeos manuales — es consistente con el resto del código y evita duplicar lógica de permisos. Pedí explícitamente que cada test corriera en rojo antes de ver la implementación, y en un caso detecté que un test había quedado mal pegado en la clase equivocada (`test_success_message_shown_after_deciding_expense` en `ExpenseCreateViewTests` en vez de `ExpenseDecisionViewTests`) — el error de `AttributeError` lo evidenció, lo corregí moviendo el método a la clase correcta.
- **Verificación:** cada ciclo se corrió con `docker compose exec web python manage.py test applications.expenses` tras el rojo y tras el verde, confirmando el mensaje de error exacto antes de aceptar cualquier implementación. Cobertura final verificada con `coverage run --branch --source='applications' manage.py test` seguido de `coverage report -m`.

---

### 8. Bug real detectado por cobertura de ramas: `r-dash` inexistente

- **Objetivo/prompt representativo:** Al revisar el primer reporte de cobertura, `applications/users/views.py` marcaba 82%, con la rama `is_responsible=True` de `CustomLoginView.get_success_url()` sin cubrir.
- **Resultado obtenido:** La IA señaló que esa rama nunca se había testeado, y que además la URL `r-dash` que intentaba reversear no existía todavía en el proyecto — es decir, cualquier responsable que se logueara en ese momento iba a recibir un `NoReverseMatch` real en producción, no un problema teórico de cobertura.
- **Qué acepté/rechacé:** Acepté el diagnóstico y pedí resolverlo con TDD: primero el test que reproduce el fallo (login de responsable → debe redirigir a `r-dash`), confirmando que fallaba con el mismo `NoReverseMatch` que ocurriría en producción, y luego la implementación de `ResponsibleDashboardView` y su URL.
- **Verificación:** el test replicó el error real antes de la corrección; tras implementar, la suite completa pasó y la cobertura de `users/views.py` subió a 100%. Este caso quedó documentado como ejemplo concreto de que la cobertura de ramas detecta bugs reales, no solo estadísticas — ver `DECISIONS.md`, ciclo correspondiente.

---

### 9. Cobertura de modelos: `can_be_edited` y `__str__` sin uso

- **Objetivo/prompt representativo:** Con la cobertura en 98%, quedaban tres líneas sueltas en `models.py` (los métodos `__str__` de `Expense` y `Decision`, y `can_be_edited`). Pregunté qué hacer con ellas.
- **Resultado obtenido:** La IA señaló que `can_be_edited()` estaba definido pero nunca se usaba en ninguna vista ni template — código muerto sin justificación — y propuso dos caminos: testearlo aislado, o darle un uso real.
- **Qué acepté/rechacé:** Elegí la segunda opción: usar `can_be_edited` en el template de detalle para mostrar el link "Editar" condicionalmente, en vez de solo escribir un test que lo ejercitara sin propósito. Esto mejora la UX real (nadie ve un link a editar un gasto ya decidido) y cierra la cobertura como consecuencia, no como objetivo en sí.
- **Verificación:** tests de modelo (`test_pending_expense_can_be_edited`, `test_approved_expense_cannot_be_edited`, `test_str_representation` para ambos modelos) corridos en verde; cobertura final de `models.py` en 100%.