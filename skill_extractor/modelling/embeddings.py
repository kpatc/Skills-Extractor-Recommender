"""
Module pour générer des embeddings avec différents modèles.
Supporte: Gemini API, sentence-transformers, TF-IDF
"""

import logging
import numpy as np
from typing import List, Optional
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

logger = logging.getLogger(__name__)


class GeminiEmbedder:
    """Génère des embeddings avec l'API Google Gemini."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialise l'embedder Gemini."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("Clé API Gemini non trouvée (GEMINI_API_KEY)")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.genai = genai
            logger.info("✓ Client Gemini API initialisé")
        except ImportError:
            raise ImportError("pip install google-generativeai")
        except Exception as e:
            raise RuntimeError(f"Erreur Gemini: {e}")

    def encode(self, texts: List[str]) -> np.ndarray:
        """Génère les embeddings."""
        logger.info(f"Embeddings Gemini pour {len(texts)} textes...")
        embeddings = []
        
        for i, text in enumerate(texts):
            if (i + 1) % 10 == 0:
                logger.info(f"  {i + 1}/{len(texts)} traités...")
            
            try:
                response = self.genai.embed_content(
                    model="models/embedding-001",
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(response['embedding'])
            except Exception as e:
                logger.warning(f"Erreur texte {i}: {e}")
                embeddings.append([0] * 768)
        
        result = np.array(embeddings, dtype=np.float32)
        logger.info(f"✓ {result.shape}")
        return result


class SentenceTransformerEmbedder:
    """Utilise sentence-transformers."""

    def __init__(self):
        """Initialise le modèle."""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Chargement sentence-transformers...")
            self.model = SentenceTransformer(
                "sentence-transformers/multilingual-MiniLM-L12-v2"
            )
            logger.info("✓ sentence-transformers chargé")
        except Exception as e:
            raise ImportError(f"sentence-transformers: {e}")

    def encode(self, texts: List[str]) -> np.ndarray:
        """Génère les embeddings."""
        logger.info(f"sentence-transformers pour {len(texts)} textes...")
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.astype(np.float32)


class TFIDFEmbedder:
    """Utilise TF-IDF."""

    def __init__(self):
        """Initialise TF-IDF."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.model = TfidfVectorizer(max_features=1000)
        self.is_fitted = False

    def encode(self, texts: List[str]) -> np.ndarray:
        """Génère les embeddings."""
        logger.info(f"TF-IDF pour {len(texts)} textes...")
        
        if not self.is_fitted:
            embeddings = self.model.fit_transform(texts).toarray()
            self.is_fitted = True
        else:
            embeddings = self.model.transform(texts).toarray()
        
        return embeddings.astype(np.float32)


class HybridEmbedder:
    """Embedder hybride avec fallback automatique - BERT prioritaire."""

    def __init__(self):
        """Initialise avec fallback automatique: sentence-transformers > Gemini > TF-IDF"""
        self.embedder = None
        self.method = None
        
        # PRIORITÉ 1: sentence-transformers (BERT) - Meilleur rapport performance/vitesse
        try:
            self.embedder = SentenceTransformerEmbedder()
            self.method = "sentence_transformers"
            logger.info("✓ Embedder: sentence-transformers (BERT) - ACTIVÉ")
            return
        except Exception as e:
            logger.warning(f"sentence-transformers non disponible: {e}")
        
        # PRIORITÉ 2: Gemini (si API key disponible)
        if os.getenv("GEMINI_API_KEY"):
            try:
                self.embedder = GeminiEmbedder()
                self.method = "gemini"
                logger.info("✓ Embedder: Gemini API")
                return
            except Exception as e:
                logger.warning(f"Gemini non disponible: {e}")
        
        # FALLBACK: TF-IDF (dernier recours)
        try:
            self.embedder = TFIDFEmbedder()
            self.method = "tfidf"
            logger.warning("⚠️  Fallback: TF-IDF (performance limitée)")
            return
        except Exception as e:
            logger.error(f"Aucun embedder disponible: {e}")
            raise

    def encode(self, texts: List[str]) -> np.ndarray:
        """Génère les embeddings."""
        if not self.embedder:
            raise RuntimeError("Aucun embedder")
        return self.embedder.encode(texts)

    def get_method(self) -> str:
        """Retourne la méthode utilisée."""
        return self.method
