# Plateforme Intelligente d'Extraction de Compétences Tech

## 📋 Vue d'ensemble

**Extraction et analyse automatique des compétences techniques** à partir des offres d'emploi marocaines et internationales.

### Objectif Principal
Automatiser la collecte, l'analyse et la valorisation des compétences demandées pour aider :
- ✅ **Étudiants** : identifier les compétences à apprendre
- ✅ **Écoles** : aligner les cursus avec le marché
- ✅ **Recruteurs** : mieux comprendre le marché des talents

---

## 🏗️ Architecture du Projet

### Pipeline de Traitement

```
[Sources Web]
    ↓
[Scrapers Python]
    ↓
[Raw Data - JSON/CSV]
    ↓
[Preprocessing NLP]
    ↓
[Extraction des compétences]
    ↓
[Vectorisation / Embeddings]
    ↓
[Clustering]
    ↓
[Recommandation]
    ↓
[Dashboard / API]
```

### Structure des Répertoires

```
skill_extractor/
├── scrapping/          # Module de scraping des offres
│   └── scraper.py
├── nlp/                # Module NLP & nettoyage
│   ├── text_cleaner.py
│   └── skills_extractor.py
├── modelling/          # Module clustering & vectorisation
│   └── clustering.py
├── recommendtion/      # Module recommandation
│   └── recommender.py
├── data/               # Données
│   ├── raw/
│   └── processed/
├── models/             # Modèles sauvegardés
├── utils/              # Utilitaires
│   └── config.py
├── pipeline.py         # Orchestration complète
├── test_pipeline.py    # Tests
├── setup_env.py        # Configuration
└── requirements.txt    # Dépendances
```

---

## 🔧 Installation et Configuration

### 1. Prérequis
- Python 3.8+
- pip (gestionnaire de paquets)
- Git

### 2. Installation des dépendances

```bash
# Cloner le projet (si applicable)
cd skill_extractor

# Installer les paquets
pip install -r requirements.txt

# Configurer l'environnement
python setup_env.py
```

Cela téléchargera automatiquement les modèles spaCy nécessaires.

### 3. Vérification

```bash
# Exécuter les tests
pytest test_pipeline.py -v
```

---

## 📊 Modules Détaillés

### Module 1: Scraping (`scrapping/scraper.py`)

**Responsabilité** : Collecter les offres d'emploi

**Sources supportées** :
- 🇲🇦 Marocaines: ReKrute, Emploi.ma
- 🌍 Internationales: Indeed, Glassdoor, LinkedIn

**Fonctionnalités** :
- ✅ Pagination automatique
- ✅ Gestion des doublons
- ✅ Extraction du texte complet
- ✅ Gestion des erreurs et retry

**Structure d'une offre** :
```python
{
    "job_id": "rekrute_001",
    "title": "Data Engineer",
    "company": "TechCorp",
    "location": "Casablanca",
    "description": "We are looking for...",
    "source": "rekrute",
    "scrape_date": "2024-01-10"
}
```

**Utilisation** :
```python
from skill_extractor.scrapping.scraper import scrape_all_sources

# Mode test (données simulées)
offers = scrape_all_sources(test_mode=True)

# Mode production (scraping réel)
offers = scrape_all_sources(test_mode=False)
```

---

### Module 2: NLP et Nettoyage (`nlp/text_cleaner.py`)

**Responsabilité** : Nettoyer et préparer les textes

**Étapes de nettoyage** :
1. Suppression du HTML
2. Suppression des URLs et emails
3. Conversion en minuscules
4. Suppression des caractères spéciaux
5. Suppression des espaces superflus
6. Lemmatisation (optionnel)
7. Suppression des stopwords (optionnel)

**Utilisation** :
```python
from skill_extractor.nlp.text_cleaner import TextCleaner

cleaner = TextCleaner()

# Nettoyer un texte
cleaned = cleaner.clean(
    "<p>Senior Python Developer</p>",
    lemmatize=True,
    remove_stopwords=True
)

# Nettoyer plusieurs offres
cleaned_offers = cleaner.clean_job_offers(offers)
```

---

### Module 3: Extraction des Compétences (`nlp/skills_extractor.py`)

**Responsabilité** : Extraire les compétences techniques

**Deux approches combinées** :

#### A. Dictionnaire + Regex
- ✅ Rapide et fiable
- ❌ Nécessite un dictionnaire à jour
- Couverture: `TECH_SKILLS` (config.py)

```python
extractor = SkillExtractor()
skills_set = extractor.extract_skills_regex(text)
# → {"python", "sql", "docker"}
```

#### B. Extraction Sémantique
- ✅ Détecte les variations
- ❌ Plus lent, nécessite GPU pour performance
- Utilise: sentence-transformers + similarité cosinus

```python
skills_data = extractor.extract_skills(
    text,
    method="semantic"  # ou "regex", "spacy", "combined"
)
# → {
#     "skills": ["python", "sql"],
#     "count": 2,
#     "categorized": {...}
# }
```

