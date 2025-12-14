"""
Module de scraping pour la collecte des offres d'emploi.
Supporte : ReKrute, Emploi.ma, Indeed, LinkedIn (light).
"""

import requests
import csv
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin

from ..utils.config import SCRAPING_CONFIG, RAW_DATA_DIR

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobOfferScraper:
    """Classe de base pour le scraping des offres d'emploi."""

    def __init__(self, source_name: str):
        self.source_name = source_name
        self.session = requests.Session()
        self.session.headers.update(SCRAPING_CONFIG.get("headers", {}))
        self.offers = []

    def fetch_page(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Récupère une page avec gestion des erreurs et retry."""
        for attempt in range(SCRAPING_CONFIG.get("max_retries", 3)):
            try:
                response = self.session.get(
                    url,
                    timeout=SCRAPING_CONFIG.get("timeout", 10),
                    **kwargs
                )
                response.raise_for_status()
                time.sleep(SCRAPING_CONFIG.get("delay_between_requests", 2))
                return response
            except requests.RequestException as e:
                logger.warning(
                    f"Tentative {attempt + 1} échouée pour {url}: {e}"
                )
                if attempt == SCRAPING_CONFIG.get("max_retries", 3) - 1:
                    logger.error(f"Impossible de récupérer {url}")
                    return None
                time.sleep(2 ** attempt)

    def parse_page(self, html: str) -> List[Dict]:
        """À surcharger dans les classes enfants."""
        raise NotImplementedError

    def scrape(self, urls: List[str], **kwargs) -> List[Dict]:
        """Scrape une liste d'URLs."""
        all_offers = []
        for url in urls:
            logger.info(f"Scraping {url}")
            response = self.fetch_page(url, **kwargs)
            if response:
                offers = self.parse_page(response.text)
                all_offers.extend(offers)
        return all_offers

    def save_to_csv(self, filename: str = "job_offers.csv"):
        """Sauvegarde les offres en CSV."""
        if not self.offers:
            logger.warning("Aucune offre à sauvegarder")
            return

        filepath = RAW_DATA_DIR / filename
        keys = self.offers[0].keys()

        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(self.offers)
            logger.info(f"Sauvegardé {len(self.offers)} offres dans {filepath}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")


class ReKruteScraper(JobOfferScraper):
    """Scraper pour ReKrute.com (Maroc)."""

    def __init__(self):
        super().__init__("rekrute")
        self.base_url = "https://www.rekrute.com"

    def parse_page(self, html: str) -> List[Dict]:
        """Parse une page ReKrute."""
        soup = BeautifulSoup(html, "html.parser")
        offers = []

        # Structure spécifique à ReKrute (à adapter selon le HTML réel)
        job_cards = soup.find_all("div", class_="job-card")

        for card in job_cards:
            try:
                title = card.find("h2", class_="job-title")
                company = card.find("span", class_="company-name")
                location = card.find("span", class_="location")
                description = card.find("div", class_="job-description")

                if title and company:
                    offer = {
                        "job_id": f"{self.source_name}_{len(offers)}",
                        "title": title.get_text(strip=True),
                        "company": company.get_text(strip=True),
                        "location": location.get_text(strip=True) if location else "Non spécifié",
                        "description": description.get_text(strip=True) if description else "",
                        "source": self.source_name,
                        "scrape_date": datetime.now().isoformat(),
                    }
                    offers.append(offer)
            except Exception as e:
                logger.warning(f"Erreur parsing offre: {e}")

        return offers


class EmploiMaScraper(JobOfferScraper):
    """Scraper pour Emploi.ma (Maroc)."""

    def __init__(self):
        super().__init__("emploi_ma")
        self.base_url = "https://emploi.ma"

    def parse_page(self, html: str) -> List[Dict]:
        """Parse une page Emploi.ma."""
        soup = BeautifulSoup(html, "html.parser")
        offers = []

        # Structure spécifique à Emploi.ma (à adapter)
        job_items = soup.find_all("li", class_="job-item")

        for item in job_items:
            try:
                title = item.find("a", class_="job-title")
                company = item.find("span", class_="company")
                description = item.find("div", class_="job-desc")

                if title:
                    offer = {
                        "job_id": f"{self.source_name}_{len(offers)}",
                        "title": title.get_text(strip=True),
                        "company": company.get_text(strip=True) if company else "Non spécifié",
                        "location": "Maroc",
                        "description": description.get_text(strip=True) if description else "",
                        "source": self.source_name,
                        "scrape_date": datetime.now().isoformat(),
                    }
                    offers.append(offer)
            except Exception as e:
                logger.warning(f"Erreur parsing offre: {e}")

        return offers


class LinkedInJobsScraper(JobOfferScraper):
    """Scraper pour LinkedIn Jobs (approche légère ou dataset)."""

    def __init__(self):
        super().__init__("linkedin")
        self.base_url = "https://www.linkedin.com/jobs"

    def parse_page(self, html: str) -> List[Dict]:
        """Parse une page LinkedIn."""
        soup = BeautifulSoup(html, "html.parser")
        offers = []

        # Note: LinkedIn a des protections anti-scraping.
        # Recommandé d'utiliser un dataset existant ou Selenium
        job_listings = soup.find_all("div", class_="base-card")

        for listing in job_listings:
            try:
                title = listing.find("h3", class_="base-search-card__title")
                company = listing.find("h4", class_="base-search-card__subtitle")
                location = listing.find("span", class_="job-search-card__location")

                if title and company:
                    offer = {
                        "job_id": f"{self.source_name}_{len(offers)}",
                        "title": title.get_text(strip=True),
                        "company": company.get_text(strip=True),
                        "location": location.get_text(strip=True) if location else "Non spécifié",
                        "description": "",  # LinkedIn demande connexion pour description complète
                        "source": self.source_name,
                        "scrape_date": datetime.now().isoformat(),
                    }
                    offers.append(offer)
            except Exception as e:
                logger.warning(f"Erreur parsing offre: {e}")

        return offers


def scrape_all_sources(test_mode=False) -> List[Dict]:
    """
    Scrape les offres de toutes les sources configurées.
    
    Args:
        test_mode: Si True, utilise des données de test
    
    Returns:
        Liste de dictionnaires contenant les offres
    """
    all_offers = []

    if test_mode:
        logger.info("Mode test activé - utilisation de données simulées")
        all_offers = _generate_test_data()
    else:
        # ReKrute
        logger.info("Scraping ReKrute...")
        rekrute = ReKruteScraper()
        rekrute.offers = rekrute.scrape(["https://www.rekrute.com"])
        all_offers.extend(rekrute.offers)

        # Emploi.ma
        logger.info("Scraping Emploi.ma...")
        emploi = EmploiMaScraper()
        emploi.offers = emploi.scrape(["https://emploi.ma"])
        all_offers.extend(emploi.offers)

        # LinkedIn
        logger.info("Scraping LinkedIn...")
        linkedin = LinkedInJobsScraper()
        linkedin.offers = linkedin.scrape(["https://www.linkedin.com/jobs"])
        all_offers.extend(linkedin.offers)

    # Suppression des doublons (basée sur titre + entreprise)
    unique_offers = {}
    for offer in all_offers:
        key = f"{offer['title']}_{offer['company']}"
        if key not in unique_offers:
            unique_offers[key] = offer

    return list(unique_offers.values())


def _generate_test_data() -> List[Dict]:
    """Génère des données de test pour développement."""
    return [
        {
            "job_id": "test_001",
            "title": "Data Engineer",
            "company": "TechCorp",
            "location": "Casablanca",
            "description": "We are looking for a Data Engineer with Python, SQL, and Spark experience. Must have AWS knowledge.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_002",
            "title": "Backend Developer",
            "company": "StartupXYZ",
            "location": "Rabat",
            "description": "Seeking Backend Developer proficient in Node.js, Express, PostgreSQL, and Docker.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_003",
            "title": "DevOps Engineer",
            "company": "CloudSystems",
            "location": "Tangier",
            "description": "DevOps Engineer needed with Kubernetes, Docker, CI/CD, and Terraform expertise.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_004",
            "title": "ML Engineer",
            "company": "AILab",
            "location": "Fez",
            "description": "Machine Learning Engineer required: TensorFlow, PyTorch, Python, NLP, deep learning.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_005",
            "title": "Frontend Developer",
            "company": "WebStudio",
            "location": "Casablanca",
            "description": "Frontend Developer: React, TypeScript, HTML5, CSS3, Tailwind CSS, responsive design.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
    ]
