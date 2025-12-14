#!/usr/bin/env python3
"""
Test script for the new GitHub API tool
"""

import sys
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.github_api_tool import GitHubAPITool
import json

def test_github_api_tool():
    """Test the GitHub API tool with a known profile."""
    
    print("🧪 Testing GitHub API Tool")
    print("This tool should be more reliable than web scraping")
    
    # Vérifier si le token GitHub est configuré
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("⚠️  ATTENTION: Aucun token GitHub configuré!")
        print("   Pour une meilleure stabilité, créez un token sur:")
        print("   https://github.com/settings/tokens")
        print("   Et ajoutez GITHUB_TOKEN=votre_token dans le fichier .env")
        print("   Continuing with unauthenticated requests (limited to 60/hour)...")
    else:
        print(f"✅ Token GitHub configuré (commence par: {github_token[:8]}...)")
    
    tool = GitHubAPITool()
    
    # Test with a popular GitHub profile
    test_urls = [
        "https://github.com/octocat",  # GitHub's mascot account
        "https://github.com/torvalds",  # Linus Torvalds
        "https://github.com/gaearon",   # Dan Abramov (React)
    ]
    
    for url in test_urls:
        print(f"\n{'='*50}")
        print(f"Testing with: {url}")
        print(f"{'='*50}")
        
        try:
            result = tool._run(url)
            data = json.loads(result)
            
            if "error" in data:
                print(f"❌ Error: {data['error']}")
            else:
                print(f"✅ Success!")
                print(f"Username: {data.get('username', 'N/A')}")
                print(f"Real name: {data.get('user_info', {}).get('name', 'N/A')}")
                print(f"Public repos: {data.get('user_info', {}).get('public_repos', 0)}")
                print(f"Repositories found: {data.get('repositories_count', 0)}")
                
                # Show languages
                tech_analysis = data.get('technical_analysis', {})
                if tech_analysis and 'primary_languages' in tech_analysis:
                    print(f"Primary languages: {', '.join(tech_analysis['primary_languages'][:5])}")
                
                # Show most starred repos
                most_starred = tech_analysis.get('most_starred_repos', [])
                if most_starred:
                    print("Top repositories:")
                    for repo in most_starred[:3]:
                        stars = repo.get('stargazers_count', 0)
                        name = repo.get('name', 'Unknown')
                        desc = repo.get('description', 'No description')[:50] + '...' if repo.get('description') else 'No description'
                        print(f"  - {name} ({stars} stars): {desc}")
                        
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
        
        print("\n" + "-"*30)

if __name__ == "__main__":
    print("🧪 Testing GitHub API Tool")
    print("This tool should be more reliable than web scraping")
    test_github_api_tool()
    print("\n✅ Test completed!")
