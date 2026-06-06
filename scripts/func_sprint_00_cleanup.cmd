@echo off
REM FUNC-SPRINT-00 cleanup wrapper for Windows CMD/PowerShell.
REM This wrapper avoids PowerShell ExecutionPolicy restrictions by executing the Python cleanup helper.
python "%~dp0func_sprint_00_cleanup.py" %*
