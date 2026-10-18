param([switch]$SkipTests, [switch]$OneDir)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not $IsWindows -and $env:OS -ne 'Windows_NT') { throw 'Build on Windows x64.' }
function Invoke-Python {
    & $script:Python @args
    if ($LASTEXITCODE -ne 0) { throw "Python failed with exit code $LASTEXITCODE" }
}
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    if ($env:pythonLocation -and (Test-Path -LiteralPath (Join-Path $env:pythonLocation 'python.exe'))) {
        & (Join-Path $env:pythonLocation 'python.exe') -m venv .venv
    } else {
        & py -3 -m venv .venv
    }
    if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.11+ x64 and the Python launcher first.' }
}
$script:Python = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
Invoke-Python -m pip install -r requirements-build.txt -r requirements-dev.txt
if (-not $SkipTests) {
    $previousQt = $env:QT_QPA_PLATFORM
    try {
        $env:QT_QPA_PLATFORM = 'offscreen'
        Invoke-Python -m pytest --ignore=tests/test_server.py
    } finally {
        if ($null -eq $previousQt) { Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue }
        else { $env:QT_QPA_PLATFORM = $previousQt }
    }
}
$buildArgs = @('build.py', '--target', 'gui', '--clean')
if ($OneDir) { $buildArgs += '--onedir' }
Invoke-Python @buildArgs
$exe = if ($OneDir) { 'dist/bilibili-drops-miner-gui/bilibili-drops-miner-gui.exe' } else { 'dist/bilibili-drops-miner-gui.exe' }
$resultFile = Join-Path $PSScriptRoot 'dist/windows-smoke-result.json'
Remove-Item -LiteralPath $resultFile -ErrorAction SilentlyContinue
$process = Start-Process -FilePath (Join-Path $PSScriptRoot $exe) -ArgumentList @('--smoke-test', '--smoke-result', ('"' + $resultFile + '"')) -WindowStyle Hidden -PassThru
if (-not $process.WaitForExit(60000)) { $process.Kill(); throw 'Packaged app smoke test timed out.' }
if ($process.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $resultFile)) { throw 'Packaged app smoke test failed.' }
$result = Get-Content -LiteralPath $resultFile -Raw | ConvertFrom-Json
if (-not $result.ok) { throw "Packaged app smoke test failed: $($result.error)" }
Write-Host "Windows app ready: $exe"
