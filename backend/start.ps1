$env:PYTHONUTF8 = "1"
& ".\.venv\Scripts\uvicorn.exe" main:app --reload --port 8000
