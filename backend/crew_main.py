#!/usr/bin/env python
import sys
import os
from dotenv import load_dotenv
from crew import AiCvPersonalizerLinkedinGithubIntegrationCrew

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# This main file is intended to be a way for your to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'linkedin_data_file': 'knowledge/linkedin_data.json',
        'job_description': '''
            Big Data Engineer:
            About the job
            Aperçu 

            Leyton Morocco is a global leader providing top-tier business and engineering services. With expert handling complex operations and a multilingual team, we support clients worldwide in areas such as innovation funding, consulting, energy and outsourced services.

            Who We're Looking For :

            We need a Data Engineer who thrives at the intersection of Backend Development and Data Engineering. If you have strong Python skills, fluency in SQL / Data Modeling, and experience working with big data technologies, you're exactly who we need !

            Required Skills & Experience :

            Python Expertise - Strong experience in backend development and data transformation using Pandas, Flask, FastAPI or Django. 
            SQL & Data Modeling - Solid understanding of relational database design and optimization.
            Web Scraping & Automation - Experience using Selenium or BeautifulSoup for data extraction from websites.
            Big Data Processing - Hands-on experience with PySpark and familiarity with the Hadoop ecosystem.
            Communication - Professional profeciency in French & English.
            Bonus Skills - Knowledge of Docker and CI/CD workflows is a plus.
            Experience - 1 to 3 years in a similar position.
            Education - Master's Degree in Software Development or a related field.
             Missions 

            Main Responsibilities:

            Design and implement infrastructure for managing the company's data in alignment with various business challenges. 
            Develop and manage data flows, including ingestion, modeling, warehousing, and cleaning, using Big Data technologies. 
            Analyze source systems to define optimal data management strategies from collection to analysis. 
            Collaborate with cross-functional teams to integrate Big Data solutions with existing systems. 
            Optimize and maintain Big Data platforms for performance, reliability, and scalability. 
            Develop and enforce data governance policies to ensure data quality and security. 
            Create and maintain documentation related to data architecture, processes, and workflows. 
            Conduct performance tuning and troubleshooting to resolve data-related issues. 
            Develop data visualizations and reports to support business decision-making. 
            Lead and participate in code reviews to ensure code quality and best practices. 

            Profil 

            Qualifications :

            Bachelor's Degree in Software Development, Computer Engineering, or a related field.
            Expertise in one or more Big Data technologies.
            Certifications in Big Data technologies are a plus.
            1 to 3 years of experience in a similar role.
            Proficiency in understanding complex data processing algorithms and mechanisms.
            Skills & experience in Python and SQL, Spark, Airflow, Kafka, RabbitMQ, ElasticSearch (and the ELK Suite), MongoDB, Neo4J, Docker, and front-end frameworks like Angular, React, or Vue.js.
            Excellent listening, synthesis, and analytical skills.
            Intellectual curiosity, initiative, and proactivity.
            Strong organizational skills and the ability to work autonomously.
            Excellent interpersonal skills and the ability to facilitate team collaboration.

        ''',
        'github_profile_url': 'https://github.com/kpatc'
    }
    result = AiCvPersonalizerLinkedinGithubIntegrationCrew().crew().kickoff(inputs=inputs)
    # Sauvegarde du CV généré
    if result:
        # On suppose que le résultat est un texte markdown
        from json import load
        with open('knowledge/linkedin_data.json') as f:
            data = load(f)
        name = data.get('personal_info', {}).get('name', 'cv')
        filename = f"RECOMMENDATIONS/cv_{name.replace(' ', '_')}.md"
        with open(filename, "w") as f:
            f.write(str(result))
        print(f"CV généré et sauvegardé dans {filename}")
    else:
        print("Aucun résultat généré.")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        'linkedin_data_file': 'knowledge/linkedin_data.json',
        'job_description': '''
            Description du poste
            ORANGE BUSINESS

            Rabat
            Stage
            Sur site
            il y a 2 semaine(s)

            Pour un stagiaire automatisation / EDH : SQL, Python (pandas + autres librairies de traitement de données / Polars), Spark, power bi , git , Hadoop ( de preference ) , Excel est un plus . Si une expérience en data engineer ou software engineer c’est plus favorable.

            Pour un stagiaire AI : Power bi (maitrise de Dax), Python, SQL, expérience en LLMS (Une expérience sur un projet de mise en production d’un LLM , avec l’API c’est un plus) et Deep Learning (keras , tensorflow ) , git , docker .

            Vous avez un bac+5, avec les compétences suivantes :

            Niveau de communication excellent en Français
            Niveau souhaitable correct en Anglais
            Vous êtes à la recherche d’un stage en ANAPEC en Data engineer ou Data Analyst
            Orange Business est l’entité du Groupe Orange qui accompagne les entreprises et organisations dans leur transformation digitale. Forts de 29 100 collaborateurs à travers le monde, nous concilions présence globale et approche locale pour inventer avec nos clients de nouveaux business models permettant de libérer tout leur potentiel. Ainsi, nous créons un impact positif, à la fois pour leur activité et pour le monde qui les entoure.

            Ce qui nous distingue de nos concurrents ? Notre double expertise : nous sommes à la fois opérateur de réseaux et intégrateur de solutions digitales. En tant qu’opérateur, nous construisons et exploitons des infrastructures complexes. En tant qu’intégrateur, nous concevons et manageons des solutions digitales de bout-en-bout.

            Nous apportons à nos clients des solutions autour de 5 grands enjeux transverses : mettre en place leur espace de travail numérique, améliorer leur expérience client, faciliter l’essor de l’industrie 4.0, collecter et traiter les données, transformer et sécuriser leur infrastructure réseau.

            C’est parce qu’Orange Business maîtrise toutes les étapes de la transformation digitale que nous proposons à nos clients les solutions les plus pertinentes.

            Nous imaginons un futur épatant avec nos clients et nos collaborateurs !

            Alors, prêt à rejoindre l’aventure ?

            Rejoignez-nous !

            Orange Business
        ''',
        'github_profile_url': 'https://github.com/kpatc'
    }
    try:
        AiCvPersonalizerLinkedinGithubIntegrationCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        AiCvPersonalizerLinkedinGithubIntegrationCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        'linkedin_data_file': '../knowledge/linkedin_data.json',
        'job_description': '''
            Description du poste
            ORANGE BUSINESS

            Rabat
            Stage
            Sur site
            il y a 2 semaine(s)

            Pour un stagiaire automatisation / EDH : SQL, Python (pandas + autres librairies de traitement de données / Polars), Spark, power bi , git , Hadoop ( de preference ) , Excel est un plus . Si une expérience en data engineer ou software engineer c’est plus favorable.

            Pour un stagiaire AI : Power bi (maitrise de Dax), Python, SQL, expérience en LLMS (Une expérience sur un projet de mise en production d’un LLM , avec l’API c’est un plus) et Deep Learning (keras , tensorflow ) , git , docker .

            Vous avez un bac+5, avec les compétences suivantes :

            Niveau de communication excellent en Français
            Niveau souhaitable correct en Anglais
            Vous êtes à la recherche d’un stage en ANAPEC en Data engineer ou Data Analyst
            Orange Business est l’entité du Groupe Orange qui accompagne les entreprises et organisations dans leur transformation digitale. Forts de 29 100 collaborateurs à travers le monde, nous concilions présence globale et approche locale pour inventer avec nos clients de nouveaux business models permettant de libérer tout leur potentiel. Ainsi, nous créons un impact positif, à la fois pour leur activité et pour le monde qui les entoure.

            Ce qui nous distingue de nos concurrents ? Notre double expertise : nous sommes à la fois opérateur de réseaux et intégrateur de solutions digitales. En tant qu’opérateur, nous construisons et exploitons des infrastructures complexes. En tant qu’intégrateur, nous concevons et manageons des solutions digitales de bout-en-bout.

            Nous apportons à nos clients des solutions autour de 5 grands enjeux transverses : mettre en place leur espace de travail numérique, améliorer leur expérience client, faciliter l’essor de l’industrie 4.0, collecter et traiter les données, transformer et sécuriser leur infrastructure réseau.

            C’est parce qu’Orange Business maîtrise toutes les étapes de la transformation digitale que nous proposons à nos clients les solutions les plus pertinentes.

            Nous imaginons un futur épatant avec nos clients et nos collaborateurs !

            Alors, prêt à rejoindre l’aventure ?

            Rejoignez-nous !

            Orange Business
        ''',
        'github_profile_url': 'https://github.com/kpatc'
    }
    try:
        AiCvPersonalizerLinkedinGithubIntegrationCrew().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: main.py <command> [<args>]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "run":
        run()
    elif command == "train":
        train()
    elif command == "replay":
        replay()
    elif command == "test":
        test()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
