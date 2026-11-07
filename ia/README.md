# Componente de IA — Taller 1, Corte 2

Asistente local para el **Sistema de Gestión de Consultas Académicas**:
Ollama con un modelo derivado, Open WebUI con una base de conocimiento (MD,
TXT y PDF), un bot de Telegram con el **mismo modelo y la misma colección**, y
(Fase 2) consulta de datos de PostgreSQL en la nube mediante MCP Toolbox +
mcpo.

> **Alcance.** Este directorio **no forma parte de FastAPI ni de Express** y
> **no se despliega**. Corre en el PC (Windows, Ryzen 7 5700U, 16 GB de RAM,
> **sin GPU dedicada, solo CPU**, poco disco) y se **valida en video**. El
> responsable ejecuta Ollama, Open WebUI, Toolbox, mcpo y el bot; aquí solo
> están los archivos, los scripts y las instrucciones.

---

## 1. Arquitectura

```
                         +---------------------------+
                         |  Ollama NATIVO en Windows  |
                         |  qwen3:4b-instruct-...     |
                         |  -> "consultas-asistente"  |
                         |  OLLAMA_KEEP_ALIVE=30m     |
                         +-------------+-------------+
                                       | http://localhost:11434
                                       v
  ia/conocimiento/  --->  +---------------------------+  <--- bot (Telegram)
  (10 .md/.txt + 2 PDF)   |       Open WebUI           |       /api/chat/completions
   cargar_conocimiento.py  |  puerto 3000 (pip o docker)|       mismo modelo + KNOWLEDGE_ID
                           |  coleccion "consultas-...  |
                           +-------------+-------------+
                                         | Fase 2: tool_ids (OpenAPI externo)
                                         v
                           mcpo :8000  <-  Toolbox :5000  <-  Neon (PostgreSQL)
                                             vistas v_ia_* / rol ia_lectura (solo SELECT)
```

- **Ollama** sirve el modelo local por CPU. El modelo derivado
  `consultas-asistente` fija `temperature 0.2`, `top_p 0.8`, `num_ctx 4096` y
  el `SYSTEM` de `ia/prompts/sistema.md`.
- **Open WebUI** es la aplicación: conexión a Ollama, base de conocimiento y
  API `/api/chat/completions`.
- **El bot de Telegram** no habla con Ollama directamente: llama a la API de
  Open WebUI con el **mismo** `OLLAMA_MODEL` y el **mismo** `KNOWLEDGE_ID`.
- **Fase 2**: Toolbox expone herramientas MCP de solo lectura sobre vistas;
  mcpo las convierte a OpenAPI; Open WebUI las registra como herramienta
  externa.

Docker es **OPCIONAL**. Hay dos modos, elegidos con `OPENWEBUI_MODE` en
`ia/.env`:

| `OPENWEBUI_MODE` | Significado | Contenedores |
|---|---|---|
| `pip` (**por defecto**) | Open WebUI instalado con pip en un venv fuera del repo | ninguno |
| `docker` (alternativo) | Open WebUI en Docker Compose; Ollama sigue nativo en Windows | solo `open-webui` |

---

## 2. Requisitos

- Windows con **Ollama nativo** instalado y en ejecución.
- **Python 3.11 o 3.12** para el venv de Open WebUI (Open WebUI 0.13.0
  **no soporta Python 3.13**). Para el bot y los scripts basta Python 3.9+.
- `git`, `psql` (Fase 2) y, solo en modo Docker, Docker Desktop con WSL2.
- Conexión a internet **la primera vez** (descarga del modelo base, del
  modelo de embeddings y de los paquetes pip/MCP).
- Sin GPU: el modelo `qwen3:4b-instruct-2507-q4_K_M` es 4B cuantizado y corre
  por CPU; `num_ctx 4096` mantiene el consumo de RAM acotado.

---

## 3. Variables de entorno

Copia `ia/.env.example` a `ia/.env` y rellena **solo ahí** los secretos.
`ia/.env` está en `ia/.gitignore`; **nunca** se versiona ni se imprime.

