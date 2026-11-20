# Registro de decisiones: publicación automática

## 2026-11-16: Metricool gratis llegó a su límite
Metricool (plan gratuito) permite 20 posts publicados al mes, contados por red. Se alcanzó el 16/11 y fallaron en las tres redes los videos de Luna (10:00), barcos (14:00) y Foucault (18:00). El límite se renueva el 1/12. Se busca un método gratuito y mantenible.

## 2026-11-17: Viabilidad por red (solo análisis)
| Red | Veredicto | Motivo |
|---|---|---|
| YouTube | Viable | API oficial gratis; `videos.insert` con `privacyStatus=private` + `publishAt` agenda de verdad. |
| Instagram | Viable (cuenta propia, profesional) | Graph API: contenedor → `media_publish`. No agenda a futuro: se publica en el momento (requiere cron puntual). Token a renovar cada 60 días. |
| TikTok | No viable con app propia | Apps sin auditar solo publican en privado. Alternativas: Zernio (gratis, 2 cuentas) o publicar manualmente desde TikTok Studio. |

## 2026-11-17: Se implementa primero YouTube
- Script en Python, solo librería estándar (`scripts/youtube_scheduler.py`), sin dependencias que mantener.
- Agenda con `publishAt` al subir (privado hasta la hora): la hora de publicación no depende del cron de GitHub, que puede atrasarse 5-30 min.
- Metadatos leídos del `.docx` de cada video para no duplicar texto en una segunda fuente.
- Videos y portadas se leen del propio repo (sin hosting externo).
- Estado en `programacion/youtube.json`, guardado tras cada paso (incl. si el workflow falla) para no duplicar subidas.
- Primer comentario: se publica solo cuando el video ya es público.
- Secrets solo en GitHub Secrets. Refresh token: la app OAuth debe estar *In production* para que no caduque a los 7 días.

## Pendiente
- Prueba real con un video (no se pudo probar contra la API real desde este entorno; las pruebas usan respuestas simuladas).
- Verificar en la práctica que un proyecto no verificado puede agendar (desde 2/11/2026 ya no se fuerza a privado, pero hay que comprobarlo).
- Decidir método para Instagram y TikTok.
- Qué hacer con los posts ya agendados en Metricool desde el 17/11 (fallarán hasta el 1/12) y con los 3 del 16/11 que fallaron.

## 2026-11-19: Cambio de método para YouTube, sin Google Cloud
El usuario no quiere crear un proyecto en Google Cloud. Windsor.ai (conectores general y Social Media) no sube videos: en YouTube solo edita videos ya subidos y TikTok no tiene acciones de publicación. Instagram sí tiene `create_video_post` (publica al momento, desde una URL pública), pero no está conectado.

**Zapier (conector de Claude) sí sube a YouTube.** Acción `upload_video` + `upload_video_thumbnail`, con la app aprobada de Zapier; el usuario solo autorizó su canal con un clic.
- Prueba real (19/11): "¿Cómo flota un barco de acero?" subido como privado con `publish_at` 2026-11-20 14:00 (Santiago) = 17:00 UTC. Zapier lo aceptó (a pesar de su nota "solo Partner"), YouTube devolvió `privacyStatus=private` y `publishAt` correctos, y la portada quedó aplicada. Video leído desde la URL raw de GitHub.
- Zapier no tiene acción de comentar, así que el primer comentario queda pendiente (posible vía `_zap_raw_request` a `commentThreads`).
- El script de `scripts/youtube_scheduler.py` y su workflow quedan como respaldo; no hace falta configurar los Secrets si se usa Zapier.

## 2026-11-19: Instagram vía Windsor.ai for Social Media (prueba real)
- Conectada la cuenta datopixel3d (Instagram Login). Acción `create_video_post` publica un Reel desde una URL pública (raw de GitHub); `create_comment` agrega el primer comentario.
- Prueba: Reel "Barco de acero flota" publicado a las 22:00 (Santiago) con texto del .docx, aparece en el feed; primer comentario publicado. Media id 18109477697629549.
- Limitación: publica al momento, sin programación. Portada personalizada solo JPEG por URL; se usó el primer fotograma.
- TikTok: ninguna herramienta conectada publica (Zapier solo tiene anuncios/leads, Windsor solo lee). Opciones: Metricool solo para TikTok desde el 1/12 (20 al mes por red), o manual.

## 2026-11-20: TikTok vía Zernio (prueba real)
- Zernio (conector MCP, OAuth) con la cuenta TikTok @datopixel3d conectada; plan gratis (2 primeras cuentas, posts ilimitados, programación). Cuenta sana y con permiso `video.publish`.
- Prueba: "Barco de acero flota" publicado en TikTok con `posts_publish_now` desde la URL raw de GitHub (estado "published"). Post ID Zernio 6b00d13212205d28e28e9f78.
- Pendiente: confirmar en la app que quedó público con buena calidad, probar programación (`schedule_minutes`) y encontrar cómo agregar el primer comentario (la herramienta de Zernio solo responde comentarios existentes).
- Estado por red: YouTube = Zapier (programa hora); Instagram = Windsor (al momento); TikTok = Zernio (programable según documentación, por verificar).
