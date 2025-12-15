"""
Advanced Skills Extractor using NLP techniques
- Section detection
- Intelligent tokenization
- Fuzzy matching
- Context-aware extraction
"""

import re
from typing import List, Dict, Set, Tuple
from difflib import SequenceMatcher
import json

# Comprehensive skills database with variations
SKILLS_DATABASE = {
    # Programming Languages
    "langages_programmation": {
        "python": ["python", "py", "python3"],
        "java": ["java"],
        "javascript": ["javascript", "js"],
        "node.js": ["node.js", "nodejs", "node"],
        "typescript": ["typescript", "ts"],
        "csharp": ["csharp", "c#", ".net"],
        "cpp": ["c++", "cpp"],
        "c": ["c language"],
        "php": ["php"],
        "ruby": ["ruby"],
        "go": ["go", "golang"],
        "rust": ["rust"],
        "scala": ["scala"],
        "kotlin": ["kotlin"],
        "matlab": ["matlab"],
        "swift": ["swift"],
        "objective-c": ["objective-c", "objc"],
        "perl": ["perl"],
    },
    
    # Web Frameworks
    "frameworks_web": {
        "django": ["django"],
        "flask": ["flask"],
        "fastapi": ["fastapi"],
        "react": ["react", "reactjs", "react.js"],
        "angular": ["angular", "angular.js"],
        "vue": ["vue", "vue.js"],
        "nextjs": ["nextjs", "next.js"],
        "express": ["express", "express.js"],
        "spring": ["spring"],
        "spring boot": ["spring boot", "springboot"],
        "laravel": ["laravel"],
        "rails": ["rails", "ruby on rails"],
        "asp.net": ["asp.net", "aspnet"],
        "remix": ["remix"],
        "svelte": ["svelte"],
        "nuxt": ["nuxt", "nuxt.js"],
    },
    
    # Databases
    "bases_donnees": {
        "postgresql": ["postgresql", "postgres"],
        "mysql": ["mysql"],
        "mongodb": ["mongodb"],
        "redis": ["redis"],
        "elasticsearch": ["elasticsearch"],
        "graphql": ["graphql"],
        "sql": ["sql", "sql server", "tsql"],
        "oracle": ["oracle"],
        "cassandra": ["cassandra"],
        "dynamodb": ["dynamodb"],
        "firebase": ["firebase"],
        "supabase": ["supabase"],
        "mariadb": ["mariadb"],
    },
    
    # Cloud & DevOps
    "cloud_devops": {
        "aws": ["aws", "amazon web services", "amazon aws"],
        "azure": ["azure", "microsoft azure"],
        "gcp": ["gcp", "google cloud", "google cloud platform"],
        "docker": ["docker"],
        "kubernetes": ["kubernetes", "k8s", "k8"],
        "jenkins": ["jenkins"],
        "gitlab ci": ["gitlab ci", "gitlab-ci"],
        "github actions": ["github actions"],
        "terraform": ["terraform"],
        "ansible": ["ansible"],
        "helm": ["helm"],
        "prometheus": ["prometheus"],
        "grafana": ["grafana"],
        "nginx": ["nginx"],
        "apache": ["apache"],
        "linux": ["linux"],
    },
    
    # AI/ML
    "ai_ml": {
        "machine learning": ["machine learning", "ml"],
        "deep learning": ["deep learning"],
        "tensorflow": ["tensorflow", "tf"],
        "pytorch": ["pytorch"],
        "scikit-learn": ["scikit-learn", "scikit learn", "sklearn"],
        "pandas": ["pandas"],
        "numpy": ["numpy"],
        "nlp": ["nlp", "natural language processing"],
        "computer vision": ["computer vision", "cv", "image processing"],
        "hugging face": ["hugging face"],
        "openai": ["openai"],
        "llm": ["llm", "large language model"],
    },
    
    # Development Tools
    "outils_dev": {
        "git": ["git", "github", "gitlab", "bitbucket"],
        "vscode": ["vscode", "visual studio code"],
        "jira": ["jira"],
        "confluence": ["confluence"],
        "slack": ["slack"],
        "postman": ["postman"],
        "swagger": ["swagger", "openapi"],
        "npm": ["npm"],
        "pip": ["pip"],
        "maven": ["maven"],
        "gradle": ["gradle"],
        "webpack": ["webpack"],
        "docker compose": ["docker compose", "docker-compose"],
        "versionning": ["versionning"],
    },
    
    # Technical Concepts
    "concepts_techniques": {
        "rest api": ["rest", "rest api", "restful"],
        "graphql": ["graphql"],
        "microservices": ["microservices"],
        "devops": ["devops"],
        "ci/cd": ["ci/cd", "cicd", "continuous integration", "continuous deployment"],
        "agile": ["agile", "scrum", "kanban"],
        "sre": ["sre", "site reliability"],
        "iac": ["iac", "infrastructure as code"],
        "event driven": ["event driven", "event-driven"],
        "serverless": ["serverless"],
        "containerization": ["containerization"],
        "testing": ["unit testing", "integration testing", "e2e testing", "testing"],
        "api": ["api", "apis"],
    },
}

# Keywords that define skill sections
SKILL_SECTION_KEYWORDS = [
    r"required\s+skills?",
    r"technical\s+skills?",
    r"qualifications?",
    r"requirements?",
    r"must\s+have",
    r"nice\s+to\s+have",
    r"tech\s+stack",
    r"technologies?",
    r"expertise",
    r"experience\s+with",
    r"knowledge\s+of",
    r"proficiency",
    r"familiarity\s+with",
]

