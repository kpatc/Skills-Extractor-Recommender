"""
Module de scraping pour la collecte des offres d'emploi.
Supporte : ReKrute, Emploi.ma, Indeed, LinkedIn (light).
"""

import requests
import csv
import time
import logging
import sys
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from utils.config import SCRAPING_CONFIG, RAW_DATA_DIR

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


class IndeedScraper(JobOfferScraper):
    """Scraper pour Indeed."""

    def __init__(self):
        super().__init__("indeed")
        self.base_url = "https://fr.indeed.com"

    def parse_page(self, html: str) -> List[Dict]:
        """Parse une page Indeed."""
        soup = BeautifulSoup(html, "html.parser")
        offers = []

        job_listings = soup.find_all("div", class_="job_seen_beacon")

        for listing in job_listings:
            try:
                title_elem = listing.find("h2", class_="jobTitle")
                company_elem = listing.find("span", class_="companyName")
                location_elem = listing.find("div", class_="companyLocation")
                desc_elem = listing.find("div", class_="job-snippet")

                if title_elem and company_elem:
                    offer = {
                        "job_id": f"{self.source_name}_{len(offers)}",
                        "title": title_elem.get_text(strip=True),
                        "company": company_elem.get_text(strip=True),
                        "location": location_elem.get_text(strip=True) if location_elem else "Non spécifié",
                        "description": desc_elem.get_text(strip=True) if desc_elem else "",
                        "source": self.source_name,
                        "scrape_date": datetime.now().isoformat(),
                    }
                    offers.append(offer)
            except Exception as e:
                logger.warning(f"Erreur parsing offre Indeed: {e}")

        return offers


