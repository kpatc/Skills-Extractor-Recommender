"""
Scraper avancé avec Selenium pour sites avec JavaScript.
Sources: ReKrute, Emploi.ma, Indeed, LinkedIn, Glassdoor, Welcome to the Jungle
"""

import logging
import time
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from utils.config import RAW_DATA_DIR

logger = logging.getLogger(__name__)


class SeleniumScraper:
    """Scraper utilisant Selenium pour sites dynamiques."""

    def __init__(self):
        """Initialise Selenium."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            
            self.webdriver = webdriver
            self.Service = Service
            self.ChromeDriverManager = ChromeDriverManager
            self.By = By
            self.WebDriverWait = WebDriverWait
            
            logger.info("✓ Selenium initialisé")
        except ImportError as e:
            logger.error(f"Selenium non disponible: {e}. pip install selenium webdriver-manager")
            raise

    def get_driver(self, headless=True):
        """Crée un driver Chrome."""
        options = self.webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        
        driver = self.webdriver.Chrome(
            service=self.Service(self.ChromeDriverManager().install()),
            options=options
        )
        return driver


class RekruteScraper(SeleniumScraper):
    """Scraper pour ReKrute.com (Maroc)."""

    def __init__(self):
        super().__init__()
        self.base_url = "https://www.rekrute.com"
        self.source = "rekrute"

    def scrape(self, num_pages: int = 5) -> List[Dict]:
        """Scrape ReKrute - n pages."""
        offers = []
        driver = None
        
        try:
            driver = self.get_driver(headless=True)
            
            for page in range(1, num_pages + 1):
                url = f"{self.base_url}/offres.html?page={page}"
                logger.info(f"ReKrute page {page}: {url}")
                
                try:
                    driver.get(url)
                    time.sleep(3)  # Laisser charger la page
                    
                    # Trouver les offres
                    job_items = driver.find_elements(self.By.CLASS_NAME, "job-item")
                    
                    for item in job_items:
                        try:
                            title = item.find_element(self.By.CLASS_NAME, "job-title").text
                            company = item.find_element(self.By.CLASS_NAME, "company-name").text
                            location = item.find_element(self.By.CLASS_NAME, "location").text
                            
                            # Essayer de récupérer la description
                            desc = ""
                            try:
                                desc = item.find_element(self.By.CLASS_NAME, "job-description").text
                            except:
                                pass
                            
                            offer = {
                                "job_id": f"rekrute_{len(offers)}",
                                "title": title,
                                "company": company,
                                "location": location,
                                "description": desc,
                                "source": self.source,
                                "scrape_date": datetime.now().isoformat(),
                            }
                            offers.append(offer)
                            
                        except Exception as e:
                            logger.debug(f"Erreur parsing offre: {e}")
                            continue
                    
                    logger.info(f"  ✓ {len(job_items)} offres trouvées")
                    
                except Exception as e:
                    logger.warning(f"Erreur page {page}: {e}")
                    continue
            
            logger.info(f"✓ ReKrute: {len(offers)} offres au total")
            
        except Exception as e:
            logger.error(f"Erreur ReKrute: {e}")
        finally:
            if driver:
                driver.quit()
        
        return offers


class EmploiMaScraper(SeleniumScraper):
    """Scraper pour Emploi.ma (Maroc)."""

    def __init__(self):
        super().__init__()
        self.base_url = "https://emploi.ma"
        self.source = "emploi.ma"

    def scrape(self, num_pages: int = 5) -> List[Dict]:
        """Scrape Emploi.ma - n pages."""
        offers = []
        driver = None
        
        try:
            driver = self.get_driver(headless=True)
            
            for page in range(1, num_pages + 1):
                url = f"{self.base_url}/offres-emploi?page={page}"
                logger.info(f"Emploi.ma page {page}: {url}")
                
                try:
                    driver.get(url)
                    time.sleep(3)
                    
                    # Trouver les offres
                    job_items = driver.find_elements(self.By.CLASS_NAME, "job-offer")
                    
                    for item in job_items:
                        try:
                            title = item.find_element(self.By.CLASS_NAME, "title").text
                            company = item.find_element(self.By.CLASS_NAME, "company").text
                            location = item.find_element(self.By.CLASS_NAME, "location").text
                            
                            desc = ""
                            try:
                                desc = item.find_element(self.By.CLASS_NAME, "description").text
                            except:
                                pass
                            
                            offer = {
                                "job_id": f"emploi_ma_{len(offers)}",
                                "title": title,
                                "company": company,
                                "location": location,
                                "description": desc,
                                "source": self.source,
                                "scrape_date": datetime.now().isoformat(),
                            }
                            offers.append(offer)
                            
                        except Exception as e:
                            logger.debug(f"Erreur parsing: {e}")
                            continue
                    
                    logger.info(f"  ✓ {len(job_items)} offres trouvées")
                    
                except Exception as e:
                    logger.warning(f"Erreur page {page}: {e}")
                    continue
            
            logger.info(f"✓ Emploi.ma: {len(offers)} offres au total")
            
        except Exception as e:
            logger.error(f"Erreur Emploi.ma: {e}")
        finally:
            if driver:
                driver.quit()
        
        return offers


class IndeedScraper(SeleniumScraper):
    """Scraper pour Indeed."""

    def __init__(self):
        super().__init__()
        self.base_url = "https://fr.indeed.com"
        self.source = "indeed"

    def scrape(self, num_pages: int = 5, query: str = "developer") -> List[Dict]:
        """Scrape Indeed - n pages."""
        offers = []
        driver = None
        
        try:
            driver = self.get_driver(headless=True)
            
            for page in range(0, num_pages):
                url = f"{self.base_url}/jobs?q={query}&start={page*10}"
                logger.info(f"Indeed page {page+1}: {url}")
                
                try:
                    driver.get(url)
                    time.sleep(3)
                    
                    # Trouver les offres
                    job_cards = driver.find_elements(self.By.CLASS_NAME, "job_seen_beacon")
                    
                    for card in job_cards:
                        try:
                            title = card.find_element(self.By.TAG_NAME, "h2").text
                            company = card.find_element(self.By.CLASS_NAME, "companyName").text
                            location = card.find_element(self.By.CLASS_NAME, "companyLocation").text
                            
                            desc = ""
                            try:
                                desc = card.find_element(self.By.CLASS_NAME, "job-snippet").text
                            except:
                                pass
                            
                            offer = {
                                "job_id": f"indeed_{len(offers)}",
                                "title": title,
                                "company": company,
                                "location": location,
                                "description": desc,
                                "source": self.source,
                                "scrape_date": datetime.now().isoformat(),
                            }
                            offers.append(offer)
                            
                        except Exception as e:
                            logger.debug(f"Erreur parsing: {e}")
                            continue
                    
                    logger.info(f"  ✓ {len(job_cards)} offres trouvées")
                    
                except Exception as e:
                    logger.warning(f"Erreur page {page+1}: {e}")
                    continue
            
            logger.info(f"✓ Indeed: {len(offers)} offres au total")
            
        except Exception as e:
            logger.error(f"Erreur Indeed: {e}")
        finally:
            if driver:
                driver.quit()
        
        return offers
