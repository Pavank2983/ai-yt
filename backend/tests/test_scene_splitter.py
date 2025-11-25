import json
import os
import pytest
from types import SimpleNamespace
from unittest.mock import patch

# Import module under test
from app.services.scene_splitter import split_into_scenes


#############################
# Fixtures
#############################

@pytest.fixture
def fake_script():
    return SimpleNamespace(
        id=101,
        title="Test Script",
        description="Test description",
        content=(
            "This is a long test script used to verify semantic splitting. "
            "It contains multiple sentences. This should produce more than one scene. "
            "Scene transitions must be handled."
        ),
        category_id=1
    )


@pytest.fixture
def fake_asmr_script():
    return SimpleNamespace(
        id=102,
        title="ASMR Script",
        description="Soft spoken ASMR content",
        content=(
            "Relax... breathe in... The wind moves slowly. "
            "Soft tapping... gentle whispers... ambience flows."
        ),
        category_id=4  # ASMR category
    )


@pytest.fixture
def fake_voice_length():
    return 22  # seconds


@pytest.fixture
def env_dev_mode(monkeypatch):
    monkeypatch.setenv("AIYT_ENV", "DEV")


@pytest.fixture
def env_prod_mode(monkeypatch):
    monkeypatch.setenv("AIYT_ENV", "PROD")


@pytest.fixture
def monkeypatch_openai(monkeypatch):
    """Force fallback (no OpenAI call)."""
    monkeypatch.setenv("OPENAI_API_KEY", "")


@pytest.fixture
def tmp_scene_dir(tmp_path, monkeypatch):
    base = tmp_path / "scenes"
    base.mkdir()

    def fake_folder(script_id):
        p = base / str(script_id)
        p.mkdir()
        return str(p)

    monkeypatch.setattr("app.services.scene_splitter._ensure_scene_folder", fake_folder)
    return base


#############################
# Tests
#############################

def test_asmr_duration_split(fake_asmr_script, fake_voice_length, monkeypatch_openai, tmp_scene_dir, env_dev_mode):
    scenes, manifest_path = split_into_scenes(fake_asmr_script, fake_voice_length)

    assert len(scenes) >= 3
    for sc in scenes:
        assert "variation" in sc
        assert sc["variation"] in {"zoom_in", "camera_sweep", "ambient"}
        assert "prompt" in sc

    # Manifest file must exist
    assert os.path.exists(manifest_path)
    data = json.load(open(manifest_path))
    assert "scenes" in data
    assert len(data["scenes"]) == len(scenes)


def test_semantic_split_normal(fake_script, fake_voice_length, monkeypatch_openai, tmp_scene_dir, env_dev_mode):
    scenes, manifest_path = split_into_scenes(fake_script, fake_voice_length)

    assert len(scenes) > 0
    for sc in scenes:
        assert "title" in sc
        assert "emotion" in sc
        assert "summary" in sc

    assert os.path.exists(manifest_path)


def test_dev_max_scenes(fake_script, monkeypatch_openai, tmp_scene_dir, env_dev_mode):
    scenes, _ = split_into_scenes(fake_script, 40)  # Large duration → many scenes
    assert len(scenes) <= 5


def test_prod_max_scenes(fake_script, monkeypatch_openai, tmp_scene_dir, env_prod_mode):
    scenes, _ = split_into_scenes(fake_script, 60)
    assert len(scenes) <= 7


def test_empty_script(monkeypatch_openai, tmp_scene_dir):
    script = SimpleNamespace(
        id=999,
        title="Empty",
        description="",
        content="",
        category_id=1,
    )

    scenes, _ = split_into_scenes(script, 12)
    assert len(scenes) == 1
    assert scenes[0]["title"] == "Scene 1"