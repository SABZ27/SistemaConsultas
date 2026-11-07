# entorno.ps1 - lector minimalista de ia/.env para Windows PowerShell 5.
# Es ASCII (sin tildes) a proposito: PS5 lee sin BOM como ANSI.
# No imprime NINGUN valor: solo carga variables en el proceso actual.

function Importar-Entorno {
    param([Parameter(Mandatory = $true)][string]$RutaEnv)

    if (-not (Test-Path -LiteralPath $RutaEnv)) {
        return
    }

    foreach ($linea in (Get-Content -LiteralPath $RutaEnv)) {
        $texto = $linea.Trim()
        if ($texto -eq '' -or $texto.StartsWith('#')) {
            continue
        }
        $pos = $texto.IndexOf('=')
        if ($pos -lt 1) {
            continue
        }
        $clave = $texto.Substring(0, $pos).Trim()
        $valor = $texto.Substring($pos + 1).Trim()

        # Quitar comillas envolventes si las hay.
        if ($valor.Length -ge 2) {
            $primero = $valor.Substring(0, 1)
            $ultimo = $valor.Substring($valor.Length - 1, 1)
            if (($primero -eq '"' -and $ultimo -eq '"') -or ($primero -eq "'" -and $ultimo -eq "'")) {
                $valor = $valor.Substring(1, $valor.Length - 2)
            }
        }

        # No sobrescribir variables ya definidas en el entorno del proceso.
        $actual = [Environment]::GetEnvironmentVariable($clave, 'Process')
        if ([string]::IsNullOrEmpty($actual)) {
            [Environment]::SetEnvironmentVariable($clave, $valor, 'Process')
        }
    }
}
