# Auditoría de dependencias (Bloque D.b — solo informe)

Ejecutada localmente el 2026-11-06; actualizada en el **Bloque G**. `pip-audit`
se instaló únicamente en el entorno local del usuario.

## Bloque G: corrección aplicada

- **`body-parser` 1.20.8 → 1.20.9** aplicada de forma selectiva en
  `infraestructura-service/package-lock.json` (dependencia transitiva de
  `express`, que declara `body-parser: ~1.20.5`, por lo que 1.20.9 cabe en el
  rango sin cambio de major). Se usó `npm update body-parser` **sin `--force`**:
  un `npm audit fix` normal también habría subido `qs` a 6.16.2, fuera del
  alcance del bloque. Al reescribir el lock, npm normaliza además
  `engines.node` de `>=20` a `24.x`; ese hunk se revirtió con una edición
  puntual. El diff final del lock son **solo las 3 líneas de `body-parser`**
  (versión, `resolved`, `integrity`) y **`package.json` no cambió**.
- Comprobación con `npm.cmd audit --json`: la alta de `body-parser`
  desaparece; quedan **1 alta** (`zod`), **1 moderada** (`qs`) y **6 bajas**
  (cadena de `jest`), **0 críticas**. Es el resultado esperado, no una
  regresión. `npm.cmd test` sigue en 84 passed / 10 suites.
- **`zod` NO se toca.** El aviso GHSA-mrhx-c7xc-m3w5 exige `zod` **4.6.7**
  (`isSemVerMajor: true`), es decir migrar de 3.x a 4.x: un cambio mayor que
  obligaría a revisar y reescribir todos los validadores
  (`src/validators/*.js`) y sus mensajes de error, y a revalidar las 10 suites
  de jest. Aplicarlo aquí **rompería compatibilidad**; se pospone a un bloque
  propio con aprobación explícita.
- **`qs` 6.16.0** (moderada) y la cadena de **jest** (bajas) se mantienen sin
  corregir, por el mismo criterio de no cambiar nada más en este bloque.

## Backend (Python) — `pip-audit` 2.10.1

Comando: `python -m pip_audit -r requirements.txt --format json`

Resultado: **"No known vulnerabilities found"**. 37 dependencias resueltas,
`vulns: []` en todas y `fixes: []`.

| Severidad | Cantidad |
|---|---|
| Críticas | 0 |
| Altas | 0 |

Versión corregida: no aplica (no hay hallazgos).

## Servicio Express (Node) — `npm audit`

Comando: `npm.cmd audit --json`. El comando `npm` directo está bloqueado por la
política de ejecución de scripts de PowerShell en este equipo, por lo que se
usó `npm.cmd`. El comando devuelve código de salida 1 porque hay hallazgos.

Totales: **9 vulnerabilidades** — **0 críticas, 2 altas**, 1 moderada, 6 bajas.
Dependencias analizadas: 384 (99 prod, 286 dev, 1 opcional).

### Vulnerabilidades altas y críticas

| Paquete | Instalada | Severidad | Aviso | Rango afectado | Versión corregida | ¿Rompe compatibilidad? |
|---|---|---|---|---|---|---|
| `body-parser` | 1.20.8 | **ALTA** | GHSA-27r3-jxmh-p828 — DoS por bytes sobrantes tras un cuerpo comprimido (CVSS 7.5, CWE-248) | `<1.20.9` | **1.20.9** | **No**: `fixAvailable: true`. Es dependencia transitiva de `express` ^4.19.2; se resuelve dentro del rango declarado, sin cambio de major. |
| `zod` | 3.25.76 | **ALTA** | GHSA-mrhx-c7xc-m3w5 — agotamiento de memoria al validar colecciones sobredimensionadas (CVSS 7.5, CWE-770) | `<4.6.6` | **4.6.7** | **Sí**: `isSemVerMajor: true`. Exige migrar de zod 3.x a 4.x y revisar todos los validadores. **No aplicar** en este bloque. |
| Críticas | — | — | — | — | — | 0 hallazgos. |

### Contexto (severidades fuera del resumen solicitado)

- **Moderada (1):** `qs` 6.16.0, GHSA-6pq8-jhm2-2vcw, rango `>=6.7.0 <=6.16.0`.
  `fixAvailable: true`; el informe no indica una versión corregida concreta
  para esta severidad (se resolvería con `npm audit fix`). No se aplica.
- **Bajas (6):** cadena de `jest` 29.7.0 (`@jest/core`, `jest-cli`,
  `jest-config`, `create-jest`) y `deepmerge` (GHSA-gcqx-w48m-w2h4). El
  informe propone `jest` **25.1.0** con `isSemVerMajor: true`, es decir un
  *downgrade* incompatible con la suite actual. No se aplica.

## Estado tras el Bloque G

| Paquete | Estado |
|---|---|
| `body-parser` 1.20.9 | **Corregido** en G (único cambio del lockfile). |
| `zod` 3.25.76 | Diferido: requiere major 4.x y migración de validadores. |
| `qs` 6.16.0 | Diferido (moderada, fuera de alcance). |
| `jest` 29.7.0 y `deepmerge` | Diferidos (bajas; el informe propone un downgrade incompatible). |

Para un bloque posterior, con aprobación explícita, se puede evaluar por
separado la migración a `zod` 4.6.7 y la corrección de `qs`. No se ha usado
`npm audit fix --force` en ningún momento.
