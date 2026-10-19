@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Creando Bo7 Zombies Simple Tool.exe ===
echo.

set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
    echo No encuentro Python. Instalalo desde https://www.python.org/downloads/
    echo y marca la casilla "Add python.exe to PATH" durante la instalacion.
    pause
    exit /b 1
)
echo Usando: %PY%
echo.

%PY% -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo.
    echo No se pudo instalar PyInstaller.
    pause
    exit /b 1
)
%PY% -m PyInstaller --noconfirm --onefile --noconsole --uac-admin ^
    --name "Bo7 Zombies Simple Tool" "Bo7 Zombies Simple Tool.pyw"
if errorlevel 1 (
    echo.
    echo Hubo un error al crear el .exe
    pause
    exit /b 1
)
echo.
echo Listo! El programa esta en la carpeta "dist":
echo   %~dp0dist\Bo7 Zombies Simple Tool.exe
echo.
explorer "%~dp0dist"
pause
