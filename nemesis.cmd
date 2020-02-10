@ECHO OFF
CD %HOMEPATH%/nemesis-mbmi/main
CALL %HOMEPATH%/nemesis-mbmi/nemesis_env/scripts/activate.bat
CALL python -m elite.app.builder.main