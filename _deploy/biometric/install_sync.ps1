# تثبيت مزامنة جهاز البصمة على كمبيوتر العميل (Windows) — بيتشغل بأمر واحد:
#   $env:ZK_SN='CJMS213461364'; iwr -UseBasicParsing https://raw.githubusercontent.com/johnsamire-coder/motionhr/fix/group16-documents/_deploy/biometric/install_sync.ps1 | iex
# اختياري: $env:ZK_SINCE='2026-10-22' (أول مرة يبعت من التاريخ ده بس)
# بيحط البرنامج في C:\MotionHR-Biometric ويخليه يشتغل لوحده كل ما الكمبيوتر يفتح (من غير صلاحيات أدمن).
# للإلغاء: امسح الملف "MotionHR Biometric.cmd" من فولدر Startup واقفل pythonw من Task Manager.

$ErrorActionPreference = 'Continue'
$sn = "$env:ZK_SN".Trim()
if (-not $sn) { Write-Host 'لازم تكتب الرقم التسلسلي الأول: $env:ZK_SN=...' -ForegroundColor Red; return }
$since = "$env:ZK_SINCE".Trim()
$dir = 'C:\MotionHR-Biometric'
$base = 'https://raw.githubusercontent.com/johnsamire-coder/motionhr/fix/group16-documents/_deploy/biometric'

# 1) Python
$py = (Get-Command py -ErrorAction SilentlyContinue).Source
if (-not $py) {
    Write-Host 'بنزّل Python...'
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    foreach ($c in @("$env:LOCALAPPDATA\Programs\Python\Launcher\py.exe", 'C:\Windows\py.exe')) { if (Test-Path $c) { $py = $c; break } }
}
if (-not $py) { Write-Host 'Python ماتثبتش. اقفل PowerShell وافتحه تاني والصق الأمر مرة كمان.' -ForegroundColor Red; return }

# 2) المكتبة والأداة
& $py -m pip install --quiet --disable-pip-version-check pyzk
New-Item -ItemType Directory -Force -Path $dir | Out-Null
Invoke-WebRequest -UseBasicParsing "$base/zk_tool.py" -OutFile "$dir\zk_tool.py"
$pyw = (& $py -c "import sys, os; print(os.path.join(os.path.dirname(sys.executable), 'pythonw.exe'))").Trim()

# 3) نتأكد إننا شايفين الجهاز
Write-Host 'بدور على الجهاز في الشبكة (ممكن ياخد دقيقة)...'
& $py "$dir\zk_tool.py" auto info --sn $sn
if ($LASTEXITCODE -ne 0) { Write-Host 'مش لاقي الجهاز. اتأكد إن الكمبيوتر والجهاز على نفس الراوتر.' -ForegroundColor Red; return }

# 4) يشتغل لوحده مع فتح الكمبيوتر، ونشغله دلوقتي
$targs = "`"$dir\zk_tool.py`" auto sync --sn $sn"
if ($since) { $targs += " --since $since" }
$startup = [Environment]::GetFolderPath('Startup')
Set-Content -Encoding ASCII -Path "$startup\MotionHR Biometric.cmd" -Value "@echo off`r`ncd /d `"$dir`"`r`nstart `"`" `"$pyw`" $targs"
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" | Where-Object { $_.CommandLine -like '*zk_tool.py*sync*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-Process -FilePath $pyw -ArgumentList $targs -WorkingDirectory $dir -WindowStyle Hidden
Start-Sleep -Seconds 20
Write-Host ''
Get-Content "$dir\zk_sync.log" -Tail 5 -ErrorAction SilentlyContinue
Write-Host ''
Write-Host 'تم ✅ البرنامج شغال وهيشتغل لوحده كل ما الكمبيوتر يفتح. السجل في C:\MotionHR-Biometric\zk_sync.log' -ForegroundColor Green
