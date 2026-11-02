from pathlib import Path

from dream.config import REPO_ROOT, media_dir


def test_media_dir_uses_synced_folder_when_set(monkeypatch, tmp_path):
    monkeypatch.setenv("DREAMBERRY_MEDIA_DIR", str(tmp_path))
    assert media_dir("03 TESTS", "night-ab", "data/dream/x", when="2026-09") == tmp_path / "03 TESTS" / "2026-09 night-ab"


def test_media_dir_falls_back_to_local(monkeypatch):
    monkeypatch.setattr("dream.config._load_dotenv", lambda: None)
    monkeypatch.delenv("DREAMBERRY_MEDIA_DIR", raising=False)
    assert media_dir("03 TESTS", "night-ab", "data/dream/x") == REPO_ROOT / Path("data/dream/x")
