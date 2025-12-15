#!/bin/bash

# Installation des dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements.txt

# Lancer Streamlit
echo "🚀 Lancement du dashboard..."
streamlit run app.py --logger.level=info
