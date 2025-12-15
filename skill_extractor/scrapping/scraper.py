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
        
        # 1️⃣ REKRUTE - PRIORITÉ (Maroc, 30 pages)
        logger.info("🔄 ReKrute (Maroc) - PRIORITÉ (30 pages)...")
        try:
            rekrute_offers = scrape_rekrute(num_pages=30)
            if rekrute_offers:
                all_offers.extend(rekrute_offers)
                logger.info(f"✅ {len(rekrute_offers)} offres ReKrute\n")
            else:
                logger.warning("⚠️  0 offres ReKrute\n")
        except Exception as e:
            logger.warning(f"❌ Erreur ReKrute: {e}\n")
        
        # 2️⃣ GITHUB JOBS - BeautifulSoup (30 pages)
        if len(all_offers) < min_offers:
            logger.info("🔄 GitHub Careers (30 pages)...")
            try:
                github_offers = scrape_github_jobs(num_pages=30)
                if github_offers:
                    all_offers.extend(github_offers)
                    logger.info(f"✅ {len(github_offers)} offres GitHub\n")
                else:
                    logger.warning("⚠️  0 offres GitHub\n")
            except Exception as e:
                logger.warning(f"❌ Erreur GitHub: {e}\n")
        
        # 3️⃣ LINKEDIN JOBS - BeautifulSoup (20 pages)
        if len(all_offers) < min_offers:
            logger.info("🔄 LinkedIn Jobs (20 pages)...")
            try:
                linkedin_offers = scrape_linkedin_jobs(num_pages=20)
                if linkedin_offers:
                    all_offers.extend(linkedin_offers)
                    logger.info(f"✅ {len(linkedin_offers)} offres LinkedIn\n")
                else:
                    logger.warning("⚠️  0 offres LinkedIn\n")
            except Exception as e:
                logger.warning(f"❌ Erreur LinkedIn: {e}\n")

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



