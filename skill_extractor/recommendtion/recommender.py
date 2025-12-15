"""
Recommendation Module - Recommandations personnalisées basées sur les embeddings
Utilise la similarité cosinus pour matcher les profils aux offres
"""

import json
import logging
from typing import List, Dict
from pathlib import Path
import pickle
import numpy as np
from modelling.embedding import SkillEmbedder

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """Moteur de recommandation basé sur les embeddings"""
    
    def __init__(self, embeddings_file: str = None):
        """
        Initialize le moteur de recommandation
        
        Args:
            embeddings_file: Chemin au fichier des embeddings
        """
        self.embedder = SkillEmbedder()
        self.offer_embeddings = {}
        self.offers_data = {}
        
        if embeddings_file:
            self.load_embeddings(embeddings_file)
    
    def load_embeddings(self, embeddings_file: str):
        """Charge les embeddings depuis un fichier"""
        logger.info(f"Chargement des embeddings: {embeddings_file}")
        with open(embeddings_file, 'rb') as f:
            self.offer_embeddings = pickle.load(f)
        logger.info(f"✅ {len(self.offer_embeddings)} embeddings chargés")
    
    def load_offers_data(self, json_file: str):
        """Charge les données des offres"""
        logger.info(f"Chargement des offres: {json_file}")
        with open(json_file, 'r', encoding='utf-8') as f:
            offers = json.load(f)
        
        for offer in offers:
            offer_id = offer.get('job_id', '')
            self.offers_data[offer_id] = offer
        
        logger.info(f"✅ {len(self.offers_data)} offres chargées")
    
    def recommend_for_user(self, user_skills: List[str], 
                           user_preferences: str = "",
                           top_k: int = 10) -> List[Dict]:
        """
        Recommande des offres pour un utilisateur
        
        Args:
            user_skills: Compétences de l'utilisateur
            user_preferences: Préférences textuelles
            top_k: Nombre de recommandations
            
        Returns:
            Liste des offres recommandées avec scores
        """
        # Créer l'embedding du profil utilisateur
        user_embedding = self.embedder.embed_user_profile(user_skills, user_preferences)
        
        # Trouver les offres similaires
        similar_offers = self.embedder.find_similar_offers(
            user_embedding,
            self.offer_embeddings,
            top_k=top_k
        )
        
        # Enrichir avec les données des offres
        recommendations = []
        for offer_id, similarity_score in similar_offers:
            offer_data = self.offers_data.get(offer_id, {})
            
            recommendation = {
                'job_id': offer_id,
                'title': offer_data.get('title', ''),
                'company': offer_data.get('company', ''),
                'location': offer_data.get('location', ''),
                'source': offer_data.get('source', ''),
                'skills': offer_data.get('skills', []),
                'num_skills': offer_data.get('num_skills', 0),
                'similarity_score': float(similarity_score),
                'match_percentage': round(similarity_score * 100, 2)
            }
            
            recommendations.append(recommendation)
        
        return recommendations


# Alias for compatibility
SkillRecommender = RecommendationEngine


def generate_recommendations_pipeline(clustering_result: Dict) -> Dict:
    """Fonction de recommandation pipeline - compatible avec l'ancien code"""
    logger.info("Génération des recommandations...")
    return {"status": "success", "recommendations": []}