**Catégories de compétences** :
- 🐍 Languages: python, java, javascript, go, rust...
- 📊 Data & ML: sql, spark, tensorflow, pytorch...
- ☁️ DevOps: docker, kubernetes, aws, azure...
- 🎨 Frontend: react, vue, angular...
- 🔧 Backend: nodejs, fastapi, django, spring...

---

### Module 4: Vectorisation & Clustering (`modelling/clustering.py`)

**Responsabilité** : Regrouper les offres par profil

#### Vectorisation

```python
from skill_extractor.modelling.clustering import SkillsVectorizer

vectorizer = SkillsVectorizer()
embeddings = vectorizer.vectorize_descriptions(offers)
# → shape: (n_offers, embedding_dim)
```

**Modèles disponibles** :
- Sentence-Transformers (par défaut, recommandé)
- TF-IDF (fallback)

#### Clustering

```python
from skill_extractor.modelling.clustering import OffersClustering

clusterer = OffersClustering()
clusterer.fit(embeddings)

# Clusters: 0=Data, 1=Backend, 2=DevOps, 3=AI/ML, 4=Frontend
```

**Algorithmes** :
- K-Means (simple, pédagogique)
- HDBSCAN (détecte clusters de formes arbitraires)

---

### Module 5: Recommandation (`recommendtion/recommender.py`)

**Responsabilité** : Générer des recommandations personnalisées

**Profils supportés** :
- 🔢 `data_engineer`: Python, SQL, Spark, AWS
- 🖥️ `backend_dev`: Node.js, PostgreSQL, Docker
- ⚙️ `devops_engineer`: Docker, Kubernetes, CI/CD
- 🤖 `ml_engineer`: TensorFlow, PyTorch, NLP
- 🎨 `frontend_dev`: React, TypeScript, Tailwind

**Recommandations par profil** :

```python
from skill_extractor.recommendtion.recommender import SkillRecommender

recommender = SkillRecommender()

# Recommandation personnalisée
rec = recommender.recommend_for_profile(
    profile_name="data_engineer",
    cluster_data=clustering_result,
    top_n=15
)

# Résultat:
# {
#     "profile": "data_engineer",
#     "current_skills": ["python", "sql", ...],
#     "recommended_skills": [
#         {
#             "skill": "spark",
#             "frequency": 45,
#             "importance_score": 0.92,
#             "priority": 67.5
#         },
#         ...
#     ],
#     "learning_path": [
#         {
#             "phase": "Fondamentaux (0-3 mois)",
#             "skills": [...]
#         },
#         ...
#     ]
# }
```

**Analyse de l'écart** :

```python
gap = recommender.get_skills_gap("data_engineer", cluster_data)
# → {
#     "missing_skills": [...],
#     "gap_percentage": 45.2
# }
```

---

## 🚀 Exécution du Pipeline

### Mode Test (Recommandé pour démarrer)

```python
from skill_extractor.pipeline import main

# Exécuter le pipeline complet
result = main(test_mode=True)

print(f"Offres traitées: {result['offers_raw_count']}")
print(f"Recommandations générées: {len(result['recommendations'])}")
```

### Mode Production

```python
from skill_extractor.pipeline import SkillExtractionPipeline

pipeline = SkillExtractionPipeline(test_mode=False)
result = pipeline.run_full_pipeline()

# Les données sont sauvegardées dans:
# - data/raw/job_offers_raw.csv
# - data/processed/job_offers_cleaned.csv
# - data/processed/recommendations.json
```

### Exécution Step-by-Step

```python
from skill_extractor.scrapping.scraper import scrape_all_sources
from skill_extractor.nlp.text_cleaner import clean_offers_pipeline
from skill_extractor.nlp.skills_extractor import extract_skills_pipeline
from skill_extractor.modelling.clustering import cluster_offers
from skill_extractor.recommendtion.recommender import generate_recommendations_pipeline

# Étape 1: Scraping
offers = scrape_all_sources(test_mode=True)

# Étape 2: Nettoyage
offers = clean_offers_pipeline(offers)

# Étape 3: Extraction des compétences
offers = extract_skills_pipeline(offers)

# Étape 4: Clustering
clustering_result = cluster_offers(offers)

# Étape 5: Recommandations
recommendations = generate_recommendations_pipeline(clustering_result)

# Afficher les résultats
for profile, data in recommendations.items():
    print(f"\n{profile}:")
    for rec in data['recommended_skills'][:5]:
        print(f"  - {rec['skill']}: {rec['priority']:.1f}")
```

---

## 📈 Résultats et Sortie

### Fichiers générés

```
skill_extractor/data/
├── raw/
│   └── job_offers_raw.csv           # Offres brutes
├── processed/
│   ├── job_offers_cleaned.csv       # Offres nettoyées
│   ├── skills_embeddings.npy        # Embeddings vectorisés
│   └── recommendations.json         # Recommandations
└── models/
    └── clustering_model.pkl         # Modèle clustering sauvegardé
```

### Format des recommandations (JSON)

