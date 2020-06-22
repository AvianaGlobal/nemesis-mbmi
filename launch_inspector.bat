@echo on
cd %HOMEPATH%\install_test\nemesis-mbmi\main
call ..\venv\Scripts\activate.bat
call python -v -m nemesis.app.inspector.main 