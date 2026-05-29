from __future__ import annotations

import base64
import json
from pathlib import Path

import app.core.image_service as image_service


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_generate_image_via_api_saves_png(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        image_service,
        "_get_image_generation_config",
        lambda: {
            "api_url": "https://example.com/images",
            "api_key": "test-key",
            "auth_header": "api-key",
            "model": "gpt-image-2",
            "size": "1024x1024",
            "quality": "auto",
        },
    )
    monkeypatch.setattr(image_service, "_get_generated_image_dir", lambda: tmp_path)
    png_bytes = b"\x89PNG\r\n\x1a\nfakepng"

    def _fake_urlopen(req, timeout=0):
        assert req.full_url == "https://example.com/images"
        assert req.headers["Api-key"] == "test-key"
        body = json.loads(req.data.decode("utf-8"))
        assert body["prompt"] == "academic robot"
        return _FakeResponse({"data": [{"b64_json": base64.b64encode(png_bytes).decode("ascii")}]})

    monkeypatch.setattr(image_service.urllib.request, "urlopen", _fake_urlopen)

    result = image_service._generate_image_via_api("academic robot")

    assert result is not None
    saved_path = Path(result.removeprefix("file://"))
    assert saved_path.exists()
    assert saved_path.read_bytes() == png_bytes


def test_search_image_url_falls_back_to_generation(monkeypatch):
    monkeypatch.setattr(image_service, "_search_pixabay", lambda keyword, api_key: None)
    monkeypatch.setattr(image_service, "_search_openverse", lambda keyword: None)
    monkeypatch.setattr(image_service, "_search_wikimedia", lambda keyword: None)
    monkeypatch.setattr(image_service, "_validate_image_url", lambda url: True)
    monkeypatch.setattr(image_service, "_generate_image_via_api", lambda keyword: "file:///tmp/generated.png")

    result = image_service._search_image_url("test keyword", pixabay_key="", use_ai_optimize=False)

    assert result == "file:///tmp/generated.png"
