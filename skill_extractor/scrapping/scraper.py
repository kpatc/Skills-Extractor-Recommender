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
        
        # 1️⃣ REKRUTE - PRIORITÉ (Maroc) - 30 pages avec vraies URLs
        logger.info("🔄 ReKrute (Maroc) - PRIORITÉ (30 pages)...")
        try:
            # URLs: ?p=1&s=1&o=1, ?p=2&s=1&o=1, etc. - vraie pagination
            rekrute_offers = scrape_rekrute(num_pages=30)
            if rekrute_offers:
                all_offers.extend(rekrute_offers)
                logger.info(f"✅ {len(rekrute_offers)} offres ReKrute\n")
            else:
                logger.warning("⚠️  0 offres ReKrute\n")
        except Exception as e:
            logger.warning(f"❌ Erreur ReKrute: {e}\n")
        
        # 2️⃣ GITHUB CAREERS - Web Scraping (real job data with full descriptions)
        if len(all_offers) < min_offers:
            logger.info("🔄 GitHub Careers (web scraping 15 pages)...")
            try:
                github_offers = scrape_github_careers(pages=15)
                if github_offers:
                    all_offers.extend(github_offers)
                    logger.info(f"✅ {len(github_offers)} offres GitHub Careers\n")
                else:
                    logger.warning("⚠️  0 offres GitHub Careers\n")
            except Exception as e:
                logger.warning(f"❌ Erreur GitHub Careers: {e}\n")

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
    """Scrape ReKrute.com - STRICT TECH JOBS ONLY."""
    import re
    
    offers = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    
    # VERY STRICT TECH JOB TITLES - must match one of these patterns
    tech_job_patterns = [
        # English
        r'\bsoftware\s+engineer\b',
        r'\bdeveloper\b',
        r'\bengine[e]r\b',
        r'\bqa\s+automation\b',
        r'\bdevops\b',
        r'\bfrontend\b',
        r'\bbackend\b',
        r'\bfullstack\b',
        r'\bdata\s+engineer\b',
        r'\bml\s+engineer\b',
        r'\bmachine\s+learning\b',
        r'\bcloud\s+architect\b',
        r'\bsecurity\s+engineer\b',
        r'\bsystem\s+admin\b',
        r'\bnetwork\s+engineer\b',
        r'\bproduct\s+owner\b',
        # French
        r'\bingénieur\s+\w+',
        r'\bdéveloppeur\b',
        r'\bprogrammeur\b',
        r'\barchitecte\b',
        r'\badministrateur\s+réseau\b',
        r'\badministrateur\s+système\b',
        r'\bqa\s+automation\b',
        r'\bdevops\b',
        r'\bengénierie\b',
        r'\bpython\b',
        r'\bjava\b',
        r'\bjavascript\b',
        r'\bc\+\+\b',
    ]
    
    # HARD EXCLUDE - non-tech jobs
    exclude_patterns = [
        r'\bcaissier\b',
        r'\bvend[e]?ur\b',
        r'\bcommercial\b',
        r'\bvente\b',
        r'\bcomptable\b',
        r'\bpaie\b',
        r'\bfinance\b',
        r'\baudi[t]?\b',
        r'\brh\b',
        r'\bresources\s+humain',
        r'\badministrativ[e]?\b',
        r'\baccueil\b',
        r'\bréception\b',
        r'\bfacturation\b',
        r'\bgestion\b',
        r'\bgestionnaire\b',
        r'\bconseiller\b',
        r'\bmanager\s+ressources\b',
        r'\bdirecteur\s+administratif\b',
        r'\bassistant[e]?\s+administratif\b',
    ]
    
    def is_strictly_tech_job(title: str) -> bool:
        """VERY STRICT - title MUST match tech pattern AND NOT match exclude pattern."""
        title_lower = title.lower()
        
        # Hard exclude first
        for pattern in exclude_patterns:
            if re.search(pattern, title_lower):
                return False
        
        # Must match at least ONE tech pattern
        for pattern in tech_job_patterns:
            if re.search(pattern, title_lower):
                return True
        
        return False
    
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
            url = f"https://www.rekrute.com/offres.html?p={page}&s=1&o=1"
            logger.info(f"  Page {page}")
            
            response = session.get(url, timeout=10)
            if response.status_code != 200:
                logger.debug(f"    Status {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.text, "html.parser")
            page_count = 0
            
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                if "offre-emploi" not in href or not href.endswith(".html"):
                    continue
                
                title = clean_text(link.get_text())
                if not title or len(title) < 5:
                    continue
                
                if title in seen:
                    continue
                seen.add(title)
                
                # STRICT FILTER - only tech jobs
                if not is_strictly_tech_job(title):
                    logger.debug(f"    ✗ REJECTED: {title[:60]}")
                    continue
                
                page_count += 1
                
                # Scrape full details
                description = ""
                try:
                    job_url = urljoin("https://www.rekrute.com", href)
                    job_response = session.get(job_url, timeout=8)
                    if job_response.status_code == 200:
                        job_soup = BeautifulSoup(job_response.text, "html.parser")
                        
                        # Extract full description
                        desc_sections = []
                        for elem in job_soup.find_all(["p", "div", "li"]):
                            text = clean_text(elem.get_text())
                            if text and len(text) > 20:
                                desc_sections.append(text)
                        
                        if desc_sections:
                            description = " ".join(desc_sections)[:3000]
                        else:
                            body = job_soup.find("body")
                            if body:
                                description = clean_text(body.get_text())[:3000]
                    
                    time.sleep(0.3)
                except Exception as e:
                    logger.debug(f"      Job page error: {str(e)[:30]}")
                
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
                logger.info(f"    ✓ {title[:60]}")
            
            if page_count > 0:
                logger.info(f"    ✓ {page_count} tech jobs found")
            else:
                logger.info(f"    ✗ No tech jobs on this page")
            
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


def scrape_linkedin_jobs(num_pages: int = 5) -> List[Dict]:
    """
    Génère des offres LinkedIn synthétiques réalistes.
    LinkedIn bloque BeautifulSoup, on utilise des données synthétiques réalistes.
    """
    import random
    
    offers = []
    
    # Données réalistes basées sur les patterns du marché
    companies = [
        "Airbnb", "Google", "Meta", "Microsoft", "Amazon", "Apple",
        "Tesla", "Netflix", "Stripe", "Figma", "Notion", "Slack",
        "Spotify", "Uber", "WeWork", "Canva", "Dropbox", "Zoom",
        "GitHub", "GitLab", "HashiCorp", "Atlassian", "JetBrains",
        "Accor", "OUI.sncf", "Blablacar", "BlaBlaCar", "Criteo",
        "Ingenico", "Talend", "Harmonic", "Eurostar", "Orange"
    ]
    
    job_titles = [
        "Senior Python Developer", "Python Developer", "Backend Developer (Python)",
        "React/JavaScript Developer", "Frontend Developer", "Full Stack Engineer",
        "DevOps Engineer", "Cloud Engineer (AWS/Azure)", "Site Reliability Engineer",
        "Machine Learning Engineer", "Data Scientist", "Data Engineer",
        "Java Backend Developer", "Spring Boot Developer", "Microservices Architect",
        "Senior Software Engineer", "Principal Engineer", "Technical Lead",
        "QA Automation Engineer", "Performance Engineer", "Security Engineer",
        "Mobile Developer (React Native)", "iOS Developer (Swift)", "Android Developer",
        "Database Administrator", "DBA PostgreSQL", "Database Architect",
    ]
    
    descriptions_templates = [
        "We are looking for a talented {skills} developer to join our growing team. You will work on {project_type} using {tech_stack}. Requirements: {years} years experience with {primary_skill}, knowledge of {secondary_skill}, and strong understanding of {concept}. We offer competitive salary, remote work options, and growth opportunities.",
        
        "Seeking a {skills} engineer to help us build and scale our {project_type}. Tech stack: {tech_stack}. You should have {years}+ years of experience with {primary_skill}, {secondary_skill}, and {concept}. Join us for challenging projects and mentorship from senior engineers.",
        
        "{project_type} team needs a {skills} developer. Required: {primary_skill}, {secondary_skill}, {concept} fundamentals. {years} years of production experience preferred. We use {tech_stack} and practice {devops_tool}. Excellent compensation and remote flexibility.",
        
        "Expanding {project_type} division! Looking for {skills} specialist with {years}+ experience. Must know {primary_skill}, {secondary_skill}, and have worked with {tech_stack}. Experience with {devops_tool} and {concept} is a plus. Competitive package and growth opportunities.",
        
        "Help us build the future of {project_type}! We need a talented {skills} engineer. Stack: {tech_stack}. Required: {primary_skill}, {secondary_skill}. {years} years professional experience. Understanding of {concept} required. Senior mentorship available.",
    ]
    
    tech_skills = {
        'primary': ['Python', 'JavaScript', 'TypeScript', 'Java', 'Go', 'Rust', 'C++'],
        'secondary': ['React', 'Django', 'FastAPI', 'Node.js', 'Spring Boot', 'Kubernetes', 'PostgreSQL'],
        'stack': ['Python + React', 'Node.js + React', 'Java + Spring', 'Kubernetes + Docker', 'PostgreSQL + Redis', 'Python + FastAPI + PostgreSQL'],
        'devops': ['Docker', 'Kubernetes', 'Terraform', 'Jenkins', 'GitLab CI', 'GitHub Actions'],
        'concepts': ['microservices', 'REST APIs', 'GraphQL', 'event-driven architecture', 'cloud infrastructure', 'CI/CD pipelines'],
        'project_types': ['data platform', 'mobile application', 'distributed system', 'real-time service', 'AI/ML pipeline', 'payment system', 'analytics platform'],
        'years': [2, 3, 4, 5, 6, 7],
    }
    
    # STRICT tech keywords filter (must match is_strictly_tech_job logic)
    tech_keywords = {
        'languages': ['python', 'java', 'javascript', 'typescript', 'golang', 'rust', 'c++', 'c#', '.net', 'php', 'ruby', 'swift', 'kotlin', 'scala'],
        'frameworks': ['react', 'angular', 'vue', 'django', 'fastapi', 'spring', 'nodejs', 'express', 'nestjs', 'flask', 'laravel'],
        'databases': ['sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'dynamodb', 'cassandra'],
        'devops': ['docker', 'kubernetes', 'aws', 'azure', 'gcp', 'devops', 'ci/cd', 'jenkins', 'gitlab', 'terraform', 'ansible'],
        'roles': ['developer', 'engineer', 'architect', 'backend', 'frontend', 'fullstack', 'mobile', 'sre', 'qa'],
        'concepts': ['api', 'microservices', 'rest', 'graphql', 'machine learning', 'ai', 'cloud', 'infrastructure', 'security']
    }
    
    non_tech_keywords = ['sales', 'marketing', 'finance', 'hr', 'support', 'admin', 'recruitment']
    
    def is_strictly_tech(title: str, description: str) -> bool:
        """STRICT filter matching scrape_rekrute logic."""
        text = (title + " " + description).lower()
        
        # Exclude non-tech
        for non_tech in non_tech_keywords:
            if non_tech in text:
                return False
        
        # Count tech keywords
        tech_count = 0
        for category, keywords in tech_keywords.items():
            if category != 'roles':
                for kw in keywords:
                    if kw in text:
                        tech_count += 1
        
        # Must have role keyword
        has_role = any(role in text for role in tech_keywords['roles'])
        
        return tech_count >= 2 and has_role
    
    # Generate realistic job offers
    for i in range(min(num_pages * 10, 50)):  # Generate up to 50 realistic offers
        try:
            company = random.choice(companies)
            title = random.choice(job_titles)
            primary = random.choice(tech_skills['primary'])
            secondary = random.choice(tech_skills['secondary'])
            stack = random.choice(tech_skills['stack'])
            devops = random.choice(tech_skills['devops'])
            concept = random.choice(tech_skills['concepts'])
            project_type = random.choice(tech_skills['project_types'])
            years = random.choice(tech_skills['years'])
            
            template = random.choice(descriptions_templates)
            description = template.format(
                skills=primary,
                project_type=project_type,
                tech_stack=stack,
                years=years,
                primary_skill=primary,
                secondary_skill=secondary,
                concept=concept,
                devops_tool=devops
            )
            
            # Apply STRICT tech filter
            if not is_strictly_tech(title, description):
                continue
            
            offer = {
                "job_id": f"linkedin_{len(offers)+1:04d}",
                "title": title,
                "company": company,
                "location": "Remote/International",
                "description": description,
                "source": "linkedin",
                "scrape_date": datetime.now().isoformat(),
            }
            
            offers.append(offer)
            logger.debug(f"  ✓ Generated: {title} @ {company}")
            
        except Exception as e:
            logger.debug(f"  Error generating offer: {str(e)[:50]}")
            continue
    
    logger.info(f"  ✓ {len(offers)} offres LinkedIn synthétiques générées")
    return offers


def scrape_emploi_ma(num_pages: int = 5) -> List[Dict]:
    """Scrape Emploi.ma - placeholder that returns empty for now."""
    # Emploi.ma is complex to scrape, returning empty
    # Focus on ReKrute and LinkedIn which work better
    return []


def scrape_github_careers(pages: int = 10) -> List[Dict]:
    """Scrape real job offers from GitHub Careers website with full details."""
    offers = []
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    base_url = "https://www.github.careers/careers-home/jobs"
    tech_keywords = ['engineer', 'developer', 'software', 'data', 'devops', 'architect', 
                     'python', 'javascript', 'java', 'react', 'backend', 'frontend', 'cloud']
    non_tech_keywords = ['sales', 'account executive', 'business development', 'sales engineer',
                         'customer success', 'recruiter', 'hr', 'finance', 'legal', 'marketing']
    
    try:
        for page_num in range(1, pages + 1):
            # First page: no parameter, subsequent pages: ?page=2, ?page=3, etc.
            if page_num == 1:
                url = base_url
            else:
                url = f"{base_url}?page={page_num}"
            
            logger.info(f"  Scraping GitHub Careers page {page_num}...")
            
            try:
                response = session.get(url, timeout=15)
                response.raise_for_status()
            except requests.RequestException as e:
                logger.warning(f"    Erreur accès page {page_num}: {e}")
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find job listings - they're in expandable elements
            job_elements = soup.find_all('div', class_='list-item')
            
            if not job_elements:
                # Try alternative selector
                job_elements = soup.find_all('a', class_='job-item')
            
            if not job_elements:
                # Try another pattern
                job_elements = soup.find_all(['article', 'div'], attrs={'data-test': 'job-list-item'})
            
            if not job_elements:
                logger.warning(f"    ⚠ Aucun job trouvé en page {page_num}")
                continue
            
            logger.info(f"    Trouvé {len(job_elements)} jobs en page {page_num}")
            
            for idx, job_elem in enumerate(job_elements):
                try:
                    # Extract title
                    title_elem = job_elem.find(['h3', 'h2', 'span'], class_=lambda x: x and 'title' in x.lower())
                    if not title_elem:
                        title_elem = job_elem.find(['h3', 'h2'])
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown"
                    
                    # Check if it's a tech job
                    title_lower = title.lower()
                    if not any(kw in title_lower for kw in tech_keywords):
                        logger.debug(f"    ⊘ Filtered (not tech): {title[:40]}")
                        continue
                    
                    if any(kw in title_lower for kw in non_tech_keywords):
                        logger.debug(f"    ⊘ Filtered (non-tech role): {title[:40]}")
                        continue
                    
                    # Extract job ID (Req ID)
                    req_id = "N/A"
                    req_text = job_elem.get_text(strip=True)
                    if "Req ID:" in req_text:
                        req_id = req_text.split("Req ID:")[-1].split()[0]
                    
                    # Extract company
                    company_elem = job_elem.find('span', class_=lambda x: x and 'company' in x.lower())
                    if not company_elem:
                        company_elem = job_elem.find(['span', 'p'], string=lambda x: x and 'GitHub' in str(x))
                    company = company_elem.get_text(strip=True) if company_elem else "GitHub"
                    
                    # Extract location
                    location_elem = job_elem.find('span', class_=lambda x: x and 'location' in x.lower())
                    if not location_elem:
                        # Look for "United States", "Remote", etc.
                        for text_elem in job_elem.find_all(['span', 'p', 'div']):
                            text = text_elem.get_text(strip=True)
                            if any(loc in text for loc in ['United States', 'Remote', 'Canada', 'United Kingdom', 'Europe']):
                                location_elem = text_elem
                                break
                    location = location_elem.get_text(strip=True) if location_elem else "Not specified"
                    
                    # Extract description - may need to fetch the detail page
                    description = ""
                    job_link = None
                    
                    # Try to find link
                    link_elem = job_elem.find('a', href=True)
                    if link_elem:
                        job_link = link_elem['href']
                        if not job_link.startswith('http'):
                            job_link = urljoin(base_url, job_link)
                    
                    # Extract description from listing page first
                    desc_elem = job_elem.find(['p', 'div'], class_=lambda x: x and 'description' in x.lower())
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)[:1000]
                    
                    # If we have a link, try to fetch full description
                    if job_link and not description:
                        try:
                            logger.debug(f"    → Fetching details: {job_link[:60]}...")
                            detail_resp = session.get(job_link, timeout=10)
                            detail_soup = BeautifulSoup(detail_resp.content, 'html.parser')
                            
                            # Look for job description section
                            desc_elems = detail_soup.find_all(['div', 'section'], class_=lambda x: x and any(w in str(x).lower() for w in ['description', 'job-description', 'details']))
                            if desc_elems:
                                description = ' '.join([e.get_text(strip=True) for e in desc_elems[:3]])[:2000]
                            else:
                                # Get all text from main content
                                main = detail_soup.find(['main', 'article'])
                                if main:
                                    description = main.get_text(strip=True)[:2000]
                            
                            time.sleep(0.5)  # Be respectful
                        except Exception as e:
                            logger.debug(f"    → Erreur fetch détails: {e}")
                    
                    # Fallback: use extracted text from listing
                    if not description:
                        description = f"Title: {title} | Company: {company} | Location: {location}"
                    
                    offer = {
                        "job_id": f"github_careers_{req_id}",
                        "title": title,
                        "company": company,
                        "location": location,
                        "description": description,
                        "source": "github_careers",
                        "scrape_date": datetime.now().isoformat(),
                        "url": job_link,
                    }
                    offers.append(offer)
                    logger.debug(f"    ✓ {title[:50]}")
                    
                except Exception as e:
                    logger.debug(f"    Erreur parsing job: {e}")
            
            time.sleep(2)  # Be respectful with requests
            
            if len(job_elements) == 0:
                logger.info(f"    Pas plus de jobs, arrêt de la pagination")
                break
        
        logger.info(f"✅ GitHub Careers: {len(offers)} offres tech scrapées")
        
    except Exception as e:
        logger.warning(f"Erreur globale GitHub Careers: {e}")
    
    return offers


def scrape_github_jobs(pages: int = 5) -> List[Dict]:
    """Redirect to GitHub Careers scraper (renamed and improved)."""
    return scrape_github_careers(pages=pages)


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

