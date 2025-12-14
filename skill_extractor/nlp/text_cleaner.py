"""
Module NLP pour le nettoyage et la préparation des textes.
"""

import re
import logging
import sys
from typing import List, Dict, Tuple
from pathlib import Path
import spacy
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))
from utils.config import NLP_CONFIG

logger = logging.getLogger(__name__)


class TextCleaner:
    """Nettoie et prétraite les textes des offres d'emploi."""

    def __init__(self):
        # Charger le modèle spaCy français
        try:
            self.nlp = spacy.load("fr_core_news_sm")
        except OSError:
            logger.warning(
                "Modèle spaCy 'fr_core_news_sm' non trouvé. "
                "Installez avec: python -m spacy download fr_core_news_sm"
            )
            self.nlp = None

        # Stopwords français (liste basique)
        self.stopwords = self._get_french_stopwords()

    def _get_french_stopwords(self) -> set:
        """Retourne un ensemble de stopwords français."""
        return {
            "le", "la", "les", "de", "du", "des", "et", "ou", "un", "une",
            "à", "en", "avec", "pour", "par", "que", "ce", "est", "sont",
            "il", "elle", "nous", "vous", "eux", "leur", "son", "sa", "ses",
            "plus", "moins", "très", "tout", "nous", "vous", "faire",
            "peut", "peuvent", "pouvez", "pouvoir", "aller", "avoir", "être",
        }

    def clean_html(self, text: str) -> str:
        """Supprime les balises HTML."""
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text(separator=" ")

    def remove_urls(self, text: str) -> str:
        """Supprime les URLs."""
        return re.sub(r"http\S+|www\S+", "", text)

    def remove_emails(self, text: str) -> str:
        """Supprime les adresses email."""
        return re.sub(r"\S+@\S+", "", text)

    def lowercase(self, text: str) -> str:
        """Convertit en minuscules."""
        return text.lower()

    def remove_special_chars(self, text: str) -> str:
        """Supprime les caractères spéciaux (mais garde les tirets et apostrophes)."""
        # Garde les lettres, chiffres, espaces, tirets, apostrophes
        return re.sub(r"[^a-zA-Z0-9\s\-\']", " ", text)

    def remove_extra_whitespace(self, text: str) -> str:
        """Supprime les espaces multiples et lignes vides."""
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """Supprime les stopwords."""
        return [t for t in tokens if t.lower() not in self.stopwords]

    def lemmatize(self, text: str) -> str:
        """Lemmatise le texte avec spaCy."""
        if self.nlp is None:
            logger.warning("spaCy non disponible, retour du texte original")
            return text

        doc = self.nlp(text)
        lemmas = [token.lemma_ for token in doc]
        return " ".join(lemmas)

    def clean(self, text: str, lemmatize: bool = True, remove_stopwords: bool = True) -> str:
        """
        Pipeline de nettoyage complet.
        
        Args:
            text: Texte à nettoyer
            lemmatize: Applique la lemmatisation
            remove_stopwords: Supprime les stopwords
        
        Returns:
            Texte nettoyé
        """
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

        # 6. Lemmatisation (optionnel)
        if lemmatize and self.nlp:
            text = self.lemmatize(text)

        # 7. Stopwords (optionnel mais garder les termes techniques)
        if remove_stopwords:
            tokens = text.split()
            tokens = self.remove_stopwords(tokens)
            text = " ".join(tokens)

        return text

    def clean_job_offers(self, offers: List[Dict]) -> List[Dict]:
        """
        Nettoie une liste d'offres d'emploi.
        
        Args:
            offers: Liste de dictionnaires d'offres
        
        Returns:
            Liste d'offres nettoyées
        """
        cleaned_offers = []

        for offer in offers:
            cleaned_offer = offer.copy()

            # Nettoyer la description
            if "description" in offer:
                cleaned_offer["description_cleaned"] = self.clean(
                    offer["description"]
                )
                # Garder aussi le titre nettoyé
                cleaned_offer["title_cleaned"] = self.clean(offer["title"])

            cleaned_offers.append(cleaned_offer)

        return cleaned_offers


def tokenize_text(text: str) -> List[str]:
    """Tokenize un texte simple (par espaces)."""
    return text.split()


def extract_ngrams(text: str, n: int = 2) -> List[Tuple[str, ...]]:
    """Extrait les n-grams d'un texte."""
    tokens = tokenize_text(text)
    return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]


# Initialisation globale du cleaner
cleaner = TextCleaner()


def clean_offers_pipeline(offers: List[Dict]) -> List[Dict]:
    """Pipeline de nettoyage complet pour les offres."""
    logger.info(f"Nettoyage de {len(offers)} offres...")
    cleaned = cleaner.clean_job_offers(offers)
    logger.info("Nettoyage terminé")
    return cleaned
