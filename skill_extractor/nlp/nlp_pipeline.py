"""
Pipeline NLP complet pour traiter les offres d'emploi.
Combine nettoyage de texte + extraction de compétences.
"""

import logging
import sys
from typing import List, Dict, Tuple
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from .text_cleaner import get_cleaner, TextCleaner
from .skills_extractor_v2 import (
    get_skill_extractor, extract_skills_from_jobs, get_top_skills
)

logger = logging.getLogger(__name__)


class NLPPipeline:
    """Pipeline NLP complet pour traitement des offres d'emploi."""

    def __init__(self):
        """Initialise le pipeline NLP."""
        self.cleaner = get_cleaner()
        self.skill_extractor = get_skill_extractor()
        logger.info("NLPPipeline initialized")

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
                if 'description' in job and job['description']:
                    cleaned_desc = self.cleaner.clean(
                        job['description'],
                        remove_stopwords=False  # Garder les stopwords pour extraction
                    )
                    processed_job['description_cleaned'] = cleaned_desc
                
                if 'title' in job and job['title']:
                    cleaned_title = self.cleaner.clean(job['title'], remove_stopwords=False)
                    processed_job['title_cleaned'] = cleaned_title
                
                # 2. Extraction des compétences (utiliser le texte original ou nettoyé)
                combined_text = f"{job.get('title', '')} {job.get('description', '')}"
                skills_categorized = self.skill_extractor.extract_skills_categorized(combined_text)
                skills_flat = self.skill_extractor.extract_skills_flat(combined_text)
                
                processed_job['skills_categorized'] = skills_categorized
                processed_job['skills'] = skills_flat
                processed_job['num_skills'] = len(skills_flat)
                
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
        skills_by_category = {}
        
        for job in processed_jobs:
            if 'skills' in job:
                total_unique_skills.update(job['skills'])
            
            if 'skills_categorized' in job:
                for category, skills in job['skills_categorized'].items():
                    if category not in skills_by_category:
                        skills_by_category[category] = set()
                    skills_by_category[category].update(skills)
        
        # Top 20 skills
        top_skills = get_top_skills(processed_jobs, top_n=20)
        
        return {
            'total_jobs': total_jobs,
            'jobs_with_skills': jobs_with_skills,
            'total_unique_skills': len(total_unique_skills),
            'skills_by_category': {k: len(v) for k, v in skills_by_category.items()},
            'top_20_skills': top_skills,
        }

    def save_processed_jobs(self, processed_jobs: List[Dict], output_path: str):
        """
        Sauvegarde les offres traitées dans un CSV.
        
        Args:
            processed_jobs: Offres traitées
            output_path: Chemin du fichier CSV de sortie
        """
        logger.info(f"Saving processed jobs to {output_path}...")
        
        # Convertir les listes et dicts en strings pour le CSV
        df_data = []
        
        for job in processed_jobs:
            row = {
                'job_id': job.get('job_id', ''),
                'title': job.get('title', ''),
                'company': job.get('company', ''),
                'location': job.get('location', ''),
                'source': job.get('source', ''),
                'description': job.get('description', '')[:500],  # Limiter pour readabilité
                'title_cleaned': job.get('title_cleaned', ''),
                'skills': ' | '.join(job.get('skills', [])),
                'num_skills': job.get('num_skills', 0),
                'scrape_date': job.get('scrape_date', ''),
            }
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        logger.info(f"Saved {len(df_data)} jobs to {output_path}")


def process_csv_file(input_csv: str, output_csv: str) -> Dict:
    """
    Traite un fichier CSV d'offres brutes.
    
    Args:
        input_csv: Chemin du CSV raw (de la scraping)
        output_csv: Chemin du CSV processed (avec skills)
    
    Returns:
        Stats de traitement
    """
    logger.info(f"Loading jobs from {input_csv}...")
    
    # Charger les offres
    df = pd.read_csv(input_csv)
    jobs = df.to_dict('records')
    
    logger.info(f"Loaded {len(jobs)} jobs")
    
    # Traiter
    pipeline = NLPPipeline()
    processed_jobs = pipeline.process_job_offers(jobs)
    
    # Sauvegarder
    pipeline.save_processed_jobs(processed_jobs, output_csv)
    
    # Stats
    stats = pipeline.get_statistics(processed_jobs)
    
    logger.info("=" * 60)
    logger.info("NLP PROCESSING STATISTICS")
    logger.info("=" * 60)
    logger.info(f"Total jobs processed: {stats['total_jobs']}")
    logger.info(f"Jobs with skills: {stats['jobs_with_skills']}")
    logger.info(f"Total unique skills: {stats['total_unique_skills']}")
    logger.info("\nSkills by category:")
    for cat, count in stats['skills_by_category'].items():
        logger.info(f"  {cat}: {count} unique skills")
    logger.info("\nTop 20 Most Demanded Skills:")
    for skill, count in stats['top_20_skills']:
        logger.info(f"  {skill}: {count} offers")
    logger.info("=" * 60)
    
    return stats


# Instance globale
_nlp_pipeline = None

def get_nlp_pipeline() -> NLPPipeline:
    """Obtient l'instance globale du pipeline NLP."""
    global _nlp_pipeline
    if _nlp_pipeline is None:
        _nlp_pipeline = NLPPipeline()
    return _nlp_pipeline
