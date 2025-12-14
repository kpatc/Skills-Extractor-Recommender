"""
CV Personalizer: Génère des recommandations pour personnaliser le CV.
Basé sur le profil candidat, le gap d'écarts, et le cluster cible.
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class CVPersonalizer:
    """Personnalise les recommandations CV basées sur le profil et le marché."""

    def __init__(self):
        """Initialise le personnaliseur."""
        self.cv_templates = self._load_cv_templates()

    def _load_cv_templates(self) -> Dict:
        """Charge les templates de sections CV."""
        return {
            "Data": {
                "title": "Data Engineer / Data Scientist",
                "skills_section_title": "Technical Skills",
                "key_skills": ["Python", "SQL", "Big Data", "Cloud Platforms"],
                "keywords": ["data pipeline", "ETL", "analytics", "scalability"],
            },
            "Backend": {
                "title": "Backend Developer",
                "skills_section_title": "Core Competencies",
                "key_skills": ["APIs", "Databases", "Microservices", "DevOps"],
                "keywords": ["scalable systems", "REST", "optimization", "security"],
            },
            "DevOps": {
                "title": "DevOps / Cloud Engineer",
                "skills_section_title": "Infrastructure & Tools",
                "key_skills": ["Containerization", "Orchestration", "CI/CD", "Monitoring"],
                "keywords": ["automation", "deployment", "infrastructure as code"],
            },
            "AI/ML": {
                "title": "ML / AI Engineer",
                "skills_section_title": "Artificial Intelligence Skills",
                "key_skills": ["Machine Learning", "Deep Learning", "NLP", "MLOps"],
                "keywords": ["model deployment", "feature engineering", "neural networks"],
            },
            "Frontend": {
                "title": "Frontend Developer",
                "skills_section_title": "Frontend Technologies",
                "key_skills": ["React", "TypeScript", "UI/UX", "Performance"],
                "keywords": ["responsive design", "accessibility", "web optimization"],
            },
        }

    def generate_cv_recommendations(
        self,
        candidate_name: str,
        cluster_name: str,
        gap_analysis: Dict,
        mastered_skills: List[str]
    ) -> Dict:
        """
        Génère des recommandations personnalisées pour le CV.
        
        Args:
            candidate_name: Nom du candidat
            cluster_name: Cluster cible (Data, Backend, etc.)
            gap_analysis: Résultats de skill gap
            mastered_skills: Compétences maîtrisées
        
        Returns:
            Recommandations CV personnalisées
        """
        logger.info(f"Génération des recommandations CV pour {candidate_name}...")

        template = self.cv_templates.get(cluster_name, {})

        recommendations = {
            "candidate": candidate_name,
            "target_role": template.get("title", f"{cluster_name} Engineer"),
            "cv_title_suggestion": self._suggest_cv_title(cluster_name, mastered_skills),
            "professional_summary": self._generate_summary(
                cluster_name,
                mastered_skills,
                gap_analysis
            ),
            "skills_section": self._organize_skills_section(
                cluster_name,
                mastered_skills,
                gap_analysis
            ),
            "experience_highlights": self._suggest_experience_highlights(
                cluster_name,
                mastered_skills
            ),
            "keywords_to_emphasize": template.get("keywords", []),
            "sections_to_highlight": self._suggest_sections(cluster_name, mastered_skills),
            "action_items": self._generate_action_items(gap_analysis),
        }

        return recommendations

    def _suggest_cv_title(self, cluster_name: str, mastered_skills: List[str]) -> str:
        """
        Suggère un titre professionnel.
        
        Args:
            cluster_name: Cluster cible
            mastered_skills: Compétences maîtrisées
        
        Returns:
            Titre suggéré
        """
        template_title = self.cv_templates[cluster_name]["title"]

        # Personnaliser basé sur les compétences
        if len(mastered_skills) > 8:
            level = "Senior"
        elif len(mastered_skills) > 4:
            level = "Mid-Level"
        else:
            level = "Junior"

        return f"{level} {template_title}"

    def _generate_summary(
        self,
        cluster_name: str,
        mastered_skills: List[str],
        gap_analysis: Dict
    ) -> str:
        """
        Génère un résumé professionnel.
        
        Args:
            cluster_name: Cluster cible
            mastered_skills: Compétences maîtrisées
            gap_analysis: Résultats du gap analysis
        
        Returns:
            Résumé professionnel
        """
        strengths = mastered_skills[:3]
        strengths_str = ", ".join(strengths) if strengths else "technical expertise"

        gap_percentage = gap_analysis.get("gap_percentage", 0)
        level = "expert" if gap_percentage < 30 else "skilled" if gap_percentage < 60 else "developing"

        summaries = {
            "Data": f"Results-driven {level} professional with strong expertise in {strengths_str}. "
                   f"Passionate about extracting insights from data and building scalable pipelines. "
                   f"Proven track record in optimizing data workflows and mentoring teams.",
            
            "Backend": f"Experienced {level} Backend Developer with deep knowledge of {strengths_str}. "
                      f"Specialized in designing robust, scalable APIs and microservices. "
                      f"Committed to code quality, performance optimization, and system reliability.",
            
            "DevOps": f"Seasoned {level} DevOps professional with expertise in {strengths_str}. "
                     f"Focused on automating infrastructure and streamlining deployment pipelines. "
                     f"Track record of reducing deployment times and improving system reliability.",
            
            "AI/ML": f"Innovative {level} Machine Learning Engineer with strong foundation in {strengths_str}. "
                    f"Passionate about building intelligent systems and deploying ML models at scale. "
                    f"Experience in end-to-end ML lifecycle and production optimization.",
            
            "Frontend": f"Creative {level} Frontend Developer with expertise in {strengths_str}. "
                       f"Focused on creating responsive, accessible, and performant user interfaces. "
                       f"Strong eye for design and commitment to user experience excellence.",
        }

        return summaries.get(cluster_name, f"{level} professional in {cluster_name} domain")

    def _organize_skills_section(
        self,
        cluster_name: str,
        mastered_skills: List[str],
        gap_analysis: Dict
    ) -> Dict:
        """
        Organise la section des compétences.
        
        Args:
            cluster_name: Cluster cible
            mastered_skills: Compétences maîtrisées
            gap_analysis: Résultats du gap analysis
        
        Returns:
            Section compétences structurée
        """
        template = self.cv_templates[cluster_name]
        priorities = gap_analysis.get("priorities", [])

        # Séparer les skills par niveau
        expert_skills = mastered_skills[:3]
        intermediate_skills = mastered_skills[3:6]
        learning_skills = [p["skill"] for p in priorities[:3]]

        return {
            "section_title": template.get("skills_section_title", "Technical Skills"),
            "expert_level": {
                "title": "Expert Level",
                "skills": expert_skills,
            },
            "intermediate_level": {
                "title": "Intermediate Level",
                "skills": intermediate_skills,
            },
            "developing_level": {
                "title": "Developing",
                "skills": learning_skills,
            },
            "keyword_suggestions": template.get("keywords", []),
        }

    def _suggest_experience_highlights(
        self,
        cluster_name: str,
        mastered_skills: List[str]
    ) -> List[Dict]:
        """
        Suggère des bullets points d'expérience.
        
        Args:
            cluster_name: Cluster cible
            mastered_skills: Compétences maîtrisées
        
        Returns:
            Exemples de bullets
        """
        experience_examples = {
            "Data": [
                f"Designed and optimized ETL pipelines processing {mastered_skills[0] if mastered_skills else 'data'} workflows",
                "Reduced query execution time by 40% through database optimization",
                "Built real-time dashboards providing actionable business insights",
                "Mentored junior engineers in data engineering best practices",
            ],
            "Backend": [
                f"Architected scalable REST APIs using {mastered_skills[0] if mastered_skills else 'modern frameworks'}",
                "Improved API response time by 50% through caching and optimization",
                "Led microservices migration reducing deployment complexity",
                "Implemented comprehensive testing achieving 85%+ code coverage",
            ],
            "DevOps": [
                f"Automated infrastructure provisioning using {mastered_skills[0] if mastered_skills else 'infrastructure-as-code'} tools",
                "Reduced deployment time from hours to minutes through CI/CD optimization",
                "Managed multi-region cloud infrastructure with 99.9% uptime",
                "Implemented monitoring and alerting reducing incident response time",
            ],
            "AI/ML": [
                f"Developed ML models achieving 95%+ accuracy using {mastered_skills[0] if mastered_skills else 'advanced techniques'}",
                "Deployed 5+ production ML models serving millions of predictions",
                "Optimized model inference reducing latency by 60%",
                "Built end-to-end ML pipeline from data collection to production",
            ],
            "Frontend": [
                f"Built responsive web applications using {mastered_skills[0] if mastered_skills else 'modern frameworks'}",
                "Improved page load time by 50% through performance optimization",
                "Led accessibility improvements ensuring WCAG 2.1 compliance",
                "Mentored designers in implementation and collaborated on UX improvements",
            ],
        }

        return experience_examples.get(cluster_name, [])

    def _suggest_sections(self, cluster_name: str, mastered_skills: List[str]) -> List[Dict]:
        """
        Suggère les sections CV à mettre en avant.
        
        Args:
            cluster_name: Cluster cible
            mastered_skills: Compétences maîtrisées
        
        Returns:
            Sections suggérées
        """
        sections = {
            "Data": [
                {
                    "name": "Technical Skills",
                    "priority": "HIGH",
                    "tip": "Highlight database, ETL, and analytics skills prominently",
                },
                {
                    "name": "Projects",
                    "priority": "HIGH",
                    "tip": "Include data analysis, pipeline, or ML projects",
                },
                {
                    "name": "Certifications",
                    "priority": "MEDIUM",
                    "tip": "Cloud certifications (AWS, GCP, Azure) are valuable",
                },
            ],
            "Backend": [
                {
                    "name": "Technical Skills",
                    "priority": "HIGH",
                    "tip": "Emphasize backend frameworks, databases, and APIs",
                },
                {
                    "name": "Open Source",
                    "priority": "HIGH",
                    "tip": "Include GitHub contributions if available",
                },
                {
                    "name": "Architecture",
                    "priority": "MEDIUM",
                    "tip": "Describe system design experience",
                },
            ],
            "DevOps": [
                {
                    "name": "Infrastructure",
                    "priority": "HIGH",
                    "tip": "Detail cloud, container, and CI/CD experience",
                },
                {
                    "name": "Certifications",
                    "priority": "HIGH",
                    "tip": "Cloud architect certifications are highly valued",
                },
                {
                    "name": "Automation",
                    "priority": "MEDIUM",
                    "tip": "Showcase automation success stories",
                },
            ],
            "AI/ML": [
                {
                    "name": "Technical Skills",
                    "priority": "HIGH",
                    "tip": "Highlight ML frameworks and methodologies",
                },
                {
                    "name": "Research",
                    "priority": "MEDIUM",
                    "tip": "Include papers, publications, or research projects",
                },
                {
                    "name": "Projects",
                    "priority": "HIGH",
                    "tip": "Showcase end-to-end ML project experience",
                },
            ],
            "Frontend": [
                {
                    "name": "Portfolio",
                    "priority": "HIGH",
                    "tip": "Link to live projects or GitHub portfolio",
                },
                {
                    "name": "Technical Skills",
                    "priority": "HIGH",
                    "tip": "Emphasize UI, CSS, and performance skills",
                },
                {
                    "name": "Design",
                    "priority": "MEDIUM",
                    "tip": "Mention UX/design collaboration experience",
                },
            ],
        }

        return sections.get(cluster_name, [])

    def _generate_action_items(self, gap_analysis: Dict) -> List[str]:
        """
        Génère des actions à prendre.
        
        Args:
            gap_analysis: Résultats du gap analysis
        
        Returns:
            Liste d'actions
        """
        actions = []

        # Basé sur l'écart
        gap = gap_analysis.get("gap_percentage", 0)
        if gap > 70:
            actions.append("⚠ URGENT: Acquire critical skills listed in 'Missing Skills' section")
        elif gap > 50:
            actions.append("📚 Prioritize learning high-impact skills to improve market fit")
        else:
            actions.append("✓ You're well-aligned. Focus on deepening expertise")

        # Basé sur quick wins
        quick_wins = gap_analysis.get("quick_wins", [])
        if quick_wins:
            actions.append(f"⚡ Quick Wins: Learn {quick_wins[0]['skill']} in {quick_wins[0]['learning_time']}")

        # Basé sur les priorités
        priorities = gap_analysis.get("priorities", [])
        if priorities:
            critical = [p for p in priorities if p["level"] == "CRITICAL"]
            if critical:
                actions.append(f"🔴 Critical: Master {critical[0]['skill']} - highly demanded")

        # Général
        actions.append("💼 Update your CV with keywords matching the target cluster")
        actions.append("🔗 Build portfolio projects demonstrating key skills")

        return actions
