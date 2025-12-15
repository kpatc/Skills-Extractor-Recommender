#!/usr/bin/env python3
"""
NLP Pipeline: Cleaning + Skills Extraction
Loads raw job offers, cleans them, and extracts skills
"""
import sys
import os
import json
import csv
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nlp.text_cleaner import TextCleaner, clean_offers_pipeline
from nlp.skills_extractor_v2 import extract_skills_from_jobs

# Paths
DATA_RAW = "data/raw/job_offers_raw.csv"
DATA_CLEANED = "data/processed/job_offers_cleaned.csv"
DATA_WITH_SKILLS = "data/processed/job_offers_with_skills.csv"
DATA_SKILLS_JSON = "data/processed/job_offers_skills.json"

def load_raw_data():
    """Load raw job offers from CSV"""
    jobs = []
    with open(DATA_RAW, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            jobs.append(row)
    return jobs

def save_cleaned_data(cleaned_jobs):
    """Save cleaned job offers to CSV"""
    os.makedirs(os.path.dirname(DATA_CLEANED), exist_ok=True)
    
    if not cleaned_jobs:
        print("⚠️  No cleaned jobs to save")
        return
    
    with open(DATA_CLEANED, 'w', newline='', encoding='utf-8') as f:
        fieldnames = cleaned_jobs[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_jobs)
    
    print(f"✅ Cleaned data saved: {DATA_CLEANED}")

def save_skills_data(jobs_with_skills):
    """Save jobs with extracted skills to CSV and JSON"""
    os.makedirs(os.path.dirname(DATA_WITH_SKILLS), exist_ok=True)
    
    # Save as CSV
    if jobs_with_skills:
        fieldnames = jobs_with_skills[0].keys()
        with open(DATA_WITH_SKILLS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(jobs_with_skills)
        print(f"✅ Skills data saved (CSV): {DATA_WITH_SKILLS}")
    
    # Save as JSON (for easier access)
    with open(DATA_SKILLS_JSON, 'w', encoding='utf-8') as f:
        json.dump(jobs_with_skills, f, indent=2, ensure_ascii=False)
    print(f"✅ Skills data saved (JSON): {DATA_SKILLS_JSON}")

def print_stats(jobs):
    """Print statistics about the data"""
    if not jobs:
        return
    
    print("\n" + "="*60)
    print("STATISTICS")
    print("="*60)
    print(f"Total offers: {len(jobs)}")
    
    sources = {}
    for job in jobs:
        source = job.get('source', 'unknown')
        sources[source] = sources.get(source, 0) + 1
    
    print("\nOffers by source:")
    for source, count in sources.items():
        print(f"  - {source}: {count}")
    
    # Skills statistics
    all_skills = []
    for job in jobs:
        skills = job.get('skills', [])
        if isinstance(skills, str):
            skills = json.loads(skills) if skills else []
        all_skills.extend(skills)
    
    if all_skills:
        print(f"\nTotal skills extracted: {len(all_skills)}")
        print(f"Unique skills: {len(set(all_skills))}")
        
        # Top 15 skills
        from collections import Counter
        skill_counts = Counter(all_skills)
        print("\nTop 15 skills:")
        for skill, count in skill_counts.most_common(15):
            print(f"  - {skill}: {count}")

def main():
    """Main NLP pipeline"""
    print("\n" + "="*60)
    print("🚀 NLP PIPELINE: CLEANING + SKILLS EXTRACTION")
    print("="*60)
    
    # Step 1: Load raw data
    print("\n📖 Step 1: Loading raw data...")
    try:
        jobs = load_raw_data()
        print(f"✅ Loaded {len(jobs)} job offers")
    except FileNotFoundError:
        print(f"❌ Error: {DATA_RAW} not found")
        return
    
    # Step 2: Clean text
    print("\n🧹 Step 2: Cleaning job descriptions...")
    cleaned_jobs = clean_offers_pipeline(jobs)
    print(f"✅ Cleaned {len(cleaned_jobs)} job offers")
    save_cleaned_data(cleaned_jobs)
    
    # Step 3: Extract skills
    print("\n🎯 Step 3: Extracting skills...")
    jobs_with_skills = extract_skills_from_jobs(cleaned_jobs)
    print(f"✅ Extracted skills from {len(jobs_with_skills)} job offers")
    save_skills_data(jobs_with_skills)
    
    # Step 4: Print statistics
    print_stats(jobs_with_skills)
    
    print("\n" + "="*60)
    print("✅ NLP PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*60)
    print(f"\n📊 Output files:")
    print(f"   - Cleaned: {DATA_CLEANED}")
    print(f"   - Skills (CSV): {DATA_WITH_SKILLS}")
    print(f"   - Skills (JSON): {DATA_SKILLS_JSON}")
    print()

if __name__ == "__main__":
    main()
