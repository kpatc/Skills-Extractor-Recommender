"""
Embedding Module - Vectorisation des compétences et descriptions
Utilise Google Gemini API pour créer des embeddings haute qualité
"""

import json
import logging
from typing import List, Dict
from pathlib import Path
import numpy as np
import pickle
import os
import time
from dotenv import load_dotenv
import google.generativeai as genai

# Charger les variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)

class SkillEmbedder:
    """Crée des embeddings pour les compétences et offres d'emploi avec Gemini"""
    
    def __init__(self, api_key: str = None, max_retries: int = 3, retry_delay: float = 2.0):
        """
        Initialize embedder with Google Gemini API
        
        Args:
            api_key: Clé API Google (défaut: GEMINI_API_KEY dans .env)
            max_retries: Nombre de tentatives en cas d'erreur
            retry_delay: Délai entre les tentatives (en secondes)
        """
        # Récupérer la clé API
        if api_key is None:
            api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY non trouvée dans .env")
        
        # Configurer Gemini
        genai.configure(api_key=api_key)
        logger.info("✅ Google Gemini API configuré")
        
        self.skill_embeddings = {}
        self.offer_embeddings = {}
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def _embed_with_retry(self, text: str, task_type: str = "SEMANTIC_SIMILARITY") -> np.ndarray:
        """
        Crée un embedding avec retry en cas de quota
        
        Args:
            text: Texte à embedder
            task_type: Type de tâche pour Gemini
            
        Returns:
            Vecteur d'embedding
        """
        for attempt in range(self.max_retries):
            try:
                response = genai.embed_content(
                    model="models/embedding-001",
                    content=text,
                    task_type=task_type
                )
                return np.array(response['embedding'])
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Quota dépassé, attente {wait_time}s avant retry...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Erreur quota après {self.max_retries} tentatives")
                        # Retourner un embedding zéro en dernier ressort
                        return np.zeros(768)
                else:
                    logger.error(f"Erreur embedding: {e}")
                    return np.zeros(768)
        
        return np.zeros(768)
        
    def embed_skills(self, skills: List[str]) -> Dict[str, np.ndarray]:
        """
        Crée des embeddings pour une liste de compétences
        
        Args:
            skills: Liste des compétences
            
        Returns:
            Dict {skill: embedding_vector}
        """
        embeddings = {}
        for skill in skills:
            if skill not in self.skill_embeddings:
                embedding = self._embed_with_retry(skill)
                self.skill_embeddings[skill] = embedding
                embeddings[skill] = embedding
        
        return embeddings
    
    def embed_offers(self, offers: List[Dict]) -> Dict[str, np.ndarray]:
        """
        Crée des embeddings pour les offres d'emploi
        
        Args:
            offers: Liste des offres avec leurs compétences
            
        Returns:
            Dict {offer_id: embedding_vector}
        """
        embeddings = {}
        
        for i, offer in enumerate(offers):
            offer_id = offer.get('job_id', '')
            title = offer.get('title', '')
            skills = offer.get('skills', [])
            
            if offer_id not in self.offer_embeddings:
                # Créer un texte composite: titre + compétences
                text = f"{title}. Compétences: {', '.join(skills)}"
                embedding = self._embed_with_retry(text)
                self.offer_embeddings[offer_id] = embedding
                embeddings[offer_id] = embedding
            
            if (i + 1) % 5 == 0:
                logger.info(f"   {i + 1}/{len(offers)} offres embedées")
        
        return embeddings
    
    def embed_user_profile(self, user_skills: List[str], user_preferences: str = "") -> np.ndarray:
        """
        Crée un embedding pour un profil utilisateur
        
        Args:
            user_skills: Compétences de l'utilisateur
            user_preferences: Préférences textuelles
            
        Returns:
            Vecteur d'embedding pour le profil
        """
        text = f"{' '.join(user_skills)}. Préférences: {user_preferences}"
        return self._embed_with_retry(text)
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calcule la similarité cosinus entre deux embeddings
        
        Args:
            embedding1, embedding2: Vecteurs d'embedding
            
        Returns:
            Score de similarité (0-1)
        """
        from sklearn.metrics.pairwise import cosine_similarity
        similarity = cosine_similarity([embedding1], [embedding2])[0][0]
        # Normaliser de [-1, 1] à [0, 1]
        return max(0, (similarity + 1) / 2)
    
    def find_similar_offers(self, user_embedding: np.ndarray, 
                           offer_embeddings: Dict[str, np.ndarray], 
                           top_k: int = 10) -> List[tuple]:
        """
        Trouve les offres les plus similaires à un profil utilisateur
        
        Args:
            user_embedding: Embedding du profil utilisateur
            offer_embeddings: Dict des embeddings des offres
            top_k: Nombre de résultats à retourner
            
        Returns:
            Liste de tuples (offer_id, similarité_score)
        """
        similarities = []
        
        for offer_id, offer_embedding in offer_embeddings.items():
            score = self.compute_similarity(user_embedding, offer_embedding)
            similarities.append((offer_id, score))
        
        # Trier par similarité décroissante
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]


def create_embeddings_from_file(input_json: str, output_dir: str = None) -> Dict:
    """
    Crée des embeddings à partir du fichier JSON des offres
    
    Args:
        input_json: Chemin du fichier JSON avec les offres
        output_dir: Répertoire de sortie (défaut: data/embeddings)
        
    Returns:
        Dict avec les statistiques
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / 'data' / 'embeddings'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Chargement des offres depuis: {input_json}")
    with open(input_json, 'r', encoding='utf-8') as f:
        offers = json.load(f)
    
    logger.info(f"✅ {len(offers)} offres chargées")
    
    # Initialiser l'embedder
    embedder = SkillEmbedder()
    
    # Extraire toutes les compétences uniques
    all_skills = set()
    for offer in offers:
        all_skills.update(offer.get('skills', []))
    
    logger.info(f"Création d'embeddings pour {len(all_skills)} compétences uniques...")
    embedder.embed_skills(list(all_skills))
    
    # Créer les embeddings des offres
    logger.info(f"Création d'embeddings pour {len(offers)} offres...")
    offer_embeddings = embedder.embed_offers(offers)
    
    # Sauvegarder les embeddings
    embeddings_file = output_dir / 'offer_embeddings.pkl'
    with open(embeddings_file, 'wb') as f:
        pickle.dump(offer_embeddings, f)
    
    logger.info(f"✅ Embeddings sauvegardés: {embeddings_file}")
    
    # Sauvegarder les métadonnées
    metadata = {
        'total_offers': len(offers),
        'total_skills': len(all_skills),
        'embedding_dimension': 384,
        'model': 'all-MiniLM-L6-v2'
    }
    
    metadata_file = output_dir / 'metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"✅ Métadonnées sauvegardées: {metadata_file}")
    
    return {
        'status': 'success',
        'total_offers': len(offers),
        'total_skills': len(all_skills),
        'embeddings_file': str(embeddings_file),
        'metadata_file': str(metadata_file)
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    input_file = Path(__file__).parent.parent / 'data' / 'processed' / 'job_offers_essential.json'
    result = create_embeddings_from_file(str(input_file))
    
    print(json.dumps(result, indent=2))