| Variable | Uso |
|---|---|
| `OPENWEBUI_MODE` | `pip` (defecto) o `docker` |
| `OPENWEBUI_URL` | `http://localhost:3000` |
| `OPENWEBUI_API_KEY` | clave de API de Open WebUI (Settings > Account > API Keys) |
| `KNOWLEDGE_ID` | id de la colección, lo muestra `cargar_conocimiento.py` |
| `OLLAMA_MODEL` | `consultas-asistente` |
| `TELEGRAM_BOT_TOKEN` | token de BotFather |
| `TELEGRAM_ALLOWED_USERS` | ids separados por coma; vacío = todos. **La ruta DATOS exige que no esté vacío** |
| `WEBUI_SECRET_KEY` | clave de sesión estable de Open WebUI |
| `OPENWEBUI_TOOL_IDS` | ids de herramientas de Open WebUI (Fase 2), separados por coma |
| `ROUTING_MODE` | `auto` (defecto), `documentacion` o `datos` |
| `OLLAMA_KEEP_ALIVE` | `30m` |
| `DATA_DIR`, `VENV_OPENWEBUI` | rutas fuera del repo para datos y venv |
| `MCPO_API_KEY`, `NEON_*` | Fase 2 |

`ia/scripts/entorno.ps1` carga `ia/.env` en los `.ps1` sin imprimir valores;
los `.py` usan `python-dotenv`.

---

## 4. Puesta en marcha — MODO PIP (por defecto, sin Docker)

Orden exacto:

1. **Variables**: `Copy-Item ia/.env.example ia/.env`; edita `ia/.env`
   (`OPENWEBUI_MODE=pip`, `WEBUI_SECRET_KEY`, `TELEGRAM_BOT_TOKEN`, ...).
   Define además, como variable de entorno de **Windows** (antes de arrancar
   Ollama): `OLLAMA_KEEP_ALIVE=30m`.
2. **Modelo**: `powershell -ExecutionPolicy Bypass -File ia/scripts/instalar-modelo.ps1`
   (comprueba `ollama`, hace `ollama pull qwen3:4b-instruct-2507-q4_K_M` y
   crea `consultas-asistente` con `ia/Modelfile` + `ia/prompts/sistema.md`).
3. **Venv de Open WebUI** (una sola vez, **fuera del repo**): si no existe,
   `iniciar-openwebui.ps1` imprime las instrucciones y **no instala nada**:
   ```powershell
   py -3.12 -m venv C:\dev\venv-openwebui
   & 'C:\dev\venv-openwebui\Scripts\python.exe' -m pip install --upgrade pip
   & 'C:\dev\venv-openwebui\Scripts\python.exe' -m pip install open-webui==0.13.0
   ```
4. **Arrancar Open WebUI**:
   `powershell -ExecutionPolicy Bypass -File ia/scripts/iniciar-openwebui.ps1`
   → `http://localhost:3000`. Crea la cuenta admin en el primer inicio.
5. **Activar API Keys** en Open WebUI: avatar > Settings > Account > API Keys
   (un administrador debe habilitar el interruptor global). Copia la clave a
   `OPENWEBUI_API_KEY` en `ia/.env`.
6. **Generar los PDF** (ya están generados en el repo; para regenerarlos):
   `python -m pip install -r ia/requirements.txt` y
   `python ia/scripts/generar_pdfs.py`.
7. **Cargar la base de conocimiento**:
   `python ia/scripts/cargar_conocimiento.py`. Crea la colección, sube los 10
   `.md/.txt` y los 2 `.pdf`, espera el procesado y muestra el
   **`KNOWLEDGE_ID`** (nunca la clave). Cópialo a `ia/.env`.
8. **Probar en la UI**: nuevo chat, elige `consultas-asistente`, escribe `#`
   y selecciona la colección `consultas-academicas`; pregunta, por ejemplo,
   «¿En qué estado se puede calificar una consulta?».
9. **Evaluar**: `python ia/scripts/evaluar.py` (15 preguntas de documentación
   + 3 fuera de documentación; muestra aciertos y tiempo por respuesta).
10. **Bot de Telegram**: `python -m pip install -r ia/requirements.txt` y
    `python ia/telegram/bot.py`. Comandos `/start`, `/ayuda`, `/id`.

> En modo pip, Open WebUI detecta Ollama automáticamente en
> `http://localhost:11434`.

