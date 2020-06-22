@echo on
cd %HOMEPATH%\install_test\nemesis-mbmi\main
call ..\venv\Scripts\activate.bat
call python -v -m nemesis.app.builder.main ..\examples\vsp.nam --data ..\examples\vsp.csv --debug