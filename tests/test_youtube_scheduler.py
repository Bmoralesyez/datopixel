import json
import sys
import tempfile
import unittest
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import youtube_scheduler as ys  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
NOW = datetime(2026, 11, 17, 21, 0, tzinfo=timezone.utc)


class FakeResp:
    def __init__(self, body=b"", status=200, headers=None):
        self._b, self.status, self.headers = body, status, headers or {}

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeYT:
    """Opener falso que registra las peticiones y simula la API."""

    def __init__(self, public=False, fail_thumb=False):
        self.calls, self.public, self.fail_thumb = [], public, fail_thumb

    def __call__(self, req, timeout=None):
        url, method = req.full_url, req.get_method()
        self.calls.append((method, url, req.data))
        if url.startswith(ys.TOKEN_URL):
            return FakeResp(b'{"access_token":"AT"}')
        if "uploadType=resumable" in url:
            return FakeResp(b"", headers={"Location": "https://upload.example/session1"})
        if url == "https://upload.example/session1":
            return FakeResp(b'{"id":"VID123"}')
        if "thumbnails/set" in url:
            if self.fail_thumb:
                raise _http_error(url, 400)
            return FakeResp(b"{}")
        if "/videos?part=status" in url:
            st = "public" if self.public else "private"
            return FakeResp(json.dumps({"items": [{"status": {"privacyStatus": st}}]}).encode())
        if "commentThreads" in url:
            return FakeResp(b'{"id":"COMM1"}')
        raise AssertionError(f"URL inesperada {url}")


def _http_error(url, code):
    import io
    return urllib.error.HTTPError(url, code, "err", {}, io.BytesIO(b'{"error":"x"}'))


class ParserTests(unittest.TestCase):
    def test_parse_real_docx(self):
        meta = ys.parse_youtube_metadata(REPO / "DatoPixel" / "Luna se aleja - 15-11-2026" / "guion_y_publicacion.docx")
        self.assertEqual(meta["title"], "¿Por qué la Luna se aleja de la Tierra? #Shorts")
        self.assertIn("\n\n", meta["description"])
        self.assertNotIn("\\n", meta["description"])
        self.assertIn("luna se aleja", meta["tags"])
        self.assertTrue(meta["first_comment"].startswith("¿Qué astro o fenómeno"))

    def test_all_repo_videos_have_valid_youtube_metadata(self):
        folders = [p for p in (REPO / "DatoPixel").iterdir() if p.is_dir()]
        self.assertGreater(len(folders), 0)
        for f in folders:
            item = {"carpeta": f.name, "publicar": "2030-01-01 10:00", "portada": "A"}
            ys.validate_item(item, "America/Santiago", NOW)  # no debe lanzar

    def test_missing_section(self):
        with self.assertRaises(ys.SchedulerError):
            self._bad_docx()

    def _bad_docx(self):
        import zipfile
        d = tempfile.mkdtemp()
        p = Path(d) / "x.docx"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("word/document.xml", "<w:document><w:p><w:r><w:t>nada</w:t></w:r></w:p></w:document>")
        return ys.parse_youtube_metadata(p)


class TimeTests(unittest.TestCase):
    def test_local_time_to_utc_santiago_summer(self):
        dt = ys.parse_publish_time("2026-11-18 14:00", "America/Santiago")
        self.assertEqual(ys.to_rfc3339(dt), "2026-11-18T17:00:00.000Z")  # UTC-3 en verano

    def test_iso_with_offset(self):
        dt = ys.parse_publish_time("2026-11-18T14:00:00-03:00", "America/Santiago")
        self.assertEqual(ys.to_rfc3339(dt), "2026-11-18T17:00:00.000Z")

    def test_past_time_rejected(self):
        item = {"carpeta": "Luna se aleja - 15-11-2026", "publicar": "2026-11-17 10:00"}
        with self.assertRaises(ys.SchedulerError):
            ys.validate_item(item, "America/Santiago", NOW)

    def test_body_is_private_with_publishat(self):
        body = ys.build_video_body({"title": "t", "description": "d", "tags": ["a"]}, NOW + timedelta(days=1))
        self.assertEqual(body["status"]["privacyStatus"], "private")
        self.assertTrue(body["status"]["publishAt"].endswith("Z"))
        self.assertFalse(body["status"]["selfDeclaredMadeForKids"])