```json
{
  "data_engineer": {
    "profile": "data_engineer",
    "cluster": "Data",
    "current_skills": ["python", "sql", "spark", "docker", "aws"],
    "recommended_skills": [
      {
        "skill": "apache_spark",
        "frequency": 45,
        "importance_score": 0.92,
        "already_core": false,
        "priority": 67.5
      }
    ],
    "learning_path": [
      {
        "phase": "Fondamentaux (0-3 mois)",
        "skills": ["apache_spark", "airflow"],
        "description": "..."
      }
    ]
  }
}
```

---

## 🧪 Tests

### Exécuter tous les tests

```bash
pytest test_pipeline.py -v
```

### Tests spécifiques

```bash
# Tests de scraping
pytest test_pipeline.py::TestScraping -v

# Tests de NLP
pytest test_pipeline.py::TestTextCleaning -v

# Tests d'extraction des compétences
pytest test_pipeline.py::TestSkillExtraction -v

# Tests du pipeline complet
pytest test_pipeline.py::TestPipeline -v
```

### Couverture de tests

```bash
pytest test_pipeline.py --cov=skill_extractor --cov-report=html
```

---

## 📚 Configuration Avancée

### Personnaliser les compétences

Modifier `utils/config.py` :

```python
TECH_SKILLS = {
    "languages": ["python", "java", "go", ...],
    "data_and_ml": ["sql", "spark", ...],
    # ...
}
```

### Paramètres de clustering

```python
CLUSTERING_CONFIG = {
    "algorithm": "kmeans",  # ou "hdbscan"
    "n_clusters": 5,
    "random_state": 42,
}
```

### Paramètres NLP

```python
NLP_CONFIG = {
    "model_name": "sentence-transformers/multilingual-MiniLM-L12-v2",
    "language": "fr",
    "remove_stopwords": True,
    "lemmatization": True,
}
```

---

## 🔍 Dépannage

### Erreur: "ModuleNotFoundError: No module named 'spacy'"

```bash
pip install -r requirements.txt
python setup_env.py
```

### Erreur: "OSError: [E050] Can't find model 'fr_core_news_sm'"

```bash
python -m spacy download fr_core_news_sm
```

### Erreur: "ImportError: No module named 'sentence_transformers'"

```bash
pip install sentence-transformers
```

### Performance lente

- Utilisez `test_mode=True` pour développement
- Activez GPU: `export CUDA_VISIBLE_DEVICES=0`
- Réduisez le nombre de clusters

---

## 📊 Cas d'Usage

### Cas 1: Analyser le marché data

```python
from skill_extractor.pipeline import SkillExtractionPipeline

pipeline = SkillExtractionPipeline(test_mode=False)
result = pipeline.run_full_pipeline()

# Voir les compétences les plus demandées
from skill_extractor.nlp.skills_extractor import extractor
top_skills = extractor.get_top_skills(result["offers_with_skills"], top_n=20)

for skill, count in top_skills:
    print(f"{skill}: {count} offres")
```

### Cas 2: Obtenir des recommandations personnalisées

```python
pipeline = SkillExtractionPipeline(test_mode=True)
result = pipeline.run_full_pipeline()

recommender_data = result["recommendations"]
data_eng_recommendations = recommender_data["data_engineer"]

print("Compétences recommandées:")
for rec in data_eng_recommendations["recommended_skills"][:5]:
    print(f"- {rec['skill']} (priorité: {rec['priority']})")

print("\nChemin d'apprentissage:")
for phase in data_eng_recommendations["learning_path"]:
    print(f"\n{phase['phase']}")
    for skill in phase['skills']:
        print(f"  - {skill}")
```

### Cas 3: Suivre l'évolution du marché

```python
from datetime import datetime, timedelta

# Scraper les offres chaque semaine
for i in range(4):
    offers = scrape_all_sources(test_mode=False)
    # Traiter et sauvegarder
    pipeline = SkillExtractionPipeline()
    pipeline.offers_raw = offers
    # ...

# Analyser les tendances
```

---

## 🔐 Considérations Éthiques

- ✅ Respecter le `robots.txt` des sites
- ✅ Respecter les délais entre requêtes (2s par défaut)
- ✅ Ne pas surcharger les serveurs
- ✅ Utiliser un User-Agent approprié
- ✅ Anonymiser les données personnelles

---

## 🚀 Prochaines Étapes

### Court terme (v1.1)
- [ ] API REST FastAPI
- [ ] Dashboard Streamlit
- [ ] Support de base de données (PostgreSQL)

### Moyen terme (v1.2)
- [ ] Fine-tuning sur données marocaines
- [ ] Exportation Excel/PDF
- [ ] Webhooks pour notifications

### Long terme (v2.0)
- [ ] ML en continu (online learning)
- [ ] Prédictions salariales
- [ ] Recommandations par région

---

## 📝 Licence

Ce projet est fourni à titre éducatif.

---

## 📞 Support

Pour toute question ou problème:
1. Vérifier la documentation
2. Consulter les tests
3. Examiner les logs

---

## 📚 Ressources Externes

- [spaCy Documentation](https://spacy.io/)
- [Sentence-Transformers](https://www.sbert.net/)
- [scikit-learn](https://scikit-learn.org/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)

---

**Créé avec ❤️ pour le succès des développeurs marocains et internationaux**