---

## 5. Puesta en marcha — MODO DOCKER (alternativo)

Orden exacto:

1. `Copy-Item ia/.env.example ia/.env`; pon `OPENWEBUI_MODE=docker` y rellena
   `WEBUI_SECRET_KEY` (y el resto). Define `OLLAMA_KEEP_ALIVE=30m`.
2. **Limitar WSL2** (solo modo Docker, por los 16 GB y el poco disco).
   Crea/edita `%USERPROFILE%\.wslconfig`:
   ```ini
   [wsl2]
   memory=6GB
   processors=6
   swap=2GB
   ```
   Después ejecuta `wsl --shutdown` y vuelve a abrir Docker Desktop.
3. **Modelo**: igual que el paso 2 del modo pip
   (`ia/scripts/instalar-modelo.ps1`); Ollama sigue siendo **nativo**.
4. **Levantar Open WebUI**:
   ```powershell
   cd ia
   docker compose --env-file .env up -d
   ```
   `ia/docker-compose.yml` usa solo Open WebUI: `3000:8080`,
   `OLLAMA_BASE_URL=http://host.docker.internal:11434`,
   `extra_hosts: host.docker.internal:host-gateway`, volumen persistente
   `open-webui-data` y `WEBUI_SECRET_KEY` desde `.env`.
   → `http://localhost:3000`. Logs: `docker compose logs -f`.
5. **Si el contenedor no alcanza Ollama**: define `OLLAMA_HOST=0.0.0.0` como
   variable de entorno de Windows, reinicia Ollama y comprueba el firewall de
   Windows para el puerto 11434. (`host.docker.internal` ya está configurado.)
6. Continúa con los **pasos 5 a 10 del modo pip** (API key, PDFs,
   `cargar_conocimiento.py`, `#`, evaluación y bot). El bot y los scripts
   siguen corriendo en Windows y apuntan a `http://localhost:3000` igual que
   en pip.

> En modo Docker la imagen está **fijada** a `v0.13.0` (no `:main`, que es
> rolling). No se usa `:ollama` porque Ollama corre fuera del contenedor.

---

## 6. `OLLAMA_KEEP_ALIVE=30m` (obligatorio en ambos modos)

Por defecto Ollama descarga el modelo a los **5 minutos** de inactividad. Con
un equipo sin GPU, recargar un modelo 4B en cada pausa hace que **la primera
respuesta sea muy lenta** (y en el video se nota). Define
`OLLAMA_KEEP_ALIVE=30m` como variable de entorno de Windows **antes** de
arrancar Ollama y reinícialo. Está documentado también en `ia/.env.example` y
lo recuerdan `instalar-modelo.ps1` e `iniciar-openwebui.ps1`.

## 7. Primera carga de documentos (ambos modos)

La **primera** vez que se sube un documento, Open WebUI descarga el **modelo
de embeddings** local: **requiere internet** y puede tardar. Es un hecho de la
instalación de Open WebUI (RAG), no de este repo. `cargar_conocimiento.py`
espera a que `GET /api/v1/files/{id}/process/status` pase a `completed` antes
de vincular cada archivo, evitando el error
`The content provided is empty...`. Los contenidos duplicados (un `.md` y su
`.pdf`) se omiten con aviso (`Duplicate content detected` → 400).

---

## 8. Bot de Telegram y enrutador

`ia/telegram/bot.py` usa `pyTelegramBotAPI` (`telebot`) con **long polling**
(`infinity_polling`, `threaded=True`, **sin webhook**). Por mensaje hace
**una sola** llamada a `POST {OPENWEBUI_URL}/api/chat/completions` con
`stream=false` y `timeout` de 300 s.

- Comandos: `/start`, `/ayuda`, `/id`.
- Acción «escribiendo…», división de respuestas > 4096 caracteres y limpieza
  de bloques `<think>...</think>`.
- Lista blanca opcional (`TELEGRAM_ALLOWED_USERS`); un **lock por usuario**
  garantiza una consulta a la vez.
- No registra en logs el contenido de los mensajes ni el token
  (`telebot.logger` a `CRITICAL`, errores amigables en español).

