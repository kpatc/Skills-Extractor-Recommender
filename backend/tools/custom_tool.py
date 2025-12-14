from crewai.tools import BaseTool
from typing import Type, Dict, Any, List
from pydantic import BaseModel, Field
import requests
import json
import re
from urllib.parse import urlparse


class GitHubProfileInput(BaseModel):
    """Input schema for GitHub Profile Tool."""
    github_url: str = Field(..., description="GitHub profile or repository URL to analyze")


class GitHubProfileTool(BaseTool):
    name: str = "GitHub Profile Analyzer"
    description: str = (
        "Extracts comprehensive technical information from GitHub profiles using GitHub API. "
        "Analyzes repositories, programming languages, project descriptions, and technical skills. "
        "Provides detailed information about projects, technologies used, and contribution patterns."
    )
    args_schema: Type[BaseModel] = GitHubProfileInput

    def _extract_username_from_url(self, github_url: str) -> str:
        """Extract username from GitHub URL."""
        parsed = urlparse(github_url)
        path_parts = parsed.path.strip('/').split('/')
        if path_parts and path_parts[0]:
            return path_parts[0]
        return ""

    def _get_github_api_data(self, endpoint: str) -> Dict[Any, Any]:
        """Make GitHub API request with error handling."""
        try:
            response = requests.get(f"https://api.github.com/{endpoint}", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API request failed with status {response.status_code}"}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}

    def _analyze_repositories(self, username: str) -> List[Dict[str, Any]]:
        """Analyze user repositories and extract technical information."""
        repos_data = self._get_github_api_data(f"users/{username}/repos?sort=updated&per_page=20")
        
        if isinstance(repos_data, dict) and "error" in repos_data:
            return [{"error": repos_data["error"]}]
        
        analyzed_repos = []
        languages_count = {}
        
        for repo in repos_data:
            if repo.get('fork', False):  # Skip forked repositories
                continue
                
            repo_info = {
                "name": repo.get('name', ''),
                "description": repo.get('description', 'No description available'),
                "language": repo.get('language', 'Unknown'),
                "stars": repo.get('stargazers_count', 0),
                "forks": repo.get('forks_count', 0),
                "updated_at": repo.get('updated_at', ''),
                "html_url": repo.get('html_url', ''),
                "topics": repo.get('topics', [])
            }
            
            # Count languages
            if repo_info["language"] and repo_info["language"] != "Unknown":
                languages_count[repo_info["language"]] = languages_count.get(repo_info["language"], 0) + 1
            
            # Get repository languages distribution
            languages_url = repo.get('languages_url', '')
            if languages_url:
                lang_data = self._get_github_api_data(f"repos/{username}/{repo['name']}/languages")
                if not isinstance(lang_data, dict) or "error" not in lang_data:
                    repo_info["languages_distribution"] = lang_data
            
            # Get README content
            readme_content = self._fetch_readme(username, repo['name'])
            if readme_content:
                repo_info["readme_content"] = readme_content
                repo_info["readme_summary"] = self._summarize_readme(readme_content)
                # Extract additional technologies from README
                self._extract_technologies_from_readme(readme_content, repo_info)
            
            analyzed_repos.append(repo_info)
        
        return analyzed_repos

    def _get_user_profile(self, username: str) -> Dict[str, Any]:
        """Get user profile information."""
        return self._get_github_api_data(f"users/{username}")

    def _fetch_readme(self, username: str, repo_name: str) -> str:
        """Fetch README content from a repository."""
        try:
            # Try different README file names
            readme_files = ['README.md', 'readme.md', 'README.txt', 'readme.txt', 'README.rst', 'README']
            
            for readme_file in readme_files:
                readme_data = self._get_github_api_data(f"repos/{username}/{repo_name}/contents/{readme_file}")
                
                if not isinstance(readme_data, dict) or "error" not in readme_data:
                    if readme_data.get('content'):
                        import base64
                        try:
                            content = base64.b64decode(readme_data['content']).decode('utf-8', errors='ignore')
                            return content[:2000]  # Limit content size to avoid overwhelming the LLM
                        except Exception:
                            continue
            
            return ""
        except Exception as e:
            return ""
    
    def _extract_technologies_from_readme(self, readme_content: str, repo_info: Dict[str, Any]) -> None:
        """Extract technologies mentioned in README content."""
        try:
            # Common technology keywords to look for
            tech_keywords = [
                'React', 'Vue', 'Angular', 'Node.js', 'Express', 'Django', 'Flask', 'FastAPI',
                'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#', 'Go', 'Rust', 'PHP',
                'MongoDB', 'PostgreSQL', 'MySQL', 'Redis', 'Docker', 'Kubernetes', 'AWS', 'GCP',
                'Azure', 'Firebase', 'Heroku', 'Vercel', 'Netlify', 'Git', 'GitHub Actions',
                'CI/CD', 'TensorFlow', 'PyTorch', 'Scikit-learn', 'Pandas', 'NumPy', 'OpenCV',
                'Flutter', 'React Native', 'Swift', 'Kotlin', 'Unity', 'Unreal Engine',
                'Bootstrap', 'Tailwind', 'Material-UI', 'Sass', 'SCSS', 'Webpack', 'Vite',
                'Next.js', 'Nuxt.js', 'Gatsby', 'Svelte', 'Laravel', 'Spring Boot', 'Rails',
                'SQL', 'NoSQL', 'API', 'REST', 'GraphQL', 'Microservices', 'Machine Learning',
                'AI', 'Deep Learning', 'Data Science', 'Analytics', 'Big Data', 'Cloud Computing'
            ]
            
            readme_lower = readme_content.lower()
            extracted_techs = []
            
            for tech in tech_keywords:
                if tech.lower() in readme_lower:
                    extracted_techs.append(tech)
            
            if extracted_techs:
                repo_info["readme_technologies"] = extracted_techs
                
        except Exception:
            pass
    
    def _summarize_readme(self, readme_content: str) -> str:
        """Create a concise summary of README content."""
        if not readme_content:
            return "No README available"
        
        try:
            # Extract first few meaningful lines (skip headers and badges)
            lines = readme_content.split('\n')
            meaningful_lines = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('![') and not line.startswith('[!['):
                    if len(line) > 20:  # Skip very short lines
                        meaningful_lines.append(line)
                    if len(meaningful_lines) >= 3:  # Take first 3 meaningful lines
                        break
            
            summary = ' '.join(meaningful_lines)
            if len(summary) > 300:
                summary = summary[:300] + "..."
            
            return summary or "Project documentation available in README"
        except Exception:
            return "README content available but could not be summarized"

    def _run(self, github_url: str) -> str:
        """Extract comprehensive GitHub profile information."""
        try:
            username = self._extract_username_from_url(github_url)
            if not username:
                return "Error: Could not extract username from GitHub URL"
            
            # Get user profile
            user_profile = self._get_user_profile(username)
            if isinstance(user_profile, dict) and "error" in user_profile:
                return f"Error getting user profile: {user_profile['error']}"
            
            # Get repositories analysis
            repositories = self._analyze_repositories(username)
            
            # Extract technical information
            all_languages = set()
            all_topics = set()
            notable_projects = []
            
            for repo in repositories:
                if isinstance(repo, dict) and "error" not in repo:
                    # Collect languages
                    if repo.get("language"):
                        all_languages.add(repo["language"])
                    
                    if repo.get("languages_distribution"):
                        all_languages.update(repo["languages_distribution"].keys())
                    
                    # Collect topics (technologies/frameworks)
                    all_topics.update(repo.get("topics", []))
                    
                    # Identify notable projects (with stars or good description)
                    if repo.get("stars", 0) > 0 or len(repo.get("description", "")) > 20:
                        project_info = {
                            "name": repo["name"],
                            "description": repo["description"],
                            "language": repo["language"],
                            "stars": repo["stars"],
                            "topics": repo.get("topics", []),
                            "url": repo["html_url"],
                            "readme_summary": repo.get("readme_summary", ""),
                            "readme_technologies": repo.get("readme_technologies", [])
                        }
                        notable_projects.append(project_info)
                        
                        # Add README technologies to overall tech list
                        if repo.get("readme_technologies"):
                            all_topics.update(repo["readme_technologies"])
            
            # Compile comprehensive report
            technical_summary = {
                "profile": {
                    "username": username,
                    "name": user_profile.get("name", ""),
                    "bio": user_profile.get("bio", ""),
                    "company": user_profile.get("company", ""),
                    "location": user_profile.get("location", ""),
                    "public_repos": user_profile.get("public_repos", 0),
                    "followers": user_profile.get("followers", 0),
                    "created_at": user_profile.get("created_at", "")
                },
                "technical_skills": {
                    "programming_languages": sorted(list(all_languages)),
                    "technologies_and_topics": sorted(list(all_topics)),
                    "total_repositories": len([r for r in repositories if "error" not in r])
                },
                "notable_projects": notable_projects[:10],  # Top 10 projects
                "recent_activity": repositories[:5]  # 5 most recent repos
            }
            
            # Format the output as a readable report
            report = f"""
# GitHub Technical Profile Analysis for {username}

## Profile Overview
- **Name**: {technical_summary['profile']['name'] or 'Not specified'}
- **Username**: {technical_summary['profile']['username']}
- **Bio**: {technical_summary['profile']['bio'] or 'No bio available'}
- **Company**: {technical_summary['profile']['company'] or 'Not specified'}
- **Location**: {technical_summary['profile']['location'] or 'Not specified'}
- **Public Repositories**: {technical_summary['profile']['public_repos']}
- **Followers**: {technical_summary['profile']['followers']}

## Technical Skills
### Programming Languages
{', '.join(technical_summary['technical_skills']['programming_languages']) if technical_summary['technical_skills']['programming_languages'] else 'No languages detected'}

### Technologies & Frameworks
{', '.join(technical_summary['technical_skills']['technologies_and_topics']) if technical_summary['technical_skills']['technologies_and_topics'] else 'No specific technologies tagged'}

## Notable Projects
"""
            
            for project in technical_summary['notable_projects']:
                report += f"""
### {project['name']} ⭐ {project['stars']}
- **Description**: {project['description']}
- **Primary Language**: {project['language'] or 'Not specified'}
- **Stars**: {project['stars']}
- **Technologies**: {', '.join(project['topics']) if project['topics'] else 'No tags'}
- **README Summary**: {project['readme_summary']}
- **Additional Technologies from README**: {', '.join(project['readme_technologies']) if project['readme_technologies'] else 'None detected'}
- **URL**: {project['url']}
"""
            
            report += f"""
## Recent Activity Summary
Total of {technical_summary['technical_skills']['total_repositories']} public repositories analyzed.
Most recently updated repositories demonstrate active development in: {', '.join(technical_summary['technical_skills']['programming_languages'][:5]) if technical_summary['technical_skills']['programming_languages'] else 'various technologies'}.
"""
            
            return report
            
        except Exception as e:
            return f"Error analyzing GitHub profile: {str(e)}"


# Keep the original tool for compatibility
class MyCustomToolInput(BaseModel):
    """Input schema for MyCustomTool."""
    argument: str = Field(..., description="Description of the argument.")

class MyCustomTool(BaseTool):
    name: str = "Name of my tool"
    description: str = (
        "Clear description for what this tool is useful for, your agent will need this information to use it."
    )
    args_schema: Type[BaseModel] = MyCustomToolInput

    def _run(self, argument: str) -> str:
        # Implementation goes here
        return "this is an example of a tool output, ignore it and move along."
