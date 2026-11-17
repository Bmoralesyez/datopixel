# DatoPixel
Proyecto de automatizacion de contenido informativo. Estructura: `DatoPixel/<tema> - dd-mm-aaaa/` con `video.mp4`, `portada_A.png`, `portada_B.png` y `guion_y_publicacion.docx`.

## Publicación automática (YouTube)
`scripts/youtube_scheduler.py` + `.github/workflows/youtube-scheduler.yml` agendan los videos en YouTube Shorts según `programacion/youtube.json`. Guía: [docs/youtube-setup.md](docs/youtube-setup.md). Decisiones: [docs/registro-decisiones.md](docs/registro-decisiones.md).
