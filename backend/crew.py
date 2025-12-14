import os
from crewai import LLM
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
	ScrapeWebsiteTool,
	FileReadTool
)

@CrewBase
class AiCvPersonalizerLinkedinGithubIntegrationCrew:
    """AiCvPersonalizerLinkedinGithubIntegration crew"""

    
    @agent
    def professional_data_analyzer(self) -> Agent:
        
        return Agent(
            config=self.agents_config["professional_data_analyzer"],
            tools=[
				FileReadTool()
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gemini/gemini-2.0-flash",
                temperature=0.7,
                api_key="AIzaSyAFgyaoriqZ34-VV4iDX4uRUzLUL0wXNPQ",
            ),
        )
    
    @agent
    def github_profile_data_extractor(self) -> Agent:
        
        return Agent(
            config=self.agents_config["github_profile_data_extractor"],
            tools=[
				ScrapeWebsiteTool()
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gemini/gemini-2.0-flash",
                temperature=0.7,
                api_key="AIzaSyAFgyaoriqZ34-VV4iDX4uRUzLUL0wXNPQ",
            ),
        )
    
    @agent
    def cv_personalization_specialist(self) -> Agent:
        
        return Agent(
            config=self.agents_config["cv_personalization_specialist"],
            tools=[

            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gemini/gemini-2.0-flash",
                temperature=0.7,
                api_key="AIzaSyAFgyaoriqZ34-VV4iDX4uRUzLUL0wXNPQ",
            ),
        )
    

    
    @task
    def analyze_professional_data_from_json(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_professional_data_from_json"],
        )
    
    @task
    def extract_github_technical_data(self) -> Task:
        return Task(
            config=self.tasks_config["extract_github_technical_data"],
        )
    
    @task
    def generate_personalized_cv(self) -> Task:
        return Task(
            config=self.tasks_config["generate_personalized_cv"],
        )
    

    @crew
    def crew(self) -> Crew:
        """Creates the AiCvPersonalizerLinkedinGithubIntegration crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
