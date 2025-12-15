# 🚀 Plateforme Intelligente d'Extraction et Recommandation de Compétences Techniques

## 📋 Vue d'ensemble

Plateforme data-driven complète pour l'extraction automatique de compétences à partir d'offres d'emploi tech marocaines et internationales, avec un système de recommandation basé sur le clustering et le machine learning.

**Module D** - Données Académiques et Scientifiques  
**Année**: 2025  
**Groupe**: 3-4 étudiants

---

## 🎯 Objectifs

- ✅ Scraper et collecter les offres d'emploi tech
- ✅ Extraire automatiquement les compétences techniques avec NLP
- ✅ Clustering intelligent des profils d'emploi
- ✅ Système de recommandation personnalisé
- ✅ Dashboard interactif pour exploration et analyse
- ✅ Documentation complète et rapport académique

---

## 📂 Structure du Projet

```
ProjectTD/
├── skill_extractor/                   # 🔧 Module principal
│   ├── scrapping/                     # Web scraping
│   │   ├── rekrute_scraper.py
│   │   └── linkedin_scraper.py
│   ├── nlp/                          # Traitement du langage
│   │   ├── advanced_skills_extractor.py
│   │   ├── nlp_pipeline.py
│   │   └── text_cleaner.py
│   ├── modelling/                    # ML & Clustering
│   │   ├── clustering.py
│   │   ├── embeddings.py
│   │   └── embeddings.py
│   ├── recommendtion/                # Recommandation
│   │   ├── clustering_recommender.py
│   │   ├── cv_recommender_service.py
│   │   └── skill_gap.py
│   ├── dashboard/                    # 📊 Streamlit App
│   │   ├── app.py                    # Application principale
│   │   ├── requirements.txt
│   │   └── .streamlit/config.toml
│   ├── data/                         # 📊 Données
│   │   ├── raw/                      # Données brutes scrapées
│   │   ├── processed/                # Données nettoyées
│   │   └── embeddings/               # Embeddings sauvegardés
│   ├── models/                       # 🤖 Modèles ML sauvegardés
│   ├── process_offers_nlp.py         # Pipeline complet
│   ├── requirements.txt
│   └── .env
├── rapport/                           # 📄 Documentation
│   ├── rapport_principal.tex          # Rapport LaTeX complet
│   ├── README.md
│   └── compile_rapport.sh
├── backend/                           # Backend Django (optionnel)
└── UI/                               # Frontend React (optionnel)
```

---

## 🏗️ Architecture du Pipeline

```
SCRAPING → CLEANING → EXTRACTION → VALIDATION → CLUSTERING → RECOMMENDATION → DASHBOARD
   ↓          ↓          ↓             ↓            ↓              ↓             ↓
ReKrute   Text         Skills        Filter    KMeans/      Scoring        Streamlit
LinkedIn  Cleaning     Extractor      Tech      HDBSCAN      Multi-Criteria  Interface
```

### Étapes Détaillées

1. **SCRAPING** 🕷️
   - ReKrute: BeautifulSoup4
   - LinkedIn: Selenium + Browser automation
   - Données: ~250 offres

2. **CLEANING** 🧹
   - Normalisation texte
   - Tokenization avec spaCy
   - Suppression stopwords

3. **EXTRACTION** 🔍
   - Base de 150+ compétences tech
   - Fuzzy matching (fuzzywuzzy)
   - Validation multi-couche

4. **VALIDATION** ✅
   - Filtre job tech vs non-tech
   - Vérification compétence réelle
   - Score de confiance ≥ 0.7

5. **CLUSTERING** 🎯
   - TF-IDF Vectorization
   - KMeans (k=8) ou HDBSCAN
   - Identification profils

6. **RECOMMENDATION** 💡
   - SkillMatch: Jaccard similarity
   - ClusterSim: Cosine similarity
   - ProfileFit: Critères personnalisés