def scrape_rekrute(num_pages: int = 10) -> List[Dict]:
    """Scrape ReKrute.com - avec descriptions complètes des pages individuelles."""
    import re
    
    offers = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    
    # IT keywords - comprehensive list
    it_keywords = [
        'python', 'java', 'javascript', 'developer', 'engineer', 'devops', 'frontend', 'backend',
        'fullstack', 'react', 'angular', 'nodejs', 'database', 'sql', 'cloud', 'aws', 'azure',
        'docker', 'kubernetes', 'api', 'software', 'informatique', 'tech', 'programmer', 'data',
        '.net', 'c#', 'c++', 'rust', 'golang', 'php', 'ruby', 'swift', 'architect', 'security',
        'machine learning', 'ai', 'data scientist', 'analyst', 'testing', 'qa', 'tester',
        'mongodb', 'postgresql', 'mysql', 'elasticsearch', 'redis', 'git', 'ci/cd', 'devops',
        'terraform', 'ansible', 'kafka', 'spark', 'hadoop', 'infrastructure', 'network',
        'linux', 'windows server', 'scrum', 'agile', 'microservices', 'rest', 'graphql'
    ]
    
    def is_it_job(text: str) -> bool:
        return sum(1 for kw in it_keywords if kw in text.lower()) >= 1
    
    def clean_text(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'&[a-z]+;', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    seen = set()
    
    for page in range(1, num_pages + 1):
        try:
            url = f"https://www.rekrute.com/offres.html?page={page}"
            logger.info(f"  Page {page}")
            
            response = session.get(url, timeout=10)
            if response.status_code != 200:
                logger.debug(f"    Status {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Chercher tous les liens d'offres: /offre-emploi-*-*.html
            links_found = 0
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                # Pattern: /offre-emploi-* ou offre-emploi-*
                if "offre-emploi" not in href or not href.endswith(".html"):
                    continue
                
                links_found += 1
                title = clean_text(link.get_text())
                if not title or len(title) < 5:
                    continue
                
                # Éviter doublons
                if title in seen:
                    continue
                seen.add(title)
                
                # IT filter sur titre d'abord
                if not is_it_job(title):
                    continue
                
                # SCRAPER LA PAGE INDIVIDUELLE pour la description complète
                description = title  # Fallback
                try:
                    # Construire URL complète si nécessaire
                    full_url = href if href.startswith("http") else f"https://www.rekrute.com{href}"
                    job_response = session.get(full_url, timeout=8)
                    
                    if job_response.status_code == 200:
                        job_soup = BeautifulSoup(job_response.text, "html.parser")
                        
                        # Chercher la description - essayer plusieurs sélecteurs
                        desc_elem = None
                        for selector in ["[data-test='description']", ".job-description", ".offer-description", "article", ".content-main"]:
                            try:
                                if selector.startswith("["):
                                    desc_elem = job_soup.select_one(selector)
                                else:
                                    desc_elem = job_soup.select_one(selector)
                                if desc_elem:
                                    break
                            except:
                                pass
                        
                        # Si pas trouvé, chercher tous les paragraphes
                        if not desc_elem:
                            paragraphs = job_soup.find_all("p")
                            if paragraphs:
                                description = clean_text(" ".join([p.get_text() for p in paragraphs]))[:1500]
                        else:
                            description = clean_text(desc_elem.get_text())[:1500]
                    
                    # Ensure description has content beyond title
                    if len(description) <= len(title):
                        description = title  # Fallback
                    
                except Exception as e:
                    logger.debug(f"    Job page error: {str(e)[:30]}")
                    description = title
                
                # Filtrer aussi sur description
                if not is_it_job(title + " " + description):
                    continue
                
                offer = {
                    "job_id": f"rekrute_{len(offers)+1:04d}",
                    "title": title,
                    "company": "ReKrute",
                    "location": "Maroc",
                    "description": description,
                    "source": "rekrute",
                    "scrape_date": datetime.now().isoformat(),
                }
                
                offers.append(offer)
                logger.debug(f"    ✓ {title[:50]}")
                
                time.sleep(0.2)  # Respecter le serveur
            
            logger.info(f"    Trouvé {links_found} liens, ✓ {len(offers)} offres IT")
            time.sleep(0.5)
            
        except Exception as e:
            logger.debug(f"  Error page {page}: {str(e)[:50]}")
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


def scrape_github_jobs(num_pages: int = 10) -> List[Dict]:
    """Scrape GitHub Careers - github.com/careers avec scraping BeautifulSoup."""
    offers = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    
    # IT keywords pour filtrer
    it_keywords = ['python', 'java', 'javascript', 'developer', 'engineer', 'architect', 
                   'devops', 'cloud', 'backend', 'frontend', 'fullstack', 'senior', 
                   'lead', 'tech', 'software', 'react', 'node', 'django', 'aws', 'rust', 'copilot']
    
    def is_it_job(title, description=""):
        combined = (title + " " + description).lower()
        return sum(1 for kw in it_keywords if kw in combined) >= 1
    
    def clean_text(text):
        """Remove HTML tags and entities."""
        import re
        text = re.sub(r'<[^>]+>', '', text or '')
        text = re.sub(r'&[a-z]+;', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    # GitHub Careers - scraper avec BeautifulSoup
    try:
        url = "https://github.com/careers/home/jobs"
        logger.info(f"  GitHub Careers: {url}")
        
        response = session.get(url, timeout=15)
        if response.status_code != 200:
            logger.debug(f"    Status {response.status_code}")
            return offers
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Chercher les job cards (structure peut varier)
        # Essayer plusieurs selectors possibles
        job_elements = soup.find_all("a", {"data-test": "job-list-item"})
        if not job_elements:
            job_elements = soup.find_all("div", class_=lambda x: x and "job" in (x if x else "").lower())
        
        logger.info(f"    Trouvé {len(job_elements)} éléments job")
        
        for elem in job_elements[:num_pages * 10]:  # Limiter
            try:
                # Extraire titre
                title_elem = elem.find("h2") or elem.find("h3") or elem.find(class_=lambda x: x and "title" in (x if x else "").lower())
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                if not title or len(title) < 3:
                    continue
                
                # Filtrer sur titre d'abord
                if not is_it_job(title):
                    continue
                
                # Extraire entreprise
                company_elem = elem.find(class_=lambda x: x and "company" in (x if x else "").lower())
                company = company_elem.get_text(strip=True) if company_elem else "GitHub"
                
                # Extraire location
                location_elem = elem.find(class_=lambda x: x and "location" in (x if x else "").lower())
                location = location_elem.get_text(strip=True) if location_elem else "Remote"
                
                # Extraire description si disponible
                description = ""
                desc_elem = elem.find("p")
                if desc_elem:
                    description = clean_text(desc_elem.get_text())
                
                # Si pas de description en texte, prendre le texte entier
                if not description:
                    description = clean_text(elem.get_text())[:500]
                
                # Filtrer aussi sur description
                if description and not is_it_job(title, description):
                    continue
                
                offer = {
                    "job_id": f"github_{len(offers):04d}",
                    "title": title,
                    "company": company,
                    "location": location,
                    "description": description[:800],
                    "source": "github.com",
                    "scrape_date": datetime.now().isoformat(),
                }
                
                offers.append(offer)
                logger.debug(f"    ✓ {title[:50]}")
                
            except Exception as e:
                logger.debug(f"    Element error: {str(e)[:30]}")
                continue
        
        time.sleep(1)
    except Exception as e:
        logger.debug(f"  Error: {str(e)[:50]}")
    
    logger.info(f"  ✓ GitHub: {len(offers)} offres IT extraites")
    return offers


def scrape_linkedin_jobs(num_pages: int = 20) -> List[Dict]:
    """Scrape LinkedIn Jobs - linkedin.com/jobs avec BeautifulSoup."""
    offers = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    
    # IT keywords pour filtrer
    it_keywords = ['python', 'java', 'javascript', 'developer', 'engineer', 'architect', 
                   'devops', 'cloud', 'backend', 'frontend', 'fullstack', 'senior', 
                   'lead', 'tech', 'software', 'react', 'node', 'django', 'aws', 'rust', 'data']
    
    def is_it_job(title, description=""):
        combined = (title + " " + description).lower()
        return sum(1 for kw in it_keywords if kw in combined) >= 1
    
    def clean_text(text):
        """Remove HTML tags and entities."""
        import re
        text = re.sub(r'<[^>]+>', '', text or '')
        text = re.sub(r'&[a-z]+;', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    # LinkedIn Jobs - scraper avec BeautifulSoup
    for page in range(1, num_pages + 1):
        try:
            # LinkedIn jobs search URL
            url = f"https://www.linkedin.com/jobs/search/?keywords=tech%20developer&location=worldwide&start={(page-1)*25}"
            logger.info(f"  Page {page}")
            
            response = session.get(url, timeout=15)
            if response.status_code != 200:
                logger.debug(f"    Status {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Chercher les job cards
            job_cards = soup.find_all("div", class_=lambda x: x and "base-card" in (x if x else "").lower())
            
            logger.info(f"    Trouvé {len(job_cards)} éléments job")
            
            for card in job_cards:
                try:
                    # Extraire titre
                    title_elem = card.find("h3", class_=lambda x: x and "base-search-card__title" in (x if x else "").lower())
                    if not title_elem:
                        title_elem = card.find("a", {"data-job-id": True})
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    if not title or len(title) < 3:
                        continue
                    
                    # Filtrer sur titre d'abord
                    if not is_it_job(title):
                        continue
                    
                    # Extraire entreprise
                    company_elem = card.find("h4", class_=lambda x: x and "base-search-card__subtitle" in (x if x else "").lower())
                    company = company_elem.get_text(strip=True) if company_elem else "LinkedIn"
                    
                    # Extraire location
                    location_elem = card.find("span", class_=lambda x: x and "job-search-card__location" in (x if x else "").lower())
                    location = location_elem.get_text(strip=True) if location_elem else "Remote"
                    
                    # Extraire lien pour aller à la page individuelle
                    link_elem = card.find("a", {"data-job-id": True})
                    description = ""
                    
                    if link_elem and link_elem.get("href"):
                        job_url = link_elem.get("href")
                        if not job_url.startswith("http"):
                            job_url = f"https://www.linkedin.com{job_url}"
                        
                        try:
                            job_response = session.get(job_url, timeout=10)
                            if job_response.status_code == 200:
                                job_soup = BeautifulSoup(job_response.text, "html.parser")
                                # Trouver description
                                desc_elem = job_soup.find("div", class_=lambda x: x and "show-more-less-html__markup" in (x if x else "").lower())
                                if desc_elem:
                                    description = clean_text(desc_elem.get_text())
                            time.sleep(0.5)
                        except Exception as e:
                            logger.debug(f"    Job page error: {str(e)[:30]}")
                    
                    # Si pas de description, utiliser le texte du card
                    if not description:
                        description = clean_text(card.get_text())[:500]
                    
                    # Filtrer aussi sur description
                    if description and not is_it_job(title, description):
                        continue
                    
                    offer = {
                        "job_id": f"linkedin_{len(offers):04d}",
                        "title": title,
                        "company": company,
                        "location": location,
                        "description": description[:800],
                        "source": "linkedin.com",
                        "scrape_date": datetime.now().isoformat(),
                    }
                    
                    offers.append(offer)
                    logger.debug(f"    ✓ {title[:50]}")
                    
                except Exception as e:
                    logger.debug(f"    Card error: {str(e)[:30]}")
                    continue
            
            time.sleep(1)
        except Exception as e:
            logger.debug(f"  Error page {page}: {str(e)[:50]}")
            continue
    
    logger.info(f"  ✓ LinkedIn: {len(offers)} offres IT extraites")
    return offers
    """Scrape Emploi.ma - amélioré avec filtre IT et beaucoup de pages."""
    offers = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    
    # IT keywords pour filtrer
    it_keywords = ['python', 'java', 'javascript', 'developer', 'engineer', 'architect', 
                   'devops', 'cloud', 'backend', 'frontend', 'fullstack', 'senior', 
                   'lead', 'tech', 'software', 'react', 'node', 'django', 'aws', 'infra']
    
    def is_it_job(title, description=""):
        combined = (title + " " + description).lower()
        return sum(1 for kw in it_keywords if kw in combined) >= 1
    
    def clean_text(text):
        """Remove HTML tags and entities."""
        import re
        text = re.sub(r'<[^>]+>', '', text or '')
        text = re.sub(r'&[a-z]+;', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    for page in range(1, num_pages + 1):
        try:
            # Emploi.ma listing page
            url = f"https://www.emploi.ma/offres-emploi?page={page}"
            logger.info(f"  Page {page}")
            
            response = session.get(url, timeout=10)
            if response.status_code != 200:
                logger.debug(f"    Status {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Chercher les liens d'offres
            job_links = soup.find_all("a", class_=lambda x: x and "offer" in (x if x else "").lower())
            if not job_links:
                job_links = soup.find_all("a", attrs={"href": lambda x: x and "/offres-emploi/" in x if x else False})
            
            logger.info(f"    Trouvé {len(job_links)} liens")
            
            for link in job_links:
                try:
                    href = link.get("href", "")
                    if not href or "/offres-emploi/" not in href:
                        continue
                    
                    # Construire URL complète
                    job_url = urljoin("https://www.emploi.ma", href)
                    
                    # Titre initial
                    title = link.get_text(strip=True)
                    if not title or len(title) < 3:
                        continue
                    
                    # Filtrer sur titre d'abord
                    if not is_it_job(title):
                        continue
                    
                    # Scraper la page individuelle
                    try:
                        job_response = session.get(job_url, timeout=8)
                        if job_response.status_code != 200:
                            continue
                        
                        job_soup = BeautifulSoup(job_response.text, "html.parser")
                        
                        # Extraire infos
                        company = "N/A"
                        location = "Maroc"
                        description = ""
                        
                        # Chercher détails
                        for text in job_soup.find_all(["span", "p", "div"]):
                            t = text.get_text(strip=True).lower()
                            if any(city in t for city in ["casablanca", "rabat", "fez", "marrakech", "agadir"]):
                                location = text.get_text(strip=True)
                                break
                        
                        # Description
                        desc_elem = job_soup.find("div", class_=lambda x: x and "description" in (x if x else "").lower())
                        if not desc_elem:
                            desc_elem = job_soup.find("div", class_=lambda x: x and "content" in (x if x else "").lower())
                        
                        if desc_elem:
                            description = clean_text(desc_elem.get_text())
                        
                        # Filtrer aussi sur description
                        if not description or not is_it_job(title, description):
                            continue
                        
                        offer = {
                            "job_id": f"emploi_ma_{len(offers):04d}",
                            "title": title,
                            "company": company,
                            "location": location,
                            "description": description[:800],
                            "source": "emploi.ma",
                            "scrape_date": datetime.now().isoformat(),
                        }
                        
                        offers.append(offer)
                        logger.debug(f"    ✓ {title[:50]}")
                        
                        time.sleep(0.3)
                    except Exception as e:
                        logger.debug(f"    Job error: {str(e)[:30]}")
                        continue
                
                except Exception as e:
                    logger.debug(f"    Link error: {str(e)[:30]}")
                    continue
            
            time.sleep(1)
        except Exception as e:
            logger.debug(f"  Error page {page}: {str(e)[:50]}")
            continue
    
    logger.info(f"  ✓ Emploi.ma: {len(offers)} offres IT extraites")
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