class GitHubJobsScraper(JobOfferScraper):
    """Scraper pour GitHub Jobs (API REST gratuite, pas de scraping)."""

    def __init__(self):
        super().__init__("github_jobs")
        self.base_url = "https://jobs.github.com/api"

    def fetch_jobs(self, page: int = 0, description: str = "tech") -> List[Dict]:
        """Récupère les offres via l'API GitHub Jobs."""
        offers = []
        
        try:
            url = f"{self.base_url}/jobs?page={page}&description={description}"
            logger.info(f"API GitHub Jobs: {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            jobs_data = response.json()
            
            for job in jobs_data:
                offer = {
                    "job_id": job.get("id", f"gh_{page}_{len(offers)}"),
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location", ""),
                    "description": job.get("description", ""),
                    "source": self.source_name,
                    "scrape_date": datetime.now().isoformat(),
                }
                offers.append(offer)
            
            logger.info(f"✓ {len(offers)} offres récupérées de GitHub Jobs (page {page})")
            
        except Exception as e:
            logger.warning(f"Erreur API GitHub Jobs: {e}")
        
        time.sleep(1)  # Respecter les rate limits
        return offers


class StackOverflowJobsScraper(JobOfferScraper):
    """Scraper pour Stack Overflow Jobs."""

    def __init__(self):
        super().__init__("stackoverflow_jobs")
        self.base_url = "https://stackoverflow.com/jobs"

    def parse_page(self, html: str) -> List[Dict]:
        """Parse une page Stack Overflow Jobs."""
        soup = BeautifulSoup(html, "html.parser")
        offers = []

        job_listings = soup.find_all("div", class_="-job-item")

        for listing in job_listings:
            try:
                title_elem = listing.find("h2", class_="-title")
                company_elem = listing.find("h3", class_="s-user-card--time")
                location_elem = listing.find("span", class_="-location")
                desc_elem = listing.find("div", class_="s-prose")

                if title_elem and company_elem:
                    offer = {
                        "job_id": f"{self.source_name}_{len(offers)}",
                        "title": title_elem.get_text(strip=True),
                        "company": company_elem.get_text(strip=True),
                        "location": location_elem.get_text(strip=True) if location_elem else "Non spécifié",
                        "description": desc_elem.get_text(strip=True) if desc_elem else "",
                        "source": self.source_name,
                        "scrape_date": datetime.now().isoformat(),
                    }
                    offers.append(offer)
            except Exception as e:
                logger.warning(f"Erreur parsing SO Jobs: {e}")

        return offers


def scrape_all_sources(test_mode=False, min_offers=200) -> List[Dict]:
    """
    Scrape les offres de VRAIS sites d'emploi avec BeautifulSoup + requests.
    Priorité: ReKrute > Autres sites
    AUCUN fallback synthétique - QUE DU VRAI
    
    Args:
        test_mode: Si True, utilise des données de test
        min_offers: Nombre minimum d'offres à récupérer
    
    Returns:
        Liste de dictionnaires contenant les offres
    """
    all_offers = []

    if test_mode:
        logger.info("Mode test activé - utilisation de données simulées")
        all_offers = _generate_test_data()
    else:
        logger.info(f"\n{'='*80}")
        logger.info(f"SCRAPING RÉEL (BeautifulSoup + requests) - {min_offers} offres minimum")
        logger.info(f"{'='*80}\n")
        
        # 1️⃣ REKRUTE - PRIORITÉ (Maroc, le plus accessible)
        logger.info("🔄 ReKrute (Maroc) - PRIORITÉ...")
        try:
            rekrute_offers = scrape_rekrute(num_pages=5)
            if rekrute_offers:
                all_offers.extend(rekrute_offers)
                logger.info(f"✅ {len(rekrute_offers)} offres ReKrute\n")
            else:
                logger.warning("⚠️  0 offres ReKrute\n")
        except Exception as e:
            logger.warning(f"❌ Erreur ReKrute: {e}\n")
        
        # 2️⃣ INDEED.COM - avec JSON extraction (meilleur accès)
        if len(all_offers) < min_offers:
            logger.info("🔄 Indeed.com (International + IT jobs)...")
            try:
                indeed_offers = scrape_indeed_com(num_pages=5)
                if indeed_offers:
                    all_offers.extend(indeed_offers)
                    logger.info(f"✅ {len(indeed_offers)} offres Indeed.com\n")
                else:
                    logger.warning("⚠️  0 offres Indeed.com\n")
            except Exception as e:
                logger.warning(f"❌ Erreur Indeed.com: {e}\n")
        
        # 3️⃣ STACK OVERFLOW - fallback
        if len(all_offers) < min_offers:
            logger.info("🔄 Stack Overflow Jobs...")
            try:
                so_offers = scrape_stackoverflow_jobs(num_pages=2)
                if so_offers:
                    all_offers.extend(so_offers)
                    logger.info(f"✅ {len(so_offers)} offres Stack Overflow\n")
                else:
                    logger.warning("⚠️  0 offres Stack Overflow\n")
            except Exception as e:
                logger.warning(f"❌ Erreur Stack Overflow: {e}\n")

    logger.info(f"\n{'='*80}")
    logger.info(f"RÉSUMÉ SCRAPING - {len(all_offers)} offres totales")
    logger.info(f"{'='*80}")
    
    # Suppression des doublons
    unique_offers = {}
    for offer in all_offers:
        key = f"{offer.get('title', '')}_{offer.get('company', '')}"
        if key and key != "_" and key not in unique_offers:
            unique_offers[key] = offer

    final_offers = list(unique_offers.values())
    logger.info(f"Après suppression doublons: {len(final_offers)} offres uniques")
    if final_offers:
        logger.info(f"Sources: {', '.join(set([o.get('source', 'unknown') for o in final_offers]))}")
    logger.info(f"{'='*80}\n")
    
    if len(final_offers) < min_offers:
        logger.warning(f"⚠️  ATTENTION: Seulement {len(final_offers)} offres trouvées (min demandé: {min_offers})")
    
    return final_offers



def scrape_rekrute(num_pages: int = 5) -> List[Dict]:
    """Scrape ReKrute.com avec BeautifulSoup + requests."""
    offers = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    
    for page in range(1, num_pages + 1):
        try:
            url = f"https://www.rekrute.com/offres.html?page={page}"
            logger.info(f"  Page {page}: {url}")
            
            response = session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Chercher les liens d'offres
            offer_links = []
            
            # Tous les liens contenant /offre
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                if "/offre" in href and href not in offer_links:
                    offer_links.append(href)
            
            logger.info(f"    Trouvé {len(offer_links)} offres")
            
            for link in offer_links[:15]:  # Limiter par page
                try:
                    # Construire l'URL complète
                    full_url = link if link.startswith("http") else f"https://www.rekrute.com{link}"
                    
                    # Récupérer la page de l'offre
                    offer_response = session.get(full_url, timeout=10)
                    offer_response.raise_for_status()
                    offer_soup = BeautifulSoup(offer_response.text, "html.parser")
                    
                    # Titre
                    title_elem = offer_soup.find(["h1", "h2"])
                    title = title_elem.get_text(strip=True) if title_elem else "N/A"
                    
                    # Entreprise
                    company = "N/A"
                    for elem in offer_soup.find_all(["span", "div", "p"]):
                        text = elem.get_text(strip=True)
                        if "par " in text.lower() or "entreprise" in text.lower():
                            company = text.replace("par ", "").replace("Entreprise: ", "").strip()
                            if len(company) > 50:
                                company = company[:50]
                            break
                    
                    # Description
                    desc_elem = offer_soup.find("div", class_=lambda x: x and "description" in (x.lower() if x else ""))
                    if not desc_elem:
                        # Chercher le contenu principal
                        desc_elem = offer_soup.find("div", class_=lambda x: x and "content" in (x.lower() if x else ""))
                    
                    description = desc_elem.get_text(strip=True)[:1000] if desc_elem else offer_soup.get_text(strip=True)[:500]
                    
                    # Location
                    location = "Maroc"
                    for elem in offer_soup.find_all(["span", "div", "p"]):
                        text = elem.get_text(strip=True)
                        if any(city in text for city in ["Casablanca", "Rabat", "Fez", "Marrakech", "Tangier"]):
                            location = text
                            break
                    
                    if title != "N/A" and len(title) > 3:
                        offers.append({
                            "job_id": f"rekrute_{len(offers)+1:04d}",
                            "title": title,
                            "company": company,
                            "location": location,
                            "description": description,
                            "source": "rekrute",
                            "scrape_date": datetime.now().isoformat(),
                        })
                    
                    time.sleep(1)  # Délai entre les requêtes
                    
                except Exception as e:
                    logger.debug(f"    Erreur scraping offre: {e}")
                    continue
            
            if offer_links:
                logger.info(f"    ✓ {len(offer_links)} offres extraites (page {page})")
            
            time.sleep(2)
        except Exception as e:
            logger.warning(f"  Erreur page {page}: {e}")
            continue
    
    return offers


def scrape_rekrute(num_pages: int = 3) -> List[Dict]:
    """Scrape ReKrute.com avec BeautifulSoup - RAPIDE."""
    offers = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    })
    
    for page in range(1, num_pages + 1):
        try:
            url = f"https://www.rekrute.com/offres.html?page={page}"
            logger.info(f"  Page {page}: {url}")
            
            response = session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Chercher les offres (liens vers /offres/)
            job_links = []
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                if "/offre" in href:
                    full_url = href if href.startswith("http") else f"https://www.rekrute.com{href}"
                    job_links.append(full_url)
            
            job_links = list(set(job_links))[:15]  # Limite à 15 par page
            logger.info(f"    Trouvé {len(job_links)} liens")
            
            for link in job_links:
                try:
                    offer_resp = session.get(link, timeout=8)
                    offer_soup = BeautifulSoup(offer_resp.text, "html.parser")
                    
                    # Titre - chercher h1 ou h2
                    title = "N/A"
                    for elem in offer_soup.find_all(["h1", "h2"]):
                        text = elem.get_text(strip=True)
                        if 5 < len(text) < 150:
                            title = text
                            break
                    
                    # Entreprise - chercher dans les éléments structurés
                    company = "N/A"
                    for elem in offer_soup.find_all(["span", "p", "div"]):
                        text = elem.get_text(strip=True)
                        if "entreprise" in text.lower() or "company" in text.lower():
                            # Prendre le texte suivant
                            company = text.split(":")[-1].strip() if ":" in text else text
                            break
                    
                    # Description
                    description = offer_soup.get_text()[:300]
                    
                    # Location
                    location = "Maroc"
                    for elem in offer_soup.find_all(["span", "div"]):
                        text = elem.get_text(strip=True)
                        if any(city in text for city in ["Casablanca", "Rabat", "Fez", "Marrakech", "Tangier"]):
                            location = text
                            break
                    
                    if title != "N/A" and len(title) > 5:
                        offers.append({
                            "job_id": f"rekrute_{len(offers)+1:04d}",
                            "title": title,
                            "company": company,
                            "location": location,
                            "description": description,
                            "source": "rekrute",
                            "scrape_date": datetime.now().isoformat(),
                        })
                    
                    time.sleep(0.5)
                except Exception as e:
                    logger.debug(f"    Erreur offre: {str(e)[:50]}")
                    continue
            
            if offers:
                logger.info(f"    ✓ {len(offers)} offres")
            
            time.sleep(1)
        except Exception as e:
            logger.warning(f"  Erreur page {page}: {e}")
            continue
    
    return offers


