"""
Module d'extraction des compétences techniques des offres d'emploi.
Utilise une détection basée sur regex et un dictionnaire de compétences.
"""

import re
import logging
import sys
from typing import List, Dict, Set, Tuple
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

logger = logging.getLogger(__name__)


class SkillExtractor:
    """Extrait les compétences techniques des descriptions d'offres d'emploi."""

    # Dictionnaire complet des compétences IT par catégorie
    TECH_SKILLS = {
        "langages_programmation": [
            "python", "java", "javascript", "typescript", "c++", "c#", "php",
            "ruby", "go", "rust", "kotlin", "swift", "scala", "perl", "groovy",
            "clojure", "elixir", "r", "matlab", "vb.net", "objective-c"
        ],
        "frameworks_web": [
            "django", "flask", "fastapi", "spring", "spring boot", "express",
            "nest.js", "next.js", "react", "angular", "vue.js", "laravel",
            "symfony", "ruby on rails", "gin", "echo", "actix", "axum"
        ],
        "bases_donnees": [
            "postgresql", "mysql", "mongodb", "redis", "cassandra", "elasticsearch",
            "dynamodb", "firestore", "oracle", "sql server", "neo4j", "sqlite",
            "mariadb", "couchdb", "influxdb", "timescaledb"
        ],
        "cloud_devops": [
            "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
            "terraform", "ansible", "jenkins", "gitlab ci", "github actions",
            "circleci", "travis ci", "docker compose", "helm", "prometheus",
            "grafana", "cloudformation"
        ],
        "outils_dev": [
            "git", "github", "gitlab", "bitbucket", "jira", "confluence",
            "slack", "asana", "trello", "vscode", "intellij", "sublime",
            "vim", "emacs", "postman", "swagger", "openapi"
        ],
        "ai_ml": [
            "machine learning", "deep learning", "tensorflow", "pytorch",
            "scikit-learn", "keras", "nlp", "computer vision", "pandas",
            "numpy", "scipy", "sklearn", "xgboost", "llm", "transformers",
            "huggingface", "chatgpt", "openai"
        ],
        "concepts_techniques": [
            "microservices", "rest api", "graphql", "websocket", "grpc",
            "soap", "rpc", "ci/cd", "agile", "scrum", "kanban",
            "test unitaire", "tdd", "bdd", "design pattern", "solid",
            "clean code", "devops", "sre", "iac"
        ],
        "autres_technologies": [
            "html", "css", "sass", "bootstrap", "tailwind", "webpack",
            "babel", "npm", "yarn", "pip", "maven", "gradle", "apache",
            "nginx", "linux", "unix", "windows", "macos", "bash", "shell"
        ]
    }

    def __init__(self):
        """Initialise l'extracteur de compétences."""
        # Construire un dictionnaire plat avec variations
        self.skills_dict = self._build_skills_dict()
        # Créer des patterns regex pour chaque skill
        self.skill_patterns = self._create_skill_patterns()
        logger.info(f"SkillExtractor initialized with {len(self.skills_dict)} skills")

    def _build_skills_dict(self) -> Dict[str, str]:
        """
        Construit un dictionnaire plat: skill_name -> categorie.
        
        Returns:
            Dict avec les variations de skills
        """
        skills_dict = {}
        
        for category, skills in self.TECH_SKILLS.items():
            for skill in skills:
                # Ajouter la compétence et ses variations
                base_skill = skill.lower()
                skills_dict[base_skill] = category
                
                # Variantes avec tirets
                if " " in base_skill:
                    hyphenated = base_skill.replace(" ", "-")
                    skills_dict[hyphenated] = category
                
                # Acronymes courants
                acronyms = self._get_common_acronyms(base_skill)
                for acronym in acronyms:
                    skills_dict[acronym] = category
        
        return skills_dict

    def _get_common_acronyms(self, skill: str) -> List[str]:
        """Retourne les acronymes courants pour un skill."""
        acronyms = []
        
        # Acronymes spécifiques connus
        special_acronyms = {
            "machine learning": ["ml"],
            "deep learning": ["dl"],
            "natural language processing": ["nlp"],
            "computer vision": ["cv"],
            "kubernetes": ["k8s"],
            "rest api": ["rest"],
            "graphql": ["graphql"],
            "continuous integration": ["ci"],
            "continuous deployment": ["cd"],
            "test driven development": ["tdd"],
            "behavior driven development": ["bdd"],
        }
        
        if skill in special_acronyms:
            return special_acronyms[skill]
        
        # Générer acronyme simple si multi-word
        if " " in skill:
            acronym = "".join([word[0] for word in skill.split()])
            if len(acronym) > 1:
                acronyms.append(acronym.lower())
        
        return acronyms

    def _create_skill_patterns(self) -> Dict[str, re.Pattern]:
        """Crée des patterns regex pour chaque skill."""
        patterns = {}
        
        for skill in self.skills_dict.keys():
            # Créer un pattern avec word boundaries
            pattern_str = r"\b" + re.escape(skill) + r"\b"
            patterns[skill] = re.compile(pattern_str, re.IGNORECASE)
        
        return patterns

    def extract_skills(self, text: str) -> Dict[str, Set[str]]:
        """
        Extrait les compétences d'un texte.
        
        Args:
            text: Texte à analyser (déjà nettoyé de préférence)
        
        Returns:
            Dict avec categorisation des skills trouvés
        """
        text_lower = text.lower()
        found_skills = {}
        
        # Chercher chaque skill dans le texte
        for skill, pattern in self.skill_patterns.items():
            if pattern.search(text_lower):
                category = self.skills_dict[skill]
                if category not in found_skills:
                    found_skills[category] = set()
                # Ajouter le skill "canonique" (pas la variation)
                canonical = self._get_canonical_skill(skill)
                found_skills[category].add(canonical)
        
        return found_skills

    def _get_canonical_skill(self, skill: str) -> str:
        """
        Retourne le nom canonique d'un skill.
        Ex: "k8s" -> "kubernetes", "ml" -> "machine learning"
        """
        # Reverser mapping pour trouver le skill original
        reverse_map = {
            "k8s": "kubernetes",
            "ml": "machine learning",
            "dl": "deep learning",
            "nlp": "natural language processing",
            "cv": "computer vision",
            "ci": "continuous integration",
            "cd": "continuous deployment",
            "tdd": "test driven development",
            "bdd": "behavior driven development",
            "rest": "rest api",
            "vb.net": "vb.net",
        }
        
        if skill in reverse_map:
            return reverse_map[skill]
        
        # Pour les tirets, retourner la version avec espaces
        if "-" in skill:
            return skill.replace("-", " ")
        
        return skill

    def extract_skills_flat(self, text: str) -> List[str]:
        """
        Extrait les compétences en liste plate (tous les skills trouvés).
        
        Args:
            text: Texte à analyser
        
        Returns:
            Liste des skills trouvés
        """
        skills_dict = self.extract_skills(text)
        all_skills = []
        
        for category_skills in skills_dict.values():
            all_skills.extend(category_skills)
        
        return sorted(list(set(all_skills)))

    def extract_skills_categorized(self, text: str) -> Dict[str, List[str]]:
        """
        Extrait les compétences avec catégorisation.
        
        Args:
            text: Texte à analyser
        
        Returns:
            Dict with category -> list of skills
        """
        skills_dict = self.extract_skills(text)
        
        # Convertir les sets en listes triées
        return {
            category: sorted(list(skills))
            for category, skills in skills_dict.items()
        }


