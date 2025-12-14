#!/usr/bin/env python3
"""
Test complet du système CV avec l'API GitHub stable
"""

from crew_main import generate_personalized_cv

def test_complete_system():
    """Test du système complet avec API GitHub"""
    
    print("🧪 Test du système complet de génération de CV")
    print("="*60)
    
    # Données de test
    job_description = """
    We are looking for a Senior Full-Stack Developer to join our team.
    
    Required skills:
    - Strong experience with React, Node.js, and TypeScript
    - Experience with AI/ML integration
    - Knowledge of modern development practices
    - GitHub collaboration experience
    - API development experience
    
    The ideal candidate will have experience building modern web applications
    and integrating AI capabilities into user-facing products.
    """
    
    github_profile_url = "https://github.com/octocat"
    
    print(f"📋 Job Description: Senior Full-Stack Developer")
    print(f"🔗 GitHub Profile: {github_profile_url}")
    print(f"🤖 Using stable GitHub API instead of web scraping")
    print()
    
    try:
        print("🚀 Starting CV generation...")
        result = generate_personalized_cv(
            job_description=job_description,
            github_profile_url=github_profile_url
        )
        
        print("✅ CV généré avec succès!")
        print("="*60)
        print("CV CONTENT:")
        print(result)
        print("="*60)
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_system()
