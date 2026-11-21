# DatoPixel: publicación automática (actualizado el 21/11/2026)

**Este documento reemplaza la versión del 17/11 (que describía un agendador propio con Google Cloud, ya descartado).** Las instrucciones vigentes para subir los videos están en la **sección 7 de `analisis-metricas-y-monetizacion.md`**. Resumen:

- **YouTube**: Zapier (`upload_video`, privado + `publish_at`), un video a la vez.
- **TikTok e Instagram**: Zernio (`posts_create` + `posts_update` para la hora exacta).
- **Primer comentario**: solo Instagram, con Windsor.ai (`create_comment`). YouTube y TikTok sin resolver.
- **Metricool**: ya no se usa para publicar (límite gratis de 20 posts al mes por red; se renueva el 1/12). Sus posts antiguos hay que borrarlos a mano.
- **Antes de programar**: subir la carpeta del video al repo `Bmoralesyez/datopixel` (rama `main`); las herramientas leen el video y la portada desde la URL raw de GitHub.
- **Registro técnico**: `docs/registro-decisiones.md` del repo. Agregar ahí cada cambio.
- **Respaldo** (no usar sin autorización del usuario, requiere Google Cloud): `scripts/youtube_scheduler.py` y `.github/workflows/youtube-scheduler.yml`.
- **Riesgo**: la prueba gratis de Zapier termina el 4/12/2026.
