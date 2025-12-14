"""
Module d'extraction des compétences techniques.
Combine : dictionnaire de compétences + extraction sémantique.
"""

import re
import logging
import sys
from typing import List, Dict, Set, Tuple
from pathlib import Path
from collections import Counter
import spacy

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))
from utils.config import TECH_SKILLS, NLP_CONFIG

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
        Extraction agressive basée sur regex pour IT skills.
        Détecte même les formes tronquées et variations.
        
        Args:
            text: Texte à analyser
        
        Returns:
            Ensemble des compétences trouvées
        """
        text_lower = text.lower()
        found_skills = set()
        
        # Regex patterns spécifiques pour les technologies populaires
        patterns = {
            # Langages de programmation
            "python": r"\bpython[\d\.]*\b|py\b|py[\d\.]*\b",
            "javascript": r"\bjavascript\b|js\b|nodejs|node\.js|es[\d]+\b",
            "typescript": r"\btypescript\b|ts\b",
            "java": r"\bjava[\d\.]*\b(?!script)",
            "golang": r"\bgolang\b|\bgo\b(?!\s+to)(?!\s+for)",
            "rust": r"\brust\b",
            "c\+\+": r"\bc\+\+\b|cpp\b",
            "c#": r"\bc#\b|csharp\b",
            "php": r"\bphp[\d\.]*\b",
            "ruby": r"\bruby[\d\.]*\b|rails\b",
            "swift": r"\bswift\b",
            "kotlin": r"\bkotlin\b",
            "scala": r"\bscala\b",
            "r": r"\br\b(?=\s|[^a-z])",
            
            # Frameworks Web & Backend
            "react": r"\breact\b|reactjs|react\.js",
            "vue": r"\bvue\.?js\b|vuejs|vue\b",
            "angular": r"\bangular[\d\.]*\b|angularjs",
            "django": r"\bdjango\b|django[\d\.]*\b",
            "flask": r"\bflask\b",
            "fastapi": r"\bfastapi\b|fast-api",
            "spring": r"\bspring\b|spring\s+boot\b|spring-boot",
            "express": r"\bexpress\b|express\.js",
            "next": r"\bnext\.js\b|nextjs\b",
            "nuxt": r"\bnuxt\.js\b|nuxtjs\b",
            "ember": r"\bember\.js\b|emberjs",
            "svelte": r"\bsvelte\b",
            
            # Databases
            "postgresql": r"\bpostgres(?:ql)?\b|postgres\b|psql\b",
            "mysql": r"\bmysql\b|mariadb\b",
            "mongodb": r"\bmongo(?:db)?\b",
            "redis": r"\bredis\b",
            "elasticsearch": r"\belasticsearch\b|elastic\b",
            "cassandra": r"\bcassandra\b",
            "dynamodb": r"\bdynamodb\b",
            "firebase": r"\bfirebase\b",
            "sql": r"\bsql\b|t-sql|pl-sql",
            
            # Cloud & DevOps
            "aws": r"\baws\b|amazon\s+web\s+services",
            "gcp": r"\bgcp\b|google\s+cloud|cloud\.google",
            "azure": r"\bazure\b|microsoft\s+azure",
            "docker": r"\bdocker\b",
            "kubernetes": r"\bkubernetes\b|k8s\b",
            "jenkins": r"\bjenkins\b",
            "gitlab": r"\bgitlab\b",
            "github": r"\bgithub\b",
            "terraform": r"\bterraform\b",
            "ansible": r"\bansible\b",
            "ci/cd": r"\bci[/-]cd\b|continuous\s+integration",
            "devops": r"\bdevops\b",
            
            # Data & ML
            "machine learning": r"\bmachine\s+learning\b|ml\b(?!\s+degrees?)",
            "deep learning": r"\bdeep\s+learning\b",
            "tensorflow": r"\btensorflow\b",
            "pytorch": r"\bpytorch\b|torch\b",
            "pandas": r"\bpandas\b",
            "numpy": r"\bnumpy\b",
            "scikit-learn": r"\bscikit-learn\b|sklearn\b",
            "spark": r"\bapache\s+spark\b|spark\b",
            "hadoop": r"\bhadoop\b",
            "ai": r"\b(?:artificial\s+)?intelligence\b|\bai\b",
            
            # APIs & Architectures
            "rest api": r"\brest\s+(?:api|apis)\b|restful",
            "graphql": r"\bgraphql\b",
            "grpc": r"\bgrpc\b",
            "soap": r"\bsoap\b",
            "microservices": r"\bmicroservices\b|micro-services",
            "serverless": r"\bserverless\b",
            "lambda": r"\baws\s+lambda\b|lambda\s+function",
            
            # Frontend & Mobile
            "html": r"\bhtml[\d]?\b",
            "css": r"\bcss[\d]?\b|scss\b|sass\b|less\b",
            "bootstrap": r"\bbootstrap\b",
            "material": r"\bmaterial\s+design\b|material-ui",
            "react native": r"\breact\s+native\b",
            "flutter": r"\bflutter\b",
            "android": r"\bandroid\b",
            "ios": r"\bios\b",
            
            # Other tech
            "git": r"\bgit\b",
            "linux": r"\blinux\b",
            "windows": r"\bwindows\b",
            "unix": r"\bunix\b",
            "shell": r"\bshell\b|bash\b|zsh\b",
            "json": r"\bjson\b",
            "xml": r"\bxml\b",
            "yaml": r"\byaml\b",
            "http": r"\bhttps?\b",
            "websocket": r"\bwebsocket\b|websockets",
            "agile": r"\bagile\b",
            "scrum": r"\bscrum\b",
            "kanban": r"\bkanban\b",
            "testing": r"\b(?:unit\s+)?testing\b|test\s+driven",
            "junit": r"\bjunit\b",
            "pytest": r"\bpytest\b",
            "selenium": r"\bselenium\b",
            "docker compose": r"\bdocker-compose\b|docker\s+compose",
            "git": r"\bgit\b|github\b",
            "npm": r"\bnpm\b",
            "yarn": r"\byarn\b",
            "pip": r"\bpip\b",
            "virtualenv": r"\bvirtualenv\b|venv\b",
            "conda": r"\bconda\b",
            "vim": r"\bvim\b",
            "vs code": r"\bvs\s+code\b|vscode\b",
            "intellij": r"\bintellij\b|idea\b",
        }
        
        for skill, pattern in patterns.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                found_skills.add(skill)
        
        # Parcourir aussi le dictionnaire exact
        for category, skills in self.skill_dict.items():
            for skill in skills:
                pattern = r"\b" + re.escape(skill) + r"\b"
                if re.search(pattern, text_lower, re.IGNORECASE):
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
            # Vérifier si la méthode sémantique est activée
            if NLP_CONFIG.get("use_semantic_extraction", True):
                skills = self.extract_skills_semantic(text)
            else:
                logger.debug("Méthode sémantique désactivée, utilisant regex uniquement")
                skills = self.extract_skills_regex(text)
        else:  # combined
            skills_regex = self.extract_skills_regex(text)
            skills_spacy = self.extract_skills_spacy(text)
            
            # Inclure la méthode sémantique seulement si activée
            if NLP_CONFIG.get("use_semantic_extraction", True):
                skills_semantic = self.extract_skills_semantic(text)
                skills = skills_regex.union(skills_spacy).union(skills_semantic)
            else:
                skills = skills_regex.union(skills_spacy)

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
