"""링크 미리보기 — 카카오톡 · 문자로 주소를 보내면 제목 · 설명 · 그림이 뜬다 (2026-09-29).

카카오는 og:title · og:description · og:image 를 읽는다. 그림 주소는 절대 주소여야 하고,
가로 1200 · 세로 630 이 잘리지 않는 크기다.
"""
import re
import struct
from pathlib import Path

from fastapi.testclient import TestClient

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.main import app  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://quadriga-fitness-age.onrender.com"


def _head() -> str:
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    return html.split("</head>")[0]


def _meta(head: str, key: str) -> str:
    m = re.search(rf'<meta (?:property|name)="{re.escape(key)}" content="([^"]+)" />', head)
    assert m, key
    return m.group(1)


def test_미리보기_태그가_모두_있다():
    head = _head()
    assert _meta(head, "og:title").startswith("Fitage")
    assert "국민체력100" in _meta(head, "og:description")
    assert _meta(head, "og:description") == _meta(head, "description")
    assert _meta(head, "og:url") == BASE + "/"
    assert _meta(head, "og:image") == BASE + "/img/og-image.png"      # 카카오는 절대 주소만 읽는다
    assert (_meta(head, "og:image:width"), _meta(head, "og:image:height")) == ("1200", "630")
    assert _meta(head, "twitter:card") == "summary_large_image"


def test_미리보기_그림은_1200x630_PNG_이고_서버가_내준다():
    png = (ROOT / "frontend" / "img" / "og-image.png").read_bytes()
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    가로, 세로 = struct.unpack(">II", png[16:24])                    # IHDR
    assert (가로, 세로) == (1200, 630)
    assert len(png) < 300_000                                         # 카카오 미리보기가 느려지지 않게
    r = TestClient(app).get("/img/og-image.png")
    assert r.status_code == 200 and r.content == png
