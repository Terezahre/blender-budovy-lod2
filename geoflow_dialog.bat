@ECHO OFF
REM Geoflow LoD2.2 dialog — spousti HTA dialog (JavaScript) pro vstup/vystup.
REM Projekt: blender-budovy-lod2 (S-JTSK EPSG:5514)
cd /d "%~dp0"
set GF_PLUGIN_FOLDER=C:\Users\Tereza\geoflow-local\plugins
mshta.exe "%~dp0geoflow_dialog.hta"
