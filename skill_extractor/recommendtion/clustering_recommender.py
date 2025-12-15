"""
Clustering-based Skills Recommendation System
Recommends skills based on user profile and job market clusters
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import pickle

class SkillsRecommender:
    """
    Recommends skills to users based on:
    1. User's current skills
    2. Skill clusters in job market
    3. Career progression patterns
    """
    
    def __init__(self, n_clusters: int = 8):
        self.n_clusters = n_clusters
        self.skill_clusters = None
        self.cluster_models = {}
        self.skill_to_cluster = {}
        self.jobs_data = []
        self.vectorizer = None
        self.user_profiles = {}
    
    def load_jobs(self, jobs_file: str) -> None:
        """Load job data"""
        with open(jobs_file, 'r', encoding='utf-8') as f:
            self.jobs_data = json.load(f)
        print(f"✅ Loaded {len(self.jobs_data)} jobs")
    
    def build_skill_clusters(self) -> None:
        """Build skill clusters from job market data"""
        
        if not self.jobs_data:
            raise ValueError("Load jobs first!")
        
        # Collect all skills with their context
        skill_descriptions = {}
        skill_frequency = {}
        
        for job in self.jobs_data:
            for skill in job.get('extracted_skills', []):
                skill_lower = skill.lower()
                skill_frequency[skill_lower] = skill_frequency.get(skill_lower, 0) + 1
                
                # Get context (job title, description snippet)
                if skill_lower not in skill_descriptions:
                    skill_descriptions[skill_lower] = {
                        'skill': skill,
                        'contexts': [],
                        'categories': []
                    }
                
                skill_descriptions[skill_lower]['contexts'].append(job.get('title', ''))
        
        # Filter skills that appear in at least 2 jobs
        skills_to_cluster = [s for s, freq in skill_frequency.items() if freq >= 2]
        
        if len(skills_to_cluster) < self.n_clusters:
            print(f"⚠️  Only {len(skills_to_cluster)} unique skills, reducing clusters to {len(skills_to_cluster)}")
            self.n_clusters = max(3, len(skills_to_cluster) // 2)
        
        print(f"Clustering {len(skills_to_cluster)} skills into {self.n_clusters} clusters...")
        
        # Create skill vectors based on co-occurrence
        skill_co_occurrence = self._compute_skill_cooccurrence(skills_to_cluster)
        
        # Apply clustering
        if len(skills_to_cluster) >= self.n_clusters:
            kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(skill_co_occurrence)
            
            # Map skills to clusters
            for skill, cluster_id in zip(skills_to_cluster, labels):
                self.skill_to_cluster[skill] = int(cluster_id)
                
                if cluster_id not in self.cluster_models:
                    self.cluster_models[cluster_id] = []
                self.cluster_models[cluster_id].append(skill)
        else:
            # Simple assignment if not enough skills
            for i, skill in enumerate(skills_to_cluster):
                self.skill_to_cluster[skill] = i % self.n_clusters
        
        print(f"✅ Created {len(set(self.skill_to_cluster.values()))} skill clusters")
        self._print_cluster_summary()
    
    def _compute_skill_cooccurrence(self, skills: List[str]) -> np.ndarray:
        """Compute co-occurrence matrix for skills"""
        n_skills = len(skills)
        cooccurrence = np.zeros((n_skills, n_skills))
        
        skill_to_idx = {skill: i for i, skill in enumerate(skills)}
        
        for job in self.jobs_data:
            job_skills = [s.lower() for s in job.get('extracted_skills', [])]
            
            for i, skill1 in enumerate(job_skills):
                for skill2 in job_skills[i+1:]:
                    if skill1 in skill_to_idx and skill2 in skill_to_idx:
                        idx1 = skill_to_idx[skill1]
                        idx2 = skill_to_idx[skill2]
                        cooccurrence[idx1, idx2] += 1
                        cooccurrence[idx2, idx1] += 1
        
        # Normalize
        if cooccurrence.sum() > 0:
            cooccurrence = cooccurrence / cooccurrence.sum()
        else:
            # Fallback: use random vectors
            cooccurrence = np.random.rand(n_skills, n_skills)
        
        return cooccurrence
    
    def _print_cluster_summary(self) -> None:
        """Print summary of clusters"""
        print("\n📊 Skill Clusters:")
        for cluster_id, skills in sorted(self.cluster_models.items()):
            print(f"  Cluster {cluster_id}: {', '.join(skills[:5])}")
    
    def recommend_skills(self, user_skills: List[str], 
                        n_recommendations: int = 5) -> List[Tuple[str, float]]:
        """
        Recommend skills based on user's current skills
        
        Args:
            user_skills: List of user's current skills
            n_recommendations: Number of skills to recommend
        
        Returns:
            List of (skill, score) tuples
        """
        
        if not self.skill_to_cluster:
            raise ValueError("Build clusters first!")
        
        user_skills_lower = [s.lower() for s in user_skills]
        
        # Find clusters of user's skills
        user_clusters = set()
        for skill in user_skills_lower:
            if skill in self.skill_to_cluster:
                user_clusters.add(self.skill_to_cluster[skill])
        
        # Get skills from user's clusters
        cluster_skills = set()
        for cluster_id in user_clusters:
            cluster_skills.update(self.cluster_models.get(cluster_id, []))
        
        # Remove skills user already has
        candidate_skills = cluster_skills - set(user_skills_lower)
        
        # Score candidates by frequency and relevance
        scores = {}
        for skill in candidate_skills:
            # Count jobs requiring this skill
            job_count = sum(1 for job in self.jobs_data 
                          if skill in [s.lower() for s in job.get('extracted_skills', [])])
            
            # Count jobs that also require user skills
            combined_jobs = sum(1 for job in self.jobs_data 
                              if skill in [s.lower() for s in job.get('extracted_skills', [])]
                              and any(us in [s.lower() for s in job.get('extracted_skills', [])] 
                                     for us in user_skills_lower))
            
            # Score based on relevance and demand
            relevance_score = combined_jobs / max(job_count, 1) if job_count > 0 else 0
            demand_score = job_count / len(self.jobs_data)
            
            scores[skill] = 0.7 * relevance_score + 0.3 * demand_score
        
        # Sort and return top recommendations
        recommendations = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return recommendations[:n_recommendations]
    
    def get_complementary_skills(self, user_skills: List[str], 
                                n_recommendations: int = 5) -> Dict:
        """
        Get skills that commonly appear with user's skills in job postings
        """
        user_skills_lower = [s.lower() for s in user_skills]
        skill_co_occurrences = {}
        
        for job in self.jobs_data:
            job_skills = set(s.lower() for s in job.get('extracted_skills', []))
            
            # Check if job has user's skills
            if any(us in job_skills for us in user_skills_lower):
                # Count co-occurrences with user skills
                for skill in job_skills:
                    if skill not in user_skills_lower:
                        skill_co_occurrences[skill] = skill_co_occurrences.get(skill, 0) + 1
        
        # Sort by frequency
        recommendations = sorted(skill_co_occurrences.items(), 
                               key=lambda x: x[1], reverse=True)
        return recommendations[:n_recommendations]
    
    def get_job_recommendations(self, user_skills: List[str], 
                               top_n: int = 10) -> List[Dict]:
        """
        Recommend jobs based on user skills
        """
        user_skills_lower = [s.lower() for s in user_skills]
        scored_jobs = []
        
        for job in self.jobs_data:
            job_skills = set(s.lower() for s in job.get('extracted_skills', []))
            
            # Calculate match score
            if job_skills:
                matches = len(job_skills & set(user_skills_lower))
                match_score = matches / len(job_skills)
            else:
                match_score = 0
            
            scored_jobs.append({
                'job': job,
                'match_score': match_score,
                'matches': len(job_skills & set(user_skills_lower)),
                'missing_skills': list(job_skills - set(user_skills_lower))
            })
        
        # Sort by match score
        scored_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        
        return scored_jobs[:top_n]
    
    def save_model(self, model_file: str) -> None:
        """Save model to file"""
        model_data = {
            'skill_to_cluster': self.skill_to_cluster,
            'cluster_models': self.cluster_models,
            'n_clusters': self.n_clusters
        }
        with open(model_file, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"✅ Model saved to {model_file}")
    
    def load_model(self, model_file: str) -> None:
        """Load model from file"""
        with open(model_file, 'rb') as f:
            model_data = pickle.load(f)
        
        self.skill_to_cluster = model_data['skill_to_cluster']
        self.cluster_models = model_data['cluster_models']
        self.n_clusters = model_data['n_clusters']
        print(f"✅ Model loaded from {model_file}")


def train_recommender_system(jobs_file: str, model_output: str) -> SkillsRecommender:
    """
    Train the recommendation system
    """
    recommender = SkillsRecommender(n_clusters=8)
    recommender.load_jobs(jobs_file)
    recommender.build_skill_clusters()
    recommender.save_model(model_output)
    
    return recommender


if __name__ == "__main__":
    jobs_file = Path(__file__).parent.parent / "data" / "processed" / "job_offers_tech_filtered.json"
    model_file = Path(__file__).parent.parent / "models" / "recommender_model.pkl"
    
    if jobs_file.exists():
        train_recommender_system(str(jobs_file), str(model_file))
    else:
        print(f"❌ Jobs file not found: {jobs_file}")
