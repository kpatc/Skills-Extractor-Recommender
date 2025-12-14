"""
Module d'extraction des compétences techniques.
Combine : dictionnaire de compétences + extraction sémantique.
"""

import re
import logging
from typing import List, Dict, Set, Tuple
from collections import Counter
import spacy

from ..utils.config import TECH_SKILLS, NLP_CONFIG

logger = logging.getLogger(__name__)


class SkillExtractor:
    """Extrait les compétences des offres d'emploi."""

    def __init__(self):
        # Charger le modèle spaCy
        try:
            self.nlp = spacy.load("fr_core_news_sm")
        except OSError:
            logger.warning("Modèle spaCy non disponible")
            self.nlp = None

        # Construire un dictionnaire complet des compétences
        self.skill_dict = self._build_skill_dictionary()

        # Créer un PhraseMatcher pour la détection rapide
        self._create_phrase_matcher()

    def _build_skill_dictionary(self) -> Dict[str, List[str]]:
        """
        Construit un dictionnaire complet des compétences avec variations.
        
        Returns:
            Dictionnaire catégorisé des compétences
        """
        full_skills = {}

        for category, skills in TECH_SKILLS.items():
            full_skills[category] = []

            for skill in skills:
                # Ajouter la compétence et ses variations
                variations = self._get_skill_variations(skill)
                full_skills[category].extend(variations)

        return full_skills

    def _get_skill_variations(self, skill: str) -> List[str]:
        """
        Retourne les variations d'une compétence.
        
        Args:
            skill: Compétence (ex: "machine learning")
        
        Returns:
            Liste des variations (ex: ["machine learning", "ml", "machine-learning"])
        """
        variations = [skill.lower()]

        # Variantes avec tirets
        if " " in skill:
            variations.append(skill.replace(" ", "-"))

        # Acronymes possibles
        if len(skill.split()) > 1:
            acronym = "".join([word[0] for word in skill.split()])
            variations.append(acronym.lower())

        return variations

    def _create_phrase_matcher(self):
        """Crée un PhraseMatcher spaCy pour la détection rapide."""
        if self.nlp is None:
            return

        from spacy.matcher import PhraseMatcher

        self.phrase_matcher = PhraseMatcher(self.nlp.vocab)

        # Ajouter toutes les compétences au matcher
        for category, skills in self.skill_dict.items():
            for skill in skills:
                pattern = self.nlp.make_doc(skill)
                self.phrase_matcher.add(skill, [pattern])

    def extract_skills_regex(self, text: str) -> Set[str]:
        """
        Extraction basée sur regex et dictionnaire exact.
        
        Args:
            text: Texte à analyser
        
        Returns:
            Ensemble des compétences trouvées
        """
        text_lower = text.lower()
        found_skills = set()

        # Parcourir toutes les compétences
        for category, skills in self.skill_dict.items():
            for skill in skills:
                # Pattern regex: mots limites pour éviter faux positifs
                pattern = r"\b" + re.escape(skill) + r"\b"
                if re.search(pattern, text_lower):
                    # Retourner la forme canonique (sans tirets/variations)
                    canonical = skill.replace("-", " ").lower()
                    found_skills.add(canonical)

        return found_skills

    def extract_skills_spacy(self, text: str) -> Set[str]:
        """
        Extraction avec PhraseMatcher spaCy.
        
        Args:
            text: Texte à analyser
        
        Returns:
            Ensemble des compétences trouvées
        """
        if self.nlp is None or not hasattr(self, "phrase_matcher"):
            return set()

        doc = self.nlp(text.lower())
        found_skills = set()

        for match_id, start, end in self.phrase_matcher(doc):
            matched_text = doc[start:end].text
            found_skills.add(matched_text)

        return found_skills

    def extract_skills_semantic(self, text: str) -> Set[str]:
        """
        Extraction sémantique basée sur similarité.
        Utilise des embeddings de phrases (nécessite sentence-transformers).
        
        Args:
            text: Texte à analyser
        
        Returns:
            Ensemble des compétences trouvées (approche simplifiée)
        """
        # Note: Cette implémentation simplifiée
        # Une version complète utiliserait sentence-transformers
        # et calculerait la similarité cosinus

        found_skills = set()

        try:
            from sentence_transformers import SentenceTransformer, util
            import torch

            # Charger le modèle d'embeddings multilangues
            model = SentenceTransformer(NLP_CONFIG.get("model_name"))

            # Créer une liste plate de toutes les compétences
            all_skills = []
            for skills in self.skill_dict.values():
                all_skills.extend(skills)

            # Encoder le texte et les compétences
            text_embedding = model.encode(text, convert_to_tensor=True)
            skills_embeddings = model.encode(all_skills, convert_to_tensor=True)

            # Calculer les similarités
            similarities = util.pytorch_cos_sim(text_embedding, skills_embeddings)[0]

            # Garder les compétences avec haute similarité (threshold > 0.5)
            threshold = 0.5
            for idx, similarity in enumerate(similarities):
                if similarity > threshold:
                    found_skills.add(all_skills[idx])

        except ImportError:
            logger.warning(
                "sentence-transformers non installé. "
                "Installez avec: pip install sentence-transformers"
            )

        return found_skills

    def extract_skills(self, text: str, method: str = "combined") -> Dict[str, any]:
        """
        Extrait les compétences avec la méthode spécifiée.
        
        Args:
            text: Texte à analyser
            method: "regex", "spacy", "semantic", ou "combined"
        
        Returns:
            Dictionnaire avec compétences et métadonnées
        """
        if method == "regex":
            skills = self.extract_skills_regex(text)
        elif method == "spacy":
            skills = self.extract_skills_spacy(text)
        elif method == "semantic":
            skills = self.extract_skills_semantic(text)
        else:  # combined
            skills_regex = self.extract_skills_regex(text)
            skills_spacy = self.extract_skills_spacy(text)
            skills_semantic = self.extract_skills_semantic(text)
            skills = skills_regex.union(skills_spacy).union(skills_semantic)

        # Catégoriser les compétences trouvées
        categorized = self._categorize_skills(skills)

        return {
            "skills": list(skills),
            "count": len(skills),
            "categorized": categorized,
            "method": method,
        }

    def _categorize_skills(self, skills: Set[str]) -> Dict[str, List[str]]:
        """
        Catégorise les compétences trouvées.
        
        Args:
            skills: Ensemble de compétences
        
        Returns:
            Dictionnaire catégorisé
        """
        categorized = {cat: [] for cat in self.skill_dict.keys()}

        for category, skill_list in self.skill_dict.items():
            for found_skill in skills:
                # Vérifier si la compétence trouvée correspond
                for skill_variant in skill_list:
                    if found_skill.lower() in skill_variant.lower() or \
                       skill_variant.lower() in found_skill.lower():
                        categorized[category].append(found_skill)
                        break

        return categorized

    def extract_skills_from_offers(
        self,
        offers: List[Dict],
        method: str = "combined"
    ) -> List[Dict]:
        """
        Extrait les compétences de plusieurs offres.
        
        Args:
            offers: Liste d'offres avec descriptions
            method: Méthode d'extraction
        
        Returns:
            Liste d'offres enrichies avec les compétences
        """
        enriched_offers = []

        for offer in offers:
            enriched = offer.copy()

            # Extraire des compétences
            if "description_cleaned" in offer:
                skills_data = self.extract_skills(offer["description_cleaned"], method)
            else:
                skills_data = self.extract_skills(offer.get("description", ""), method)

            enriched["extracted_skills"] = skills_data["skills"]
            enriched["skills_count"] = skills_data["count"]
            enriched["skills_categorized"] = skills_data["categorized"]

            enriched_offers.append(enriched)

        return enriched_offers

    def get_top_skills(
        self,
        offers: List[Dict],
        top_n: int = 20
    ) -> List[Tuple[str, int]]:
        """
        Retourne les compétences les plus demandées.
        
        Args:
            offers: Liste d'offres enrichies
            top_n: Nombre de top compétences à retourner
        
        Returns:
            Liste des compétences avec leur fréquence
        """
        all_skills = []

        for offer in offers:
            if "extracted_skills" in offer:
                all_skills.extend(offer["extracted_skills"])

        skill_counts = Counter(all_skills)
        return skill_counts.most_common(top_n)


# Instance globale
extractor = SkillExtractor()


def extract_skills_pipeline(offers: List[Dict]) -> List[Dict]:
    """Pipeline d'extraction complet."""
    logger.info(f"Extraction des compétences pour {len(offers)} offres...")
    enriched = extractor.extract_skills_from_offers(offers, method="combined")
    logger.info("Extraction terminée")
    return enriched
