import streamlit as st
import json
import re
from pathlib import Path
from datetime import datetime
import sys
import os

# Fix imports - Add skill_extractor to path
skill_extractor_dir = Path(__file__).parent.parent
sys.path.insert(0, str(skill_extractor_dir))
os.chdir(str(skill_extractor_dir))

# Import modules
try:
    from nlp.advanced_skills_extractor import SkillsExtractor
    from nlp.text_cleaner import TextCleaner
    from recommendtion.clustering_recommender import SkillsRecommender
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Configuration de la page
st.set_page_config(
    page_title="CV Skills Analyzer",
    page_icon="briefcase",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS styling
st.markdown("""
<style>
    .metric-card {
        background: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #0066cc;
    }
    .skill-badge {
        background: #0066cc;
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        display: inline-block;
        margin: 3px;
        font-size: 12px;
    }
    .gap-skill {
        background: #ff6b6b;
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        display: inline-block;
        margin: 3px;
    }
    .recommended-skill {
        background: #51cf66;
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        display: inline-block;
        margin: 3px;
    }
</style>
""", unsafe_allow_html=True)



# Load and cache helpers
@st.cache_resource
def load_extractors():
    """Load NLP extractors"""
    return {
        'text_cleaner': TextCleaner(),
        'skills_extractor': SkillsExtractor(),
    }

extractors = load_extractors()

# Load job offers
@st.cache_data
def load_job_offers():
    """Load processed job offers"""
    processed_dir = Path("data/processed")
    processed_files = sorted(processed_dir.glob("processed_offers_*.json"))
    
    if processed_files:
        try:
            with open(processed_files[-1], 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"Could not load offers: {e}")
            return []
    return []

# Helper functions
def extract_cv_text_section(cv_text, section_names):
    """Extract specific section from CV"""
    for section in section_names:
        pattern = rf"{re.escape(section)}[:\s]*([^a-z]*?)(?=[A-Z][a-z]|\Z)"
        match = re.search(pattern, cv_text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    return ""

def extract_skills_from_cv(cv_text):
    """Extract skills from CV"""
    # Look for competencies sections
    competences_sections = [
        "Competences", "Compétences", "Skills", "Technical Skills",
        "Competences Techniques", "Compétences Techniques"
    ]
    
    competences_text = extract_cv_text_section(cv_text, competences_sections)
    
    if not competences_text:
        competences_text = cv_text[:2000]
    
    # Extract skills
    try:
        skills = extractors['skills_extractor'].extract_skills_weighted(
            title="",
            description=competences_text,
            profile="",
            technical_skills="",
            desired_skills=""
        )
        return skills
    except Exception as e:
        st.warning(f"Error extracting skills: {e}")
        return []

def extract_title_from_cv(cv_text):
    """Extract job title from CV"""
    patterns = [
        r"(?:Titre|Title|Position|Poste|Intitulé)[:\s]+([^\n]+)",
        r"(?:Job Title|Current Role)[:\s]+([^\n]+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, cv_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return "Developer"

def calculate_skill_gap(user_skills, job_offers):
    """Calculate skill gap based on job offers"""
    user_skill_names = {s['skill'].lower() for s in user_skills}
    
    # Collect all skills from job offers
    offer_skills = {}
    for offer in job_offers:
        for skill_obj in offer.get('skills_weighted', []):
            skill = skill_obj['skill'].lower()
            offer_skills[skill] = offer_skills.get(skill, 0) + 1
    
    # Calculate gap
    gap_skills = []
    for skill, count in sorted(offer_skills.items(), key=lambda x: x[1], reverse=True):
        if skill not in user_skill_names:
            gap_skills.append({
                'skill': skill,
                'frequency': count,
                'percentage': (count / len(job_offers)) * 100 if job_offers else 0
            })
    
    return gap_skills[:10]

def get_recommendations(user_title, user_skills, job_offers):
    """Generate recommendations based on user profile"""
    if not user_skills:
        return []
    
    user_skill_names = [s['skill'].lower() for s in user_skills]
    
    # Count skill frequency in market
    skill_frequency = {}
    for offer in job_offers:
        for skill_obj in offer.get('skills_weighted', []):
            skill = skill_obj['skill'].lower()
            skill_frequency[skill] = skill_frequency.get(skill, 0) + 1
    
    # Generate recommendations based on market demand
    recommendations = []
    for skill, freq in sorted(skill_frequency.items(), key=lambda x: x[1], reverse=True):
        if skill not in user_skill_names:
            score = freq / len(job_offers) if job_offers else 0
            recommendations.append({
                'skill': skill,
                'score': score,
                'frequency': freq
            })
    
    return recommendations[:10]

# Load job offers
job_offers = load_job_offers()

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Page", [
    "Dashboard",
    "CV Analyzer",
    "Job Market Analysis"
])

# Pages
if page == "Dashboard":
    st.title("CV Skills Analyzer")
    st.markdown("Analyze your CV, identify skill gaps, and get recommendations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>Analyze CV</h3>
            <p>Upload or paste your CV to extract skills and competencies</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>Skill Gap Analysis</h3>
            <p>Compare your skills with job market requirements</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>Get Recommendations</h3>
            <p>Receive personalized skill recommendations</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if job_offers:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Job Offers Analyzed", len(job_offers))
        
        with col2:
            all_skills = set()
            for offer in job_offers:
                for skill_obj in offer.get('skills_weighted', []):
                    all_skills.add(skill_obj['skill'])
            st.metric("Unique Skills", len(all_skills))
        
        with col3:
            st.metric("Data Loaded", "Ready")

elif page == "CV Analyzer":
    st.title("CV Analyzer")
    st.markdown("Paste or upload your CV to analyze your skills")
    
    if not job_offers:
        st.error("No job offers loaded. Run the scraping and NLP pipelines first.")
    else:
        # CV Input
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Upload CV")
            cv_file = st.file_uploader("Upload CV (txt, pdf)", type=['txt', 'pdf'])
            cv_text_upload = ""
            
            if cv_file:
                if cv_file.type == 'text/plain':
                    cv_text_upload = cv_file.read().decode('utf-8')
                else:
                    st.warning("PDF support requires additional setup. Use text format for now.")
        
        with col2:
            st.subheader("Or Paste CV Text")
            cv_text_paste = st.text_area(
                "Paste your CV content here",
                height=300,
                placeholder="Titre: Senior Developer\nCompetences: Python, Java, SQL...\n..."
            )
        
        cv_text = cv_text_upload or cv_text_paste
        
        if cv_text:
            st.markdown("---")
            st.subheader("Extracted Information")
            
            # Extract title and skills
            extracted_title = extract_title_from_cv(cv_text)
            extracted_skills = extract_skills_from_cv(cv_text)
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown("**Detected Job Title:**")
                st.write(extracted_title)
            
            with col2:
                st.markdown("**Extracted Skills:**")
                if extracted_skills:
                    skills_html = "".join([
                        f'<span class="skill-badge">{s["skill"]}</span>'
                        for s in extracted_skills
                    ])
                    st.markdown(skills_html, unsafe_allow_html=True)
                else:
                    st.warning("No skills detected. Try adding more detail to your CV.")
            
            if extracted_skills:
                st.markdown("---")
                
                # Calculate skill gap
                st.subheader("Skill Gap Analysis")
                gap_skills = calculate_skill_gap(extracted_skills, job_offers)
                
                if gap_skills:
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.markdown("**Missing Skills (Top 5):**")
                        for skill in gap_skills[:5]:
                            st.write(f"- {skill['skill']} ({skill['percentage']:.0f}% of jobs)")
                    
                    with col2:
                        st.markdown("**Skills to Add:**")
                        gap_html = "".join([
                            f'<span class="gap-skill">{s["skill"]}</span>'
                            for s in gap_skills[:5]
                        ])
                        st.markdown(gap_html, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Get recommendations
                st.subheader("Personalized Recommendations")
                recommendations = get_recommendations(extracted_title, extracted_skills, job_offers)
                
                if recommendations:
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.markdown("**Recommended Skills to Learn:**")
                        for rec in recommendations[:5]:
                            priority = "HIGH" if rec['score'] > 0.8 else "MEDIUM" if rec['score'] > 0.5 else "LOW"
                            st.write(f"- {rec['skill']} [{priority}]")
                    
                    with col2:
                        st.markdown("**Why These Skills?:**")
                        rec_html = "".join([
                            f'<span class="recommended-skill">{r["skill"]}</span>'
                            for r in recommendations[:5]
                        ])
                        st.markdown(rec_html, unsafe_allow_html=True)
                        st.write(f"*Based on analysis of {len(job_offers)} job offers*")

elif page == "Job Market Analysis":
    st.title("Job Market Analysis")
    
    if not job_offers:
        st.error("No job offers loaded.")
    else:
        st.markdown(f"**Total Job Offers Analyzed:** {len(job_offers)}")
        
        # Most demanded skills
        st.subheader("Most Demanded Skills")
        skill_frequency = {}
        for offer in job_offers:
            for skill_obj in offer.get('skills_weighted', []):
                skill = skill_obj['skill']
                skill_frequency[skill] = skill_frequency.get(skill, 0) + 1
        
        top_skills = sorted(skill_frequency.items(), key=lambda x: x[1], reverse=True)[:15]
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write("**Top 15 Skills:**")
            for skill, count in top_skills:
                st.write(f"- {skill}: {count} offers ({(count/len(job_offers)*100):.1f}%)")
        
        with col2:
            import pandas as pd
            df = pd.DataFrame(top_skills, columns=['Skill', 'Count'])
            st.bar_chart(df.set_index('Skill'))

