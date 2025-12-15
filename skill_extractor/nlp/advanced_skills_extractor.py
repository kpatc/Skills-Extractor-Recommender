"""
Advanced Skills Extraction with validation
Uses multiple strategies to ensure only real tech skills are extracted
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple
from difflib import SequenceMatcher
import numpy as np

class SkillsExtractor:
    """Advanced skills extraction engine with validation"""
    
    # Comprehensive tech skills database organized by category
    TECH_SKILLS_DB = {
        'languages': {
            'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#', 'Go', 'Rust',
            'PHP', 'Ruby', 'Swift', 'Kotlin', 'R', 'MATLAB', 'Scala', 'Groovy',
            'Perl', 'Bash', 'Shell', 'PowerShell', 'VB.NET', 'Objective-C', 'Dart',
            'Elixir', 'Haskell', 'Clojure', 'Scheme'
        },
        'frontend': {
            'React', 'Angular', 'Vue.js', 'Vue', 'Svelte', 'Next.js', 'Nuxt',
            'jQuery', 'Backbone.js', 'Ember.js', 'Flutter', 'React Native',
            'HTML', 'CSS', 'SASS', 'SCSS', 'LESS', 'Tailwind', 'Bootstrap',
            'Material-UI', 'Ant Design', 'Chakra UI', 'Storybook'
        },
        'backend': {
            'Django', 'FastAPI', 'Flask', 'Spring Boot', 'Spring', 'Express.js',
            'Nestjs', 'NestJS', 'FastAPI', 'Fastify', 'Koa', 'Hapi', 'Rails',
            'Laravel', 'Symfony', 'ASP.NET', 'ASP NET', '.NET Core', '.NET',
            'Hibernate', 'JPA', 'Sequelize', 'TypeORM', 'Prisma', 'SQLAlchemy'
        },
        'databases': {
            'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
            'Oracle', 'SQL Server', 'Cassandra', 'DynamoDB', 'Firebase',
            'Firestore', 'Neo4j', 'Memcached', 'SQLite', 'MariaDB',
            'CouchDB', 'RethinkDB', 'Cosmos DB', 'InfluxDB', 'TimescaleDB'
        },
        'devops': {
            'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Google Cloud',
            'Terraform', 'Ansible', 'Jenkins', 'GitLab CI', 'GitHub Actions',
            'CircleCI', 'Travis CI', 'Helm', 'Prometheus', 'Grafana',
            'ELK Stack', 'DataDog', 'New Relic', 'Heroku', 'CloudFlare'
        },
        'ai_ml': {
            'TensorFlow', 'PyTorch', 'Scikit-learn', 'Keras', 'OpenAI',
            'Hugging Face', 'XGBoost', 'LightGBM', 'NLTK', 'SpaCy',
            'OpenCV', 'Pandas', 'NumPy', 'SciPy', 'Matplotlib',
            'Seaborn', 'Plotly', 'Jupyter', 'Anaconda', 'MLflow'
        },
        'tools': {
            'Git', 'GitHub', 'GitLab', 'Bitbucket', 'JIRA', 'Confluence',
            'Slack', 'Postman', 'VS Code', 'IntelliJ', 'Eclipse',
            'Vim', 'Emacs', 'Sublime', 'Atom', 'DataGrip',
            'Docker Compose', 'Webpack', 'Babel', 'ESLint', 'Prettier'
        },
        'concepts': {
            'REST API', 'GraphQL', 'Microservices', 'SOLID', 'Design Patterns',
            'Agile', 'Scrum', 'Kanban', 'CI/CD', 'TDD', 'BDD', 'DDD',
            'CQRS', 'Event Sourcing', 'Reactive Programming', 'Functional Programming'
        }
    }
    
    # Non-tech skills to exclude
    NON_TECH_KEYWORDS = {
        'communication', 'management', 'leadership', 'teamwork', 'organization',
        'client service', 'sales', 'marketing', 'negotiation', 'presentation',
        'analytical', 'problem solving', 'critical thinking', 'planning',
        'french', 'english', 'arabic', 'spanish', 'german', 'portuguese',
        'license', 'permit', 'driving', 'language', 'soft skills'
    }
    
    # Job titles that are NOT tech
    NON_TECH_JOB_TITLES = {
        'caissier', 'cashier', 'vendeur', 'sales', 'marketing', 'accounting',
        'comptable', 'finance', 'hr', 'ressources humaines', 'commercial',
        'manager', 'directeur', 'chef', 'assistant', 'administratif',
        'secrétaire', 'secretary', 'receptionist', 'accueil'
    }
    
    def __init__(self):
        # Build flat skill set for easier lookup
        self.all_skills_flat = set()
        for category in self.TECH_SKILLS_DB.values():
            self.all_skills_flat.update(category)
    
    def is_tech_job(self, title: str, description: str) -> bool:
        """Determine if a job is actually tech-related"""
        combined_text = f"{title} {description}".lower()
        
        # Check for non-tech job titles
        for non_tech in self.NON_TECH_JOB_TITLES:
            if non_tech in combined_text:
                # But check if there are clear tech indicators
                tech_count = sum(1 for skill in self.all_skills_flat 
                               if skill.lower() in combined_text)
                if tech_count == 0:
                    return False
        
        # Count tech indicators
        tech_indicators = [
            'développ', 'develop', 'engineer', 'ingénieur', 'technic',
            'informatic', 'informatique', 'programmer', 'coding', 'coding',
            'devops', 'sysadmin', 'architecture', 'backend', 'frontend',
            'fullstack', 'full-stack', 'cloud', 'database', 'api'
        ]
        
        tech_count = sum(1 for indicator in tech_indicators 
                        if indicator in combined_text)
        
        return tech_count >= 2 or any(skill.lower() in combined_text 
                                     for skill in self.all_skills_flat)
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from job description"""
        if not text:
            return []
        
        text_lower = text.lower()
        found_skills = []
        
        # Strategy 1: Exact matches (case-insensitive)
        for skill in self.all_skills_flat:
            # Create word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower, re.IGNORECASE):
                found_skills.append(skill)
        
        # Remove duplicates while preserving order
        found_skills = list(dict.fromkeys(found_skills))
        
        # Strategy 2: Fuzzy matching for variations
        found_skills.extend(self._fuzzy_match_skills(text_lower))
        
        # Remove duplicates and non-tech
        found_skills = list(dict.fromkeys(found_skills))
        found_skills = [s for s in found_skills 
                       if s.lower() not in [k.lower() for k in self.NON_TECH_KEYWORDS]]
        
        return found_skills
    
    def _fuzzy_match_skills(self, text: str) -> List[str]:
        """Fuzzy matching for skill variations"""
        fuzzy_matches = []
        
        # Common variations
        variations = {
            'node.js': ['nodejs', 'node js', 'node.js'],
            'c++': ['c plus plus', 'cpp'],
            'c#': ['c sharp', 'csharp'],
            '.net': ['dotnet', '.net core', 'dotnetcore'],
            'react': ['reactjs', 'react.js'],
            'angular': ['angularjs', 'angular.js'],
            'vue.js': ['vuejs', 'vue js'],
            'asp.net': ['aspnet', 'asp net'],
            'github': ['git hub', 'github actions'],
            'gitlab': ['git lab'],
            'rest api': ['restapi', 'rest-api'],
            'graphql': ['graph ql'],
            'ci/cd': ['cicd', 'ci-cd', 'continuous integration'],
        }
        
        for skill, variation_list in variations.items():
            for variation in variation_list:
                if variation in text:
                    fuzzy_matches.append(skill)
                    break
        
        return fuzzy_matches
    
    def validate_job(self, job: Dict) -> Tuple[bool, List[str]]:
        """
        Validate if a job is tech and extract its skills
        Returns: (is_tech, skills)
        """
        title = job.get('title', '')
        description = job.get('description', '')
        
        is_tech = self.is_tech_job(title, description)
        skills = self.extract_skills(description) if is_tech else []
        
        return is_tech, skills


