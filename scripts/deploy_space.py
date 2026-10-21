"""Publica el chat de Cava Agent como demo pública en un Hugging Face Space.

Crea el Space si no existe, configura sus secretos y sube solo los archivos que necesita la app.
Uso (lo ejecuta .github/workflows/deploy_space.yml):
    HF_TOKEN=... GROQ_API_KEY=... [NEWS_API_KEY=...] [HF_SPACE=usuario/cava-agent] python scripts/deploy_space.py
"""
import os
import shutil
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parent.parent
APP_FILES = ["app.py", "agent.py", "Gradio_UI.py", "prompts.yaml", "requirements.txt", "tools", "img"]
SPACE_FRONTMATTER = """---
title: Cava Agent
emoji: 📈
colorFrom: green
colorTo: red
sdk: gradio
sdk_version: 5.23.1
app_file: app.py
pinned: true
short_description: AI financial analyst agent built with smolagents
tags:
- smolagents
- agent
- finance
- agent-course
---

"""


def build_space_folder(target: Path) -> None:
    for name in APP_FILES:
        source = ROOT / name
        if source.is_dir():
            shutil.copytree(source, target / name, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(source, target / name)
    # El README del Space necesita la cabecera de configuración de HF; el contenido es el mismo que en GitHub
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    (target / "README.md").write_text(SPACE_FRONTMATTER + readme, encoding="utf-8")


def main() -> None:
    api = HfApi(token=os.environ["HF_TOKEN"])
    space_id = os.environ.get("HF_SPACE") or f"{api.whoami()['name']}/cava-agent"

    # Las cuentas gratuitas reciben ZeroGPU y no pueden pasar a CPU: app.py registra la función @spaces.GPU que exige
    api.create_repo(space_id, repo_type="space", space_sdk="gradio", exist_ok=True)
    api.add_space_variable(space_id, "MODEL_PROVIDER", "groq")
    for secret in ("GROQ_API_KEY", "NEWS_API_KEY"):
        if os.environ.get(secret):
            api.add_space_secret(space_id, secret, os.environ[secret])

    with tempfile.TemporaryDirectory() as tmp:
        build_space_folder(Path(tmp))
        api.upload_folder(
            repo_id=space_id,
            repo_type="space",
            folder_path=tmp,
            delete_patterns="*",  # el Space refleja exactamente lo que hay en GitHub
            commit_message=f"Deploy from GitHub {os.environ.get('GITHUB_SHA', 'local')[:7]}",
        )
    print(f"Desplegado en https://huggingface.co/spaces/{space_id}")


if __name__ == "__main__":
    main()
