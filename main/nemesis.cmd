@ECHO OFF
CD %homepath%\nemesis-mbmi
CALL conda activate nemesis 
CALL python -m elite.app.builder.main