**Enrutador** (`ROUTING_MODE=auto` por defecto): clasifica por reglas simples.
Palabras como *cuántas, cuántos, lista, próximas, agenda, disponibilidad,
promedio, recursos, sede* → **DATOS**; el resto → **DOCUMENTACIÓN**.

| Ruta | Cuerpo de la llamada |
|---|---|
| DOCUMENTACIÓN | `files=[{"type":"collection","id":KNOWLEDGE_ID}]` |
| DATOS | `tool_ids` desde `OPENWEBUI_TOOL_IDS`, **sin** `files`, y `params.function_calling="legacy"` |

La ruta **DATOS solo funciona si `TELEGRAM_ALLOWED_USERS` no está vacío**; si
lo está, el bot responde que esa función no está habilitada. `ROUTING_MODE`
admite `documentacion` y `datos` para forzar la ruta.

> Verificado en la referencia de Open WebUI: con `stream=false`, para que el
> servidor **ejecute** las herramientas y devuelva la respuesta en el cuerpo
> hay que usar `params.function_calling = "legacy"` (Path B). En modo nativo
> sin `chat_id`+`id` solo se devolverían `tool_calls` sin ejecutar.

---

## 9. Fase 2 (siguiente commit)

La consulta de datos de la BD (`ia/db/crear_rol_lectura.sql`,
`ia/db/tools.yaml`, `ia/scripts/iniciar-herramientas.ps1`), el registro de la
herramienta externa en Open WebUI, las reglas de datos del prompt y las 10
preguntas de datos del evaluador **se documentan en el commit de la Fase 2**.
Este README se ampliará ahí con las URL de registro: en **modo pip**
`http://localhost:8000/openapi.json` y en **modo Docker**
`http://host.docker.internal:8000/openapi.json` (**no** `localhost`).

---

## 10. Solución de problemas

| Síntoma | Causa / solución |
|---|---|
| `open-webui: command not found` | Activa el venv o usa `...\Scripts\open-webui.exe`; `iniciar-openwebui.ps1` ya lo hace |
| Error de instalación con Python 3.13 | Open WebUI 0.13.0 exige **3.11 o 3.12**; crea el venv con `py -3.12 -m venv` |
| `Set-ExecutionPolicy` / script bloqueado | Ejecuta con `powershell -ExecutionPolicy Bypass -File ...` |
| Puerto 3000 ocupado | Cambia `OPENWEBUI_PORT` (pip) o el lado izquierdo `3000:8080` (Docker) |
| Ollama no aparece en Docker | `OLLAMA_HOST=0.0.0.0`, reinicia Ollama, revisa firewall; `host.docker.internal` ya está en el compose |
| Primera respuesta muy lenta | `OLLAMA_KEEP_ALIVE=30m` y reiniciar Ollama; el modelo se estaba descargando a los 5 min |
| La primera carga de documentos falla/tarda | Descarga del modelo de embeddings: requiere internet; reintenta `cargar_conocimiento.py` |
| `The content provided is empty` | El archivo aún se procesaba; el script ya espera `process/status` |
| `Duplicate content detected` (400) | El `.md` y su `.pdf` tienen el mismo texto; el script lo omite con aviso |
| `#` no lista la colección | Ejecuta `cargar_conocimiento.py` y comprueba permisos/acceso a la colección |
| El bot no responde | Revisa `TELEGRAM_BOT_TOKEN`, `OPENWEBUI_API_KEY`, `KNOWLEDGE_ID` y que Open WebUI esté arriba; `ollama list` debe mostrar el modelo |
| Aparece `<think>` en las respuestas | El bot y el evaluador ya eliminan esos bloques |
| Las herramientas no se ejecutan | Falta `params.function_calling="legacy"` o `OPENWEBUI_TOOL_IDS` (Fase 2) |

---

## 11. Lista de evidencias para el video

1. **Versión de Ollama y modelo descargado**: `ollama --version` y
   `ollama list`, mostrando `qwen3:4b-instruct-2507-q4_K_M` y el derivado
   `consultas-asistente`. Mostrar también `OLLAMA_KEEP_ALIVE=30m`.
2. **Open WebUI con documentos cargados**: Workspace > Knowledge, la colección
   `consultas-academicas` con los 10 `.md/.txt` y los **2 PDF**.
