# PowerShell 啟動腳本，適合初學者
# 1. 設定執行權限（只對本次視窗有效）
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# 2. 啟動 Python 虛擬環境
.\venv\Scripts\activate

# 3. 清除畫面
Clear-Host

# 4. 檢查 devtunnel 是否已登入，未登入則執行登入
.\devtunnel.exe account show > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "尚未登入 devtunnel，正在執行 GitHub 登入..."
    .\devtunnel.exe login -g
}

# 5. 啟動 devtunnel 通道
.\devtunnel.exe host -p 5000 --protocol http --allow-anonymous
 