7. **DASHBOARD** 📊
   - 4 pages Streamlit
   - Visualisations Plotly
   - Filtrage avancé

---

## 🚀 Démarrage Rapide

### 1. Installation

```bash
# Cloner/Accéder au projet
cd /home/josh/ProjectTD/skill_extractor

# Créer environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate  # Windows

# Installer dépendances
pip install -r requirements.txt
```

### 2. Données

Les données sont pré-scrapées et disponibles dans:
- `data/processed/job_offers_skills_advanced.json` (~250 offres)
- `data/processed/job_offers_essential.json` (format simplifié)

Pour scraper nouveau:
```bash
python scrapping/rekrute_scraper.py
python scrapping/linkedin_scraper.py
```

### 3. Traitement NLP

```bash
# Pipeline complet
python process_offers_nlp.py
```

Cela va :
- Charger les données JSON
- Appliquer le nettoyage NLP
- Extraire les compétences
- Générer embeddings
- Sauvegarder les résultats

### 4. Lancer le Dashboard

```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

L'application est accessible sur: **http://localhost:8501**

---

## 📊 Dashboard Features

### Pages

1. **📊 Dashboard** - Vue d'ensemble et métriques
   - Total offres, compétences détectées
   - Top 10 compétences
   - Distribution par source

2. **🔍 Extraction** - Explications techniques
   - Pipeline d'extraction détaillé
   - Techniques NLP utilisées
   - Base de compétences

3. **💼 Offres** - Catalogue et recherche
   - Recherche avancée
   - Filtres (source, compétences, titre)
   - Affichage détaillé des offres

4. **🎓 Recommandations** - Matching personnalisé
   - Créer profil utilisateur
   - Sélectionner compétences
   - Recommandations avec scoring
   - Visualisation du match

---

## 📈 Résultats & Métriques

### Performance de l'Extraction

| Métrique | Valeur | Cible | Statut |
|----------|--------|-------|--------|
| Précision | 87% | ≥85% | ✅ |
| Rappel | 82% | ≥80% | ✅ |
| F1-Score | 0.845 | ≥0.82 | ✅ |
| Offres tech | 210/250 | - | 84% |
| Compétences uniques | 152 | - | - |

### Top Compétences

1. Python - 78 occurrences (37%)
2. JavaScript - 64 (30%)
3. React - 52 (24%)
4. PostgreSQL - 48 (22%)
5. Docker - 46 (21%)
6. AWS - 42 (20%)

### Clusters Identifiés

- Cluster 0: Web Developers (React, JS)
- Cluster 1: Backend Engineers (Python, Django)
- Cluster 2: Data Scientists (TensorFlow, Pandas)
- Cluster 3: DevOps/Cloud (Docker, K8s)
- Cluster 4: Full Stack
- Cluster 5: Solutions Architects
- Cluster 6: Mobile Developers
- Cluster 7: QA/Testing

---

## 🔧 Technologies Utilisées

### Data Collection
- **BeautifulSoup4** - Web scraping
- **Selenium** - JavaScript rendering
- **Requests** - HTTP client

### NLP & Text Processing
- **spaCy** - Tokenization, POS, NER
- **NLTK** - Corpus et resources
- **Transformers (HuggingFace)** - BERT embeddings
- **sentence-transformers** - Semantic embeddings
- **fuzzywuzzy** - Fuzzy string matching
- **unidecode** - Character normalization

### Machine Learning
- **scikit-learn** - KMeans clustering, TF-IDF
- **HDBSCAN** - Density-based clustering
- **numpy, pandas** - Data manipulation

### Data Visualization
- **Streamlit** - Web app framework
- **Plotly** - Interactive charts
- **matplotlib, seaborn** - Static viz

### Storage
- **JSON** - Structured data
- **CSV** - Tabular data
- **Pickle** - Model serialization

---

## 📄 Rapport Académique

Le rapport complet est disponible dans le dossier `rapport/`:

### Contenu
- Problématique et contexte
- Sources de données
- Architecture data détaillée
- Méthodes NLP et ML
- Résultats quantifiés
- Limitations et futures améliorations
- Contribution à la transformation digitale

### Compilation

```bash
cd rapport
bash compile_rapport.sh
# ou
pdflatex -interaction=nonstopmode rapport_principal.tex
```

Résultat: `rapport_principal.pdf` (5-7 pages)

---

## 🔍 Exploration des Données

### Charger les données

```python
import json
import pandas as pd

