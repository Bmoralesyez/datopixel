#!/usr/bin/env python3
"""Agenda los videos de DatoPixel en YouTube Shorts (YouTube Data API v3).

Solo usa la libreria estandar de Python (sin pip). Flujo por cada item de la cola
(`programacion/youtube.json`):

1. Lee titulo, descripcion, tags y primer comentario de la seccion "YouTube Shorts"
   del `guion_y_publicacion.docx` de la carpeta del video.
2. Sube `video.mp4` como privado con `status.publishAt` (YouTube lo publica solo
   a esa hora; no depende de que el cron de GitHub corra puntual).
3. Sube la portada (`portada_A.png` o `portada_B.png`).
4. Cuando el video ya es publico, publica el primer comentario.

El estado (video_id, comentario) se guarda en el mismo JSON de la cola, asi que
repetir la ejecucion no duplica nada.

Variables de entorno (GitHub Secrets): YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parent.parent
VIDEOS_DIR = REPO_ROOT / "DatoPixel"
QUEUE_PATH = REPO_ROOT / "programacion" / "youtube.json"

TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://www.googleapis.com/youtube/v3"
UPLOAD_API = "https://www.googleapis.com/upload/youtube/v3"

CATEGORY_EDUCATION = "27"
MAX_TITLE = 100
MAX_DESCRIPTION_BYTES = 5000
MAX_TAGS_CHARS = 500
MAX_THUMB_BYTES = 2 * 1024 * 1024
MIN_LEAD = timedelta(minutes=15)  # YouTube exige publishAt en el futuro


class SchedulerError(Exception):
    """Error de validacion o de la API que impide procesar un item."""


# ----------------------------------------------------------------------------
# Lectura del .docx
# ----------------------------------------------------------------------------
def _docx_paragraphs(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    out = []
    for p in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S):
        text = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", p, re.S))
        text = (text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", '"').replace("&apos;", "'"))
        out.append(text)
    return out


def parse_youtube_metadata(docx_path: Path) -> dict:
    """Devuelve titulo, descripcion, tags y primer comentario de la seccion YouTube Shorts."""
    paras = _docx_paragraphs(docx_path)
    try:
        start = next(i for i, t in enumerate(paras) if t.strip() == "YouTube Shorts")
    except StopIteration:
        raise SchedulerError(f"{docx_path}: no existe la seccion 'YouTube Shorts'")
    end = next((i for i in range(start + 1, len(paras)) if paras[i].strip() == "Instagram Reels"),
               len(paras))
    fields = {}
    labels = {
        "Título:": "title",
        "Descripción:": "description",
        "Tags de YouTube:": "tags",
        "Primer comentario:": "first_comment",
    }
    for text in paras[start + 1:end]:
        for label, key in labels.items():
            if text.startswith(label):
                # el docx guarda los saltos de linea como el texto literal "\n"
                fields[key] = text[len(label):].strip().replace("\\n", "\n")
    missing = [k for k in ("title", "description", "tags") if not fields.get(k)]
    if missing:
        raise SchedulerError(f"{docx_path}: faltan campos de YouTube: {', '.join(missing)}")
    fields["tags"] = [t.strip() for t in fields["tags"].split(",") if t.strip()]
    fields.setdefault("first_comment", "")
    return fields


# ----------------------------------------------------------------------------
# Cola y validacion
# ----------------------------------------------------------------------------
def load_queue(path: Path = QUEUE_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_queue(queue: dict, path: Path = QUEUE_PATH) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def parse_publish_time(value: str, tz_name: str) -> datetime:
    """Acepta 'YYYY-MM-DD HH:MM' (hora local de la zona) o ISO 8601 con offset."""
    value = value.strip()
    dt = datetime.fromisoformat(value.replace(" ", "T") if " " in value else value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(tz_name))
    return dt.astimezone(timezone.utc)


def to_rfc3339(dt_utc: datetime) -> str:
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def build_video_body(meta: dict, publish_at: datetime, language: str = "es") -> dict:
    return {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta["tags"],
            "categoryId": CATEGORY_EDUCATION,
            "defaultLanguage": language,
            "defaultAudioLanguage": language,
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": to_rfc3339(publish_at),
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
        },
    }


def validate_item(item: dict, tz_name: str, now: datetime, check_future: bool = True) -> dict:
    """Valida un item sin tocar la red. Devuelve los datos listos para subir."""
    folder = VIDEOS_DIR / item["carpeta"]
    video = folder / "video.mp4"
    thumb = folder / f"portada_{item.get('portada', 'A')}.png"
    docx = folder / "guion_y_publicacion.docx"
    for f in (video, thumb, docx):
        if not f.is_file():
            raise SchedulerError(f"{item['carpeta']}: no existe {f.name}")
    meta = parse_youtube_metadata(docx)
    if len(meta["title"]) > MAX_TITLE:
        raise SchedulerError(f"{item['carpeta']}: titulo de {len(meta['title'])} caracteres (max {MAX_TITLE})")
    if len(meta["description"].encode("utf-8")) > MAX_DESCRIPTION_BYTES:
        raise SchedulerError(f"{item['carpeta']}: descripcion supera {MAX_DESCRIPTION_BYTES} bytes")
    if len(",".join(meta["tags"])) > MAX_TAGS_CHARS:
        raise SchedulerError(f"{item['carpeta']}: tags superan {MAX_TAGS_CHARS} caracteres")
    if thumb.stat().st_size > MAX_THUMB_BYTES:
        raise SchedulerError(f"{item['carpeta']}: la portada pesa mas de 2 MB")
    publish_at = parse_publish_time(item["publicar"], tz_name)
    if check_future and publish_at < now + MIN_LEAD:
        raise SchedulerError(f"{item['carpeta']}: la hora {item['publicar']} ya paso o es muy cercana")
    return {"video": video, "thumb": thumb, "meta": meta, "publish_at": publish_at}


# ----------------------------------------------------------------------------
# Cliente HTTP / YouTube
# ----------------------------------------------------------------------------
class YouTubeClient:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str, opener=None):
        self.client_id, self.client_secret, self.refresh_token = client_id, client_secret, refresh_token
        self._open = opener or urllib.request.urlopen
        self._access_token: str | None = None

    # -- bajo nivel ---------------------------------------------------------
    def _request(self, req: urllib.request.Request, retries: int = 4):
        delay = 2.0
        for attempt in range(retries + 1):
            try:
                with self._open(req, timeout=300) as resp:
                    body = resp.read()
                    return resp.status, dict(resp.headers), body
            except urllib.error.HTTPError as e:
                body = e.read()
                if e.code in (500, 502, 503, 504) and attempt < retries:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise SchedulerError(f"HTTP {e.code} en {req.full_url.split('?')[0]}: {body.decode('utf-8', 'replace')[:600]}")
            except urllib.error.URLError as e:
                if attempt < retries:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise SchedulerError(f"Error de red en {req.full_url.split('?')[0]}: {e}")
        raise SchedulerError("reintentos agotados")

    def _json(self, method: str, url: str, payload: dict | None = None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Authorization": f"Bearer {self.token()}"}
        if data is not None:
            headers["Content-Type"] = "application/json; charset=UTF-8"
        _, _, body = self._request(urllib.request.Request(url, data=data, headers=headers, method=method))
        return json.loads(body) if body else {}

    # -- OAuth --------------------------------------------------------------
    def token(self) -> str:
        if self._access_token:
            return self._access_token
        data = urllib.parse.urlencode({
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }).encode()
        req = urllib.request.Request(TOKEN_URL, data=data, method="POST",
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        try:
            _, _, body = self._request(req)
        except SchedulerError as e:
            if "invalid_grant" in str(e):
                raise SchedulerError(
                    "El refresh token fue rechazado (invalid_grant). Si la pantalla de consentimiento "
                    "esta en 'Testing' el token caduca a los 7 dias: pasala a 'In production' y "
                    "genera uno nuevo con scripts/youtube_auth.py. Detalle: " + str(e))
            raise
        self._access_token = json.loads(body)["access_token"]
        return self._access_token

    # -- API ----------------------------------------------------------------
    def upload_video(self, video: Path, body: dict) -> str:
        """Subida resumable. Devuelve el video_id."""
        size = video.stat().st_size
        init = urllib.request.Request(
            f"{UPLOAD_API}/videos?uploadType=resumable&part=snippet,status&notifySubscribers=false",
            data=json.dumps(body).encode("utf-8"), method="POST",
            headers={
                "Authorization": f"Bearer {self.token()}",
                "Content-Type": "application/json; charset=UTF-8",
                "X-Upload-Content-Length": str(size),
                "X-Upload-Content-Type": "video/mp4",
            })
        _, headers, _ = self._request(init)
        location = {k.lower(): v for k, v in headers.items()}.get("location")
        if not location:
            raise SchedulerError("YouTube no devolvio la URL de subida resumable")
        put = urllib.request.Request(location, data=video.read_bytes(), method="PUT",
                                     headers={"Content-Type": "video/mp4", "Content-Length": str(size)})
        _, _, resp = self._request(put)
        video_id = json.loads(resp).get("id")
        if not video_id:
            raise SchedulerError(f"Respuesta de subida sin id: {resp[:300]!r}")
        return video_id

    def set_thumbnail(self, video_id: str, thumb: Path) -> None:
        req = urllib.request.Request(
            f"{UPLOAD_API}/thumbnails/set?videoId={urllib.parse.quote(video_id)}&uploadType=media",
            data=thumb.read_bytes(), method="POST",
            headers={"Authorization": f"Bearer {self.token()}", "Content-Type": "image/png"})
        self._request(req)

    def video_status(self, video_id: str) -> dict | None:
        data = self._json("GET", f"{API}/videos?part=status&id={urllib.parse.quote(video_id)}")
        items = data.get("items", [])
        return items[0]["status"] if items else None

    def post_comment(self, video_id: str, text: str) -> str:
        data = self._json("POST", f"{API}/commentThreads?part=snippet", {
            "snippet": {"videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": text}}}})
        return data.get("id", "")


# ----------------------------------------------------------------------------
# Orquestacion
# ----------------------------------------------------------------------------
def process_queue(queue: dict, client: YouTubeClient | None, now: datetime, *, dry_run: bool,
                  horizon_hours: float, only: str | None = None, save=None) -> list[str]:
    """Procesa la cola. Devuelve lineas de log. `save()` se llama tras cada cambio de estado."""
    tz_name = queue.get("zona_horaria", "America/Santiago")
    log: list[str] = []
    errors = 0
    for item in queue["items"]:
        name = item["carpeta"]
        if only and only not in name:
            continue
        state = item.setdefault("estado", {})
        try:
            if "video_id" not in state:
                publish_at = parse_publish_time(item["publicar"], tz_name)
                if publish_at > now + timedelta(hours=horizon_hours):
                    log.append(f"- {name}: fuera del horizonte ({item['publicar']}), se subira mas adelante")
                    continue
                data = validate_item(item, tz_name, now)
                if dry_run:
                    log.append(f"* {name}: OK, se subiria '{data['meta']['title']}' para {item['publicar']} ({tz_name})")
                    continue
                body = build_video_body(data["meta"], data["publish_at"])
                video_id = client.upload_video(data["video"], body)
                state.update(video_id=video_id, subido=now.isoformat(timespec="seconds"),
                             publica_utc=to_rfc3339(data["publish_at"]))
                if save:
                    save()  # guardar ya: evita subir dos veces si falla algo despues
                log.append(f"+ {name}: subido https://youtube.com/shorts/{video_id}, publica {item['publicar']}")
                try:
                    client.set_thumbnail(video_id, data["thumb"])
                    state["portada"] = True
                except SchedulerError as e:
                    log.append(f"! {name}: portada no aplicada ({e}); se reintentara")
                if save:
                    save()
            # portada pendiente de reintento
            if state.get("video_id") and not state.get("portada") and not dry_run:
                folder = VIDEOS_DIR / name
                try:
                    client.set_thumbnail(state["video_id"], folder / f"portada_{item.get('portada', 'A')}.png")
                    state["portada"] = True
                    log.append(f"+ {name}: portada aplicada")
                except SchedulerError as e:
                    log.append(f"! {name}: portada sigue fallando ({e})")
                if save:
                    save()
            # primer comentario: solo cuando el video ya es publico
            if state.get("video_id") and not state.get("comentario") and not dry_run:
                publish_utc = datetime.fromisoformat(state["publica_utc"].replace("Z", "+00:00"))
                if now >= publish_utc:
                    docx = VIDEOS_DIR / name / "guion_y_publicacion.docx"
                    text = parse_youtube_metadata(docx).get("first_comment", "")
                    st = client.video_status(state["video_id"])
                    if not text:
                        state["comentario"] = "sin_texto"
                    elif st and st.get("privacyStatus") == "public":
                        state["comentario"] = client.post_comment(state["video_id"], text) or "ok"
                        log.append(f"+ {name}: primer comentario publicado")
                    else:
                        log.append(f"- {name}: aun no es publico, el comentario queda pendiente")
                    if save:
                        save()
        except (SchedulerError, KeyError, ValueError) as e:
            errors += 1
            state["ultimo_error"] = str(e)[:500]
            log.append(f"! {name}: {e}")
            if save:
                save()
    if errors:
        log.append(f"== {errors} item(s) con error")
    return log


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="valida y muestra lo que haria, sin red")
    ap.add_argument("--horizon-hours", type=float, default=72,
                    help="solo sube items cuya hora de publicacion cae dentro de este margen (def. 72)")
    ap.add_argument("--only", help="procesa solo carpetas cuyo nombre contenga este texto")
    ap.add_argument("--queue", type=Path, default=QUEUE_PATH)
    args = ap.parse_args(argv)

    queue = load_queue(args.queue)
    now = datetime.now(timezone.utc)
    client = None
    if not args.dry_run:
        try:
            client = YouTubeClient(os.environ["YT_CLIENT_ID"], os.environ["YT_CLIENT_SECRET"],
                                   os.environ["YT_REFRESH_TOKEN"])
        except KeyError as e:
            print(f"Falta la variable de entorno {e}. Configura los GitHub Secrets (ver docs/youtube-setup.md).",
                  file=sys.stderr)
            return 2
    log = process_queue(queue, client, now, dry_run=args.dry_run, horizon_hours=args.horizon_hours,
                        only=args.only, save=None if args.dry_run else (lambda: save_queue(queue, args.queue)))
    print("\n".join(log) if log else "Nada que hacer.")
    return 1 if any(line.startswith(("!", "==")) for line in log) else 0


if __name__ == "__main__":
    sys.exit(main())
