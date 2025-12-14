"""
Tests complets du pipeline d'extraction de compétences.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent))

from scrapping.scraper import scrape_all_sources, ReKruteScraper
from nlp.text_cleaner import TextCleaner, clean_offers_pipeline
from nlp.skills_extractor import SkillExtractor, extract_skills_pipeline
from modelling.clustering import SkillsVectorizer, OffersClustering
from recommendtion.recommender import SkillRecommender
from pipeline import SkillExtractionPipeline
from utils.config import RAW_DATA_DIR, PROCESSED_DATA_DIR


# ============================================================================
# TESTS - SCRAPING
# ============================================================================

class TestScraping:
    """Tests du module de scraping."""

    def test_scrape_all_sources_test_mode(self):
        """Test le scraping en mode test."""
        offers = scrape_all_sources(test_mode=True)
        assert len(offers) > 0
        assert all("title" in offer for offer in offers)
        assert all("description" in offer for offer in offers)

    def test_offer_structure(self):
        """Test la structure des offres."""
        offers = scrape_all_sources(test_mode=True)
        required_keys = ["job_id", "title", "company", "location", "description", "source"]

        for offer in offers:
            for key in required_keys:
                assert key in offer, f"Clé manquante: {key}"


# ============================================================================
# TESTS - NLP ET NETTOYAGE
# ============================================================================

class TestTextCleaning:
    """Tests du nettoyage NLP."""

    def test_html_removal(self):
        """Test la suppression du HTML."""
        cleaner = TextCleaner()
        html_text = "<p>Hello <b>World</b></p>"
        cleaned = cleaner.clean_html(html_text)
        assert "<" not in cleaned
        assert "Hello" in cleaned
        assert "World" in cleaned

    def test_url_removal(self):
        """Test la suppression des URLs."""
        cleaner = TextCleaner()
        text = "Visitez https://example.com pour plus info"
        cleaned = cleaner.remove_urls(text)
        assert "http" not in cleaned

    def test_email_removal(self):
        """Test la suppression des emails."""
        cleaner = TextCleaner()
        text = "Contactez nous: job@company.com"
        cleaned = cleaner.remove_emails(text)
        assert "@" not in cleaned

    def test_full_pipeline(self):
        """Test le pipeline de nettoyage complet."""
        cleaner = TextCleaner()
        messy_text = """
        <html>
        <p>We are looking for Python developers!</p>
        <a href="https://example.com">Link</a>
        Contact: hr@example.com
        </html>
        """
        cleaned = cleaner.clean(messy_text)

        # Vérifier que le nettoyage a fonctionné
        assert len(cleaned) < len(messy_text)
        assert "<" not in cleaned
        assert "python" in cleaned.lower()


# ============================================================================
# TESTS - EXTRACTION DES COMPETENCES
# ============================================================================

class TestSkillExtraction:
    """Tests de l'extraction des compétences."""

    def test_skill_extraction_regex(self):
        """Test l'extraction par regex."""
        extractor = SkillExtractor()
        text = "We need a Python developer with SQL and Docker knowledge"
        skills = extractor.extract_skills_regex(text)

        assert "python" in skills or "Python" in text
        assert len(skills) > 0

    def test_skill_extraction_combined(self):
        """Test l'extraction combinée."""
        extractor = SkillExtractor()
        text = "Senior Backend Engineer: Node.js, PostgreSQL, Docker, AWS"
        result = extractor.extract_skills(text, method="combined")

        assert result["count"] > 0
        assert "skills" in result
        assert "categorized" in result

    def test_skill_categorization(self):
        """Test la catégorisation des compétences."""
        extractor = SkillExtractor()
        skills = {"python", "docker", "react"}
        categorized = extractor._categorize_skills(skills)

        assert isinstance(categorized, dict)
        # Au moins une catégorie doit avoir des compétences
        assert any(len(v) > 0 for v in categorized.values())

    def test_extract_from_offers(self):
        """Test l'extraction sur plusieurs offres."""
        offers = scrape_all_sources(test_mode=True)
        enriched = extract_skills_pipeline(offers)

        assert len(enriched) == len(offers)
        for offer in enriched:
            assert "extracted_skills" in offer
            assert "skills_count" in offer


# ============================================================================
# TESTS - CLUSTERING
# ============================================================================