def process_jobs_with_advanced_extraction(input_file: str, output_file: str) -> None:
    """Process all jobs with advanced extraction"""
    
    extractor = SkillsExtractor()
    
    # Load original data
    with open(input_file, 'r', encoding='utf-8') as f:
        jobs = json.load(f)
    
    processed_jobs = []
    stats = {
        'total': len(jobs),
        'tech_jobs': 0,
        'non_tech_filtered': 0,
        'total_skills_extracted': 0,
        'jobs_with_skills': 0
    }
    
    print(f"Processing {len(jobs)} jobs...")
    
    for job in jobs:
        is_tech, skills = extractor.validate_job(job)
        
        if is_tech:
            stats['tech_jobs'] += 1
            
            # Enhance job with new extraction
            job['is_tech_job'] = True
            job['extracted_skills'] = skills
            job['num_skills'] = len(skills)
            
            if skills:
                stats['jobs_with_skills'] += 1
                stats['total_skills_extracted'] += len(skills)
            
            processed_jobs.append(job)
        else:
            stats['non_tech_filtered'] += 1
    
    # Save processed jobs
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_jobs, f, ensure_ascii=False, indent=2)
    
    print("\n✅ Processing Complete!")
    print(f"Total jobs: {stats['total']}")
    print(f"Tech jobs kept: {stats['tech_jobs']}")
    print(f"Non-tech filtered: {stats['non_tech_filtered']}")
    print(f"Jobs with skills: {stats['jobs_with_skills']}")
    print(f"Total skills extracted: {stats['total_skills_extracted']}")
    print(f"Output saved to: {output_file}")
    
    return processed_jobs


if __name__ == "__main__":
    input_file = Path(__file__).parent.parent / "data" / "processed" / "job_offers_skills_advanced.json"
    output_file = Path(__file__).parent.parent / "data" / "processed" / "job_offers_tech_filtered.json"
    
    process_jobs_with_advanced_extraction(str(input_file), str(output_file))
