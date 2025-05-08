# PowerShell 啟動腳本，適合初學者
# 1. 設定執行權限（只對本次視窗有效）
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# 2. 啟動 Python 虛擬環境
.\venv\Scripts\activate

# 3. 清除畫面
Clear-Host

 .\devtunnel.exe host -p 5000 --protocol http --allow-anonymous
 