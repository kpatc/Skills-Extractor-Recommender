# Skills Extractor & Recommender Dashboard

Dashboard Streamlit moderne et stylisé pour visualiser et recommander des compétences.

## 🚀 Démarrage Rapide

### Installation

```bash
cd skill_extractor/dashboard
pip install -r requirements.txt
```

### Lancement

```bash
streamlit run app.py
```

Ou avec le script:

```bash
bash run.sh
```

L'application sera accessible sur `http://localhost:8501`

## 📋 Pages du Dashboard

### 1. 📊 Dashboard
- **Métriques principales**: nombre d'offres, compétences détectées, statistiques
- **Graphiques**: top compétences, distribution des compétences
- **Analyse par source**: répartition des offres

### 2. 🔍 Extraction
- **Pipeline d'extraction**: explication des 3 étapes
- **Techniques utilisées**: fuzzy matching, tokenization
- **Base de compétences**: liste des domaines couverts

### 3. 💼 Offres
- **Recherche avancée**: filtrer par source, compétences, titre
- **Affichage des offres**: avec badges de compétences
- **Détails complets**: entreprise, localisation, skills

### 4. 🎓 Recommandations
- **Profil utilisateur**: sélection de compétences
- **Préférences**: spécifications personnelles
- **Recommendations intelligentes**: scoring automatique
- **Matching visual**: badge de correspondance

## 🎨 Design

- **Gradients modernes**: couleurs harmonieuses (indigo, rose, vert)
- **Responsive**: adapté à tous les écrans
- **Smooth animations**: transitions fluides
- **Dark mode support**: thème adaptatif

## 📊 Données Utilisées

Les données proviennent de:
- Fichier: `/data/processed/job_offers_essential.json`
- Format: JSON avec offres d'emploi et compétences extractées
- Champs: title, company, location, skills, num_skills, source

## 🔧 Configuration

Le fichier `.streamlit/config.toml` contient:
- Couleurs personnalisées
- Thème par défaut
- Paramètres de logging

## 📈 Fonctionnalités Principales

✅ Tableau de bord avec métriques  
✅ Visualisations interactives (Plotly)  
✅ Recherche et filtrage avancés  
✅ Système de recommandation  
✅ Responsive design  
✅ Performance optimisée avec cache  

## 📦 Dépendances

- `streamlit`: framework web
- `pandas`: manipulation de données
- `plotly`: graphiques interactifs
- `python-dotenv`: variables d'environnement

## 🎯 Points Clés

- **Cache Streamlit**: `@st.cache_data` pour les données JSON
- **Layout Wide**: utilisation maximale de l'espace
- **Custom CSS**: styles personnalisés pour une meilleure UX
- **Composants réutilisables**: structures cohérentes

---
**Version**: 1.0  
**Status**: POC Mode
