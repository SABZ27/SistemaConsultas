# Auditoría de dependencias (Bloque D.b — solo informe)

Ejecutada localmente el 2026-11-06. **No se aplicó ninguna corrección** ni se
modificaron `requirements.txt`, `package.json` ni ningún lockfile. `pip-audit`
se instaló únicamente en el entorno local del usuario.

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

## Decisión del bloque

Solo informe. No se ejecutó `npm audit fix`, no se subieron majors y no se
editaron archivos de dependencias. Para un bloque posterior, con aprobación
explícita, se puede evaluar por separado:

1. `body-parser` → 1.20.9 (corrección sin romper compatibilidad declarada).
2. `zod` → 4.6.7 (requiere migración de validadores; requiere autorización).
3. `qs` → revisar con `npm audit fix` en un entorno aislado.