# Instance globale
_skill_extractor = None

def get_skill_extractor() -> SkillExtractor:
    """Obtient l'instance globale de l'extracteur de compétences."""
    global _skill_extractor
    if _skill_extractor is None:
        _skill_extractor = SkillExtractor()
    return _skill_extractor


def extract_skills_from_job(job_dict: Dict) -> Dict:
    """
    Extrait les skills d'une offre d'emploi (titre + description).
    
    Args:
        job_dict: Dict avec au minimum 'title' et 'description'
    
    Returns:
        Dict augmenté avec les skills trouvés
    """
    extractor = get_skill_extractor()
    
    # Combiner titre et description
    combined_text = f"{job_dict.get('title', '')} {job_dict.get('description', '')}"
    
    # Extraire les skills
    skills_categorized = extractor.extract_skills_categorized(combined_text)
    skills_flat = extractor.extract_skills_flat(combined_text)
    
    # Ajouter au job dict
    job_with_skills = job_dict.copy()
    job_with_skills['skills_categorized'] = skills_categorized
    job_with_skills['skills'] = skills_flat
    job_with_skills['num_skills'] = len(skills_flat)
    
    return job_with_skills


def extract_skills_from_jobs(jobs: List[Dict]) -> List[Dict]:
    """
    Extrait les skills de plusieurs offres d'emploi.
    
    Args:
        jobs: Liste de dicts avec offres d'emploi
    
    Returns:
        Liste augmentée avec les skills
    """
    logger.info(f"Extracting skills from {len(jobs)} jobs...")
    jobs_with_skills = []
    
    for job in jobs:
        job_with_skills = extract_skills_from_job(job)
        jobs_with_skills.append(job_with_skills)
    
    logger.info(f"Skills extraction complete. Processed {len(jobs_with_skills)} jobs.")
    return jobs_with_skills


def get_top_skills(jobs: List[Dict], top_n: int = 20) -> List[Tuple[str, int]]:
    """
    Retourne les top N skills les plus demandés.
    
    Args:
        jobs: Liste de dicts avec offres (doit contenir 'skills' key)
        top_n: Nombre de top skills à retourner
    
    Returns:
        Liste de tuples (skill, count) triée par count décroissant
    """
    skill_counts = Counter()
    
    for job in jobs:
        if 'skills' in job:
            for skill in job['skills']:
                skill_counts[skill] += 1
    
    return skill_counts.most_common(top_n)
