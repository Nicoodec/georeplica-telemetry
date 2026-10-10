# Publicar en GitHub Pages

Esta carpeta ya es el contenido completo del repositorio. Faltan dos pasos que tienen
que salir de tu cuenta.

## 1. Crear el repositorio y subirlo

**Con GitHub CLI** (si tienes `gh` instalado y con sesión iniciada):

```
cd "%USERPROFILE%\Desktop\Georeplica\repo"
git init -b main
git add -A
git commit -m "Consola de telemetría de pista"
gh repo create georeplica-telemetry --public --source=. --push
```

**Sin GitHub CLI**: crea el repositorio vacío en https://github.com/new con el nombre
`georeplica-telemetry`, sin README ni .gitignore, y luego:

```
cd "%USERPROFILE%\Desktop\Georeplica\repo"
git init -b main
git add -A
git commit -m "Consola de telemetría de pista"
git remote add origin https://github.com/Nicoodec/georeplica-telemetry.git
git push -u origin main
```

O usa `publicar.cmd`, que hace exactamente eso.

## 2. Activar Pages

En el repositorio: **Settings → Pages → Build and deployment**, fuente **Deploy from a
branch**, rama `main`, carpeta `/ (root)`, y Save.

La página queda en:

```
https://nicoodec.github.io/georeplica-telemetry/
```

Tarda uno o dos minutos la primera vez.

## Antes de hacerlo público

El clip de `match.mp4` y `match.webm` es metraje de retransmisión de ATP Media / Tennis
TV. Publicarlo en un repositorio público lo redistribuye. Si eso es un problema,
sustituye los dos archivos por un clip con derechos y vuelve a generar `data/telemetry.json`
con el pipeline; la consola no depende de ese clip concreto.

## Para que yo lo haga directamente la próxima vez

Esta sesión puede leer tu GitHub pero no escribir. Se arregla reconectando GitHub en
https://claude.ai/customize/connectors o instalando la app en
https://github.com/apps/claude/installations/select_target. Con eso puedo crear el
repositorio, subirlo y activar Pages sin que toques nada.
