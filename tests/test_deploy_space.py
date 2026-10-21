import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "deploy_space", Path(__file__).resolve().parent.parent / "scripts" / "deploy_space.py"
)
deploy_space = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy_space)


def test_space_folder_contains_only_app_files(tmp_path):
    deploy_space.build_space_folder(tmp_path)
    files = {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file()}

    assert {"app.py", "agent.py", "Gradio_UI.py", "prompts.yaml", "requirements.txt", "README.md"} <= files
    assert "tools/market_data.py" in files
    # Ni secretos, ni el bot de Telegram, ni tests/legacy acaban en la demo pública
    assert not any(f.startswith((".env", "tests/", "legacy/", ".github/")) for f in files)
    assert "telegram_client.py" not in files
    assert not any("__pycache__" in f for f in files)


def test_space_readme_has_hf_config_header(tmp_path):
    deploy_space.build_space_folder(tmp_path)
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")

    assert readme.startswith("---\ntitle: Cava Agent")
    assert "sdk: gradio" in readme
    assert "app_file: app.py" in readme
