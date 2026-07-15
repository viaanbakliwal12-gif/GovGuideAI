$env:PYTHONPATH = Join-Path $PSScriptRoot ".venv\Lib\site-packages"
Set-Location $PSScriptRoot

& (Join-Path $PSScriptRoot ".uv-python\cpython-3.11.15-windows-x86_64-none\python.exe") -m app.database.migrate
