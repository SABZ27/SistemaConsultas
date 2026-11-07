# iniciar-openwebui.ps1 - MODO PIP (por defecto, sin Docker).
# Requiere Windows PowerShell 5. Es ASCII (sin tildes) a proposito.
# No instala nada: si el venv no existe, imprime las instrucciones y sale.

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'entorno.ps1')
Importar-Entorno -RutaEnv (Join-Path $PSScriptRoot '..\.env')

$modo = $env:OPENWEBUI_MODE
if ([string]::IsNullOrEmpty($modo)) { $modo = 'pip' }

if ($modo -ne 'pip') {
    Write-Host "OPENWEBUI_MODE=$modo. Este script es solo para el MODO PIP."
    Write-Host "Para el MODO DOCKER ejecuta: cd ia; docker compose --env-file .env up -d"
    exit 1
}

$venv = $env:VENV_OPENWEBUI
if ([string]::IsNullOrEmpty($venv)) { $venv = 'C:\dev\venv-openwebui' }
$pythonExe = Join-Path $venv 'Scripts\python.exe'
$openwebuiExe = Join-Path $venv 'Scripts\open-webui.exe'

if (-not (Test-Path -LiteralPath $openwebuiExe)) {
    Write-Host '------------------------------------------------------------------'
    Write-Host "No existe el entorno virtual de Open WebUI en: $venv"
    Write-Host 'El script NO instala nada. Crea el venv FUERA del repo, una sola vez:'
    Write-Host ''
    Write-Host "  py -3.12 -m venv $venv"
    Write-Host "  & '$pythonExe' -m pip install --upgrade pip"
    Write-Host "  & '$pythonExe' -m pip install open-webui==0.13.0"
    Write-Host ''
    Write-Host 'Nota: Open WebUI 0.13.0 exige Python 3.11 o 3.12 (NO 3.13).'
    Write-Host 'En Linux sin GPU se puede instalar antes el PyTorch CPU; en Windows'
    Write-Host 'no es necesario (no se arrastran las librerias CUDA).'
    Write-Host 'Version verificada contra la documentacion oficial de Open WebUI:'
    Write-Host '  pip install open-webui / open-webui serve --port 3000'
    Write-Host '------------------------------------------------------------------'
    exit 1
}

$dataDir = $env:DATA_DIR
if ([string]::IsNullOrEmpty($dataDir)) { $dataDir = 'C:\dev\openwebui-data' }
if (-not (Test-Path -LiteralPath $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
}
$env:DATA_DIR = $dataDir

if ([string]::IsNullOrEmpty($env:WEBUI_SECRET_KEY)) {
    Write-Host 'Falta WEBUI_SECRET_KEY en ia/.env. Genera una clave estable y no la compartas.'
    exit 1
}

$puerto = $env:OPENWEBUI_PORT
if ([string]::IsNullOrEmpty($puerto)) { $puerto = '3000' }

Write-Host "Iniciando Open WebUI (MODO PIP) en http://localhost:$puerto ..."
Write-Host "DATA_DIR=$dataDir"
Write-Host 'Recuerda: Ollama debe estar corriendo y OLLAMA_KEEP_ALIVE=30m.'
Write-Host 'La primera carga de documentos descarga el modelo de embeddings (internet).'
Write-Host 'Detener con Ctrl+C.'

& $openwebuiExe serve --port $puerto
