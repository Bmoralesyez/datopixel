# Agendador de YouTube: puesta en marcha

El script `scripts/youtube_scheduler.py` sube cada video como **privado con `publishAt`**: YouTube lo publica solo a la hora indicada. El workflow de GitHub Actions lo ejecuta cada 6 horas y sube los videos que se publican en las próximas 72 h.

## 1. Proyecto en Google Cloud (una vez, gratis)
1. https://console.cloud.google.com → crear proyecto `datopixel`.
2. APIs y servicios → Biblioteca → habilitar **YouTube Data API v3**.
3. Pantalla de consentimiento OAuth → tipo **Externo**, agregar tu correo como usuario de prueba.
4. **Importante:** en "Público objetivo" pulsa **Publicar aplicación** (estado *In production*). En estado *Testing* el refresh token caduca a los 7 días y el agendador deja de funcionar. Google mostrará un aviso de "app no verificada" al autorizar; es tu propia app, acéptalo ("Avanzado → Ir a datopixel").
5. Credenciales → Crear credenciales → ID de cliente OAuth:
   - **Aplicación de escritorio** si usarás `scripts/youtube_auth.py`.
   - **Aplicación web** con URI de redirección `https://developers.google.com/oauthplayground` si usarás OAuth Playground.

## 2. Obtener el refresh token (una vez)
**Opción A, con Python en un computador:**
```
YT_CLIENT_ID=... YT_CLIENT_SECRET=... python3 scripts/youtube_auth.py
```
**Opción B, sin instalar nada (sirve desde el celular):** https://developers.google.com/oauthplayground → engranaje ⚙ → "Use your own OAuth credentials" → pega client id y secret → en el paso 1 escribe los scopes `https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.force-ssl` → Authorize → entra con la cuenta del canal → "Exchange authorization code for tokens" → copia el `refresh_token`.

## 3. GitHub Secrets
Repo → Settings → Secrets and variables → Actions → New repository secret:
`YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`. Nunca van en el código ni en el chat.

## 4. Programar videos
Edita `programacion/youtube.json` (formato abajo) y haz commit. El workflow hace el resto.

```json
{
  "zona_horaria": "America/Santiago",
  "items": [
    {"carpeta": "Luna se aleja - 15-11-2026", "publicar": "2026-11-18 14:00", "portada": "A"}
  ]
}
```
- `carpeta`: nombre exacto de la carpeta dentro de `DatoPixel/`.
- `publicar`: hora local de `zona_horaria` (`YYYY-MM-DD HH:MM`) o ISO con offset.
- `portada`: `A` o `B`.
- El script lee título, descripción, tags y primer comentario de la sección **YouTube Shorts** del `guion_y_publicacion.docx`. Mantener ese formato de etiquetas (`Título:`, `Descripción:`, `Tags de YouTube:`, `Primer comentario:`).
- El campo `estado` lo escribe el script (video_id, portada, comentario). No lo borres: evita subir el mismo video dos veces.

## 5. Probar
- Local: `python3 scripts/youtube_scheduler.py --dry-run` valida todo sin red.
- Tests: `python3 -m unittest discover -s tests`.
- En GitHub: Actions → "Agendar videos en YouTube" → Run workflow (con `dry_run` marcado la primera vez).
- Primera prueba real: programa **un** video, revisa en YouTube Studio que aparece como "Programado" con la hora correcta y la portada puesta.

## Límites y cuidados
- La API gratuita permite ~100 subidas/día en este proyecto (cuota por proyecto) y el canal tiene su propio tope diario de subidas; con 2-3 videos/día sobra.
- El primer comentario se publica en la ejecución posterior a la hora de publicación (el video debe ser público). Puede demorar hasta 6 h; si se quiere antes, se puede disparar el workflow a mano o acortar el cron.
- GitHub desactiva los workflows programados tras 60 días sin actividad en el repo; cada commit de estado cuenta como actividad.
- Si el workflow falla con `invalid_grant`: el refresh token caducó o fue revocado; repite el paso 2.
- Los videos pesan ~5 MB cada uno y viven en el repo: a 2-3 por día el repo crece ~500 MB/año (límite recomendado por GitHub: 1 GB). Cuando se acerque, mover los videos ya publicados a otro almacenamiento.
