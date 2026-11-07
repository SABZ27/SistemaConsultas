# Festivos y reglas de fecha

## Proveedor y flujo de validación

- Los festivos se consultan con **Nager.Date** (API v4:
  `GET /Holidays/{CountryCode}/{Year}`), con país por defecto **`CO`**
  (Colombia). La URL base del proveedor se lee de la tabla MySQL
  `servicios_externos`.
- El backend llama a
  `GET {INFRA_SERVICE_URL}/festivos/validar?fecha=YYYY-MM-DD&pais=CO`
  reenviando el `Authorization: Bearer` del usuario. `INFRA_SERVICE_URL` vale
  `http://localhost:3001` por defecto.
- El validador exige el formato **`YYYY-MM-DD`** y una fecha de calendario real
  (rechaza, por ejemplo, `2026-02-30`).
- Si `esFestivo = true`: **400** con el mensaje exacto
  `La fecha seleccionada es festivo: <nombre>`.
- Si el servicio no responde (red, timeout, 5xx o respuesta inválida):
  **503 fail-closed**. No se crea ni se reprograma una consulta sin haber
  validado la fecha. El cliente usa timeout de **45 s** y **2 intentos** solo
  para errores de conexión/5xx; el HTTP del servicio externo usa **15 000 ms**.

## Ley Emiliani

Solo dos festivos móviles se trasladan al **lunes siguiente** cuando no caen
en lunes: **`Ascension Day`** (Ascensión) y **`Corpus Christi`**. Ningún otro
festivo se mueve. El cálculo del día de la semana se hace en **UTC** para no
depender de la zona del servidor. Ejemplo en 2026: Ascensión 14-05 (jueves)
→ 18-05 (lunes); Corpus 04-06 → 08-06 (lunes). Los nombres de festivos se
traducen al español mediante un mapa; si un nombre no está en el mapa se
conserva el original.

## Caché local

Los festivos se guardan en la tabla MySQL `festivos` con `UNIQUE (fecha,
pais)`. Si ya hay filas activas del año se resuelven **localmente** sin llamar
a Nager.Date. Si existe cualquier fila del año (aunque esté desactivada) no se
resincroniza. La operación de guardado nunca reactiva registros desactivados.
La trazabilidad de las llamadas queda en `consultas_servicio_externo`.

## Otras reglas de fecha al agendar

- **Periodo académico vigente**: la `fechaConsulta` debe estar dentro de un
  periodo con `estado = true` (`fecha_inicio <= fecha <= fecha_fin`); si no,
  400. El `CHECK` del periodo exige `fecha_fin > fecha_inicio`.
- **Disponibilidad del docente**: `dia_semana` va de **1 (Lunes)** a
  **7 (Domingo)**; la hora debe caer dentro de `[hora_inicio, hora_fin]` de un
  tramo activo, con `hora_fin > hora_inicio`.
- La fecha de la consulta **no puede ser anterior a hoy**.
- Al **reprogramar**, si cambia la fecha se **revalida el festivo** y si cambia
  fecha u hora se exige un `motivo`. No se revalidan periodo, docente-módulo ni
  disponibilidad.

## Zona horaria

`fecha_consulta` es `DATE` y `hora_consulta` es `TIME WITHOUT TIME ZONE`. Se
comparan con la **hora local del servidor** (`date.today()` / `datetime.now()`,
valores *naive*): **no hay conversión de zona horaria** para la agenda. En
cambio, los `iat`/`exp` del JWT se calculan en UTC y el cálculo de la Ley
Emiliani también usa UTC.

## Fallos del proveedor

Desde el Bloque A la validación es fail-closed: si Nager.Date o el servicio
externo no responden, la creación/reprogramación se rechaza con **503** en
lugar de omitir la validación. Los festivos ya en caché no dependen del
proveedor.
