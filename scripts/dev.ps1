param()

Start-Process -NoNewWindow -FilePath pwsh -ArgumentList "-NoLogo -NoProfile -Command cd backend; uvicorn app.main:app --reload" | Out-Null
Start-Process -NoNewWindow -FilePath pwsh -ArgumentList "-NoLogo -NoProfile -Command cd frontend; npm run dev" | Out-Null

Write-Host "Dev servers started. Press Ctrl+C in each window to stop."