def scrape_emploi_ma(num_pages: int = 5) -> List[Dict]:
    """Scrape Emploi.ma avec BeautifulSoup."""
    offers = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    
    for page in range(1, num_pages + 1):
        try:
            url = f"https://emploi.ma/offres-emploi?page={page}"
            logger.info(f"  Page {page}: {url}")
            
            response = session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Chercher les offres (adapt aux vrais sélecteurs d'Emploi.ma)
            job_cards = soup.find_all("div", class_=lambda x: x and ("job" in x.lower() or "offer" in x.lower()))
            
            if not job_cards:
                job_cards = soup.find_all("a", href=lambda x: x and "/offre" in x)
            
            logger.info(f"    Trouvé {len(job_cards)} éléments")
            
            for card in job_cards[:15]:  # Limiter par page
                try:
                    # Titre
                    title_elem = card.find(["h2", "h3", "span"])
                    title = title_elem.get_text(strip=True) if title_elem else "N/A"
                    
                    # Entreprise
                    company = "N/A"
                    company_elem = card.find(["strong", "span"], class_=lambda x: x and "company" in (x.lower() if x else ""))
                    if company_elem:
                        company = company_elem.get_text(strip=True)
                    
                    # Description
                    description = card.get_text(strip=True)[:500]
                    
                    # Location
                    location = "Maroc"
                    for elem in card.find_all(["span", "div"]):
                        text = elem.get_text(strip=True)
                        if any(city in text for city in ["Casablanca", "Rabat", "Fez", "Marrakech", "Tangier"]):
                            location = text
                            break
                    
                    if title != "N/A" and len(title) > 3:
                        offers.append({
                            "job_id": f"emploi_ma_{len(offers)+1:04d}",
                            "title": title,
                            "company": company,
                            "location": location,
                            "description": description,
                            "source": "emploi.ma",
                            "scrape_date": datetime.now().isoformat(),
                        })
                except Exception as e:
                    logger.debug(f"    Erreur parsing offre: {e}")
                    continue
            
            if offers:
                logger.info(f"    ✓ {len(offers)} offres extraites (page {page})")
            
            time.sleep(2)
        except Exception as e:
            logger.warning(f"  Erreur page {page}: {e}")
            continue
    
    return offers


def scrape_indeed_com(num_pages: int = 5) -> List[Dict]:
    """Scrape Indeed.com avec pattern JSON - meilleur accès international."""
    import re
    import json
    
    offers = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    
    # Chercher les offres IT
    keywords = ["software engineer", "python developer", "backend developer", "devops engineer", "cloud architect"]
    
    for keyword in keywords:
        if len(offers) >= 150:
            break
            
        for page in range(num_pages):
            try:
                offset = page * 10
                url = f"https://www.indeed.com/jobs?q={keyword.replace(' ', '+')}&start={offset}"
                logger.info(f"  {keyword} page {page+1}: {url}")
                
                response = session.get(url, timeout=15)
                response.raise_for_status()
                
                # Extraction du JSON comme le spider Scrapy
                script_tag = re.findall(
                    r'window.mosaic.providerData\["mosaic-provider-jobcards"\]=(\{.+?\});',
                    response.text
                )
                
                if script_tag:
                    try:
                        json_blob = json.loads(script_tag[0])
                        jobs_list = json_blob['metaData']['mosaicProviderJobCardsModel']['results']
                        logger.info(f"    Trouvé {len(jobs_list)} offres")
                        
                        for job in jobs_list:
                            try:
                                title = job.get('title', 'N/A')
                                company = job.get('company', 'N/A')
                                
                                # Filtrer pour IT uniquement
                                if not any(it_keyword in title.lower() for it_keyword in ['engineer', 'developer', 'architect', 'devops', 'cloud', 'senior', 'lead', 'tech']):
                                    continue
                                
                                offer = {
                                    "job_id": f"indeed_com_{job.get('jobkey', f'job_{len(offers)}')[:20]}",
                                    "title": title,
                                    "company": company,
                                    "location": f"{job.get('jobLocationCity', '')}, {job.get('jobLocationState', '')}".strip(', '),
                                    "description": job.get('snippet', '')[:500],
                                    "source": "indeed.com",
                                    "scrape_date": datetime.now().isoformat(),
                                }
                                
                                if offer['title'] != 'N/A' and len(offer['title']) > 3:
                                    offers.append(offer)
                            except Exception as e:
                                logger.debug(f"    Erreur: {e}")
                                continue
                        
                        if offers:
                            logger.info(f"    ✓ {len(offers)} offres total")
                        
                    except json.JSONDecodeError as e:
                        logger.warning(f"    Erreur JSON: {e}")
                else:
                    logger.warning(f"    Pas de JSON trouvé")
                
                time.sleep(2)
            except Exception as e:
                logger.warning(f"  Erreur {keyword} page {page+1}: {e}")
                continue
    
    return offers


def scrape_indeed_fr(num_pages: int = 5) -> List[Dict]:
    """
    Scrape Indeed (en.indeed.com + fr.indeed.com) avec extraction JSON.
    Basé sur le spider Scrapy scrap_base/indeed/.
    Recherche: IT jobs (developer, engineer, architect, etc.)
    """
    import re
    import json
    
    offers = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.indeed.com/",
        "DNT": "1",
    })
    
    # Keywords IT + locations pour plus de données
    keywords = [
        "software developer", "python developer", "senior developer",
        "backend engineer", "frontend engineer", "full stack developer",
        "devops engineer", "data engineer", "machine learning engineer",
        "software architect", "senior engineer",
    ]
    
    locations = ["", "remote", "paris", "london", "berlin"]  # vide = worldwide
    
    for keyword in keywords[:5]:  # Limiter pour pas trop de requêtes
        for location in locations[:3]:  # Limiter locations
            if len(offers) >= 200:
                break
            
            for page in range(num_pages):
                try:
                    offset = page * 10
                    
                    # Utiliser indeed.com avec parametres
                    if location:
                        url = f"https://www.indeed.com/jobs?q={keyword.replace(' ', '+')}&l={location}&start={offset}"
                    else:
                        url = f"https://www.indeed.com/jobs?q={keyword.replace(' ', '+')}&start={offset}"
                    
                    logger.info(f"  {keyword} ({location or 'worldwide'}) p{page+1}...")
                    
                    response = session.get(url, timeout=15)
                    response.raise_for_status()
                    
                    # Extraire JSON avec regex (pattern du spider Scrapy)
                    script_tag = re.findall(
                        r'window.mosaic.providerData\["mosaic-provider-jobcards"\]=(\{.+?\});',
                        response.text,
                        re.DOTALL
                    )
                    
                    if script_tag:
                        try:
                            json_blob = json.loads(script_tag[0])
                            jobs_list = json_blob['metaData']['mosaicProviderJobCardsModel']['results']
                            
                            for job in jobs_list:
                                try:
                                    # Extraire tous les details disponibles
                                    offer = {
                                        "job_id": f"indeed_{job.get('jobkey', f'job_{len(offers)}')[:25]}",
                                        "title": job.get('title', 'N/A'),
                                        "company": job.get('company', 'N/A'),
                                        "location": f"{job.get('jobLocationCity', '')}, {job.get('jobLocationState', '')}".strip(', '),
                                        "description": job.get('snippet', job.get('summary', ''))[:800],
                                        "source": "indeed.com",
                                        "scrape_date": datetime.now().isoformat(),
                                        "jobkey": job.get('jobkey'),
                                        "rating": job.get('companyRating'),
                                        "review_count": job.get('companyReviewCount'),
                                        "salary_min": job.get('estimatedSalary', {}).get('min') if job.get('estimatedSalary') else None,
                                        "salary_max": job.get('estimatedSalary', {}).get('max') if job.get('estimatedSalary') else None,
                                    }
                                    
                                    if offer['title'] != 'N/A' and len(offer['title']) > 3:
                                        offers.append(offer)
                                except Exception as e:
                                    logger.debug(f"    Erreur job: {str(e)[:50]}")
                                    continue
                            
                            if jobs_list:
                                logger.info(f"    ✓ {len(jobs_list)} jobs extraits")
                        except Exception as e:
                            logger.debug(f"    Erreur JSON: {str(e)[:50]}")
                    
                    time.sleep(2)
                    
                except Exception as e:
                    logger.debug(f"  Erreur requête: {str(e)[:50]}")
                    continue
    
    return offers


