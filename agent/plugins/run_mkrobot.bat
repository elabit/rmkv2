@echo off
echo XXXXXXXXXXXXXXXXXXXXXXXXX
:: cd ..\..\mkrobot
:: start /B mkrobot.bat
powershell Start-Process -NoNewWindow C:\ProgramData\checkmk\mkrobot\mkrobot.bat
:: cd ..\agent\plugins
echo XXXXXXXXXXXXXXXXXXXXXXXXX
ping 127.0.0.1 -n 20 > nul
exit 0