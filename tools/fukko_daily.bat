@echo off
rem ============================================================
rem  九州ふっこう応援割の見張りを1日1回回す。
rem  変化(県公式の一覧PDFの版が上がった/宿が追加された)があれば
rem  ログに残る。何も変わらなければ「変化なし」の1行だけ。
rem
rem  タスクスケジューラへの登録(ユーザー自身が1回実行する):
rem    schtasks /Create /TN "fukko_daily" /TR "\"C:\Users\totor\Dropbox\ショート動画用\4.MAP生成\tools\fukko_daily.bat\"" /SC DAILY /ST 09:07
rem  登録の確認:  schtasks /Query /TN "fukko_daily"
rem  今すぐ試す:  schtasks /Run /TN "fukko_daily"
rem  やめるとき:  schtasks /Delete /TN "fukko_daily" /F
rem
rem  ※9:07 のような端数の時刻にしているのは、0分/30分に集中させないため
rem ============================================================
setlocal
set PYTHONIOENCODING=utf-8
set HERE=%~dp0
set LOG=%HERE%..\data\fukko_daily.log

for /f "tokens=1-3 delims=/ " %%a in ("%DATE%") do set D=%%a-%%b-%%c
echo ---- %D% %TIME% ---->> "%LOG%"
python "%HERE%fukko_daily.py" >> "%LOG%" 2>&1
endlocal
