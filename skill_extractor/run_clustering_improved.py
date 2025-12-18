#!/usr/bin/env python3
"""
Improved Clustering Pipeline - Creates distinct job clusters
Uses HDBSCAN for better clustering with multiple distinct clusters
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import logging
from collections import Counter
import numpy as np

# Setup paths
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
DATA_DIR = project_root / "data" / "processed"
DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import AgglomerativeClustering
    import hdbscan
except ImportError as e:
    logger.error(f"Missing dependency: {e}")
    sys.exit(1)


def load_processed_offers():
    """Load processed job offers with extracted skills"""
    processed_files = sorted(DATA_DIR.glob("processed_offers_*.json"))
    
    if not processed_files:
        logger.error("No processed offers found!")
        return []
    
    latest_file = processed_files[-1]
    logger.info(f"Loading: {latest_file.name}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_skill_based_vectors(offers):
    """Create vectors based on skills presence"""
    logger.info("Creating skill-based vectors...")
    
    # Collect all unique skills
    all_skills = set()
    for offer in offers:
        skills_weighted = offer.get('skills_weighted', [])
        for skill_obj in skills_weighted:
            skill = skill_obj.get('skill', '') if isinstance(skill_obj, dict) else str(skill_obj)
            if skill:
                all_skills.add(skill)
    
    skill_list = sorted(list(all_skills))
    logger.info(f"Total unique skills: {len(skill_list)}")
    
    # Create binary matrix
    vectors = []
    for offer in offers:
        vector = np.zeros(len(skill_list))
        skills_weighted = offer.get('skills_weighted', [])
        
        for skill_obj in skills_weighted:
            skill = skill_obj.get('skill', '') if isinstance(skill_obj, dict) else str(skill_obj)
            if skill and skill in skill_list:
                idx = skill_list.index(skill)
                vector[idx] = 1
        
        vectors.append(vector)
    
    return np.array(vectors), skill_list


def cluster_with_hdbscan(vectors):
    """Cluster using HDBSCAN with tuned parameters"""
    logger.info("Clustering with HDBSCAN...")
    
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=2,
        min_samples=1,
        cluster_selection_epsilon=0.5,
        cluster_selection_method='eom'
    )
    
    labels = clusterer.fit_predict(vectors)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    
    logger.info(f"Generated {n_clusters} clusters (+ noise points)")
    
    return labels


def cluster_with_agglomerative(vectors, n_clusters=5):
    """Cluster using Agglomerative Clustering for guaranteed clusters"""
    logger.info(f"Clustering with Agglomerative Clustering ({n_clusters} clusters)...")
    
    clusterer = AgglomerativeClustering(
        n_clusters=n_clusters,
        linkage='ward',
        metric='euclidean'
    )
    
    labels = clusterer.fit_predict(vectors)
    
    logger.info(f"Generated {n_clusters} clusters")
    
    return labels


def assign_clusters_to_offers(offers, labels):
    """Add cluster assignments to offers"""
    for idx, offer in enumerate(offers):
        offer['cluster'] = int(labels[idx])


def compute_cluster_stats(offers, skill_list):
    """Compute detailed statistics for each cluster"""
    clusters = {}
    
    for offer in offers:
        cluster_id = offer.get('cluster', -1)
        
        if cluster_id not in clusters:
            clusters[cluster_id] = {
                'offers': [],
                'skills': [],
                'titles': []
            }
        
        clusters[cluster_id]['offers'].append(offer)
        clusters[cluster_id]['titles'].append(offer.get('title', 'Unknown'))
        
        # Collect skills
        skills_weighted = offer.get('skills_weighted', [])
        for skill_obj in skills_weighted:
            skill = skill_obj.get('skill', '') if isinstance(skill_obj, dict) else str(skill_obj)
            if skill:
                clusters[cluster_id]['skills'].append(skill)
    
    # Compute summaries
    stats = {}
    for cluster_id, data in clusters.items():
        top_skills = Counter(data['skills']).most_common(10)
        top_titles = Counter(data['titles']).most_common(5)
        
        stats[cluster_id] = {
            'size': len(data['offers']),
            'top_skills': [{'skill': s[0], 'count': s[1]} for s in top_skills],
            'top_titles': [{'title': t[0], 'count': t[1]} for t in top_titles],
            'description': f"Cluster {cluster_id}: {top_titles[0][0] if top_titles else 'Mixed'}"
        }
    
    return stats


def save_clustered_offers(offers, stats):
    """Save clustered offers and statistics"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save offers with clusters
    output_file = DATA_DIR / f"offers_clustered_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(offers, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved clustered offers: {output_file.name}")
    
    # Save cluster statistics
    stats_file = DATA_DIR / f"cluster_stats_{timestamp}.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved cluster stats: {stats_file.name}")
    
    return output_file, stats_file


def main():
    """Main pipeline"""
    print("\n" + "="*70)
    print("IMPROVED CLUSTERING PIPELINE")
    print("="*70)
    
    # Load data
    logger.info("\n[1] Loading processed offers...")
    offers = load_processed_offers()
    
    if not offers:
        logger.error("No offers loaded!")
        return
    
    logger.info(f"✓ Loaded {len(offers)} offers")
    
    # Create vectors
    logger.info("\n[2] Creating skill-based vectors...")
    vectors, skill_list = create_skill_based_vectors(offers)
    logger.info(f"✓ Vector shape: {vectors.shape}")
    
    # Try HDBSCAN first
    logger.info("\n[3] Clustering (HDBSCAN)...")
    labels = cluster_with_hdbscan(vectors)
    
    # If too few clusters, use Agglomerative Clustering
    n_unique = len(set(labels)) - (1 if -1 in labels else 0)
    if n_unique < 3:
        logger.info(f"HDBSCAN produced only {n_unique} clusters, trying Agglomerative...")
        labels = cluster_with_agglomerative(vectors, n_clusters=5)
    
    # Assign clusters
    logger.info("\n[4] Assigning clusters to offers...")
    assign_clusters_to_offers(offers, labels)
    
    # Compute statistics
    logger.info("\n[5] Computing cluster statistics...")
    stats = compute_cluster_stats(offers, skill_list)
    
    # Display summary
    print("\n" + "="*70)
    print("CLUSTERING RESULTS")
    print("="*70)
    
    for cluster_id in sorted(stats.keys()):
        cluster_info = stats[cluster_id]
        print(f"\nCluster {cluster_id}:")
        print(f"  Size: {cluster_info['size']} offers")
        print(f"  Top titles: {', '.join([t['title'] for t in cluster_info['top_titles'][:2]])}")
        print(f"  Top skills: {', '.join([s['skill'] for s in cluster_info['top_skills'][:5]])}")
    
    # Save
    logger.info("\n[6] Saving results...")
    offers_file, stats_file = save_clustered_offers(offers, stats)
    
    print("\n" + "="*70)
    print(f"✓ Clustering complete!")
    print(f"  Offers: {offers_file.name}")
    print(f"  Stats: {stats_file.name}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
