"""
Configuration centralisée pour le projet d'extraction de compétences.
"""

import os
from pathlib import Path

# === Chemins ===
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "models"

# Créer les répertoires s'ils n'existent pas
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# === Chemins de fichiers ===
JOB_OFFERS_RAW = RAW_DATA_DIR / "job_offers_raw.csv"
JOB_OFFERS_CLEANED = PROCESSED_DATA_DIR / "job_offers_cleaned.csv"
SKILLS_EMBEDDINGS = PROCESSED_DATA_DIR / "skills_embeddings.npy"
CLUSTERING_MODEL = MODELS_DIR / "clustering_model.pkl"

# === Sources d'offres d'emploi ===
SOURCES = {
    "morocco": {
        "rekrute": "https://www.rekrute.com",
        "emploi_ma": "https://emploi.ma",
    },
    "international": {
        "indeed": "https://www.indeed.com",
        "glassdoor": "https://www.glassdoor.com",
    },
}

# === Paramètres de scraping ===
SCRAPING_CONFIG = {
    "timeout": 10,
    "max_retries": 3,
    "headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    },
    "delay_between_requests": 2,  # en secondes
}

# === Compétences Tech référence ===
TECH_SKILLS = {
    "languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "php", "ruby", "swift", "kotlin", "r", "scala", "haskell", "perl",
    ],
    "data_and_ml": [
        "sql", "spark", "hadoop", "pytorch", "tensorflow", "scikit-learn",
        "pandas", "numpy", "nlp", "machine learning", "deep learning",
        "computer vision", "data science", "big data", "kafka",
    ],
    "devops_and_infra": [
        "docker", "kubernetes", "aws", "gcp", "azure", "jenkins", "gitlab-ci",
        "terraform", "ansible", "git", "ci/cd", "monitoring", "prometheus",
    ],
    "frontend": [
        "react", "vue", "angular", "html", "css", "tailwind", "sass", "webpack",
        "vite", "nextjs", "nuxt", "flutter", "react native",
    ],
    "backend": [
        "nodejs", "fastapi", "django", "spring", "express", "nestjs",
        "graphql", "rest api", "microservices", "rabbitmq",
    ],
}

# === Paramètres NLP ===
NLP_CONFIG = {
    "model_name": "sentence-transformers/multilingual-MiniLM-L12-v2",
    "language": "fr",  # français
    "remove_stopwords": True,
    "lemmatization": True,
}

# === Paramètres clustering ===
CLUSTERING_CONFIG = {
    "algorithm": "kmeans",  # ou "hdbscan"
    "n_clusters": 5,
    "random_state": 42,
    "min_cluster_size": 3,  # pour HDBSCAN
}

# === Profils étudiants pour recommandation ===
STUDENT_PROFILES = {
    "data_engineer": {
        "cluster": "Data",
        "core_skills": ["python", "sql", "spark", "docker", "aws"],
        "level": "junior",
    },
    "backend_dev": {
        "cluster": "Backend",
        "core_skills": ["javascript", "nodejs", "sql", "docker", "rest api"],
        "level": "junior",
    },
    "devops_engineer": {
        "cluster": "DevOps",
        "core_skills": ["docker", "kubernetes", "ci/cd", "aws", "terraform"],
        "level": "junior",
    },
    "ml_engineer": {
        "cluster": "AI/ML",
        "core_skills": ["python", "tensorflow", "pytorch", "sql", "nlp"],
        "level": "junior",
    },
}

# === Paramètres API ===
API_CONFIG = {
    "host": "127.0.0.1",
    "port": 8000,
    "debug": True,
}

# === Paramètres Streamlit (si utilisé pour dashboard) ===
STREAMLIT_CONFIG = {
    "page_title": "Plateforme d'extraction de compétences Tech",
    "layout": "wide",
}
