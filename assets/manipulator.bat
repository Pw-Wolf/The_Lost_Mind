@echo off
ping 127.0.0.1 -n 1 -w 500> nul
xcopy /Y /I /E /C update .\
rmdir /S /Q update
start The_Lost_Mind.exe
exit