# Charger JSON
with open('data/processed/job_offers_skills_advanced.json', 'r') as f:
    offers = json.load(f)

# Créer DataFrame
df = pd.DataFrame(offers)

# Statistiques
print(f"Total offres: {len(df)}")
print(f"Colonnes: {df.columns.tolist()}")
print(f"Compétences uniques: {len(set(s for skills in df['skills'] for s in skills))}")
```

### Analyser les compétences

```python
from collections import Counter

# Compter les compétences
all_skills = []
for skills in df['skills']:
    all_skills.extend(skills)

skill_counts = Counter(all_skills)
print(skill_counts.most_common(10))
```

---

## 🛠️ Development

### Code Structure

```python
# Extraction de compétences
from nlp.advanced_skills_extractor import SkillsExtractor

extractor = SkillsExtractor()
job_desc = "Looking for Python + React developer..."
skills = extractor.extract_skills(job_desc)
# → ['Python', 'React']
```

```python
# Clustering
from modelling.clustering import SkillsVectorizer, SkillsClusterer

vectorizer = SkillsVectorizer()
embeddings = vectorizer.vectorize_descriptions(offers)

clusterer = SkillsClusterer()
clusters = clusterer.cluster(embeddings, n_clusters=8)
```

```python
# Recommandation
from recommendtion.clustering_recommender import ClusteringRecommender

recommender = ClusteringRecommender(offers, clusters)
recommendations = recommender.recommend(user_skills=['Python', 'Docker'])
```

---

## 📋 Checklist de Développement

- ✅ Web Scraping (ReKrute, LinkedIn)
- ✅ NLP Cleaning & Preprocessing
- ✅ Skills Extraction (Advanced)
- ✅ Validation Multi-couche
- ✅ Vectorization & Clustering
- ✅ Recommendation Engine
- ✅ Streamlit Dashboard
- ✅ Rapport académique complet
- ✅ Documentation
- ✅ Code cleanup & organization

---

## 🚧 Prochaines Améliorations

### Court Terme
- [ ] Augmenter dataset à 2000+ offres
- [ ] Fine-tuner NER model
- [ ] Ajouter nouvelles sources (Indeed, GitHub Jobs)
- [ ] Système de notation utilisateur

### Moyen Terme
- [ ] API REST (FastAPI/Flask)
- [ ] Système de recommandation collaboratif
- [ ] Email alerts
- [ ] DB (PostgreSQL)

### Long Terme
- [ ] Support multilingue (EN, ES, DE)
- [ ] Prédiction salaires
- [ ] Trend prediction ML
- [ ] App mobile (Flutter)
- [ ] LinkedIn API integration

---

## 📧 Contact & Support

Pour des questions sur le projet:
- Consulter la documentation: `rapport/README.md`
- Explorer le code: Commentaires détaillés dans tous les fichiers
- Tester le dashboard: Lancer l'application Streamlit

---

## 📜 Licence

Projet académique - Année 2025

---

## 🙏 Remerciements

Merci aux sources de données:
- **ReKrute.com** - Offres d'emploi marocaines
- **LinkedIn** - Offres internationales
- **Open Data Communities** - Ressources NLP

---

**Dernière mise à jour**: Décembre 2025  
**Version**: 1.0 - Production Ready  
**Status**: ✅ Complet et documenté
