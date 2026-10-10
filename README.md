# Georeplica · Court Telemetry

Consola de telemetría de tenis construida sobre **un punto real** de Nadal–Dimitrov
(Rolex Shanghai Masters 2017): 1 043 fotogramas a 1080p60, 17,4 segundos.

El seguimiento de los jugadores, su esqueleto, la geometría de la pista y los impactos
están **medidos del vídeo**. Las pulsaciones, el gasto energético, el vuelo de la bola y
la probabilidad de victoria están **calculados por modelo**. No hay nada inventado
presentado como medición, y la interfaz etiqueta cada panel con su procedencia.

## Qué está medido

| Señal | Método | Resultado |
|---|---|---|
| Movimiento de cámara | Homografía ORB + RANSAC de cada fotograma contra el de referencia | Paneo de hasta 104 px, compensado |
| Geometría de pista | Casco convexo de las líneas, ajustado a la pista reglamentaria | Las líneas de servicio, que no entran en el ajuste, caen sobre las reales |
| Jugadores | Sustracción de fondo en el espacio estabilizado, Viterbi global, suavizado Kalman RTS | 0 pérdidas de identidad y 0 fotogramas sin detección en 1 043 |
| Caja | Extremos del blob con dilatación temporal y suelo geométrico | 98,8 % y 95,2 % de la silueta cubierta |
| Esqueleto | Red de pose sobre el recorte de cada jugador, 13 articulaciones | Confianza media 0,90 y 0,95 |
| Extremidades | Ángulos y distancias entre articulaciones, convertidos con la calibración | Rodilla 113–177°, apertura de pies 0,10–1,02 m |
| Impactos | Transitorios en la banda de 1,2–7 kHz del audio | 12 impactos en el punto |

Detalle que importa: a 20 m de profundidad **un píxel vale 0,21 m**, así que derivar
velocidades fotograma a fotograma da disparates (15 m/s, 6 g). La covarianza de medida
del filtro de Kalman sale del jacobiano de la homografía en cada punto, de modo que el
suavizado es mayor donde el ruido de proyección es mayor. Con eso las velocidades caen
en 6,6 y 7,9 m/s de pico, que es lo que hace un jugador de élite.

## Qué está calculado

- **Fisiología**: coste de carrera de di Prampero sobre el movimiento medido, más una
  respuesta cardíaca de primer orden. Son estimaciones, no telemetría de pulsómetro.
- **Vuelo de la bola**: integración RK4 con arrastre cuadrático (Cd = 0,55 + 0,18·S) y
  efecto Magnus (Cl = S/(2S+1)). Validación independiente: un saque a 186 km/h y −6°
  pasa la red a 0,83 m y bota a 15,3 m, dentro del cuadro de servicio, sin haber ajustado
  nada para que eso ocurriera.
- **Marcador**: cadena de Markov exacta de punto, juego, set y partido, con tie-break.
  Todos los casos simétricos devuelven exactamente 0,5000.

## Qué no hay

**Seguimiento de bola.** A 30 fps la bola se confunde con las líneas y la publicidad, y
los candidatos los dominan objetos amarillos estáticos del fondo. **Efecto medido**
tampoco: 1 980 rpm no se recuperan de un vídeo normal. Por eso el panel de vuelo es un
modelo con parámetros a mano y la barra lateral marca esas entradas en rojo.

## Estructura

```
index.html              La consola, autocontenida (datos incluidos)
data/telemetry.json     Los mismos datos, sueltos, para reutilizar
pipeline/               Los scripts que produjeron esos datos, en orden de ejecución
logo.svg                Logotipo vectorizado, versión apilada
logo-bar.svg            Versión horizontal para cabeceras
```

Orden del pipeline: `homog.py` → `bg.py` → `track.py` → `viterbi.py` → `kalman.py` →
`toscreen.py` → `pose.py` → `limbs.py` → `metrics.py` → `export.py`. `qa.py` mide la
cobertura de las cajas y `vec2.py` vectoriza el logotipo.

Dependencias: `opencv-python`, `numpy`, `scipy`, `ultralytics`, `ffmpeg`.

## Uso

Abre `index.html` en el navegador. No necesita servidor.

## Sobre el vídeo

`match.mp4` y `match.webm` son un recorte de 17 segundos de una retransmisión de ATP
Media / Tennis TV, usado aquí como material de prueba técnica. **No es material propio y
su redistribución tiene su propia capa de licencias.** Si este repositorio va a ser
público o comercial, sustituye el clip por metraje con derechos y regenera los datos con
el pipeline: ningún número de la consola depende de ese clip en particular.