def scrape_stackoverflow_jobs(num_pages: int = 3) -> List[Dict]:
    """Scrape Stack Overflow Jobs avec BeautifulSoup."""
    offers = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    
    for page in range(1, num_pages + 1):
        try:
            # Stack Overflow Jobs a changé mais on peut essayer
            url = f"https://stackoverflow.com/jobs?pg={page}"
            logger.info(f"  Page {page}: {url}")
            
            response = session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Chercher les offres
            job_cards = soup.find_all("div", class_=lambda x: x and "s-job-card" in (x if x else ""))
            
            logger.info(f"    Trouvé {len(job_cards)} offres")
            
            for card in job_cards:
                try:
                    # Titre
                    title_elem = card.find("h2")
                    title = title_elem.get_text(strip=True) if title_elem else "N/A"
                    
                    # Entreprise
                    company_elem = card.find("h3")
                    company = company_elem.get_text(strip=True) if company_elem else "N/A"
                    
                    # Description
                    desc_elem = card.find("p", class_="s-user-card--time")
                    description = desc_elem.get_text(strip=True) if desc_elem else card.get_text(strip=True)[:300]
                    
                    # Location
                    location = "Remote/International"
                    for elem in card.find_all("span"):
                        if "remote" in elem.get_text(strip=True).lower():
                            location = "Remote"
                            break
                    
                    if title != "N/A" and len(title) > 3:
                        offers.append({
                            "job_id": f"so_jobs_{len(offers)+1:04d}",
                            "title": title,
                            "company": company,
                            "location": location,
                            "description": description,
                            "source": "stackoverflow",
                            "scrape_date": datetime.now().isoformat(),
                        })
                except Exception as e:
                    logger.debug(f"    Erreur parsing: {e}")
                    continue
            
            if job_cards:
                logger.info(f"    ✓ Offres extraites")
            
            time.sleep(2)
        except Exception as e:
            logger.warning(f"  Erreur page {page}: {e}")
            continue
    
    return offers


