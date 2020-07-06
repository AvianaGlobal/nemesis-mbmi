@echo on
call .\venv27\Scripts\activate.bat
cd main
call python -v -m nemesis.app.builder.main --debug