3. **Respuestas correctas usando `#`**: en un chat nuevo, escribir `#`,
   seleccionar la colección y hacer 2–3 preguntas de `ia/pruebas/preguntas.md`,
   más una fuera de documentación que devuelva exactamente
   `No encuentro esa información en la documentación disponible.`
4. **El mismo modelo y la misma base de conocimiento desde Telegram**: mostrar
   en `ia/.env` que `OLLAMA_MODEL` y `KNOWLEDGE_ID` son los mismos, y repetir
   una pregunta equivalente en el bot (con `/id` de ejemplo).
5. **Consulta de datos de la BD** (Fase 2): una pregunta de datos respondida
   con la herramienta de solo lectura, y la comparación con la llamada directa
   a mcpo.

Opcional: `python ia/scripts/evaluar.py` mostrando aciertos y tiempos.

---

## 12. Limitaciones

- **El historial de Telegram y el de Open WebUI NO se comparten**: son dos
  clientes distintos. Lo compartido es **el modelo** (`consultas-asistente`)
  y **la base de conocimiento** (`KNOWLEDGE_ID`).
- El bot envía cada mensaje como una conversación de un solo turno (no
  mantiene contexto entre mensajes).
- El enrutador es de reglas simples: una pregunta de documentación que contenga
  «lista» puede clasificarse como DATOS. Con `ROUTING_MODE=documentacion` se
  fuerza la ruta correcta.
- Todo corre por **CPU**; las respuestas son más lentas que con GPU.
- No se despliega, no hay alta disponibilidad ni persistencia compartida.
- Los resultados de las preguntas de datos (Fase 2) dependen de los **datos de
  demo** que existan en la BD.

---

## 13. Verificación de esta Fase 1

**Verificado de forma estática** (sin ejecutar servicios):
- `py_compile` de los `.py`, parseo YAML del compose, validez de los 2 PDF.
- Nombres de tablas/columnas, estados y reglas: `backend/app/models`,
  `backend/app/services`, `docs/sql/01_postgres_schema.sql`,
  `docs/04-Seguridad.md`, `docs/05-API.md`, `docs/decisiones.md` y `README.md`.

**Verificado contra documentación oficial (web)**:
- `pip install open-webui==0.13.0`, `open-webui serve --port 3000`,
  `DATA_DIR`, `WEBUI_SECRET_KEY`, Python 3.11/3.12 (no 3.13) — Quick Start y
  PyPI (v0.13.0, publicada 2026-11-03).
- Docker: `-p 3000:8080`, `--add-host=host.docker.internal:host-gateway`,
  volumen `/app/backend/data`, `OLLAMA_BASE_URL`, `OLLAMA_HOST=0.0.0.0`.
- API: `POST /api/chat/completions` con `files=[{"type":"collection","id":…}]`,
  `tool_ids` y `params.function_calling="legacy"`;
  `POST /api/v1/knowledge/create`, `POST /api/v1/files/`,
  `GET /api/v1/files/{id}/process/status`,
  `POST /api/v1/knowledge/{id}/file/add` (referencia de API y código v0.13.0).
- mcpo: `mcpo --port 8000 --api-key ... --server-type streamable-http -- URL`.

**NO VERIFICADO** (por las reglas del taller: no se ejecuta nada):
- Que la etiqueta `qwen3:4b-instruct-2507-q4_K_M` exista en el registro de
  Ollama (es el nombre indicado por el responsable; no se ejecuta `ollama`).
- Que el modelo derivado responda **exactamente** la frase de «no encuentro»
  en la práctica, ni la calidad de las respuestas (no se ejecuta el modelo).
- El rendimiento real en la PC y el consumo de RAM (no se ejecuta).
- Que la primera carga descargue un modelo de embeddings concreto ni su
  tamaño: se documenta el hecho desde Open WebUI, no se ejecuta.
- El formato **exacto** del id de herramienta que Open WebUI asigna a un
  servidor OpenAPI/mcpo: el campo `tool_ids` está verificado, pero el id se
  obtiene en cada instalación con `GET /api/v1/tools/` (Fase 2).
- La integración end-to-end Ollama → Open WebUI → bot (no se arranca nada).
