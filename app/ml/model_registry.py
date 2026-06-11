"""
Model registry — ensures trained .pkl files are present before FastAPI serves requests.
On Fly.io, the filesystem is ephemeral so models must be downloaded on each deploy.
Downloads from the latest GitHub Release if saved_models/ is empty.
"""
import os
import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

MODEL_DIR    = Path(__file__).parent / "saved_models"
DISEASES     = ["malaria", "flu", "cholera", "dengue", "pneumonia", "meningitis"]
MODEL_TYPES  = ["xgb", "rf"]
GITHUB_REPO  = os.getenv("GITHUB_REPO", "manziosee/ClimateHealth-AI")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

REQUIRED_MODELS = [f"{d}_{t}.pkl" for d in DISEASES for t in MODEL_TYPES]


def models_exist() -> bool:
    return all((MODEL_DIR / f).exists() for f in REQUIRED_MODELS)


async def download_models() -> bool:
    """
    Download all .pkl files from the latest GitHub Release.
    Returns True if successful, False if download failed.
    """
    MODEL_DIR.mkdir(exist_ok=True)

    if models_exist():
        logger.info("All ML models already present — skipping download.")
        return True

    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"Could not fetch GitHub Release: {e}")
            return False

        release = resp.json()
        assets  = {a["name"]: a["browser_download_url"] for a in release.get("assets", [])}

        downloaded = 0
        for filename in REQUIRED_MODELS:
            if filename not in assets:
                logger.warning(f"Model {filename} not found in latest release.")
                continue

            dest = MODEL_DIR / filename
            try:
                dl = await client.get(assets[filename], follow_redirects=True)
                dl.raise_for_status()
                dest.write_bytes(dl.content)
                logger.info(f"Downloaded {filename} ({len(dl.content) // 1024} KB)")
                downloaded += 1
            except Exception as e:
                logger.error(f"Failed to download {filename}: {e}")

    if downloaded == len(REQUIRED_MODELS):
        logger.info("All ML models downloaded successfully.")
        return True

    logger.warning(f"Only {downloaded}/{len(REQUIRED_MODELS)} models downloaded — will use heuristic fallback.")
    return False
