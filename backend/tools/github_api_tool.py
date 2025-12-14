from crewai.tools import BaseTool
from typing import Type, Dict, Any, List, Optional
from pydantic import BaseModel, Field
import requests
import json
import time
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()


class GitHubAPIInput(BaseModel):
    """Input schema for GitHub API Tool."""
    github_url: str = Field(..., description="GitHub profile URL to analyze (e.g., https://github.com/username)")


class GitHubAPITool(BaseTool):
    name: str = "GitHub API Analyzer"
    description: str = (
        "Reliable GitHub repository analyzer using official GitHub API. "
        "Extracts repositories, languages, descriptions, topics, and technical details. "
        "More stable than web scraping with built-in retry mechanisms and rate limiting."
    )
    args_schema: Type[BaseModel] = GitHubAPIInput

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for GitHub API requests."""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'CV-Personalizer-Bot/1.0'
        }
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        return headers

    def _extract_username_from_url(self, github_url: str) -> str:
        """Extract username from GitHub URL."""
        try:
            parsed = urlparse(github_url.strip())
            path_parts = [p for p in parsed.path.strip('/').split('/') if p]
            if path_parts:
                return path_parts[0]
            return ""
        except Exception:
            return ""

    def _make_api_request(self, endpoint: str, retries: int = 3) -> Optional[Dict[Any, Any]]:
        """Make GitHub API request with retry mechanism."""
        for attempt in range(retries):
            try:
                url = f"https://api.github.com/{endpoint}"
                response = requests.get(url, headers=self._get_headers(), timeout=15)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 403:
                    # Rate limit hit
                    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                    current_time = int(time.time())
                    wait_time = max(0, reset_time - current_time + 1)
                    
                    if wait_time > 0 and wait_time < 3600:  # Wait max 1 hour
                        print(f"Rate limit hit, waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return {"error": "GitHub rate limit exceeded"}
                elif response.status_code == 404:
                    return {"error": "GitHub user not found"}
                else:
                    if attempt < retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return {"error": f"GitHub API error: {response.status_code}"}
                    
            except requests.RequestException as e:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return {"error": f"Network error: {str(e)}"}
        
        return {"error": "Failed after multiple retries"}

    def _get_user_info(self, username: str) -> Dict[str, Any]:
        """Get user profile information."""
        user_data = self._make_api_request(f"users/{username}")
        if not user_data or "error" in user_data:
            return user_data or {"error": "Failed to fetch user info"}
        
        return {
            "name": user_data.get("name") or username,
            "bio": user_data.get("bio", ""),
            "company": user_data.get("company", ""),
            "location": user_data.get("location", ""),
            "public_repos": user_data.get("public_repos", 0),
            "followers": user_data.get("followers", 0),
            "following": user_data.get("following", 0),
            "created_at": user_data.get("created_at", ""),
            "blog": user_data.get("blog", ""),
            "twitter_username": user_data.get("twitter_username", "")
        }

    def _get_user_repositories(self, username: str) -> List[Dict[str, Any]]:
        """Get user repositories with detailed information."""
        # Get repositories sorted by updated date
        repos_data = self._make_api_request(f"users/{username}/repos?sort=updated&per_page=50")
        
        if not repos_data or "error" in repos_data:
            return [{"error": repos_data.get("error", "Failed to fetch repositories")}]
        
        if not isinstance(repos_data, list):
            return [{"error": "Invalid repository data format"}]
        
        repositories = []
        for repo in repos_data:
            try:
                # Get additional repository details
                repo_details = {
                    "name": repo.get("name", ""),
                    "full_name": repo.get("full_name", ""),
                    "description": repo.get("description", ""),
                    "language": repo.get("language", ""),
                    "languages_url": repo.get("languages_url", ""),
                    "stargazers_count": repo.get("stargazers_count", 0),
                    "forks_count": repo.get("forks_count", 0),
                    "watchers_count": repo.get("watchers_count", 0),
                    "size": repo.get("size", 0),
                    "default_branch": repo.get("default_branch", "main"),
                    "topics": repo.get("topics", []),
                    "homepage": repo.get("homepage", ""),
                    "created_at": repo.get("created_at", ""),
                    "updated_at": repo.get("updated_at", ""),
                    "pushed_at": repo.get("pushed_at", ""),
                    "is_fork": repo.get("fork", False),
                    "archived": repo.get("archived", False),
                    "disabled": repo.get("disabled", False),
                    "private": repo.get("private", False)
                }
                
                # Get languages for this repository
                if repo_details["languages_url"]:
                    languages = self._make_api_request(repo_details["languages_url"].replace("https://api.github.com/", ""))
                    if languages and "error" not in languages:
                        repo_details["languages"] = languages
                    else:
                        repo_details["languages"] = {}
                
                repositories.append(repo_details)
                
            except Exception as e:
                print(f"Error processing repository {repo.get('name', 'unknown')}: {str(e)}")
                continue
        
        return repositories

    def _analyze_technical_profile(self, repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze technical profile from repositories."""
        if not repositories or (len(repositories) == 1 and "error" in repositories[0]):
            return {"error": "No repositories to analyze"}
        
        # Count languages across all repositories
        language_stats = {}
        topics_stats = {}
        total_stars = 0
        total_forks = 0
        active_repos = []
        
        for repo in repositories:
            if "error" in repo:
                continue
                
            # Skip forks and archived repositories for main analysis
            if repo.get("is_fork", False) or repo.get("archived", False):
                continue
            
            # Count primary language
            if repo.get("language"):
                language_stats[repo["language"]] = language_stats.get(repo["language"], 0) + 1
            
            # Count detailed languages if available
            if repo.get("languages"):
                for lang, bytes_count in repo["languages"].items():
                    if lang not in language_stats:
                        language_stats[lang] = 0
                    language_stats[lang] += bytes_count / 1000  # Convert to KB for weighting
            
            # Count topics
            for topic in repo.get("topics", []):
                topics_stats[topic] = topics_stats.get(topic, 0) + 1
            
            # Aggregate metrics
            total_stars += repo.get("stargazers_count", 0)
            total_forks += repo.get("forks_count", 0)
            
            # Consider as active if updated in last year or has activity
            if (repo.get("stargazers_count", 0) > 0 or 
                repo.get("forks_count", 0) > 0 or 
                repo.get("watchers_count", 0) > 0):
                active_repos.append(repo)
        
        # Sort languages by usage
        sorted_languages = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
        sorted_topics = sorted(topics_stats.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "primary_languages": [lang for lang, _ in sorted_languages[:10]],
            "language_distribution": dict(sorted_languages[:15]),
            "popular_topics": [topic for topic, _ in sorted_topics[:20]],
            "total_stars": total_stars,
            "total_forks": total_forks,
            "active_repositories_count": len(active_repos),
            "most_starred_repos": sorted(
                [r for r in repositories if not r.get("is_fork", False) and "error" not in r],
                key=lambda x: x.get("stargazers_count", 0),
                reverse=True
            )[:10]
        }

    def _run(self, github_url: str) -> str:
        """Execute the GitHub API analysis."""
        try:
            username = self._extract_username_from_url(github_url)
            if not username:
                return json.dumps({
                    "error": "Could not extract username from GitHub URL",
                    "provided_url": github_url
                }, indent=2)
            
            print(f"Analyzing GitHub profile: {username}")
            
            # Get user information
            user_info = self._get_user_info(username)
            if "error" in user_info:
                return json.dumps({
                    "error": f"Failed to fetch user info: {user_info['error']}",
                    "username": username
                }, indent=2)
            
            # Get repositories
            repositories = self._get_user_repositories(username)
            if repositories and len(repositories) == 1 and "error" in repositories[0]:
                return json.dumps({
                    "error": f"Failed to fetch repositories: {repositories[0]['error']}",
                    "username": username,
                    "user_info": user_info
                }, indent=2)
            
            # Analyze technical profile
            technical_analysis = self._analyze_technical_profile(repositories)
            
            # Compile comprehensive analysis
            analysis_result = {
                "username": username,
                "url": github_url,
                "user_info": user_info,
                "repositories_count": len([r for r in repositories if "error" not in r]),
                "repositories": repositories,
                "technical_analysis": technical_analysis,
                "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "data_source": "GitHub API v3"
            }
            
            return json.dumps(analysis_result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                "error": f"Unexpected error during GitHub analysis: {str(e)}",
                "github_url": github_url
            }, indent=2)