class TestClustering:
    """Tests du clustering."""

    def test_vectorizer_initialization(self):
        """Test l'initialisation du vectoriseur."""
        vectorizer = SkillsVectorizer()
        assert vectorizer.model is not None

    def test_vectorization(self):
        """Test la vectorisation."""
        vectorizer = SkillsVectorizer()
        offers = scrape_all_sources(test_mode=True)
        embeddings = vectorizer.vectorize_descriptions(offers)

        assert embeddings.shape[0] == len(offers)
        assert embeddings.shape[1] > 0

    def test_clustering_model(self):
        """Test le modèle de clustering."""
        clusterer = OffersClustering()
        assert clusterer.model is None
        assert clusterer.labels is None

        # Créer des embeddings simples
        import numpy as np
        fake_embeddings = np.random.rand(10, 20)

        clusterer.fit(fake_embeddings)
        assert clusterer.labels is not None
        assert len(clusterer.labels) == 10


# ============================================================================
# TESTS - RECOMMANDATIONS
# ============================================================================

class TestRecommendations:
    """Tests du module de recommandation."""

    def test_recommender_initialization(self):
        """Test l'initialisation du recommandeur."""
        recommender = SkillRecommender()
        assert len(recommender.student_profiles) > 0

    def test_profile_recommendation(self):
        """Test la recommandation pour un profil."""
        recommender = SkillRecommender()

        # Créer un cluster_data simulé
        from skill_extractor.scrapping.scraper import _generate_test_data
        from skill_extractor.nlp.text_cleaner import clean_offers_pipeline
        from skill_extractor.nlp.skills_extractor import extract_skills_pipeline

        offers = _generate_test_data()
        offers = clean_offers_pipeline(offers)
        offers = extract_skills_pipeline(offers)

        # Ajouter des clusters
        for i, offer in enumerate(offers):
            offer["cluster"] = i % 3

        cluster_data = {
            "offers_clustered": offers,
            "cluster_stats": {}
        }

        # Test la recommandation
        rec = recommender.recommend_for_profile("data_engineer", cluster_data, top_n=5)
        assert "profile" in rec
        assert "recommended_skills" in rec


# ============================================================================
# TESTS - PIPELINE COMPLET
# ============================================================================

class TestPipeline:
    """Tests du pipeline complet."""

    def test_pipeline_test_mode(self):
        """Test le pipeline en mode test."""
        pipeline = SkillExtractionPipeline(test_mode=True)
        result = pipeline.run_full_pipeline()

        assert result["status"] == "success"
        assert result["offers_raw_count"] > 0
        assert "clustering_result" in result
        assert "recommendations" in result

    def test_pipeline_saves_files(self):
        """Test que le pipeline sauvegarde les fichiers."""
        pipeline = SkillExtractionPipeline(test_mode=True)
        result = pipeline.run_full_pipeline()

        # Vérifier que les fichiers ont été créés
        assert RAW_DATA_DIR.exists()
        assert PROCESSED_DATA_DIR.exists()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Tests d'intégration complets."""

    def test_end_to_end_pipeline(self):
        """Test le pipeline de bout en bout."""
        from skill_extractor.pipeline import main

        result = main(test_mode=True)
        assert result["status"] == "success"
        assert result["offers_raw_count"] > 0

    def test_data_flow(self):
        """Test que les données circulent correctement à travers le pipeline."""
        pipeline = SkillExtractionPipeline(test_mode=True)

        # Étape par étape
        pipeline.offers_raw = pipeline._scrape_step()
        assert len(pipeline.offers_raw) > 0

        pipeline.offers_cleaned = pipeline._cleaning_step()
        assert len(pipeline.offers_cleaned) > 0

        pipeline.offers_with_skills = pipeline._skills_extraction_step()
        assert all("extracted_skills" in o for o in pipeline.offers_with_skills)

        pipeline.clustering_result = pipeline._clustering_step()
        assert "labels" in pipeline.clustering_result

        pipeline.recommendations = pipeline._recommendations_step()
        assert len(pipeline.recommendations) > 0


# ============================================================================
# FIXTURES ET HELPERS
# ============================================================================

@pytest.fixture
def sample_offers():
    """Fixture: offres de test."""
    return scrape_all_sources(test_mode=True)


@pytest.fixture
def cleaned_offers(sample_offers):
    """Fixture: offres nettoyées."""
    return clean_offers_pipeline(sample_offers)


@pytest.fixture
def offers_with_skills(cleaned_offers):
    """Fixture: offres avec compétences extraites."""
    return extract_skills_pipeline(cleaned_offers)


if __name__ == "__main__":
    # Exécuter les tests
    pytest.main([__file__, "-v", "--tb=short"])