def _generate_realistic_offers(count: int) -> List[Dict]:
    """
    Génère des offres d'emploi synthétiques réalistes basées sur les patterns du marché.
    
    Args:
        count: Nombre d'offres à générer
    
    Returns:
        Liste d'offres synthétiques
    """
    import random
    from datetime import datetime, timedelta
    
    # Patterns du marché réel (skills les plus demandés)
    job_titles = [
        "Senior Python Developer", "Python Developer", "Junior Python Developer",
        "Senior React Developer", "React Developer", "Frontend Developer",
        "Backend Developer with Python", "Full Stack Developer",
        "Machine Learning Engineer", "Data Scientist",
        "Data Engineer", "DevOps Engineer",
        "Cloud Architect", "Systems Engineer",
        "Frontend Engineer", "Backend Engineer",
        "Mobile Developer (iOS)", "Mobile Developer (Android)",
        "QA Engineer", "Test Automation Engineer",
        "Database Administrator", "DBA",
        "Security Engineer", "Cybersecurity Analyst",
        "Solutions Architect", "Technical Lead",
        "Engineering Manager", "Product Manager",
        "Technical Support Engineer", "Customer Success Engineer",
        "Infrastructure Engineer", "Site Reliability Engineer",
        "Software Architect", "Principal Engineer",
    ]
    
    companies = [
        "TechCorp", "DataFlow", "CloudSystems", "InnovateAI",
        "WebDynamics", "MobileFirst", "SecureNet", "DataVault",
        "SwiftCode", "ByteForce", "PixelStudio", "CloudPeak",
        "NeuralAI", "AutoScale", "ProDev", "CoreSystems",
        "StreamTech", "QuantumLeap", "VisionAI", "EdgeCompute",
        "CodeFactory", "DevOpsPlus", "APIFirst", "ZeroDowntime",
        "AsyncFlow", "RealTime", "ScaleUp", "FastTrack",
        "SoftShift", "TechHub", "Innovation Labs", "Digital Future",
    ]
    
    locations = [
        "Casablanca", "Rabat", "Fez", "Marrakech", "Tangier",
        "Remote", "Paris", "London", "Berlin", "Amsterdam",
        "Madrid", "Brussels", "Toronto", "New York", "San Francisco",
        "Singapore", "Dubai", "Toronto", "Mexico City",
        "São Paulo", "Buenos Aires", "Istanbul",
    ]
    
    # Skills groupés par domaine (patterns réels)
    skill_combinations = [
        # Backend Python
        ["Python", "Django", "REST APIs", "PostgreSQL", "Git"],
        ["Python", "FastAPI", "SQLAlchemy", "Celery", "Docker"],
        ["Python", "Flask", "MongoDB", "RabbitMQ", "AWS"],
        
        # Frontend
        ["React", "TypeScript", "CSS", "HTML", "Redux"],
        ["React", "Next.js", "Tailwind CSS", "GraphQL", "Jest"],
        ["Vue.js", "Vuex", "Webpack", "SASS", "Node.js"],
        
        # Full Stack
        ["Python", "React", "Django", "PostgreSQL", "Docker", "Kubernetes"],
        ["Node.js", "React", "MongoDB", "Express", "AWS"],
        ["Python", "Vue.js", "FastAPI", "MySQL", "Docker"],
        
        # Data Science
        ["Python", "Pandas", "NumPy", "Scikit-learn", "TensorFlow"],
        ["Python", "Data Analysis", "Matplotlib", "Seaborn", "Jupyter"],
        ["Machine Learning", "Deep Learning", "PyTorch", "Python", "Statistics"],
        
        # DevOps / Infrastructure
        ["Docker", "Kubernetes", "AWS", "CI/CD", "Linux"],
        ["Terraform", "Jenkins", "GitLab CI", "Monitoring", "Python"],
        ["Cloud Architecture", "AWS", "GCP", "Azure", "Networking"],
        
        # Mobile
        ["React Native", "JavaScript", "Mobile Development", "Git", "Redux"],
        ["Flutter", "Dart", "Mobile UI", "Firebase", "Testing"],
        ["iOS", "Swift", "Objective-C", "XCode", "CocoaPods"],
        
        # QA / Testing
        ["Selenium", "Python", "Test Automation", "JUnit", "CI/CD"],
        ["Testing", "QA", "Python", "JavaScript", "Cypress"],
        ["Performance Testing", "Load Testing", "JMeter", "Monitoring"],
    ]
    
    descriptions_template = [
        "{skills}: Experience with {top_skill} in production environments.",
        "We're looking for a {job} with expertise in {skills}.",
        "Join our {company} team! Required: {skills}.",
        "Develop and maintain {top_skill} applications. Must know {skills}.",
        "Position: {job}. Tech stack: {skills}.",
        "Looking for an expert in {top_skill}, {second_skill}, and {third_skill}.",
        "Build scalable solutions with {skills}. Remote option available.",
        "Lead development of {top_skill} projects. Knowledge of {skills} required.",
    ]
    
    offers = []
    now = datetime.now()
    
    for i in range(count):
        job_id = f"synthetic_{i+1:04d}"
        title = random.choice(job_titles)
        company = random.choice(companies)
        location = random.choice(locations)
        skills = random.choice(skill_combinations)
        
        # Create description
        try:
            desc_template = random.choice(descriptions_template)
            description = desc_template.format(
                job=title.lower(),
                company=company,
                skills=", ".join(skills[:3]),
                top_skill=skills[0],
                second_skill=skills[1] if len(skills) > 1 else skills[0],
                third_skill=skills[2] if len(skills) > 2 else skills[0],
            )
        except:
            description = f"{title}: {', '.join(skills)}"
        
        # Simulate realistic posting dates
        days_ago = random.randint(0, 30)
        post_date = (now - timedelta(days=days_ago)).isoformat()
        
        offer = {
            "job_id": job_id,
            "title": title,
            "company": company,
            "location": location,
            "description": description,
            "skills": skills,  # Keep skills as separate field
            "source": "synthetic",
            "scrape_date": now.isoformat(),
            "posted_date": post_date,
            "contract_type": random.choice(["Full-time", "Contract", "CDI"]),
        }
        
        offers.append(offer)
    
    logger.info(f"✓ {count} offres synthétiques générées avec patterns réalistes")
    return offers


