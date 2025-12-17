"""
Pipeline NLP complet pour traiter les offres d'emploi.
Combine nettoyage de texte + extraction de compétences.
"""

import logging
import sys
import json
from typing import List, Dict, Tuple
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from .text_cleaner import TextCleaner
from .advanced_skills_extractor import SkillsExtractor

logger = logging.getLogger(__name__)


class NLPPipeline:
    """Pipeline NLP complet pour traitement des offres d'emploi."""

    def __init__(self):
        """Initialise le pipeline NLP."""
        self.cleaner = TextCleaner()
        self.skill_extractor = SkillsExtractor()
        logger.info("NLPPipeline initialized with TextCleaner and SkillsExtractor")

    def process_job_offers(self, jobs: List[Dict]) -> List[Dict]:
        """
        Traite une liste d'offres d'emploi complet:
        1. Nettoyage des textes
        2. Extraction des compétences
        
        Args:
            jobs: Liste de dicts avec offres
        
        Returns:
            Liste augmentée avec textes nettoyés et skills
        """
        logger.info(f"Processing {len(jobs)} job offers...")
        
        processed_jobs = []
        
        for idx, job in enumerate(jobs):
            try:
                # Copier le job original
                processed_job = job.copy()
                
                # 1. Nettoyage du texte
                description = job.get('description', '')
                title = job.get('title', '')
                
                if description:
                    cleaned_desc = self.cleaner.clean(description, remove_stopwords=False)
                    processed_job['description_cleaned'] = cleaned_desc
                else:
                    cleaned_desc = ""
                    processed_job['description_cleaned'] = ""
                
                if title:
                    cleaned_title = self.cleaner.clean(title, remove_stopwords=False)
                    processed_job['title_cleaned'] = cleaned_title
                else:
                    cleaned_title = ""
                    processed_job['title_cleaned'] = ""
                
                # 2. Extraction des compétences (utiliser texte original + title)
                combined_text = f"{title} {description}"
                
                # Extraire skills avec la méthode pondérée qui exploite les sections
                extracted_skills, weighted_skills = self.skill_extractor.extract_skills_weighted(
                    description=combined_text,
                    title=title
                )
                
                # Garder les skills dans un format structuré
                processed_job['skills'] = extracted_skills
                processed_job['skills_weighted'] = [
                    {"skill": skill, "weight": float(weight)} 
                    for skill, weight in weighted_skills
                ][:20]  # Garder top 20
                processed_job['num_skills'] = len(extracted_skills)
                processed_job['processed_at'] = datetime.now().isoformat()
                
                processed_jobs.append(processed_job)
                
                if (idx + 1) % 10 == 0:
                    logger.info(f"  Processed {idx + 1}/{len(jobs)} jobs...")
                
            except Exception as e:
                logger.error(f"Error processing job {idx}: {e}")
                processed_jobs.append(job)
        
        logger.info(f"Processing complete. {len(processed_jobs)} jobs processed.")
        return processed_jobs

    def get_statistics(self, processed_jobs: List[Dict]) -> Dict:
        """
        Retourne des statistiques sur les offres traitées.
        
        Args:
            processed_jobs: Offres avec skills extraits
        
        Returns:
            Dict avec statistiques
        """
        total_jobs = len(processed_jobs)
        jobs_with_skills = sum(1 for job in processed_jobs if job.get('skills'))
        total_unique_skills = set()
        skills_frequency = {}
        
        for job in processed_jobs:
            if 'skills' in job and job['skills']:
                for skill in job['skills']:
                    total_unique_skills.add(skill)
                    skills_frequency[skill] = skills_frequency.get(skill, 0) + 1
        
        # Top 20 skills
        top_skills = sorted(
            skills_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]
        
        return {
            'total_jobs': total_jobs,
            'jobs_with_skills': jobs_with_skills,
            'coverage': round((jobs_with_skills / total_jobs * 100) if total_jobs > 0 else 0, 2),
            'total_unique_skills': len(total_unique_skills),
            'top_20_skills': top_skills,
        }

    def save_processed_jobs(self, processed_jobs: List[Dict], output_path: str):
        """
        Sauvegarde les offres traitées dans un fichier JSON.
        
        Args:
            processed_jobs: Offres traitées
            output_path: Chemin du fichier JSON de sortie
        """
        logger.info(f"Saving {len(processed_jobs)} processed jobs to {output_path}...")
        
        # Créer le répertoire s'il n'existe pas
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder en JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_jobs, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Saved {len(processed_jobs)} processed jobs to {output_path}")


def process_json_file(input_json: str, output_json: str) -> Dict:
    """
    Traite un fichier JSON d'offres brutes (de la scraping).
    
    Args:
        input_json: Chemin du JSON raw (de la scraping)
        output_json: Chemin du JSON processed (avec skills)
    
    Returns:
        Stats de traitement
    """
    logger.info(f"Loading jobs from {input_json}...")
    
    # Charger les offres
    with open(input_json, 'r', encoding='utf-8') as f:
        jobs = json.load(f)
    
    logger.info(f"Loaded {len(jobs)} jobs")
    
    # Traiter
    pipeline = NLPPipeline()
    processed_jobs = pipeline.process_job_offers(jobs)
    
    # Sauvegarder
    pipeline.save_processed_jobs(processed_jobs, output_json)
    
    # Stats
    stats = pipeline.get_statistics(processed_jobs)
    
    logger.info("=" * 80)
    logger.info("🎯 NLP PROCESSING STATISTICS")
    logger.info("=" * 80)
    logger.info(f"Total jobs processed: {stats['total_jobs']}")
    logger.info(f"Jobs with skills extracted: {stats['jobs_with_skills']}")
    logger.info(f"Coverage: {stats['coverage']}%")
    logger.info(f"Total unique skills found: {stats['total_unique_skills']}")
    logger.info("\nTop 20 Most Demanded Skills:")
    for rank, (skill, count) in enumerate(stats['top_20_skills'], 1):
        logger.info(f"  {rank:2d}. {skill:<30s} {count:3d} offers")
    logger.info("=" * 80)
    
    return stats


# Instance globale
_nlp_pipeline = None

def get_nlp_pipeline() -> NLPPipeline:
    """Obtient l'instance globale du pipeline NLP."""
    global _nlp_pipeline
    if _nlp_pipeline is None:
        _nlp_pipeline = NLPPipeline()
    return _nlp_pipeline
