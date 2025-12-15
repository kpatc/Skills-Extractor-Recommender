"""
Module NLP pour le nettoyage et la préparation des textes.
Nettoie les descriptions d'offres d'emploi pour l'extraction de compétences.
"""

import re
import logging
import sys
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

logger = logging.getLogger(__name__)


class TextCleaner:
    """Nettoie et prétraite les textes des offres d'emploi."""

    # Stopwords français
    FRENCH_STOPWORDS = {
        "le", "la", "les", "de", "du", "des", "et", "ou", "un", "une",
        "à", "en", "avec", "pour", "par", "que", "ce", "est", "sont",
        "il", "elle", "nous", "vous", "eux", "leur", "son", "sa", "ses",
        "plus", "moins", "très", "tout", "faire", "peut", "peuvent",
        "pouvez", "pouvoir", "aller", "avoir", "être", "qui", "quoi",
        "où", "comment", "pourquoi", "lequel", "auquel", "duquel",
    }

    def __init__(self):
        """Initialise le nettoyeur de texte."""
        logger.info("TextCleaner initialized")

    @staticmethod
    def clean_html(text: str) -> str:
        """Supprime les balises HTML."""
        if not text:
            return ""
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text(separator=" ")

    @staticmethod
    def remove_urls(text: str) -> str:
        """Supprime les URLs."""
        return re.sub(r"http\S+|www\S+|ftp\S+", "", text, flags=re.IGNORECASE)

    @staticmethod
    def remove_emails(text: str) -> str:
        """Supprime les adresses email."""
        return re.sub(r"\S+@\S+", "", text)

    @staticmethod
    def remove_special_chars(text: str) -> str:
        """Supprime les caractères spéciaux (garde tirets, apostrophes, slashes)."""
        return re.sub(r"[^a-zA-Z0-9\s\-\'/+]", " ", text)

    @staticmethod
    def remove_extra_whitespace(text: str) -> str:
        """Supprime les espaces multiples."""
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def lowercase(text: str) -> str:
        """Convertit en minuscules."""
        return text.lower() if text else ""

    @staticmethod
    def remove_numbers(text: str) -> str:
        """Supprime les nombres purs."""
        return re.sub(r"\b\d+\b", "", text)

    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """Supprime les stopwords français."""
        return [t for t in tokens if t.lower() not in self.FRENCH_STOPWORDS and len(t) > 2]

    def tokenize(self, text: str) -> List[str]:
        """Tokenize le texte en mots."""
        return text.split() if text else []

    def clean(self, text: str, remove_stopwords: bool = False) -> str:
        """
        Pipeline de nettoyage complet.
        
        Args:
            text: Texte à nettoyer
            remove_stopwords: Supprime les stopwords
        
        Returns:
            Texte nettoyé
        """
        if not text:
            return ""
        
        # 1. HTML
        text = self.clean_html(text)

        # 2. URLs et emails
        text = self.remove_urls(text)
        text = self.remove_emails(text)

        # 3. Minuscules
        text = self.lowercase(text)

        # 4. Caractères spéciaux
        text = self.remove_special_chars(text)

        # 5. Espaces superflus
        text = self.remove_extra_whitespace(text)

        # 6. Suppression optionnelle des stopwords
        if remove_stopwords:
            tokens = self.tokenize(text)
            tokens = self.remove_stopwords(tokens)
            text = " ".join(tokens)

        return text


# Instance globale pour utilisation rapide
_cleaner = None

def get_cleaner() -> TextCleaner:
    """Obtient l'instance globale du cleaner."""
    global _cleaner
    if _cleaner is None:
        _cleaner = TextCleaner()
    return _cleaner


def clean_offers_pipeline(offers: List[Dict]) -> List[Dict]:
    """
    Nettoie les descriptions de toutes les offres d'emploi.
    
    Args:
        offers: Liste des offres avec descriptions
        
    Returns:
        Liste des offres avec descriptions nettoyées
    """
    cleaner = get_cleaner()
    cleaned_offers = []
    
    for offer in offers:
        cleaned_offer = offer.copy()
        if "description" in cleaned_offer:
            cleaned_offer["description"] = cleaner.clean(
                cleaned_offer["description"],
                remove_stopwords=False
            )
        cleaned_offers.append(cleaned_offer)
        
    logger.info(f"✅ Nettoyage appliqué à {len(cleaned_offers)} offres")
    return cleaned_offers