def _generate_test_data() -> List[Dict]:
    """Génère des données de test pour développement (50+ offres)."""
    test_offers = [
        # Data & Analytics
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
            "title": "Data Scientist",
            "company": "DataViz Inc",
            "location": "Casablanca",
            "description": "Data Scientist needed: Python, Machine Learning, Pandas, Scikit-learn, TensorFlow, and statistical analysis.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_003",
            "title": "Analytics Engineer",
            "company": "InsightCo",
            "location": "Rabat",
            "description": "Analytics Engineer: SQL, Python, Data Visualization, Tableau, Power BI, and ETL pipelines.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        # Backend Development
        {
            "job_id": "test_004",
            "title": "Backend Developer",
            "company": "StartupXYZ",
            "location": "Rabat",
            "description": "Seeking Backend Developer proficient in Node.js, Express, PostgreSQL, and Docker.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_005",
            "title": "Senior Backend Engineer",
            "company": "CloudApp",
            "location": "Casablanca",
            "description": "Senior Backend Engineer: Python, Django, FastAPI, Redis, MongoDB, microservices architecture.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_006",
            "title": "API Developer",
            "company": "APIHub",
            "location": "Fez",
            "description": "API Developer: REST, GraphQL, Node.js, Java, Spring Boot, API Design patterns.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        # DevOps & Infrastructure
        {
            "job_id": "test_007",
            "title": "DevOps Engineer",
            "company": "CloudSystems",
            "location": "Tangier",
            "description": "DevOps Engineer needed with Kubernetes, Docker, CI/CD, and Terraform expertise.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_008",
            "title": "Infrastructure Engineer",
            "company": "InfraOps",
            "location": "Marrakech",
            "description": "Infrastructure Engineer: AWS, Azure, GCP, Terraform, Ansible, Linux administration.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_009",
            "title": "Cloud Architect",
            "company": "CloudFirst",
            "location": "Casablanca",
            "description": "Cloud Architect: AWS Solutions Architecture, Cloud Security, Scalability, Cost Optimization.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        # Machine Learning & AI
        {
            "job_id": "test_010",
            "title": "ML Engineer",
            "company": "AILab",
            "location": "Fez",
            "description": "Machine Learning Engineer required: TensorFlow, PyTorch, Python, NLP, deep learning.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_011",
            "title": "AI/ML Researcher",
            "company": "ResearchAI",
            "location": "Rabat",
            "description": "AI Researcher: Deep Learning, Neural Networks, Computer Vision, Research publication skills.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        # Frontend Development
        {
            "job_id": "test_012",
            "title": "Frontend Developer",
            "company": "WebStudio",
            "location": "Casablanca",
            "description": "Frontend Developer: React, TypeScript, HTML5, CSS3, Tailwind CSS, responsive design.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_013",
            "title": "React Developer",
            "company": "UIFlow",
            "location": "Tangier",
            "description": "React Developer: React Hooks, Redux, Next.js, Webpack, Performance optimization.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_014",
            "title": "Vue.js Developer",
            "company": "VueApp",
            "location": "Fez",
            "description": "Vue.js Developer: Vue 3, Nuxt, Vuex, Component design, CSS frameworks.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_015",
            "title": "Angular Developer",
            "company": "AngularWorks",
            "location": "Marrakech",
            "description": "Angular Developer: Angular 15+, RxJS, TypeScript, Material Design, Testing.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        # Full Stack
        {
            "job_id": "test_016",
            "title": "Full Stack Developer",
            "company": "FullStack Inc",
            "location": "Casablanca",
            "description": "Full Stack Developer: React, Node.js, PostgreSQL, Docker, AWS, DevOps basics.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_017",
            "title": "Full Stack Engineer",
            "company": "TechStack",
            "location": "Rabat",
            "description": "Full Stack Engineer: Python, JavaScript, AWS, Database design, Agile methodology.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        # QA & Testing
        {
            "job_id": "test_018",
            "title": "QA Engineer",
            "company": "QATeam",
            "location": "Fez",
            "description": "QA Engineer: Selenium, Test automation, API testing, Jest, Cypress, Test plans.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_019",
            "title": "Automation Tester",
            "company": "TestWorks",
            "location": "Tangier",
            "description": "Automation Tester: Selenium, Python, Java, Test frameworks, CI/CD integration.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        # Database & Data
        {
            "job_id": "test_020",
            "title": "Database Administrator",
            "company": "DataCore",
            "location": "Casablanca",
            "description": "DBA: PostgreSQL, MySQL, MongoDB, Database optimization, Backup strategies, Performance tuning.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_021",
            "title": "Database Engineer",
            "company": "DBSystems",
            "location": "Marrakech",
            "description": "Database Engineer: SQL, NoSQL, Elasticsearch, Caching strategies, Sharding, Replication.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        # Mobile Development
        {
            "job_id": "test_022",
            "title": "iOS Developer",
            "company": "MobileFirst",
            "location": "Casablanca",
            "description": "iOS Developer: Swift, SwiftUI, iOS SDK, Core Data, Networking, App Store deployment.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_023",
            "title": "Android Developer",
            "company": "AndroidCorp",
            "location": "Rabat",
            "description": "Android Developer: Kotlin, Java, Android SDK, Jetpack, Material Design, Firebase.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_024",
            "title": "React Native Developer",
            "company": "CrossPlatform",
            "location": "Fez",
            "description": "React Native: JavaScript, TypeScript, Native modules, Redux, Firebase integration.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        # Security & Compliance
        {
            "job_id": "test_025",
            "title": "Security Engineer",
            "company": "SecureCode",
            "location": "Casablanca",
            "description": "Security Engineer: OWASP, Penetration testing, Cryptography, Network security, SSL/TLS.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_026",
            "title": "Cybersecurity Analyst",
            "company": "CyberDefense",
            "location": "Tangier",
            "description": "Cybersecurity: Threat analysis, Firewalls, IDS/IPS, SIEM, Incident response.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        # Growth & Performance
        {
            "job_id": "test_027",
            "title": "Performance Engineer",
            "company": "FastTech",
            "location": "Marrakech",
            "description": "Performance Engineer: Load testing, Profiling, Caching, Optimization techniques, JMeter.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_028",
            "title": "SRE Engineer",
            "company": "ReliabilityFirst",
            "location": "Casablanca",
            "description": "Site Reliability Engineer: Kubernetes, Prometheus, Grafana, Linux, Scripting, SLO/SLA.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        # Specializations
        {
            "job_id": "test_029",
            "title": "Blockchain Developer",
            "company": "BlockChain Inc",
            "location": "Casablanca",
            "description": "Blockchain: Solidity, Ethereum, Smart contracts, Web3.js, DeFi protocols.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_030",
            "title": "Game Developer",
            "company": "GameStudio",
            "location": "Rabat",
            "description": "Game Developer: Unity, Unreal Engine, C#, C++, Game design patterns, Physics.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_031",
            "title": "IoT Engineer",
            "company": "SmartDevices",
            "location": "Fez",
            "description": "IoT Engineer: Arduino, Raspberry Pi, Embedded C, MQTT, Sensor integration, AWS IoT.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_032",
            "title": "Big Data Engineer",
            "company": "DataLake",
            "location": "Casablanca",
            "description": "Big Data: Apache Spark, Hadoop, Hive, Scala, Kafka, Distributed systems.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_033",
            "title": "NLP Engineer",
            "company": "NLPLabs",
            "location": "Marrakech",
            "description": "NLP Engineer: Transformers, BERT, NLP libraries, Text processing, Tokenization.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_034",
            "title": "Computer Vision Engineer",
            "company": "VisionAI",
            "location": "Tangier",
            "description": "Computer Vision: OpenCV, CNN, Image processing, Object detection, PyTorch.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_035",
            "title": "GraphQL Developer",
            "company": "GraphQLStudio",
            "location": "Casablanca",
            "description": "GraphQL: Apollo Server, Schema design, Query optimization, Subscriptions.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_036",
            "title": "Microservices Architect",
            "company": "MicroArch",
            "location": "Rabat",
            "description": "Microservices: Service mesh, API Gateway, Circuit breaker, Distributed tracing.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_037",
            "title": "Serverless Developer",
            "company": "ServerlessFirst",
            "location": "Fez",
            "description": "Serverless: AWS Lambda, Google Cloud Functions, Azure Functions, Event-driven.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_038",
            "title": "WebGL Developer",
            "company": "3DWeb",
            "location": "Marrakech",
            "description": "WebGL: Three.js, Babylon.js, Shaders, 3D graphics, Performance optimization.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_039",
            "title": "Data Pipeline Engineer",
            "company": "DataFlow",
            "location": "Casablanca",
            "description": "Data Pipeline: Airflow, Dbt, ETL, Data validation, Scheduling, Monitoring.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_040",
            "title": "Observability Engineer",
            "company": "ObservabilityPlus",
            "location": "Tangier",
            "description": "Observability: Prometheus, Grafana, ELK stack, Tracing, Logging, Metrics.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_041",
            "title": "Java Developer",
            "company": "JavaCorp",
            "location": "Casablanca",
            "description": "Java Developer: Spring Boot, Hibernate, JPA, Maven, Testing, Microservices.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_042",
            "title": "Go Developer",
            "company": "GoLang Inc",
            "location": "Rabat",
            "description": "Go Developer: Goroutines, Channels, Gin, gRPC, Concurrency patterns.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_043",
            "title": "Rust Developer",
            "company": "RustSystems",
            "location": "Fez",
            "description": "Rust: Memory safety, Performance, Cargo, Ownership, Systems programming.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_044",
            "title": "PHP Developer",
            "company": "WebDev",
            "location": "Marrakech",
            "description": "PHP: Laravel, Symfony, MySQL, RESTful APIs, Code quality.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_045",
            "title": "C++ Developer",
            "company": "SystemsCore",
            "location": "Casablanca",
            "description": "C++: Low-level programming, Performance critical, Templates, STL, Modern C++.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_046",
            "title": "Technical Lead",
            "company": "TechLeads",
            "location": "Casablanca",
            "description": "Tech Lead: Architecture decisions, Code reviews, Mentoring, System design, Leadership.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_047",
            "title": "Solutions Architect",
            "company": "Solutions Co",
            "location": "Rabat",
            "description": "Solutions Architect: System design, Client requirements, Technical documentation.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_048",
            "title": "Engineering Manager",
            "company": "TechManagement",
            "location": "Tangier",
            "description": "Engineering Manager: Team leadership, Project management, Hiring, Performance reviews.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_049",
            "title": "Product Engineer",
            "company": "ProductDriven",
            "location": "Fez",
            "description": "Product Engineer: Feature development, A/B testing, User feedback, Product roadmap.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
        {
            "job_id": "test_050",
            "title": "Platform Engineer",
            "company": "PlatformOps",
            "location": "Marrakech",
            "description": "Platform Engineer: Internal tooling, Developer experience, Scalability, Reliability.",
            "source": "test",
            "scrape_date": datetime.now().isoformat(),
        },
    ]
    return test_offers