class FlowTests(unittest.TestCase):
    def queue(self, when="2026-11-18 14:00"):
        return {"zona_horaria": "America/Santiago",
                "items": [{"carpeta": "Luna se aleja - 15-11-2026", "publicar": when, "portada": "A"}]}

    def run_flow(self, q, fake, now=NOW, dry=False, horizon=72):
        client = ys.YouTubeClient("id", "secret", "refresh", opener=fake)
        saves = []
        log = ys.process_queue(q, client, now, dry_run=dry, horizon_hours=horizon, save=lambda: saves.append(1))
        return log, saves

    def test_upload_schedule_thumbnail(self):
        q, fake = self.queue(), FakeYT()
        log, saves = self.run_flow(q, fake)
        st = q["items"][0]["estado"]
        self.assertEqual(st["video_id"], "VID123")
        self.assertTrue(st["portada"])
        self.assertTrue(saves)
        meta_call = next(c for c in fake.calls if "uploadType=resumable" in c[1])
        body = json.loads(meta_call[2])
        self.assertEqual(body["status"]["publishAt"], "2026-11-18T17:00:00.000Z")
        put = next(c for c in fake.calls if c[1] == "https://upload.example/session1")
        self.assertGreater(len(put[2]), 1000)  # bytes reales del video
        self.assertFalse(any("commentThreads" in c[1] for c in fake.calls))  # aun privado

    def test_idempotent(self):
        q = self.queue()
        self.run_flow(q, FakeYT())
        fake2 = FakeYT()
        self.run_flow(q, fake2)
        self.assertFalse(any("uploadType=resumable" in c[1] for c in fake2.calls))

    def test_comment_after_publication(self):
        q = self.queue()
        self.run_flow(q, FakeYT())
        later = datetime(2026, 11, 18, 17, 30, tzinfo=timezone.utc)
        fake = FakeYT(public=True)
        self.run_flow(q, fake, now=later)
        self.assertEqual(q["items"][0]["estado"]["comentario"], "COMM1")
        sent = next(c for c in fake.calls if "commentThreads" in c[1])
        self.assertIn("VID123", sent[2].decode())

    def test_comment_waits_if_not_public_yet(self):
        q = self.queue()
        self.run_flow(q, FakeYT())
        later = datetime(2026, 11, 18, 17, 30, tzinfo=timezone.utc)
        fake = FakeYT(public=False)
        self.run_flow(q, fake, now=later)
        self.assertNotIn("comentario", q["items"][0]["estado"])

    def test_outside_horizon_not_uploaded(self):
        q, fake = self.queue("2026-12-30 14:00"), FakeYT()
        log, _ = self.run_flow(q, fake)
        self.assertEqual(fake.calls, [])
        self.assertIn("fuera del horizonte", log[0])

    def test_dry_run_makes_no_calls(self):
        q, fake = self.queue(), FakeYT()
        log, _ = self.run_flow(q, fake, dry=True)
        self.assertEqual(fake.calls, [])
        self.assertIn("OK", log[0])

    def test_thumbnail_failure_keeps_video_and_retries(self):
        q = self.queue()
        self.run_flow(q, FakeYT(fail_thumb=True))
        st = q["items"][0]["estado"]
        self.assertEqual(st["video_id"], "VID123")
        self.assertFalse(st.get("portada"))
        self.run_flow(q, FakeYT())
        self.assertTrue(q["items"][0]["estado"]["portada"])

    def test_invalid_item_records_error_and_continues(self):
        q = self.queue()
        q["items"].insert(0, {"carpeta": "No existe", "publicar": "2026-11-18 10:00"})
        log, _ = self.run_flow(q, FakeYT())
        self.assertIn("ultimo_error", q["items"][0]["estado"])
        self.assertEqual(q["items"][1]["estado"]["video_id"], "VID123")

    def test_invalid_grant_message(self):
        def opener(req, timeout=None):
            import io
            raise urllib.error.HTTPError(req.full_url, 400, "bad", {}, io.BytesIO(b'{"error":"invalid_grant"}'))
        c = ys.YouTubeClient("i", "s", "r", opener=opener)
        with self.assertRaises(ys.SchedulerError) as cm:
            c.token()
        self.assertIn("In production", str(cm.exception))

    def test_retry_on_503_then_ok(self):
        calls = {"n": 0}

        def opener(req, timeout=None):
            calls["n"] += 1
            if calls["n"] == 1:
                raise _http_error(req.full_url, 503)
            return FakeResp(b'{"access_token":"AT"}')
        c = ys.YouTubeClient("i", "s", "r", opener=opener)
        with mock.patch.object(ys.time, "sleep"):
            self.assertEqual(c.token(), "AT")
        self.assertEqual(calls["n"], 2)


if __name__ == "__main__":
    unittest.main()
