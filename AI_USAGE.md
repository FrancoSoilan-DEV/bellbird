# AI_USAGE.md

Registro de interacciones con IA que influyeron materialmente en la solución, según lo pedido en el enunciado. Se documentan solo las que produjeron una decisión o cambio real; se omiten consultas triviales de sintaxis o autocompletado.

Herramienta usada en todos los casos: **Claude** (Anthropic, vía claude.ai).

---

### 1. Limpieza de configuración ASGI → WSGI

- **Objetivo/prompt representativo:** Partía de un esqueleto de proyecto configurado para ASGI/uvicorn (pensado originalmente para otro tipo de app). Consulté qué implicaba esa diferencia y qué había que ajustar para una app Django estándar con templates.
- **Resultado obtenido:** Confirmación de que ASGI no aporta nada funcional para este caso de uso (sin WebSockets ni async), y una lista concreta de cambios: cambiar `CMD` del Dockerfile a `gunicorn config.wsgi:application`, sacar dependencias de `uvicorn`/`anyio`/`uvloop` de `requirements/base.txt`, mantener `asgiref` (dependencia interna de Django).
- **Qué acepté/rechacé:** Acepté el diagnóstico completo. Antes de aplicarlo, revisé manualmente cada dependencia del `requirements/base.txt` original y decidí por mi cuenta cuáles sacar, dejando afuera algunas que la IA marcó como opcionales pero que preferí evaluar caso por caso (`click`, `idna`, `PyYAML`).
- **Verificación:** `docker compose up --build` — la app levanta correctamente con `runserver`/WSGI sin errores de import ni de servidor.

---

### 2. Debug de conexión Postgres en Docker Compose

- **Objetivo/prompt representativo:** El contenedor `web` fallaba con `could not translate host name "db"` al intentar migrar contra Postgres.
- **Resultado obtenido:** Diagnóstico de condición de carrera (Postgres "iniciado" pero no necesariamente listo para conexiones) y sugerencia de agregar `healthcheck` con `pg_isready` al servicio `db` más `depends_on: condition: service_healthy` en `web`.
- **Qué acepté/rechacé:** Apliqué el healthcheck. El primer intento igual falló por una razón distinta (config vieja aún cacheada); lo resolví yo mismo con `docker compose down -v` para forzar una reconstrucción limpia de red y volumen, antes de reintentar.
- **Verificación:** Log de `docker compose up --build` mostrando migraciones aplicadas correctamente y el servidor de desarrollo arrancando sin excepciones.

---

### 3. Representación de roles: booleanos vs. Django Groups

- **Objetivo/prompt representativo:** Consulté si convenía usar `django.contrib.auth.models.Group` o campos propios en el modelo `User` para distinguir empleado/responsable.
- **Resultado obtenido:** La IA sugirió inicialmente considerar ambas opciones. Cuestioné específicamente el argumento de performance ("¿no es Groups más liviano para la base?"), y tras pedir el detalle de cómo funciona cada opción a nivel de tablas (Groups implica tablas intermedias many-to-many; booleanos son columnas directas), confirmé que mi intuición inicial (booleanos) era además la opción más simple en cuanto a lectura de datos, no solo en cuanto a legibilidad de código.
- **Qué acepté/rechacé:** Rechacé la sugerencia de considerar un tercer rol tipo "superusuario aprobador" para resolver el caso límite de un único responsable con gasto propio — decidí que excedía el alcance del enunciado y lo documenté como limitación conocida en vez de implementarlo.
- **Verificación:** Razonamiento validado manualmente contra el texto del enunciado (regla de que un usuario puede tener ambos roles simultáneamente) antes de decidir; pendiente de verificación automatizada vía tests unitarios sobre el modelo `User`.

---

### 4. Diseño de `CustomLoginView` y mixins de permiso por rol

- **Objetivo/prompt representativo:** Cómo transformar una vista de login basada en `TemplateView` a una que use la autenticación real de Django, y cómo redirigir según el rol del usuario tras loguearse.
- **Resultado obtenido:** Estructura de `CustomLoginView(LoginView)` con `get_success_url()` sobreescrito, más un par de mixins (`EmployeeRequiredMixin`, `ResponsibleRequiredMixin`) basados en `LoginRequiredMixin` + `UserPassesTestMixin`.
- **Qué acepté/rechacé:** Acepté la estructura general. Adapté los mixins para que lean los campos booleanos del `User` en vez de grupos, en línea con la decisión del punto 3.
- **Verificación:** Pendiente — se validará con tests de integración HTTP (usuario sin rol correcto recibe 403 al intentar acceder a una vista protegida).