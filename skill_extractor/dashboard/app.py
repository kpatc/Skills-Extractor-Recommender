import streamlit as st
import json
import pandas as pd
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter

# Configuration de la page
st.set_page_config(
    page_title="Skills Extractor & Recommender",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    :root {
        --primary-color: #6366f1;
        --secondary-color: #ec4899;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
    }
    
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 4px solid var(--primary-color);
    }
    
    .skill-badge {
        display: inline-block;
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        margin: 4px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .job-card {
        background: white;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        margin-bottom: 10px;
        transition: all 0.3s ease;
    }
    
    .job-card:hover {
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("🎯 Navigation")
page = st.sidebar.radio(
    "Sélectionnez une page",
    ["📊 Dashboard", "🔍 Extraction", "💼 Offres", "🎓 Recommandations"],
    label_visibility="collapsed"
)

# Charger les données
@st.cache_data
def load_data():
    try:
        json_file = Path(__file__).parent.parent / "data" / "processed" / "job_offers_essential.json"
        with open(json_file, 'r', encoding='utf-8') as f:
            offers = json.load(f)
        return offers
    except:
        return []

offers = load_data()

if page == "📊 Dashboard":
    st.title("🚀 Skills Extractor & Recommender")
    st.markdown("Plateforme intelligente d'extraction et recommandation de compétences")
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📌 Offres Totales",
            value=len(offers),
            delta="POC Mode",
            delta_color="off"
        )
    
    with col2:
        offers_with_skills = sum(1 for o in offers if o.get('num_skills', 0) > 0)
        st.metric(
            label="✅ Offres Analysées",
            value=offers_with_skills,
            delta=f"{100*offers_with_skills//len(offers) if offers else 0}%",
            delta_color="normal"
        )
    
    with col3:
        total_skills = sum(o.get('num_skills', 0) for o in offers)
        avg_skills = total_skills / len(offers) if offers else 0
        st.metric(
            label="🎯 Compétences Détectées",
            value=total_skills,
            delta=f"{avg_skills:.2f} par offre",
            delta_color="off"
        )
    
    with col4:
        # Compter les compétences uniques
        all_skills = []
        for o in offers:
            all_skills.extend(o.get('skills', []))
        unique_skills = len(set(all_skills))
        st.metric(
            label="💎 Compétences Uniques",
            value=unique_skills,
            delta="Profils variés",
            delta_color="normal"
        )
    
    st.divider()
    
    # Graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Top 10 Compétences")
        
        if all_skills:
            skills_count = Counter(all_skills).most_common(10)
            skills_df = pd.DataFrame(skills_count, columns=['Compétence', 'Fréquence'])
            
            fig = px.bar(
                skills_df,
                x='Compétence',
                y='Fréquence',
                color='Fréquence',
                color_continuous_scale='Viridis',
                template='plotly_white'
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 Distribution des Compétences par Offre")
        
        skills_per_offer = [o.get('num_skills', 0) for o in offers]
        fig = go.Figure(data=[
            go.Histogram(
                x=skills_per_offer,
                nbinsx=10,
                marker=dict(
                    color='rgba(99, 102, 241, 0.7)',
                    line=dict(color='rgba(99, 102, 241, 1)', width=1.5)
                )
            )
        ])
        fig.update_layout(
            title="",
            xaxis_title="Nombre de compétences",
            yaxis_title="Nombre d'offres",
            template='plotly_white',
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Résumé par source
    st.subheader("📍 Offres par Source")
    sources = {}
    for o in offers:
        source = o.get('source', 'Unknown')
        sources[source] = sources.get(source, 0) + 1
    
    if sources:
        sources_df = pd.DataFrame(list(sources.items()), columns=['Source', 'Nombre'])
        fig = px.pie(sources_df, values='Nombre', names='Source, title='')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

elif page == "🔍 Extraction":
    st.title("🔍 Analyse d'Extraction de Compétences")
    
    st.subheader("📋 Pipeline d'Extraction")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**Étape 1: Scraping**\n\nRécupération des offres d'emploi depuis ReKrute et LinkedIn")
    with col2:
        st.info("**Étape 2: NLP Cleaning**\n\nNettoyage et prétraitement des descriptions")
    with col3:
        st.info("**Étape 3: Skills Extraction**\n\nExtraction avancée des compétences avec fuzzy matching")
    
    st.divider()
    
    st.subheader("🧠 Technique d'Extraction")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Approche Multi-étapes
        
        1. **Détection de Sections**
           - Identification des sections "Skills", "Requirements"
           - Extraction du contexte pertinent
        
        2. **Tokenization Intelligente**
           - Séparation par délimiteurs (virgules, "et", "ou")
           - Suppression des préfixes inutiles
        
        3. **Fuzzy Matching**
           - Comparaison avec base de 100+ compétences
           - Threshold de 75% de similarité
           - Gestion des variations (Node.js/NodeJS)
        """)
    
    with col2:
        st.markdown("""
        ### Base de Compétences
        
        - **Langages**: Python, Java, JavaScript, TypeScript, C++, Go...
        - **Frameworks**: Django, React, Angular, Spring Boot...
        - **Bases de données**: PostgreSQL, MongoDB, Redis...
        - **DevOps**: Docker, Kubernetes, AWS, Azure, Terraform...
        - **AI/ML**: TensorFlow, PyTorch, Scikit-learn...
        - **Autres**: Git, REST API, Microservices, Agile...
        """)

elif page == "💼 Offres":
    st.title("💼 Catalogue des Offres d'Emploi")
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        source_filter = st.multiselect(
            "Filtrer par source",
            options=list(set(o.get('source', 'Unknown') for o in offers)),
            default=list(set(o.get('source', 'Unknown') for o in offers))
        )
    
    with col2:
        min_skills = st.slider("Compétences minimum", 0, 10, 0)
    
    with col3:
        search = st.text_input("🔍 Rechercher par titre ou compétence")
    
    # Filtrer les offres
    filtered_offers = offers.copy()
    
    if source_filter:
        filtered_offers = [o for o in filtered_offers if o.get('source') in source_filter]
    
    if min_skills > 0:
        filtered_offers = [o for o in filtered_offers if o.get('num_skills', 0) >= min_skills]
    
    if search:
        search_lower = search.lower()
        filtered_offers = [
            o for o in filtered_offers 
            if search_lower in o.get('title', '').lower() 
            or any(search_lower in s.lower() for s in o.get('skills', []))
        ]
    
    st.write(f"**{len(filtered_offers)} offres trouvées**")
    st.divider()
    
    # Afficher les offres
    for offer in filtered_offers:
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### {offer.get('title', 'N/A')}")
                st.caption(f"🏢 {offer.get('company', 'N/A')} • 📍 {offer.get('location', 'N/A')}")
                
                if offer.get('skills'):
                    st.markdown("**Compétences requises:**")
                    skills_html = " ".join([f'<span class="skill-badge">{s}</span>' for s in offer.get('skills', [])])
                    st.markdown(skills_html, unsafe_allow_html=True)
            
            with col2:
                st.metric("Compétences", offer.get('num_skills', 0))
            
            st.divider()

elif page == "🎓 Recommandations":
    st.title("🎓 Recommandations Personnalisées")
    
    st.subheader("Créez votre profil")
    
    col1, col2 = st.columns(2)
    
    with col1:
        user_skills = st.multiselect(
            "Sélectionnez vos compétences",
            options=[
                "Python", "JavaScript", "TypeScript", "Java", "Go",
                "React", "Angular", "Vue.js", "Django", "FastAPI",
                "PostgreSQL", "MongoDB", "Redis",
                "Docker", "Kubernetes", "AWS", "Azure",
                "Machine Learning", "TensorFlow", "PyTorch",
                "Git", "REST API", "Microservices"
            ],
            default=["Python", "Docker"]
        )
    
    with col2:
        preferences = st.text_area(
            "Vos préférences",
            value="Télétravail, équipe agile, innovation",
            height=100
        )
    
    st.divider()
    
    if st.button("🔍 Obtenir des Recommandations", use_container_width=True):
        st.info("💡 Recommandations basées sur votre profil et les offres disponibles")
        
        # Matcher les compétences
        recommendations = []
        
        for offer in offers:
            offer_skills = set(offer.get('skills', []))
            user_skills_set = set(s.lower() for s in user_skills)
            
            # Calculer le score de correspondance
            matches = len(offer_skills & user_skills_set)
            total = len(offer_skills) + len(user_skills_set)
            score = (2 * matches / total * 100) if total > 0 else 0
            
            recommendations.append({
                'offer': offer,
                'score': score,
                'matches': matches
            })
        
        # Trier par score
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        # Afficher les recommandations
        for i, rec in enumerate(recommendations[:5], 1):
            offer = rec['offer']
            score = rec['score']
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"### {i}. {offer.get('title', 'N/A')}")
                st.caption(f"🏢 {offer.get('company', 'N/A')} • 📍 {offer.get('location', 'N/A')}")
            
            with col2:
                st.metric("Match", f"{score:.0f}%")
            
            with col3:
                if score >= 75:
                    st.success("⭐ Excellent")
                elif score >= 50:
                    st.warning("👍 Bon")
                else:
                    st.info("📈 À explorer")
            
            if offer.get('skills'):
                st.markdown("**Compétences:**")
                skills_html = " ".join([f'<span class="skill-badge">{s}</span>' for s in offer.get('skills', [])])
                st.markdown(skills_html, unsafe_allow_html=True)
            
            st.divider()

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>Skills Extractor & Recommender</strong> • Powered by NLP & Machine Learning</p>
    <p>Version 1.0 • POC Dashboard</p>
</div>
""", unsafe_allow_html=True)
