# instalar-modelo.ps1 - Ollama en Windows, SOLO CPU.
# Requiere Windows PowerShell 5. Es ASCII (sin tildes) a proposito.
# Comprueba ollama, descarga el modelo base y crea "consultas-asistente"
# con ia/Modelfile + el SYSTEM de ia/prompts/sistema.md.

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'entorno.ps1')
Importar-Entorno -RutaEnv (Join-Path $PSScriptRoot '..\.env')

$ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
if ($null -eq $ollamaCmd) {
    Write-Host "No se encontro 'ollama' en el PATH. Instala Ollama para Windows y reintenta."
    exit 1
}

Write-Host 'Version de Ollama (evidencia para el video):'
& ollama --version

$base = $env:OLLAMA_MODELO_BASE
if ([string]::IsNullOrEmpty($base)) { $base = 'qwen3:4b-instruct-2507-q4_K_M' }
$destino = $env:OLLAMA_MODEL
if ([string]::IsNullOrEmpty($destino)) { $destino = 'consultas-asistente' }

Write-Host "Descargando el modelo base (solo CPU, puede tardar): $base"
& ollama pull $base
if ($LASTEXITCODE -ne 0) {
    Write-Host "Fallo 'ollama pull'. Revisa el nombre del modelo y la conexion."
    exit 1
}

$plantilla = Join-Path $PSScriptRoot '..\Modelfile'
$prompt = Join-Path $PSScriptRoot '..\prompts\sistema.md'
if (-not (Test-Path -LiteralPath $plantilla)) { Write-Host 'Falta ia/Modelfile'; exit 1 }
if (-not (Test-Path -LiteralPath $prompt)) { Write-Host 'Falta ia/prompts/sistema.md'; exit 1 }

# Construir un Modelfile temporal FUERA del repo, sin BOM (Ollama no tolera BOM).
$temporal = Join-Path $env:TEMP 'consultas-asistente.Modelfile'
$lineas = @()
$lineas += (Get-Content -LiteralPath $plantilla)
$lineas += 'SYSTEM """'
$lineas += (Get-Content -LiteralPath $prompt -Encoding UTF8)
$lineas += '"""'
$texto = ($lineas -join "`n") + "`n"
$utf8SinBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($temporal, $texto, $utf8SinBom)

Write-Host "Creando el modelo derivado '$destino' (temperature 0.2, top_p 0.8, num_ctx 4096) ..."
& ollama create $destino -f $temporal
$resultado = $LASTEXITCODE
Remove-Item -LiteralPath $temporal -Force -ErrorAction SilentlyContinue
if ($resultado -ne 0) {
    Write-Host "Fallo 'ollama create'. Revisa el Modelfile generado."
    exit 1
}

Write-Host ''
Write-Host "Listo. Modelo derivado: $destino"
Write-Host 'Comprueba con: ollama list'
Write-Host 'Importante: define OLLAMA_KEEP_ALIVE=30m en las variables de entorno'
Write-Host 'de Windows ANTES de iniciar Ollama; si no, el modelo se descarga a los'
Write-Host '5 minutos y la primera respuesta de cada ronda vuelve a ser lenta.'
