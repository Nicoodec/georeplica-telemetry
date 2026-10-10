@echo off
setlocal
cd /d "%~dp0"
echo.
echo  Georeplica - publicar en GitHub
echo.
set /p NOMBRE=Nombre del repositorio [georeplica-telemetry]: 
if "%NOMBRE%"=="" set NOMBRE=georeplica-telemetry
git rev-parse --git-dir >nul 2>&1 || (git init -b main)
git add -A
git commit -m "Consola de telemetria de pista" 2>nul
where gh >nul 2>&1
if %errorlevel%==0 (
  echo  Creando %NOMBRE% con GitHub CLI...
  gh repo create %NOMBRE% --public --source=. --push
  gh api -X POST repos/:owner/%NOMBRE%/pages -f "source[branch]=main" -f "source[path]=/" 2>nul
  echo.
  echo  Listo. Pages tardara 1-2 minutos.
) else (
  echo  No encuentro GitHub CLI. Crea el repo vacio en https://github.com/new
  set /p URL=Pega la URL del repositorio: 
  git remote remove origin 2>nul
  git remote add origin %URL%
  git push -u origin main
  echo.
  echo  Subido. Ahora activa Settings ^> Pages ^> branch main ^> / (root).
)
pause