class AdvancedSkillsExtractor:
    def __init__(self):
        self.skills_db = SKILLS_DATABASE
        self.create_flat_skills_map()
    
    def create_flat_skills_map(self):
        """Create a flat map of all skills for faster lookup"""
        self.flat_skills = {}
        for category, skills in self.skills_db.items():
            for skill_name, variations in skills.items():
                for variation in variations:
                    self.flat_skills[variation.lower()] = (skill_name, category)
    
    def extract_skill_sections(self, text: str) -> List[str]:
        """Extract sections that likely contain skills"""
        sections = []
        text_lower = text.lower()
        
        # Split by common section separators
        parts = re.split(r'\n\s*(?=\w+\s*:)', text)
        
        for part in parts:
            # Check if this part matches skill section keywords
            for keyword in SKILL_SECTION_KEYWORDS:
                if re.search(keyword, part, re.IGNORECASE):
                    sections.append(part)
                    break
        
        return sections if sections else [text]
    
    def tokenize_skills(self, text: str) -> List[str]:
        """Tokenize text to extract potential skills"""
        # Remove common words and clean
        text = text.lower()
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Split by common delimiters but preserve multi-word skills
        tokens = re.split(r'[,\n/•\-]|\s+and\s+|\s+or\s+|\s*\|\s*|\s+with\s+', text)
        
        # Clean tokens
        cleaned = []
        for token in tokens:
            token = token.strip()
            # Remove common prefix words
            token = re.sub(r'^\s*(using|knowledge\s+of|experience\s+in|proficiency\s+in|familiarity\s+with|basic|advanced|intermediate|years?|experience|strong|good|fluent|proficient|certified|certification|able\s+to)\s+', '', token)
            # Remove trailing suffixes
            token = re.sub(r'\s+(required|preferred|optional|desired)s?\s*$', '', token)
            # Remove parentheses and content
            token = re.sub(r'\s*\([^)]*\)\s*', ' ', token)
            token = token.strip()
            
            if len(token) > 2 and not re.match(r'^\d+', token):
                cleaned.append(token)
        
        return cleaned
    
    def fuzzy_match_skill(self, token: str, threshold: float = 0.75) -> Tuple[str, str, float]:
        """
        Fuzzy match a token against the skills database
        Returns (skill_name, category, confidence)
        """
        token_lower = token.lower()
        
        # Filter out single letters and very short tokens (except known ones like "go", "r", "ml")
        if len(token_lower) <= 2:
            known_short = {"go", "r", "py", "ml", "ai"}
            if token_lower not in known_short:
                return (None, None, 0)
        
        # Exact match first
        if token_lower in self.flat_skills:
            skill_name, category = self.flat_skills[token_lower]
            return (skill_name, category, 1.0)
        
        # Fuzzy match
        best_match = None
        best_score = 0
        
        for skill_variation, (skill_name, category) in self.flat_skills.items():
            # Quick length check - be more strict
            if abs(len(token_lower) - len(skill_variation)) > 4:
                continue
            
            ratio = SequenceMatcher(None, token_lower, skill_variation).ratio()
            
            if ratio > best_score and ratio >= threshold:
                best_score = ratio
                best_match = (skill_name, category, ratio)
        
        return best_match if best_match else (None, None, 0)
    
    def extract_skills(self, job_description: str, title: str = "") -> Dict[str, List[str]]:
        """Extract skills from job description and title"""
        results = {
            "langages_programmation": set(),
            "frameworks_web": set(),
            "bases_donnees": set(),
            "cloud_devops": set(),
            "ai_ml": set(),
            "outils_dev": set(),
            "concepts_techniques": set(),
            "autres_technologies": set(),
        }
        
        # Extract skill sections first
        skill_sections = self.extract_skill_sections(job_description)
        
        # Tokenize and extract from description
        tokens = []
        for section in skill_sections:
            tokens.extend(self.tokenize_skills(section))
        
        # Also extract from title (always relevant for skills)
        if title:
            tokens.extend(self.tokenize_skills(title))
        
        # Match skills
        matched_skills = set()
        for token in tokens:
            skill_name, category, confidence = self.fuzzy_match_skill(token)
            
            # Only accept matches with good confidence (0.75 for fuzzy, 1.0 for exact)
            if skill_name and confidence >= 0.75:
                if category in results:
                    results[category].add(skill_name)
                    matched_skills.add(skill_name)
        
        # If we found few skills, be less strict and search the entire text
        if len(matched_skills) < 2:
            all_tokens = self.tokenize_skills(f"{title} {job_description}")
            for token in all_tokens:
                # Skip if already matched
                skill_name, category, confidence = self.fuzzy_match_skill(token)
                
                if skill_name and confidence >= 0.70 and skill_name not in matched_skills:
                    if category in results:
                        results[category].add(skill_name)
                        matched_skills.add(skill_name)
        
        # Convert sets to sorted lists
        return {k: sorted(list(v)) for k, v in results.items() if v}
    
    def extract_from_offers(self, offers: List[Dict]) -> List[Dict]:
        """Extract skills from a list of job offers"""
        for offer in offers:
            description = offer.get('description', '')
            title = offer.get('title', '')
            
            # Extract skills
            skills_categorized = self.extract_skills(description, title)
            
            # Flatten skills list
            all_skills = []
            for category, skills in skills_categorized.items():
                all_skills.extend(skills)
            
            offer['skills_categorized'] = skills_categorized
            offer['skills'] = sorted(list(set(all_skills)))
            offer['num_skills'] = len(offer['skills'])
        
        return offers


def extract_skills_from_offers_advanced(offers: List[Dict]) -> List[Dict]:
    """Main function to extract skills from job offers"""
    extractor = AdvancedSkillsExtractor()
    return extractor.extract_from_offers(offers)
