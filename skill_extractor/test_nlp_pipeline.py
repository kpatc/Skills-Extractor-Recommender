#!/usr/bin/env python3
"""
Test du pipeline NLP: nettoyage et extraction de compétences.
"""

import sys
import logging
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from nlp.nlp_pipeline import NLPPipeline


def test_nlp_pipeline():
    """Test le pipeline NLP complet."""
    
    print("=" * 70)
    print("TEST: NLP PIPELINE (Text Cleaning + Skills Extraction)")
    print("=" * 70)
    
    # Créer un pipeline
    pipeline = NLPPipeline()
    
    # Offres d'exemple
    sample_jobs = [
        {
            'job_id': 'test_0001',
            'title': 'Senior Python Developer (Django + FastAPI)',
            'company': 'TechCorp',
            'location': 'Remote',
            'source': 'linkedin',
            'description': """
            We are looking for a Senior Python Developer with 5+ years experience.
            You will work on building scalable backend services using Django and FastAPI.
            
            Requirements:
            - Strong Python knowledge (3.9+)
            - Experience with PostgreSQL and Redis
            - Docker and Kubernetes skills
            - AWS or Azure experience is a plus
            - Experience with REST APIs and GraphQL
            
            Nice to have:
            - Machine Learning background
            - CI/CD pipelines (Jenkins, GitLab CI)
            - Terraform or Ansible
            
            We offer competitive salary and remote work!
            """,
            'scrape_date': '2025-12-15T10:00:00'
        },
        {
            'job_id': 'test_0002',
            'title': 'Full Stack JavaScript Developer - React + Node.js',
            'company': 'Digital Solutions',
            'location': 'Casablanca',
            'source': 'rekrute',
            'description': """
            Hiring Full Stack JavaScript Developer (React + Node.js).
            3-5 years experience required.
            
            Tech stack:
            - React with TypeScript
            - Node.js and Express
            - MongoDB and Redis
            - Docker and docker-compose
            - Jest for testing
            - Git and GitHub
            
            You will develop modern web applications and REST APIs.
            Competitive salary and flexible hours.
            """,
            'scrape_date': '2025-12-15T11:00:00'
        }
    ]
    
    # Traiter les offres
    print("\n[1] Processing job offers...")
    processed_jobs = pipeline.process_job_offers(sample_jobs)
    
    # Afficher les résultats
    print("\n[2] Results:")
    for job in processed_jobs:
        print(f"\n  Job: {job['title']}")
        print(f"  Company: {job['company']}")
        print(f"  Skills found: {job['num_skills']}")
        if job.get('skills'):
            print(f"  Skills: {', '.join(job['skills'])}")
        if job.get('skills_categorized'):
            print(f"  By category:")
            for category, skills in job['skills_categorized'].items():
                print(f"    - {category}: {', '.join(skills)}")
    
    # Statistiques
    print("\n[3] Statistics:")
    stats = pipeline.get_statistics(processed_jobs)
    print(f"  Total jobs: {stats['total_jobs']}")
    print(f"  Jobs with skills: {stats['jobs_with_skills']}")
    print(f"  Total unique skills: {stats['total_unique_skills']}")
    print(f"  Top skills: {stats['top_20_skills'][:5]}")
    
    print("\n" + "=" * 70)
    print("✓ NLP Pipeline test PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    test_nlp_pipeline()
