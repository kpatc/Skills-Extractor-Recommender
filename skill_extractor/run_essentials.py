#!/usr/bin/env python3
"""
Pipeline essentiel: NLP Cleaning + Advanced Skills Extraction
Pas de scraping, pas de clustering - juste l'extraction de compétences
"""

import json
import csv
import logging
from pathlib import Path
from collections import Counter

from nlp.text_cleaner import TextCleaner
from nlp.skills_extractor_advanced import extract_skills_from_offers_advanced

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run():
    logger.info("=" * 80)
    logger.info("PIPELINE ESSENTIEL: NLP CLEANING + EXTRACTION AVANCÉE")
    logger.info("=" * 80)
    
    # Charger les données brutes
    raw_csv = Path(__file__).parent / 'data' / 'raw' / 'job_offers_raw.csv'
    
    logger.info(f"\n📂 Chargement des données brutes depuis: {raw_csv}")
    
    with open(raw_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        offers = list(reader)
    
    # POC: Prendre juste 10 offres pour tester
    offers = offers[:10]
    
    logger.info(f"✅ {len(offers)} offres chargées (POC mode: 10 offres)")
    
    # Étape 1: NLP Cleaning
    logger.info(f"\n🧹 ETAPE 1: NLP CLEANING")
    logger.info("-" * 80)
    
    cleaner = TextCleaner()
    cleaned_offers = []
    
    for i, offer in enumerate(offers):
        cleaned_desc = cleaner.clean(offer['description'])
        offer['description_cleaned'] = cleaned_desc
        cleaned_offers.append(offer)
        
        if (i + 1) % 10 == 0:
            logger.info(f"   Nettoyé: {i + 1}/{len(offers)}")
    
    logger.info(f"✅ {len(cleaned_offers)} offres nettoyées")
    
    # Étape 2: Advanced Skills Extraction
    logger.info(f"\n🔍 ETAPE 2: EXTRACTION AVANCÉE DES COMPETENCES")
    logger.info("-" * 80)
    
    # Utiliser les descriptions nettoyées pour l'extraction
    offers_with_skills = extract_skills_from_offers_advanced(cleaned_offers)
    
    logger.info(f"✅ Compétences extraites pour {len(offers_with_skills)} offres")
    
    # Statistiques
    offers_with_detected = sum(1 for o in offers_with_skills if o.get('num_skills', 0) > 0)
    total_skills_found = sum(o.get('num_skills', 0) for o in offers_with_skills)
    avg_skills = total_skills_found / len(offers_with_skills) if offers_with_skills else 0
    
    logger.info(f"\n📊 STATISTIQUES:")
    logger.info(f"   Total offres: {len(offers_with_skills)}")
    logger.info(f"   Offres avec compétences: {offers_with_detected}/{len(offers_with_skills)} ({100*offers_with_detected/len(offers_with_skills):.1f}%)")
    logger.info(f"   Total compétences trouvées: {total_skills_found}")
    logger.info(f"   Moyenne par offre: {avg_skills:.2f}")
    
    # Top 20 skills
    all_skills = []
    for o in offers_with_skills:
        all_skills.extend(o.get('skills', []))
    
    top_skills = Counter(all_skills).most_common(20)
    logger.info(f"\n🏆 TOP 20 COMPETENCES:")
    for skill, count in top_skills:
        logger.info(f"   {skill}: {count} offres")
    
    # Sauvegarder résultats en JSON
    output_json = Path(__file__).parent / 'data' / 'processed' / 'job_offers_essential.json'
    output_json.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(offers_with_skills, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n💾 Résultats sauvegardés en JSON: {output_json}")
    
    # Sauvegarder résultats en CSV
    output_csv = Path(__file__).parent / 'data' / 'processed' / 'job_offers_essential.csv'
    
    if offers_with_skills:
        fieldnames = ['job_id', 'title', 'company', 'location', 'source', 'scrape_date', 'num_skills', 'skills']
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for offer in offers_with_skills:
                row = {
                    'job_id': offer.get('job_id', ''),
                    'title': offer.get('title', ''),
                    'company': offer.get('company', ''),
                    'location': offer.get('location', ''),
                    'source': offer.get('source', ''),
                    'scrape_date': offer.get('scrape_date', ''),
                    'num_skills': offer.get('num_skills', 0),
                    'skills': '|'.join(offer.get('skills', []))
                }
                writer.writerow(row)
        
        logger.info(f"💾 Résultats sauvegardés en CSV: {output_csv}")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ PIPELINE ESSENTIEL TERMINÉ AVEC SUCCÈS")
    logger.info("=" * 80)
    
    return {
        'total_offers': len(offers_with_skills),
        'offers_with_skills': offers_with_detected,
        'avg_skills_per_offer': avg_skills,
        'top_skills': [s[0] for s in top_skills[:10]],
        'output_json': str(output_json),
        'output_csv': str(output_csv)
    }

if __name__ == '__main__':
    result = run()
    print("\n" + json.dumps(result, indent=2, ensure_ascii=False))