def generate_sample_recommendations(offers_with_skills: List[Dict], n_recommendations: int = 5) -> Dict:
    """
    Génère des recommandations simples basées sur les compétences extraites
    """
    logger.info(f"Génération de {n_recommendations} recommandations par offre...")
    
    recommendations = {
        "total_offers": len(offers_with_skills),
        "recommendations_by_offer": []
    }
    
    # Pour chaque offre, trouver les offres similaires
    for i, offer in enumerate(offers_with_skills[:10]):  # Limite à 10 pour la demo
        offer_skills = set(offer.get('skills', []))
        
        similar_offers = []
        for j, other_offer in enumerate(offers_with_skills):
            if i != j:
                other_skills = set(other_offer.get('skills', []))
                # Calcul de similarité Jaccard
                if offer_skills or other_skills:
                    similarity = len(offer_skills & other_skills) / len(offer_skills | other_skills)
                    if similarity > 0:
                        similar_offers.append({
                            "job_id": other_offer.get('job_id', ''),
                            "title": other_offer.get('title', ''),
                            "similarity": round(similarity, 3),
                            "common_skills": list(offer_skills & other_skills)
                        })
        
        # Tri et limitation
        similar_offers.sort(key=lambda x: x['similarity'], reverse=True)
        similar_offers = similar_offers[:n_recommendations]
        
        recommendations["recommendations_by_offer"].append({
            "offer_id": offer.get('job_id', ''),
            "offer_title": offer.get('title', ''),
            "offer_skills_count": offer.get('num_skills', 0),
            "similar_offers": similar_offers
        })
    
    return recommendations
    
    def recommend_for_user(self, user_skills: List[str], 
                           user_preferences: str = "",
                           top_k: int = 10) -> List[Dict]:
        """
        Recommande des offres pour un utilisateur
        
        Args:
            user_skills: Compétences de l'utilisateur
            user_preferences: Préférences textuelles
            top_k: Nombre de recommandations
            
        Returns:
            Liste des offres recommandées avec scores
        """
        # Créer l'embedding du profil utilisateur
        user_embedding = self.embedder.embed_user_profile(user_skills, user_preferences)
        
        # Trouver les offres similaires
        similar_offers = self.embedder.find_similar_offers(
            user_embedding,
            self.offer_embeddings,
            top_k=top_k
        )
        
        # Enrichir avec les données des offres
        recommendations = []
        for offer_id, similarity_score in similar_offers:
            offer_data = self.offers_data.get(offer_id, {})
            
            recommendation = {
                'job_id': offer_id,
                'title': offer_data.get('title', ''),
                'company': offer_data.get('company', ''),
                'location': offer_data.get('location', ''),
                'source': offer_data.get('source', ''),
                'skills': offer_data.get('skills', []),
                'num_skills': offer_data.get('num_skills', 0),
                'similarity_score': float(similarity_score),
                'match_percentage': round(similarity_score * 100, 2)
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def recommend_for_group(self, group_skills: List[str], 
                            top_k: int = 10) -> List[Dict]:
        """
        Recommande des offres pour un groupe/équipe
        
        Args:
            group_skills: Compétences du groupe combinées
            top_k: Nombre de recommandations
            
        Returns:
            Liste des offres recommandées
        """
        return self.recommend_for_user(group_skills, top_k=top_k)
    
    def get_skill_statistics(self) -> Dict:
        """Retourne les statistiques des compétences des offres"""
        all_skills = {}
        
        for offer in self.offers_data.values():
            for skill in offer.get('skills', []):
                if skill not in all_skills:
                    all_skills[skill] = {'count': 0, 'offers': []}
                all_skills[skill]['count'] += 1
                all_skills[skill]['offers'].append(offer.get('job_id', ''))
        
        # Trier par fréquence
        sorted_skills = sorted(all_skills.items(), key=lambda x: x[1]['count'], reverse=True)
        
        return {
            'total_unique_skills': len(all_skills),
            'top_skills': [{'skill': s[0], 'frequency': s[1]['count']} for s in sorted_skills[:20]],
            'all_skills': all_skills
        }
    
    def get_offer_details(self, offer_id: str) -> Dict:
        """Retourne les détails d'une offre"""
        return self.offers_data.get(offer_id, {})


def generate_sample_recommendations(offers_json: str, output_dir: str = None) -> Dict:
    """
    Génère des recommandations d'exemple
    
    Args:
        offers_json: Chemin au fichier JSON des offres
        output_dir: Répertoire de sortie
        
    Returns:
        Dict avec les statistiques
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / 'data' / 'recommendations'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialiser le moteur
    engine = RecommendationEngine()
    engine.load_offers_data(offers_json)
    
    # Charger les embeddings si disponibles
    embeddings_file = Path(__file__).parent.parent / 'data' / 'embeddings' / 'offer_embeddings.pkl'
    if embeddings_file.exists():
        engine.load_embeddings(str(embeddings_file))
    
    # Générer des recommandations d'exemple
    sample_profiles = [
        {
            'profile': 'Full Stack Developer',
            'skills': ['python', 'javascript', 'react', 'docker', 'aws'],
            'preferences': 'Télétravail, startup, équipe agile'
        },
        {
            'profile': 'DevOps Engineer',
            'skills': ['kubernetes', 'docker', 'terraform', 'jenkins', 'aws'],
            'preferences': 'Infrastructure cloud, CI/CD'
        },
        {
            'profile': 'Data Scientist',
            'skills': ['python', 'tensorflow', 'pytorch', 'pandas', 'machine learning'],
            'preferences': 'IA, machine learning, innovation'
        }
    ]
    
    recommendations_list = []
    
    for profile in sample_profiles:
        logger.info(f"\nGénération recommandations pour: {profile['profile']}")
        
        recs = engine.recommend_for_user(
            profile['skills'],
            profile['preferences'],
            top_k=10
        )
        
        profile_rec = {
            'profile': profile['profile'],
            'user_skills': profile['skills'],
            'preferences': profile['preferences'],
            'recommendations': recs
        }
        
        recommendations_list.append(profile_rec)
        logger.info(f"✅ {len(recs)} offres recommandées")
    
    # Sauvegarder les recommandations
    output_file = output_dir / 'sample_recommendations.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(recommendations_list, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n💾 Recommandations sauvegardées: {output_file}")
    
    # Statistiques des compétences
    skill_stats = engine.get_skill_statistics()
    stats_file = output_dir / 'skill_statistics.json'
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(skill_stats, f, ensure_ascii=False, indent=2)
    
    logger.info(f"💾 Statistiques sauvegardées: {stats_file}")
    
    return {
        'status': 'success',
        'profiles_processed': len(recommendations_list),
        'recommendations_file': str(output_file),
        'statistics_file': str(stats_file),
        'skill_statistics': skill_stats
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    offers_file = Path(__file__).parent.parent / 'data' / 'processed' / 'job_offers_essential.json'
    result = generate_sample_recommendations(str(offers_file))
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
