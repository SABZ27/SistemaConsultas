# iniciar-herramientas.ps1 - Fase 2: Toolbox (5000) + mcpo (8000).
# Requiere Windows PowerShell 5. Es ASCII (sin tildes) a proposito.
# NO descarga toolbox.exe: el responsable lo coloca en ia/bin/toolbox.exe.
# Lee ia/.env sin imprimir NINGUN valor secreto.

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'entorno.ps1')
Importar-Entorno -RutaEnv (Join-Path $PSScriptRoot '..\.env')

$raiz = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$repo = Split-Path -Parent $raiz

# Comprobar variables obligatorias SIN mostrar sus valores.
$faltan = @()
foreach ($nombre in @('NEON_HOST', 'NEON_DATABASE', 'NEON_USER', 'NEON_PASSWORD', 'MCPO_API_KEY')) {
    $valor = [Environment]::GetEnvironmentVariable($nombre, 'Process')
    if ([string]::IsNullOrEmpty($valor)) { $faltan += $nombre }
}
if ($faltan.Count -gt 0) {
    Write-Host 'Faltan variables en ia/.env (no se imprimen sus valores):'
    $faltan | ForEach-Object { Write-Host "  - $_" }
    exit 1
}

function Resolver-Ruta {
    param([string]$Ruta)
    if ([System.IO.Path]::IsPathRooted($Ruta)) { return $Ruta }
    return (Join-Path $repo $Ruta)
}

$toolboxExe = Resolver-Ruta (Join-Path $raiz 'bin\toolbox.exe')
if (-not [string]::IsNullOrEmpty($env:TOOLBOX_EXE)) {
    $toolboxExe = Resolver-Ruta $env:TOOLBOX_EXE
}
$config = Resolver-Ruta (Join-Path $raiz 'db\tools.yaml')
if (-not [string]::IsNullOrEmpty($env:TOOLBOX_CONFIG)) {
    $config = Resolver-Ruta $env:TOOLBOX_CONFIG
}

$puertoToolbox = if ($env:TOOLBOX_PORT) { $env:TOOLBOX_PORT } else { '5000' }
$puertoMcpo = if ($env:MCPO_PORT) { $env:MCPO_PORT } else { '8000' }
$tipoMcpo = if ($env:MCPO_SERVER_TYPE) { $env:MCPO_SERVER_TYPE } else { 'streamable-http' }
$upstream = if ($env:MCPO_UPSTREAM_URL) { $env:MCPO_UPSTREAM_URL } else { "http://127.0.0.1:$puertoToolbox/mcp" }

if (-not (Test-Path -LiteralPath $toolboxExe)) {
    Write-Host "Falta el binario de Toolbox en: $toolboxExe"
    Write-Host 'Coloca ahi toolbox.exe (lo proporciona el responsable; este repo NO lo descarga).'
    exit 1
}
if (-not (Test-Path -LiteralPath $config)) {
    Write-Host "Falta la configuracion de Toolbox: $config"
    exit 1
}

$venvMcpo = if ($env:VENV_MCPO) { $env:VENV_MCPO } else { 'C:\dev\venv-mcpo' }
$mcpoExe = Join-Path $venvMcpo 'Scripts\mcpo.exe'
if (-not (Test-Path -LiteralPath $mcpoExe)) {
    $pyMcpo = Join-Path $venvMcpo 'Scripts\python.exe'
    Write-Host "Falta mcpo en: $mcpoExe. Crea su venv propio, una sola vez:"
    Write-Host "  py -3.12 -m venv $venvMcpo"
    Write-Host "  & '$pyMcpo' -m pip install mcpo==0.0.20"
    exit 1
}

# --- 1) Toolbox: servidor MCP HTTP en 127.0.0.1:5000 ---
$argsToolbox = "--config `"$config`" --port $puertoToolbox --address 127.0.0.1 --allowed-hosts localhost,127.0.0.1 --disable-reload"
Write-Host "Iniciando Toolbox (MCP HTTP) en 127.0.0.1:$puertoToolbox ..."
$procToolbox = Start-Process -FilePath $toolboxExe -ArgumentList $argsToolbox -PassThru -WindowStyle Minimized
Write-Host "Toolbox PID=$($procToolbox.Id)"

# Dar un margen breve para que Toolbox abra el puerto antes de mcpo.
Start-Sleep -Seconds 3

# --- 2) mcpo: OpenAPI en 127.0.0.1:8000, apuntando al MCP de Toolbox ---
$claveMcpo = $env:MCPO_API_KEY
$argsMcpo = "--port $puertoMcpo --api-key `"$claveMcpo`" --server-type $tipoMcpo -- $upstream"
Write-Host "Iniciando mcpo (OpenAPI) en 127.0.0.1:$puertoMcpo ..."
$procMcpo = Start-Process -FilePath $mcpoExe -ArgumentList $argsMcpo -PassThru -WindowStyle Minimized
Write-Host "mcpo PID=$($procMcpo.Id)"

Write-Host ''
Write-Host 'Esquema OpenAPI: http://localhost:8000/openapi.json'
Write-Host 'Documentacion:   http://localhost:8000/docs'
$modo = if ($env:OPENWEBUI_MODE) { $env:OPENWEBUI_MODE } else { 'pip' }
if ($modo -eq 'docker') {
    Write-Host 'Registrar en Open WebUI (MODO DOCKER): http://host.docker.internal:8000/openapi.json'
    Write-Host '  (NO usar localhost: dentro del contenedor apunta al propio contenedor)'
} else {
    Write-Host 'Registrar en Open WebUI (MODO PIP): http://localhost:8000/openapi.json'
}
Write-Host 'Autenticacion: la MCPO_API_KEY configurada en ia/.env (Bearer).'
Write-Host 'Activa la herramienta en el modelo y copia su id a OPENWEBUI_TOOL_IDS'
Write-Host '(GET /api/v1/tools/ de Open WebUI).'
Write-Host ''
Write-Host 'Para detener: Detener-Process -Id <PID> (o cerrar las ventanas minimizadas).'
