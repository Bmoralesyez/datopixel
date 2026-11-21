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

## 2026-11-20 — Prueba en 3 redes: Péndulo de Foucault (programado)
- Video: `DatoPixel/Pendulo de Foucault - 13-11-2026`. Publicación programada para sáb 21/11 14:00 Santiago (17:00Z) en las 3 redes.
- YouTube (Zapier `upload_video`, privado + `publish_at`): id `oUcl_Y2LE_w`, confirmado `privacyStatus=private`, `publishAt=2026-11-21T17:00:00Z`.
- TikTok (Zernio, cuenta datopixel3d): post `6b00d20dfda4cd21d00e4c84`, estado `scheduled` 17:00Z.
- Instagram (Zernio, cuenta datopixel3d): post `6b00d20e9956cdf1a3d3e3c7`, estado `scheduled` 17:00Z.
- Nota: `posts_create` solo acepta minutos relativos y quedó a 16:59Z; se corrigió con `posts_update(scheduled_for)`.
- Pendiente: verificar que las 3 salgan a la hora; primer comentario en YouTube/TikTok/Instagram (Zernio no puede crear comentario propio).

## 2026-11-21 — Videos pendientes (Metricool no los publicó): programados en las 3 redes
Se cruzó la lista de Metricool con el canal de YouTube: 12 videos no estaban publicados. Se programan 2 al día (14:00 y 18:00 Santiago) desde el 21/11. "Luna cara oculta" se excluye: mismo título/tema que el video "Luna" ya publicado (10/11), pendiente de decisión del usuario.

| Video | Hora (Santiago) | YouTube (Zapier) | TikTok (Zernio) | Instagram (Zernio) |
|---|---|---|---|---|
| Space Invaders | 21/11 18:00 | nS5s4VbZGrA | 6b00d32a420d378124ff0852 | 6b00d32bea46b2536f2f1d0b |
| Golf hoyuelos | 22/11 14:00 | rKJeDtHDec8 | 6b00d32e77e9ba45a67c249a | 6b00d32f420d378124ff0868 |
| GPS y relatividad | 22/11 18:00 | cCW8DTeh5AY | 6b00d33077e9ba45a67c24ab | 6b00d33277e9ba45a67c24b3 |
| Balón sin giro | 23/11 14:00 | oKis1tuSziA | 6b00d334420d378124ff0883 | 6b00d33594b71f24ba805c1d |
| Bumerán | 23/11 18:00 | s7gbom5CEec | 6b00d33cea46b2536f2f1d3c | 6b00d33eea46b2536f2f1d51 |
| Estrella fugaz | 24/11 14:00 | qDYsk2Zecd0 | 6b00d34077e9ba45a67c250b | 6b00d341ea46b2536f2f1d59 |
| Moneda girando | 24/11 18:00 | onvF8Iu8Xiw | 6b00d34377e9ba45a67c2522 | 6b00d34494b71f24ba805c82 |
| Pelota de tenis | 25/11 14:00 | hdxfjyyDkc0 | 6b00d34a94b71f24ba805cb8 | 6b00d34cea46b2536f2f1d95 |
| Básquetbol efecto | 25/11 18:00 | PENDIENTE | 6b00d34eea46b2536f2f1da6 | 6b00d34f77e9ba45a67c2534 |
| Anillos de Saturno | 26/11 14:00 | PENDIENTE | 6b00d35130d622eb4762c08b | 6b00d353ea46b2536f2f1dc3 |
| Luna se aleja | 26/11 18:00 | PENDIENTE | 6b00d354ea46b2536f2f1dd2 | 6b00d35630d622eb4762c09c |

- Zapier limita las subidas a YouTube en paralelo ("throttled"): hay que subir de a una, con pausa. Tras 8 subidas seguidas volvió a devolver throttled de forma sostenida; quedan 3 por subir.
- Los posts de Zernio quedan a la hora exacta con `posts_update(scheduled_for)` tras crearlos con `schedule_minutes`.
- Los posts de Metricool de esas fechas seguirán en su cola y fallarán: conviene borrarlos desde Metricool antes del 1/12 para que no se dupliquen al renovarse el límite.

## 2026-11-21 — Análisis de horarios y frecuencia; documentos actualizados
- Se actualizó `docs/analisis-metricas-y-monetizacion.md` (nueva sección 6 con el resultado de la prueba de horarios y de 3 videos diarios, y sección 7 con las instrucciones del sistema de subida actual) y `docs/publicacion-automatica.md`. Ambas copias se subieron también al proyecto de Claude.
- Resultado: la hora casi no cambia las vistas (10:00 ≈ 14:00 en YouTube); 3 videos al día no restan vistas a cada video (2 días de prueba); 45 s retiene más en proporción pero no da más vistas. Con Metricool gratis, 3 videos al día no son factibles (9 posts al día frente a 20 al mes por red); con Zernio y Zapier sí.
- Anomalía: el video de las ruedas del tren (12/11) tiene 2 vistas en YouTube estando público.
- Metricool no permite borrar posts desde el conector: borrarlos a mano en el planificador.
- Zapier: los 3 videos de YouTube pendientes (básquetbol, Saturno, Luna se aleja) siguen bloqueados por límite de velocidad.

## 2026-11-21 — Decisiones del usuario: frecuencia, duración y temas
- **2 videos diarios (14:00 y 18:00)** para no saturar los servicios; el tercer video de las 10:00 queda suspendido.
- **Duración estándar ≈65 s**, con holgura de 45 s a 1:30 según el tema.
- **Temas**: análisis de apoyo por video (vistas, me gusta por 1.000 vistas, compartidos, suscriptores) en `docs/analisis-metricas-y-monetizacion.md`, sección 6.6. Lo más fuerte: física del deporte y vehículos (F1, Roberto Carlos; el básquetbol es un caso aparte). Historia y videojuegos con historia (Tetris, Eiffel) convierten suscriptores. Lo más débil: fenómenos físicos genéricos y temas muy técnicos sin protagonista. 
- Prueba natural: 4 de los 11 videos programados del 21 al 26/11 son de deporte; comparar el 28/11 contra el resto antes de subir la frecuencia de ese estilo.

## 2026-11-21 — Registro de publicación por video y marca "SUBIDO"
- Cada carpeta de video tiene `publicacion.md` (estado por red, hora, herramienta, ID, primer comentario). Script `scripts/publicacion.py`: `indice` genera `docs/estado-publicacion.md`; `marcar --aplicar` agrega el prefijo "SUBIDO - " a las carpetas publicadas en las 3 redes.
- Se marcaron 19 carpetas (publicadas en las 3), 11 quedan programadas y `Luna cara oculta` sin subir (excluida).
- No se renombra antes de publicar: los posts programados (Zernio, Zapier) leen el video por URL raw de GitHub y se romperían.
- Las URLs raw de las carpetas renombradas cambian a `.../DatoPixel/SUBIDO%20-%20<tema>.../video.mp4`.
- Péndulo de Foucault salió a las 14:00 en las 3 redes: confirmado (YouTube público con 108 vistas, TikTok e Instagram `published`). Sigue pendiente su primer comentario en Instagram.
- Zapier sigue devolviendo "throttled" para subir los 3 videos de YouTube pendientes (básquetbol, Saturno, Luna se aleja) incluso 14 horas después; la hipótesis del cupo diario no se confirmó.
