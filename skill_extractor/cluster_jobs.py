#!/usr/bin/env python3
"""
Cluster jobs by skill similarity - creates multiple meaningful clusters
Groups similar job offers together based on their skill requirements
"""

import json
from pathlib import Path
from collections import defaultdict, Counter
import sys

script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

def load_processed_offers():
    """Load processed job offers"""
    processed_dir = script_dir / "data" / "processed"
    processed_files = sorted(processed_dir.glob("processed_offers_*.json"))
    
    if processed_files:
        with open(processed_files[-1], 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def extract_job_skills(offer):
    """Extract skills from offer"""
    skills = []
    skills_weighted = offer.get('skills_weighted', [])
    
    for skill_obj in skills_weighted:
        if isinstance(skill_obj, dict):
            skill = skill_obj.get('skill', '').lower()
        else:
            skill = str(skill_obj).lower()
        if skill:
            skills.append(skill)
    
    return set(skills)

def calculate_similarity(skills1, skills2):
    """Calculate Jaccard similarity between two skill sets"""
    if not skills1 or not skills2:
        return 0
    
    intersection = len(skills1 & skills2)
    union = len(skills1 | skills2)
    
    return intersection / union if union > 0 else 0

def cluster_jobs_by_skills(offers, min_similarity=0.3):
    """
    Cluster jobs by skill similarity
    Uses hierarchical clustering approach
    """
    if not offers:
        return []
    
    # Extract skills for each offer
    offer_skills = []
    for offer in offers:
        skills = extract_job_skills(offer)
        offer_skills.append(skills)
    
    # Initialize clusters - each job starts in its own cluster
    clusters = {i: [i] for i in range(len(offers))}
    cluster_id = len(offers)
    
    # Merge similar clusters
    merged = True
    iterations = 0
    max_iterations = 100
    
    while merged and iterations < max_iterations:
        merged = False
        iterations += 1
        cluster_ids = list(clusters.keys())
        
        for i in range(len(cluster_ids)):
            for j in range(i + 1, len(cluster_ids)):
                c1_id = cluster_ids[i]
                c2_id = cluster_ids[j]
                
                if c1_id not in clusters or c2_id not in clusters:
                    continue
                
                # Calculate average similarity between clusters
                c1_jobs = clusters[c1_id]
                c2_jobs = clusters[c2_id]
                
                similarities = []
                for idx1 in c1_jobs:
                    for idx2 in c2_jobs:
                        sim = calculate_similarity(offer_skills[idx1], offer_skills[idx2])
                        similarities.append(sim)
                
                avg_similarity = sum(similarities) / len(similarities) if similarities else 0
                
                # Merge if similarity is high enough
                if avg_similarity >= min_similarity:
                    clusters[c1_id].extend(clusters[c2_id])
                    del clusters[c2_id]
                    merged = True
                    break
            
            if merged:
                break
    
    # Compact cluster IDs
    final_clusters = {}
    for new_id, (old_id, job_indices) in enumerate(sorted(clusters.items())):
        final_clusters[new_id] = job_indices
    
    return final_clusters

def assign_clusters_to_offers(offers, clusters):
    """Assign cluster IDs to each offer"""
    offers_with_clusters = []
    
    for offer in offers:
        offer_copy = offer.copy()
        offer_copy['cluster'] = -1
        offers_with_clusters.append(offer_copy)
    
    for cluster_id, job_indices in clusters.items():
        for idx in job_indices:
            if idx < len(offers_with_clusters):
                offers_with_clusters[idx]['cluster'] = cluster_id
    
    return offers_with_clusters

def analyze_clusters(offers_with_clusters):
    """Generate cluster analysis"""
    cluster_info = defaultdict(lambda: {'jobs': [], 'skills': Counter(), 'titles': []})
    
    for offer in offers_with_clusters:
        cluster_id = offer.get('cluster', -1)
        
        cluster_info[cluster_id]['jobs'].append(offer.get('title', 'Unknown'))
        cluster_info[cluster_id]['titles'].append(offer.get('title', 'Unknown'))
        
        # Count skills
        skills_weighted = offer.get('skills_weighted', [])
        for skill_obj in skills_weighted:
            skill = skill_obj.get('skill', '') if isinstance(skill_obj, dict) else str(skill_obj)
            if skill:
                cluster_info[cluster_id]['skills'][skill] += 1
    
    return cluster_info

def main():
    print("\n" + "="*70)
    print("CLUSTERING JOBS BY SKILL SIMILARITY")
    print("="*70)
    
    # Load offers
    offers = load_processed_offers()
    print(f"\n✓ Loaded {len(offers)} job offers")
    
    if not offers:
        print("❌ No offers found!")
        return
    
    # Cluster jobs
    print("\nClustering jobs by skill similarity...")
    clusters = cluster_jobs_by_skills(offers, min_similarity=0.25)
    
    print(f"✓ Created {len(clusters)} clusters")
    
    # Assign clusters to offers
    offers_with_clusters = assign_clusters_to_offers(offers, clusters)
    
    # Analyze clusters
    cluster_info = analyze_clusters(offers_with_clusters)
    
    # Print cluster details
    print("\n" + "-"*70)
    print("CLUSTER DETAILS")
    print("-"*70)
    
    for cluster_id in sorted(cluster_info.keys()):
        if cluster_id == -1:
            continue
        
        info = cluster_info[cluster_id]
        top_skills = info['skills'].most_common(5)
        
        print(f"\nCluster {cluster_id}:")
        print(f"  Size: {len(info['jobs'])} jobs")
        print(f"  Top skills: {', '.join([s[0] for s in top_skills])}")
        print(f"  Sample jobs: {', '.join(info['titles'][:3])}")
    
    # Save clustered offers
    output_path = script_dir / "data" / "processed" / "clustered_offers.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(offers_with_clusters, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Saved clustered offers to {output_path.name}")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
