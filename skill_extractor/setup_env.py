"""
Script d'initialisation des données de test et ressources.
"""

import logging
from pathlib import Path
import subprocess

logger = logging.getLogger(__name__)


def download_spacy_models():
    """Télécharge les modèles spaCy nécessaires."""
    logger.info("Téléchargement des modèles spaCy...")

    try:
        subprocess.run(
            ["python", "-m", "spacy", "download", "fr_core_news_sm"],
            check=True
        )
        logger.info("✓ Modèle spaCy français téléchargé")
    except Exception as e:
        logger.warning(f"Impossible de télécharger spaCy fr_core_news_sm: {e}")

    try:
        subprocess.run(
            ["python", "-m", "spacy", "download", "en_core_web_sm"],
            check=True
        )
        logger.info("✓ Modèle spaCy anglais téléchargé")
    except Exception as e:
        logger.warning(f"Impossible de télécharger spaCy en_core_web_sm: {e}")


def create_data_directories():
    """Crée les répertoires de données s'ils n'existent pas."""
    from skill_extractor.utils.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR

    for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Répertoire créé/vérifiée: {directory}")


def setup_environment():
    """Configure l'environnement complet."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("=" * 80)
    logger.info("CONFIGURATION DE L'ENVIRONNEMENT")
    logger.info("=" * 80)

    # Créer les répertoires
    create_data_directories()

    # Télécharger les modèles
    download_spacy_models()

    logger.info("=" * 80)
    logger.info("CONFIGURATION TERMINEE ✓")
    logger.info("=" * 80)


if __name__ == "__main__":
    setup_environment()
