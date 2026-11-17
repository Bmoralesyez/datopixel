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
