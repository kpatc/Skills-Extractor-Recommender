#!/usr/bin/env python3
"""
Simple Streamlit Dashboard - Minimal dependencies, Maximum functionality
Features:
- Top demanded skills
- Morocco vs International comparison
- Visualization by cluster
- Personalized recommendations
"""

import streamlit as st
import json
import re
from pathlib import Path
from datetime import datetime
import sys
from collections import Counter
import os

# Setup path
script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir))

# Page config
st.set_page_config(
    page_title="Skills Market Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
    .metric-card h3 {
        margin: 0;
        font-size: 24px;
    }
    .metric-card p {
        margin: 5px 0 0 0;
        font-size: 14px;
        opacity: 0.9;
    }
    .skill-badge {
        background: #0066cc;
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        display: inline-block;
        margin: 4px 4px;
        font-size: 12px;
        font-weight: 500;
    }
    .gap-skill {
        background: #ff6b6b;
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        display: inline-block;
        margin: 4px 4px;
        font-size: 12px;
    }
    .recommended-skill {
        background: #51cf66;
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        display: inline-block;
        margin: 4px 4px;
        font-size: 12px;
    }
    .cluster-box {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ====== DATA LOADING ======

@st.cache_data
def load_processed_offers():
    """Load processed job offers from JSON"""
    # Try multiple possible paths
    possible_paths = [
        script_dir / "data" / "processed",
        Path("/home/josh/ProjectTD/skill_extractor/data/processed"),
        Path.cwd() / "data" / "processed",
        Path.cwd().parent / "data" / "processed",
    ]
    
    for processed_dir in possible_paths:
        if processed_dir.exists():
            processed_files = sorted(processed_dir.glob("processed_offers_*.json"))
            if processed_files:
                try:
                    with open(processed_files[-1], 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    continue
    
    return []

@st.cache_data
def load_modelling_results():
    """Load clustering and embeddings results"""
    # Try both locations
    possible_dirs = [
        script_dir / "data" / "processed",
        Path("/home/josh/ProjectTD/skill_extractor/data/processed"),
    ]
    
    cluster_stats = {}
    for data_dir in possible_dirs:
        if data_dir.exists():
            stats_files = sorted(data_dir.glob("cluster_stats_*.json"))
            if stats_files:
                try:
                    with open(stats_files[-1], 'r', encoding='utf-8') as f:
                        cluster_stats = json.load(f)
                    break
                except:
                    continue
    
    return cluster_stats

@st.cache_data
def load_clustered_offers():
    """Load offers with cluster assignments"""
    possible_dirs = [
        script_dir / "data" / "processed",
        Path("/home/josh/ProjectTD/skill_extractor/data/processed"),
    ]
    
    for data_dir in possible_dirs:
        if data_dir.exists():
            clustered_files = sorted(data_dir.glob("offers_clustered_*.json"))
            if clustered_files:
                try:
                    with open(clustered_files[-1], 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    continue
    
    # Fallback to processed offers
    return load_processed_offers()

# ====== DATA PROCESSING ======

def get_top_skills(offers, limit=20):
    """Extract top skills from offers"""
    all_skills = []
    for offer in offers:
        skills_weighted = offer.get('skills_weighted', [])
        for skill_obj in skills_weighted:
            if isinstance(skill_obj, dict):
                skill = skill_obj.get('skill', '')
            else:
                skill = str(skill_obj)
            if skill:
                all_skills.append(skill)
    
    skill_counts = Counter(all_skills)
    return skill_counts.most_common(limit)

def categorize_by_location(offers):
    """Categorize offers by location (Morocco vs International)"""
    morocco_locations = ['maroc', 'casablanca', 'rabat', 'fez', 'marrakech', 'agadir', 'meknes', 'tangier']
    
    morocco = []
    international = []
    
    for offer in offers:
        location = offer.get('location', '').lower()
        if any(loc in location for loc in morocco_locations):
            morocco.append(offer)
        else:
            international.append(offer)
    
    return morocco, international

def get_skills_by_region(offers):
    """Get top skills by region"""
    morocco, international = categorize_by_location(offers)
    
    # Top skills in Morocco
    morocco_skills = []
    for offer in morocco:
        skills_weighted = offer.get('skills_weighted', [])
        for skill_obj in skills_weighted:
            skill = skill_obj.get('skill', '') if isinstance(skill_obj, dict) else str(skill_obj)
            if skill:
                morocco_skills.append(skill)
    
    # Top skills International
    intl_skills = []
    for offer in international:
        skills_weighted = offer.get('skills_weighted', [])
        for skill_obj in skills_weighted:
            skill = skill_obj.get('skill', '') if isinstance(skill_obj, dict) else str(skill_obj)
            if skill:
                intl_skills.append(skill)
    
    return (
        Counter(morocco_skills).most_common(10),
        Counter(intl_skills).most_common(10)
    )

def get_cluster_info(offers, clusters):
    """Get information about clusters and map offers to clusters"""
    cluster_skills = {}
    cluster_titles = {}
    cluster_offers = {}
    
    # Get cluster structure from clustering results
    if clusters and 'clusters' in clusters:
        cluster_structure = clusters['clusters']
        for cluster_id, skills in cluster_structure.items():
            cluster_id = int(cluster_id)
            cluster_skills[cluster_id] = skills if isinstance(skills, list) else list(skills)
            cluster_titles[cluster_id] = []
            cluster_offers[cluster_id] = []
    
    # Map offers to clusters based on their skills
    for idx, offer in enumerate(offers):
        best_cluster = -1
        best_score = 0
        
        # Get offer skills
        offer_skills = []
        skills_weighted = offer.get('skills_weighted', [])
        for skill_obj in skills_weighted:
            skill = skill_obj.get('skill', '') if isinstance(skill_obj, dict) else str(skill_obj)
            if skill:
                offer_skills.append(skill.lower())
        
        # Find best matching cluster
        for cluster_id, cluster_skill_list in cluster_skills.items():
            cluster_skill_set = {s.lower() for s in cluster_skill_list}
            offer_skill_set = set(offer_skills)
            
            # Calculate intersection
            intersection = len(cluster_skill_set & offer_skill_set)
            if intersection > best_score:
                best_score = intersection
                best_cluster = cluster_id
        
        # Assign to cluster
        if best_cluster != -1:
            title = offer.get('title', 'Unknown')
            cluster_titles[best_cluster].append(title)
            cluster_offers[best_cluster].append(offer)
        else:
            # Create a new cluster for unmatched offers
            if -1 not in cluster_skills:
                cluster_skills[-1] = []
                cluster_titles[-1] = []
                cluster_offers[-1] = []
            cluster_offers[-1].append(offer)
            cluster_titles[-1].append(offer.get('title', 'Unknown'))
    
    return cluster_skills, cluster_titles, cluster_offers

def calculate_skill_gap(user_skills, all_offers):
    """Calculate which skills are most demanded but missing"""
    user_skill_set = {s.lower() for s in user_skills}
    all_skills = get_top_skills(all_offers, limit=50)
    
    gap = []
    for skill, count in all_skills:
        if skill.lower() not in user_skill_set:
            gap.append((skill, count))
    
    return gap[:10]

def get_recommendations(user_skills, user_title, all_offers, cluster_skills=None):
    """Generate skill recommendations based on demand and clusters"""
    user_skill_set = {s.lower() for s in user_skills}
    
    # Get top skills
    top_skills = get_top_skills(all_offers, limit=50)
    
    # Find skills that user doesn't have but are in high demand
    recommendations = []
    for skill, frequency in top_skills:
        if skill.lower() not in user_skill_set:
            # Score based on frequency
            score = frequency / len(all_offers) if all_offers else 0
            
            # Check if skill is in cluster skills for additional weighting
            in_clusters = 0
            if cluster_skills:
                for cluster_id, skills in cluster_skills.items():
                    if cluster_id != -1 and any(skill.lower() == s.lower() for s in skills):
                        in_clusters += 1
            
            priority = 'CRITICAL' if score > 0.4 else 'HIGH' if score > 0.25 else 'MEDIUM' if score > 0.15 else 'LOW'
            
            recommendations.append({
                'skill': skill,
                'frequency': frequency,
                'score': score,
                'in_clusters': in_clusters,
                'priority': priority
            })
    
    # Sort by priority and score
    priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    recommendations.sort(
        key=lambda x: (priority_order.get(x['priority'], 4), -x['score']),
        reverse=False
    )
    
    return recommendations[:15]

# ====== MAIN APP ======

# Load data
offers = load_processed_offers()
clusters = load_modelling_results()

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select Page",
    ["Dashboard", "Morocco vs International", "Clusters Analysis", "CV Analyzer"]
)

# ====== PAGE 1: DASHBOARD ======
if page == "Dashboard":
    st.title("📊 Skills Market Dashboard")
    st.markdown("Real-time analysis of job market demands")
    
    if not offers:
        st.error("No job offers loaded. Please run the NLP pipeline first: `python run_nlp.py`")
    else:
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{len(offers)}</h3>
                <p>Job Offers</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            all_skills_unique = set()
            for offer in offers:
                for skill_obj in offer.get('skills_weighted', []):
                    skill = skill_obj.get('skill', '') if isinstance(skill_obj, dict) else str(skill_obj)
                    if skill:
                        all_skills_unique.add(skill)
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>{len(all_skills_unique)}</h3>
                <p>Unique Skills</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            morocco_count, intl_count = categorize_by_location(offers)
            st.markdown(f"""
            <div class="metric-card">
                <h3>{len(morocco_count)}</h3>
                <p>Morocco Offers</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{len(intl_count)}</h3>
                <p>International</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Top Skills - Improved visualization
        st.subheader("Top 15 Most Demanded Skills")
        top_skills = get_top_skills(offers, 15)
        
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            st.write("**Ranking:**")
            for i, (skill, count) in enumerate(top_skills, 1):
                percentage = (count / len(offers)) * 100
                st.write(f"{i:2d}. **{skill}**")
                st.write(f"    {count} offers ({percentage:.1f}%)")
        
        with col2:
            st.write("**Demand Level:**")
            for skill, count in top_skills:
                percentage = (count / len(offers)) * 100
                if percentage >= 50:
                    level = "🔴 Critical"
                elif percentage >= 30:
                    level = "🟠 High"
                elif percentage >= 15:
                    level = "🟡 Medium"
                else:
                    level = "🟢 Low"
                st.write(f"{skill}: {level}")
        
        with col3:
            st.write("**Visual:**")
            max_count = top_skills[0][1] if top_skills else 1
            for skill, count in top_skills:
                bar_length = int(count / max_count * 20)
                bar = "█" * bar_length + "░" * (20 - bar_length)
                st.write(f"{bar} {count}")

# ====== PAGE 2: MOROCCO vs INTERNATIONAL ======
elif page == "Morocco vs International":
    st.title("🌍 Market Comparison: Morocco vs International")
    
    if not offers:
        st.error("No data available")
    else:
        morocco_skills, intl_skills = get_skills_by_region(offers)
        morocco_offers, intl_offers = categorize_by_location(offers)
        
        # Overview
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{len(morocco_offers)}</h3>
                <p>Offers in Morocco</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.subheader("Top Skills in Morocco")
            for i, (skill, count) in enumerate(morocco_skills, 1):
                st.write(f"{i}. {skill} ({count} offers)")
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{len(intl_offers)}</h3>
                <p>International Offers</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.subheader("Top Skills Internationally")
            for i, (skill, count) in enumerate(intl_skills, 1):
                st.write(f"{i}. {skill} ({count} offers)")
        
        st.markdown("---")
        st.subheader("Skills Unique to Each Market")
        
        col1, col2 = st.columns(2)
        
        morocco_skill_set = {s[0].lower() for s in morocco_skills}
        intl_skill_set = {s[0].lower() for s in intl_skills}
        
        with col1:
            st.write("**Morocco-Only Skills:**")
            unique_morocco = morocco_skill_set - intl_skill_set
            if unique_morocco:
                for skill in sorted(list(unique_morocco))[:10]:
                    st.write(f"- {skill}")
            else:
                st.write("No unique skills")
        
        with col2:
            st.write("**International-Only Skills:**")
            unique_intl = intl_skill_set - morocco_skill_set
            if unique_intl:
                for skill in sorted(list(unique_intl))[:10]:
                    st.write(f"- {skill}")
            else:
                st.write("No unique skills")

# ====== PAGE 3: CLUSTERS ANALYSIS ======
elif page == "Clusters Analysis":
    st.title("🎯 Job Clusters Analysis")
    st.markdown("Jobs grouped by skill similarity - Each cluster represents a job family")
    
    clustered_offers = load_clustered_offers()
    cluster_stats = load_modelling_results()
    
    if not clustered_offers or not cluster_stats:
        st.error("No clustering data available. Please run clustering first.")
    else:
        # Get cluster info
        cluster_info = {}
        for offer in clustered_offers:
            cluster_id = offer.get('cluster', -1)
            if cluster_id not in cluster_info:
                cluster_info[cluster_id] = {
                    'offers': [],
                    'skills': [],
                    'titles': []
                }
            cluster_info[cluster_id]['offers'].append(offer)
            
            # Collect skills
            skills_weighted = offer.get('skills_weighted', [])
            for skill_obj in skills_weighted:
                skill = skill_obj.get('skill', '') if isinstance(skill_obj, dict) else str(skill_obj)
                if skill:
                    cluster_info[cluster_id]['skills'].append(skill)
            
            # Collect titles
            title = offer.get('title', '')
            if title:
                cluster_info[cluster_id]['titles'].append(title)
        
        # Overview metrics
        valid_clusters = {k: v for k, v in cluster_info.items() if k != -1}
        
        st.subheader("Overview")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{len(valid_clusters)}</h3>
                <p>Job Clusters</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            total_offers_clustered = sum(len(v['offers']) for v in valid_clusters.values())
            st.markdown(f"""
            <div class="metric-card">
                <h3>{total_offers_clustered}</h3>
                <p>Clustered Offers</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            avg_offers = total_offers_clustered / max(len(valid_clusters), 1)
            st.markdown(f"""
            <div class="metric-card">
                <h3>{avg_offers:.1f}</h3>
                <p>Avg. Offers/Cluster</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Display each cluster
        for cluster_id in sorted(valid_clusters.keys()):
            cluster_data = cluster_info[cluster_id]
            offers_in_cluster = cluster_data['offers']
            skills_in_cluster = cluster_data['skills']
            titles_in_cluster = cluster_data['titles']
            
            # Get top skills
            skill_counter = Counter(skills_in_cluster)
            top_skills = skill_counter.most_common(5)
            
            # Get top titles
            title_counter = Counter(titles_in_cluster)
            top_titles = title_counter.most_common(3)
            
            # Determine cluster theme
            if top_skills:
                theme = ", ".join([s[0] for s in top_skills])
            else:
                theme = "Mixed"
            
            st.markdown(f"""
            <div class="cluster-box">
                <h4>Cluster {cluster_id}: {theme}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.write(f"**Size:** {len(offers_in_cluster)} offers")
                st.write(f"**Unique Skills:** {len(skill_counter)}")
                st.write("**Top Job Titles:**")
                for title, count in top_titles:
                    st.write(f"- {title[:50]}... ({count})")
            
            with col2:
                st.write("**Top Skills Required:**")
                for skill, count in top_skills:
                    pct = (count / len(offers_in_cluster)) * 100 if offers_in_cluster else 0
                    st.write(f"- {skill}: {count} offers ({pct:.0f}%)")
            
            st.markdown("---")
            
            # Show sample job offers from this cluster
            with st.expander(f"See {len(offers_in_cluster)} job offers in this cluster"):
                for offer in offers_in_cluster[:5]:
                    st.write(f"**{offer.get('title', 'Unknown')}**")
                    location = offer.get('location', 'Unknown')
                    st.caption(f"📍 {location}")
                    if offer.get('skills_weighted'):
                        skills_str = ", ".join([s.get('skill', '') if isinstance(s, dict) else str(s) for s in offer['skills_weighted'][:5]])
                        st.write(f"Skills: {skills_str}...")
                    st.divider()
            
            st.markdown("")  # Spacing

# ====== PAGE 4: CV ANALYZER ======
elif page == "CV Analyzer":
    st.title("📄 CV Skill Analyzer")
    st.markdown("Analyze your skills and get personalized recommendations")
    
    if not offers:
        st.error("No job data available")
    else:
        st.subheader("Your Profile")
        col1, col2 = st.columns(2)
        
        with col1:
            user_title = st.text_input(
                "Job Title",
                value="Software Developer",
                placeholder="e.g., Senior Python Developer",
                key="title_input"
            )
        
        with col2:
            st.write("")  # Spacer
            st.write("")  # Spacer
        
        st.subheader("Your Skills")
        user_skills_text = st.text_area(
            "Enter your skills (comma-separated)",
            value="Python, JavaScript, React, Docker",
            placeholder="e.g., Python, Java, SQL, Docker...",
            height=100,
            key="skills_input"
        )
        
        user_skills = [s.strip() for s in user_skills_text.split(',') if s.strip()]
        
        if user_skills:
            st.markdown("---")
            
            # Display extracted skills
            st.subheader("Extracted Skills")
            skills_html = "".join([
                f'<span class="skill-badge">{skill}</span>'
                for skill in user_skills
            ])
            st.markdown(skills_html, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Skill Gap Analysis
            st.subheader("📊 Skill Gap Analysis")
            gap_skills = calculate_skill_gap(user_skills, offers)
            
            if gap_skills:
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.write("**Most Demanded Missing Skills:**")
                    for skill, freq in gap_skills[:5]:
                        pct = (freq / len(offers)) * 100
                        st.write(f"- {skill} ({pct:.1f}% of jobs)")
                
                with col2:
                    st.write("**Recommended to Learn:**")
                    gap_html = "".join([
                        f'<span class="gap-skill">{s[0]}</span>'
                        for s in gap_skills[:5]
                    ])
                    st.markdown(gap_html, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Personalized Recommendations
            st.subheader("🎯 Personalized Recommendations")
            recommendations = get_recommendations(user_skills, user_title, offers)
            
            if recommendations:
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.write("**Skills to Add (Priority Order):**")
                    for i, rec in enumerate(recommendations[:8], 1):
                        clusters_text = f" (in {rec['in_clusters']} clusters)" if rec['in_clusters'] > 0 else ""
                        st.write(f"{i}. **{rec['skill']}** [{rec['priority']}]{clusters_text}")
                        st.write(f"   {rec['frequency']} offers ({rec['score']*100:.1f}%)")
                
                with col2:
                    st.write("**Why These Skills?**")
                    rec_html = "".join([
                        f'<span class="recommended-skill">{r["skill"]}</span>'
                        for r in recommendations[:8]
                    ])
                    st.markdown(rec_html, unsafe_allow_html=True)
                    st.write(f"\n*Based on analysis of {len(offers)} job offers*")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>Skills Market Dashboard</strong> • Real-time Job Market Analytics</p>
    <p>Last updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """</p>
</div>
""", unsafe_allow_html=True)
