$env:PYTHONPATH = Join-Path $PSScriptRoot ".venv\Lib\site-packages"
Set-Location $PSScriptRoot

& (Join-Path $PSScriptRoot ".uv-python\cpython-3.11.15-windows-x86_64-none\python.exe") -c "from app.server import create_app; create_app().run(host='127.0.0.1', port=5000, debug=False)"
