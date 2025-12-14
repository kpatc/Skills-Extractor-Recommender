#!/usr/bin/env python3
"""
Test du nouvel outil GitHub Repository Analyzer
Optimisé pour l'extraction détaillée d'informations de repositories
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.github_repository_analyzer import GitHubRepositoryAnalyzer

def test_github_repository_analyzer():
    print("🧪 Testing GitHub Repository Analyzer")
    print("Optimized for detailed repository analysis with README extraction")
    print("=" * 60)
    
    # Créer l'outil
    tool = GitHubRepositoryAnalyzer()
    
    # Profils de test avec des repositories intéressants
    test_profiles = [
        "https://github.com/kpatc"
    ]
    
    for github_url in test_profiles:
        print(f"\n{'='*50}")
        print(f"Testing with: {github_url}")
        print('='*50)
        
        try:
            result = tool._run(github_url)
            print(result)
            print("-" * 30)
        except Exception as e:
            print(f"❌ Error testing {github_url}: {str(e)}")
    
    print("\n✅ Repository analyzer test completed!")
    print("This tool provides comprehensive analysis of:")
    print("- Repository descriptions and programming languages")
    print("- README content extraction and analysis") 
    print("- Technology and framework detection")
    print("- Project features and achievements")
    print("- CV-ready project recommendations")

if __name__ == "__main__":
    test_github_repository_analyzer()
