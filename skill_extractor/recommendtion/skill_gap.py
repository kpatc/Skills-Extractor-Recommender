"""
Skill Gap Analysis: Analyse les écarts entre profil candidat et exigences du marché.
"""

import logging
from typing import Dict, List, Set, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


class SkillGapAnalyzer:
    """Analyse les écarts de compétences."""

    def __init__(self):
        """Initialise l'analyseur."""
        self.market_skills = {}
        self.candidate_skills = set()

    def analyze_gap(
        self,
        candidate_skills: Set[str],
        cluster_top_skills: List[Tuple],
        skill_frequencies: Dict = None
    ) -> Dict:
        """
        Analyse l'écart entre candidat et marché.
        
        Args:
            candidate_skills: Compétences du candidat
            cluster_top_skills: Top skills du cluster
            skill_frequencies: Fréquences des skills au marché
        
        Returns:
            Analyse détaillée des écarts
        """
        cluster_skills_set = set(s[0] for s in cluster_top_skills)

        # 1. Compétences maîtrisées
        mastered = candidate_skills & cluster_skills_set

        # 2. Compétences manquantes
        missing = cluster_skills_set - candidate_skills

        # 3. Compétences futures (nice-to-have)
        future_skills = self._identify_future_skills(missing, skill_frequencies)

        # 4. Priorités (par fréquence au marché)
        priorities = self._prioritize_skills(missing, cluster_top_skills)

        # 5. Chemins d'apprentissage
        learning_paths = self._create_learning_paths(
            mastered,
            missing,
            future_skills,
            skill_frequencies
        )

        return {
            "mastered_skills": list(mastered),
            "mastered_count": len(mastered),
            "missing_skills": list(missing),
            "missing_count": len(missing),
            "gap_percentage": round(len(missing) / len(cluster_skills_set) * 100, 1) if cluster_skills_set else 0,
            "future_skills": future_skills,
            "priorities": priorities,
            "learning_paths": learning_paths,
            "quick_wins": self._identify_quick_wins(missing, cluster_top_skills),
        }

    def _identify_future_skills(
        self,
        missing_skills: Set[str],
        skill_frequencies: Dict = None
    ) -> List[str]:
        """
        Identifie les compétences à apprendre (stratégiques).
        
        Args:
            missing_skills: Compétences manquantes
            skill_frequencies: Fréquences au marché
        
        Returns:
            Liste des skills prioritaires
        """
        if not missing_skills or not skill_frequencies:
            return list(missing_skills)[:5]

        # Trier par fréquence au marché
        sorted_skills = sorted(
            missing_skills,
            key=lambda x: skill_frequencies.get(x, 0),
            reverse=True
        )

        return sorted_skills[:5]

    def _prioritize_skills(
        self,
        missing_skills: Set[str],
        cluster_top_skills: List[Tuple]
    ) -> List[Dict]:
        """
        Priorise les compétences manquantes par impact.
        
        Args:
            missing_skills: Compétences manquantes
            cluster_top_skills: Top skills du cluster
        
        Returns:
            Compétences priorisées avec niveau d'importance
        """
        priorities = []

        # Créer un dict skill -> index (pour l'ordre d'importance)
        skill_importance = {skill: i for i, (skill, freq) in enumerate(cluster_top_skills)}

        for skill in missing_skills:
            importance = skill_importance.get(skill, 999)
            frequency = next((freq for s, freq in cluster_top_skills if s == skill), 0)

            # Niveau: CRITICAL si top 3, HIGH si top 6, MEDIUM sinon
            if importance < 3:
                level = "CRITICAL"
            elif importance < 6:
                level = "HIGH"
            else:
                level = "MEDIUM"

            priorities.append({
                "skill": skill,
                "level": level,
                "frequency": frequency,
                "impact_score": round(100 - (importance * 5), 1) if importance < 999 else 0,
            })

        return sorted(priorities, key=lambda x: x["impact_score"], reverse=True)

    def _create_learning_paths(
        self,
        mastered: Set[str],
        missing: Set[str],
        future_skills: List[str],
        skill_frequencies: Dict = None
    ) -> Dict:
        """
        Crée des chemins d'apprentissage structurés.
        
        Args:
            mastered: Compétences maîtrisées
            missing: Compétences manquantes
            future_skills: Skills stratégiques
            skill_frequencies: Fréquences au marché
        
        Returns:
            Chemins d'apprentissage par phase
        """
        # Diviser les missing en 3 niveaux
        critical = [s for s in missing if s in future_skills[:3]] if future_skills else []
        important = [s for s in missing if s not in critical][:4]
        nice_to_have = [s for s in missing if s not in critical and s not in important]

        return {
            "phase_1_immediate": {
                "duration": "1-2 months",
                "skills": critical[:2],
                "description": "Master critical skills for immediate job market fit",
                "resources": ["Online courses", "GitHub projects", "Documentation"],
            },
            "phase_2_consolidation": {
                "duration": "2-4 months",
                "skills": important[:3],
                "description": "Build expertise in core domain skills",
                "resources": ["Advanced courses", "Real projects", "Mentoring"],
            },
            "phase_3_specialization": {
                "duration": "4-6 months",
                "skills": nice_to_have[:3],
                "description": "Develop specialized skills for advanced roles",
                "resources": ["Certifications", "Research papers", "Open source"],
            },
        }

    def _identify_quick_wins(
        self,
        missing_skills: Set[str],
        cluster_top_skills: List[Tuple]
    ) -> List[Dict]:
        """
        Identifie les quick wins (skills faciles à apprendre).
        
        Args:
            missing_skills: Compétences manquantes
            cluster_top_skills: Top skills du cluster
        
        Returns:
            Quick wins
        """
        # Compétences faciles: frameworks/outils plutôt que langages
        easy_skills = [
            "git", "docker", "pytest", "jenkins", "webpack",
            "terraform", "ansible", "graphql", "rest", "oauth"
        ]

        quick_wins = []
        for skill in missing_skills:
            if any(easy in skill.lower() for easy in easy_skills):
                frequency = next((freq for s, freq in cluster_top_skills if s == skill), 0)
                quick_wins.append({
                    "skill": skill,
                    "effort": "Low",
                    "learning_time": "2-4 weeks",
                    "frequency": frequency,
                })

        return quick_wins[:5]

    def compare_profiles(
        self,
        profiles: Dict[str, Set[str]],
        cluster_top_skills: List[Tuple]
    ) -> Dict:
        """
        Compare plusieurs profils candidats.
        
        Args:
            profiles: Dict {name: skills_set}
            cluster_top_skills: Top skills du cluster
        
        Returns:
            Comparaison des profils
        """
        comparison = {}
        cluster_skills = set(s[0] for s in cluster_top_skills)

        for name, skills in profiles.items():
            mastered = skills & cluster_skills
            missing = cluster_skills - skills

            comparison[name] = {
                "mastered_count": len(mastered),
                "missing_count": len(missing),
                "alignment": round(len(mastered) / len(cluster_skills) * 100, 1) if cluster_skills else 0,
                "gap": len(missing),
            }

        # Trier par alignment
        sorted_comparison = sorted(
            comparison.items(),
            key=lambda x: x[1]["alignment"],
            reverse=True
        )

        return {
            "profiles": dict(sorted_comparison),
            "best_match": sorted_comparison[0][0] if sorted_comparison else None,
            "worst_match": sorted_comparison[-1][0] if sorted_comparison else None,
        }

    def generate_gap_report(
        self,
        candidate_name: str,
        gap_analysis: Dict,
        output_format: str = "text"
    ) -> str:
        """
        Génère un rapport texte de l'écart.
        
        Args:
            candidate_name: Nom du candidat
            gap_analysis: Résultats de analyze_gap
            output_format: "text" ou "html"
        
        Returns:
            Rapport formaté
        """
        report = f"""
{'='*60}
SKILL GAP ANALYSIS - {candidate_name}
{'='*60}

📊 OVERVIEW
-----------
Compétences maîtrisées: {gap_analysis['mastered_count']}
Compétences manquantes: {gap_analysis['missing_count']}
Écart: {gap_analysis['gap_percentage']}%

✓ MASTERED SKILLS
-----------
{', '.join(gap_analysis['mastered_skills']) or 'Aucune'}

❌ MISSING SKILLS (PRIORITY ORDER)
-----------
"""
        for priority in gap_analysis['priorities'][:5]:
            report += f"\n{priority['level']}: {priority['skill']} (Impact: {priority['impact_score']})"

        report += "\n\n⚡ QUICK WINS\n-----------\n"
        for quick_win in gap_analysis['quick_wins']:
            report += f"\n• {quick_win['skill']} ({quick_win['effort']}, {quick_win['learning_time']})"

        report += "\n\n" + "="*60

        return report
