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
| Básquetbol efecto | 25/11 18:00 | gUXANrbuKxY | 6b00d34eea46b2536f2f1da6 | 6b00d34f77e9ba45a67c2534 |
| Anillos de Saturno | 26/11 14:00 | pZVqK5Y-8P4 | 6b00d35130d622eb4762c08b | 6b00d353ea46b2536f2f1dc3 |
| Luna se aleja | 26/11 18:00 | M8AT94MsZSY | 6b00d354ea46b2536f2f1dd2 | 6b00d35630d622eb4762c09c |

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

## 2026-11-21 — Primer comentario de Instagram del péndulo de Foucault
- Se obtuvo el `media_id` (18189638011369937) con Windsor `get_data` (conector `instagram`, campos `media_id`, `media_caption`, `media_permalink`, `timestamp`) y se publicó con `create_comment` el texto "¿Qué otra prueba te gustaría ver? 👇" (comentario 18140526271632509).
- `publicacion.md` del video actualizado. El flujo queda documentado en la sección 7.4 de `docs/analisis-metricas-y-monetizacion.md`.

| Salto Fosbury | 27/11 14:00 | QR_6aUSfzK0 | 6b0257a74a5e4a06b9f0693a | 6b0257a8108af21c273c0866 |
| Eclipse 1919 Einstein | 27/11 18:00 | VzzHBFC_1OY | 6b02652b4a306be548224c91 | 6b02652ca53c54e9edd243b7 |

## 2026-11-22 — Subida de los 3 últimos videos a YouTube
Básquetbol (gUXANrbuKxY), Anillos de Saturno (pZVqK5Y-8P4) y Luna se aleja (M8AT94MsZSY) quedaron programados con Zapier, subiendo de a uno (funcionó sin bloqueo). Con esto, los 13 videos programados (11 + Fosbury + Eclipse 1919) están en las 3 redes. Primera franja libre: 28/11 14:00.
| Frenada F1 | 28/11 14:00 | XftOs6f8jTY (subido 22/11 tras throttled) | 6b03750e38ddb111c21fc3b9 | 6b03750f38ddb111c21fc3c2 |
| Apolo 13 filtro CO2 | 28/11 18:00 | pzX4ZTOqL48 | 6b037c025bf2792c87aa7e23 | 6b037c048227da371868f4a8 |
| Eratóstenes midió la Tierra | 29/11 14:00 | QvRDexnuPA0 | 6b04f818f187cbf25e9bb882 | 6b04f819f187cbf25e9bb88f |
| Salto de esquí V | 29/11 18:00 | Q4HeBwzHZ2E | 6b04fd777a183da92f578ef7 | 6b04fd7879983984b59de4f8 |

## 2026-11-24 — Luna cara oculta descartada y primeros comentarios de Instagram
- El usuario decidió que "Luna cara oculta - 15-11-2026" no se publica (mismo tema que la Luna del 10/11). La carpeta queda sin subir.
- Primeros comentarios publicados con Windsor `create_comment` en los Reels ya públicos: Space Invaders (17901807567394672), Golf (17961501885017511), GPS (18081149900481110), Balón sin giro (17980195734176691), Bumerán (17969080967982426). Los de los demás Reels se publican cuando cada uno salga.
| Atari cartuchos enterrados | 30/11 14:00 | gjaagec1tFk | 6b05b4afe73f9b60c4a20d3f | 6b05b4b25601072366bf05ff |
| Pale Blue Dot Voyager | 30/11 18:00 | PENDIENTE (Zapier 429, reintentar) | 6b0646730f4bfc71d6c2ec78 | 6b0646740f4bfc71d6c2ec82 |
| Semmelweis lavado de manos | 01/12 14:00 | PENDIENTE (Zapier 429, reintentar) | 6b064b0918dbb4068e6dbdc9 | 6b064b0a26ee4661c7fe6f6e |
- 24/11 23:30–23:50: Zapier/YouTube respondió 429 (demasiadas solicitudes) en 4 intentos espaciados; quedan SIN subir a YouTube: Pale Blue Dot (30/11 18:00) y Semmelweis (01/12 14:00). TikTok e Instagram de ambos ya están programados. Reintentar YouTube (uno a la vez) con los títulos/descripciones de cada publicacion.md.
- Comentarios IG publicados 24/11: Moneda (18143640814646177), Estrella fugaz (18105296801643338).
| Microondas parte 2 uvas plasma | 01/12 18:00 | PENDIENTE (Zapier throttled, reintentar) | 6b06567176a195fc16397b6c | 6b065672d24e6d7fe034da1b |
- 25/11 00:30–01:20: Zapier/YouTube sigue limitado (429 / throttled). Pendientes en YouTube: Pale Blue Dot (30/11 18:00), Semmelweis (01/12 14:00), Microondas parte 2 (01/12 18:00). Posible causa: límite diario de subidas de YouTube (se renueva ~05:00 hora de Santiago). Reintentar uno a uno.
- 25/11: primeros comentarios de Instagram añadidos (Windsor `create_comment`) a Reels que no tenían: Patinador (18146260468729082), Gatos (18134922952874172), Microondas (18128206046029333), Luna/«no cambia de tamaño» (17878665045695043). Anteriores del 24/11: Moneda (18143640814646177), Estrella fugaz (18105296801643338). Reels de 9–14/11 siguen sin comentario (publicados por Metricool antes del sistema; no se han comentado).
