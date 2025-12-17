#!/usr/bin/env python3
"""
Clustering Pipeline - Groups jobs by skill similarity and creates job clusters
Output: Adds cluster IDs to each offer
"""

import json
import sys
from pathlib import Path
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

# Setup
DATA_DIR = Path(__file__).parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"

def load_processed_offers():
    """Load processed offers"""
    processed_files = sorted(PROCESSED_DIR.glob("processed_offers_*.json"))
    if not processed_files:
        print("❌ No processed offers found!")
        return None
    
    with open(processed_files[-1], 'r', encoding='utf-8') as f:
        return json.load(f)

def cluster_offers_by_skills(offers, n_clusters=5):
    """Cluster offers based on their skill profiles"""
    print(f"\n🎯 Clustering {len(offers)} offers into {n_clusters} clusters...")
    
    # Create skill vectors for each offer
    skill_vectors = []
    for offer in offers:
        skills = []
        skills_weighted = offer.get('skills_weighted', [])
        for skill_obj in skills_weighted:
            skill = skill_obj.get('skill', '') if isinstance(skill_obj, dict) else str(skill_obj)
            if skill:
                skills.append(skill)
        skill_vectors.append(" ".join(skills))
    
    if not any(skill_vectors):
        print("⚠️  No skills found, using job titles instead")
        skill_vectors = [offer.get('title', '') for offer in offers]
    
    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
    X = vectorizer.fit_transform(skill_vectors)
    
    # Cluster
    if X.shape[0] < n_clusters:
        n_clusters = max(1, X.shape[0] - 1)
        print(f"⚠️  Adjusted clusters to {n_clusters} (fewer offers than clusters)")
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X)
    
    # Add cluster to each offer
    for i, offer in enumerate(offers):
        offer['cluster'] = int(clusters[i])
    
    print(f"✓ Clustering complete: {n_clusters} clusters created")
    return offers, n_clusters, kmeans

def analyze_clusters(offers):
    """Analyze and display cluster information"""
    print("\n📊 CLUSTER ANALYSIS")
    print("="*70)
    
    cluster_info = {}
    for offer in offers:
        cluster = offer.get('cluster', -1)
        if cluster not in cluster_info:
            cluster_info[cluster] = {
                'offers': [],
                'skills': [],
                'titles': []
            }
        cluster_info[cluster]['offers'].append(offer)
        cluster_info[cluster]['titles'].append(offer.get('title', 'Unknown'))
        
        for skill_obj in offer.get('skills_weighted', []):
            skill = skill_obj.get('skill', '') if isinstance(skill_obj, dict) else str(skill_obj)
            if skill:
                cluster_info[cluster]['skills'].append(skill)
    
    for cluster_id in sorted(cluster_info.keys()):
        info = cluster_info[cluster_id]
        top_skills = Counter(info['skills']).most_common(5)
        
        print(f"\n🔹 CLUSTER {cluster_id}")
        print(f"   Size: {len(info['offers'])} offers")
        print(f"   Top Skills: {', '.join([s[0] for s in top_skills])}")
        print(f"   Sample Titles: {', '.join(set(info['titles'][:3]))}")
    
    print("\n" + "="*70)

def save_clustered_offers(offers):
    """Save offers with cluster assignments"""
    timestamp = Path(__file__).parent.absolute()
    import datetime
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    output_file = EMBEDDINGS_DIR / f"offers_clustered_{timestamp_str}.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(offers, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved to: {output_file}")
    return output_file

def main():
    print("="*70)
    print("CLUSTERING PIPELINE - Group Jobs by Skill Similarity")
    print("="*70)
    
    # Load
    offers = load_processed_offers()
    if not offers:
        return 1
    
    print(f"✓ Loaded {len(offers)} offers")
    
    # Cluster
    offers, n_clusters, model = cluster_offers_by_skills(offers, n_clusters=5)
    
    # Analyze
    analyze_clusters(offers)
    
    # Save
    save_clustered_offers(offers)
    
    print("\n✓ Clustering pipeline complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
