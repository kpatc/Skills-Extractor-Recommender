#!/usr/bin/env python3
"""
Script principal pour traiter les offres d'emploi avec le pipeline NLP.
Charge le CSV brut, nettoie les textes et extrait les compétences.
"""

import sys
import csv
import json
import logging
from pathlib import Path
from datetime import datetime

# Setup paths
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from nlp.nlp_pipeline import NLPPipeline


def load_raw_offers(csv_file):
    """Charge les offres brutes du CSV."""
    offers = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                offers.append(row)
        logger.info(f"✓ Loaded {len(offers)} offers from {csv_file}")
        return offers
    except Exception as e:
        logger.error(f"❌ Error loading CSV: {e}")
        return []


def process_offers(offers, nlp_pipeline):
    """Traite les offres avec le pipeline NLP."""
    processed = []
    
    for i, offer in enumerate(offers, 1):
        try:
            # Extraire les infos de base
            job_id = offer.get('job_id', f'job_{i}')
            title = offer.get('title', '')
            company = offer.get('company', '')
            location = offer.get('location', '')
            description = offer.get('description', '')
            source = offer.get('source', 'unknown')
            scrape_date = offer.get('scrape_date', datetime.now().isoformat())
            
            # Nettoyer et extraire compétences
            result = nlp_pipeline.process_job({
                'title': title,
                'description': description,
                'company': company
            })
            
            # Construire l'enregistrement processé
            processed_job = {
                'job_id': job_id,
                'title': title,
                'company': company,
                'location': location,
                'original_description': description,
                'cleaned_description': result['cleaned_text'],
                'skills': result['skills'],
                'skills_by_category': result['skills_by_category'],
                'skill_count': len(result['skills']),
                'source': source,
                'scrape_date': scrape_date,
                'processed_date': datetime.now().isoformat()
            }
            processed.append(processed_job)
            
            if i % 10 == 0:
                logger.info(f"  Processed {i}/{len(offers)} offers...")
                
        except Exception as e:
            logger.warning(f"⚠️  Error processing job {i}: {e}")
            continue
    
    logger.info(f"✓ Successfully processed {len(processed)}/{len(offers)} offers")
    return processed


def save_processed_offers(offers, output_csv, output_json):
    """Sauvegarde les offres traitées."""
    try:
        # Sauvegarder en CSV
        if offers:
            fieldnames = [
                'job_id', 'title', 'company', 'location', 
                'cleaned_description', 'skills', 'skills_by_category',
                'skill_count', 'source', 'scrape_date', 'processed_date'
            ]
            
            with open(output_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for offer in offers:
                    row = {k: offer.get(k, '') for k in fieldnames}
                    # Convertir listes en chaînes JSON
                    row['skills'] = json.dumps(offer['skills']) if offer['skills'] else '[]'
                    row['skills_by_category'] = json.dumps(offer['skills_by_category']) if offer['skills_by_category'] else '{}'
                    writer.writerow(row)
            
            logger.info(f"✓ Saved processed offers to {output_csv}")
        
        # Sauvegarder en JSON
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(offers, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Saved detailed offers to {output_json}")
        
    except Exception as e:
        logger.error(f"❌ Error saving offers: {e}")


def print_statistics(offers):
    """Affiche les statistiques sur les offres traitées."""
    if not offers:
        logger.warning("No offers to analyze")
        return
    
    print("\n" + "=" * 70)
    print("PROCESSING STATISTICS")
    print("=" * 70)
    
    # Compter les offres par source
    sources = {}
    for offer in offers:
        source = offer.get('source', 'unknown')
        sources[source] = sources.get(source, 0) + 1
    
    print(f"\n[1] Offers by source:")
    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        print(f"    {source}: {count} offers")
    
    # Stats compétences
    all_skills = []
    skills_by_category = {}
    jobs_with_skills = 0
    
    for offer in offers:
        if offer['skill_count'] > 0:
            jobs_with_skills += 1
            all_skills.extend(offer['skills'])
            for category, skills in offer['skills_by_category'].items():
                if category not in skills_by_category:
                    skills_by_category[category] = []
                skills_by_category[category].extend(skills)
    
    print(f"\n[2] Skills Statistics:")
    print(f"    Jobs with skills: {jobs_with_skills}/{len(offers)} ({100*jobs_with_skills/len(offers):.1f}%)")
    print(f"    Total unique skills: {len(set(all_skills))}")
    print(f"    Average skills per job: {len(all_skills)/len(offers):.1f}")
    
    print(f"\n[3] Top 10 Most Common Skills:")
    from collections import Counter
    skill_counts = Counter(all_skills)
    for skill, count in skill_counts.most_common(10):
        print(f"    {skill}: {count} offers")
    
    print(f"\n[4] Skills by Category:")
    for category, skills in sorted(skills_by_category.items()):
        unique_skills = list(set(skills))
        print(f"    {category}: {len(unique_skills)} unique skills")
        if len(unique_skills) <= 10:
            print(f"      {', '.join(unique_skills)}")
        else:
            print(f"      {', '.join(unique_skills[:10])}... (+{len(unique_skills)-10} more)")
    
    print("\n" + "=" * 70)


def main():
    """Main entry point."""
    # Chemins
    input_csv = Path('/home/josh/ProjectTD/skill_extractor/data/raw/job_offers_raw.csv')
    output_csv = Path('/home/josh/ProjectTD/skill_extractor/data/processed/job_offers_cleaned.csv')
    output_json = Path('/home/josh/ProjectTD/skill_extractor/data/processed/offers_with_skills.json')
    
    # Créer répertoires s'ils n'existent pas
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 70)
    print("NLP PIPELINE: TEXT CLEANING & SKILLS EXTRACTION")
    print("=" * 70)
    
    # Charger les offres brutes
    print("\n[1] Loading raw offers...")
    offers = load_raw_offers(input_csv)
    if not offers:
        logger.error("No offers loaded. Exiting.")
        return
    
    # Initialiser le pipeline NLP
    print("[2] Initializing NLP pipeline...")
    nlp_pipeline = NLPPipeline()
    
    # Traiter les offres
    print("[3] Processing offers with NLP pipeline...")
    processed_offers = process_offers(offers, nlp_pipeline)
    
    # Sauvegarder les résultats
    print("[4] Saving processed offers...")
    save_processed_offers(processed_offers, output_csv, output_json)
    
    # Afficher les statistiques
    print_statistics(processed_offers)
    
    print("\n✓ NLP Processing Complete!\n")


if __name__ == '__main__':
    main()
