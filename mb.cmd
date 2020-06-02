@ECHO OFF
CD %HOMEPATH%/stabilize/main
CALL %HOMEPATH%/stabilize/nemesis_env/scripts/activate.bat
CALL python -m elite.app.builder.main
