from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json
import os
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Importer la crew locale
from crew import AiCvPersonalizerLinkedinGithubIntegrationCrew

app = FastAPI(title="AI CV Personalizer API", version="1.0.0")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # URLs du frontend React et Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles Pydantic
class JobDescriptionRequest(BaseModel):
    job_description: str
    github_profile_url: str = "https://github.com/kpatc"

class CVResponse(BaseModel):
    id: str
    job_description: str
    cv_content: str
    created_at: str
    filename: str

class HistoryItem(BaseModel):
    id: str
    job_description: str
    created_at: str
    filename: str

# Stockage en mémoire (à remplacer par une DB en production)
conversations_history = []

@app.get("/")
async def root():
    return {"message": "AI CV Personalizer API"}

@app.post("/generate-cv", response_model=CVResponse)
async def generate_cv(request: JobDescriptionRequest):
    try:
        # Génération d'un ID unique
        conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Préparer les inputs pour la crew
        inputs = {
            'linkedin_data_file': 'knowledge/linkedin_data.json',
            'job_description': request.job_description,
            'github_profile_url': request.github_profile_url
        }
        
        # Exécuter la crew
        result = AiCvPersonalizerLinkedinGithubIntegrationCrew().crew().kickoff(inputs=inputs)
        
        # Nom du fichier
        filename = f"cv_{conversation_id}.md"
        filepath = f"RECOMMENDATIONS/{filename}"
        
        # Sauvegarder le CV
        cv_content = str(result)
        os.makedirs("RECOMMENDATIONS", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(cv_content)
        
        # Ajouter à l'historique
        history_item = {
            "id": conversation_id,
            "job_description": request.job_description[:100] + "..." if len(request.job_description) > 100 else request.job_description,
            "created_at": datetime.now().isoformat(),
            "filename": filename
        }
        conversations_history.append(history_item)
        
        return CVResponse(
            id=conversation_id,
            job_description=request.job_description,
            cv_content=cv_content,
            created_at=datetime.now().isoformat(),
            filename=filename
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du CV: {str(e)}")

@app.get("/history", response_model=List[HistoryItem])
async def get_history():
    return conversations_history

@app.get("/cv/{cv_id}")
async def get_cv(cv_id: str):
    try:
        filename = f"cv_{cv_id}.md"
        filepath = f"RECOMMENDATIONS/{filename}"
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="CV non trouvé")
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {"id": cv_id, "content": content, "filename": filename}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération du CV: {str(e)}")

@app.get("/download/{cv_id}")
async def download_cv(cv_id: str):
    try:
        filename = f"cv_{cv_id}.md"
        filepath = f"RECOMMENDATIONS/{filename}"
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="CV non trouvé")
        
        return FileResponse(
            path=filepath,
            media_type='application/octet-stream',
            filename=filename
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du téléchargement: {str(e)}")

def run_server():
    """Fonction pour démarrer le serveur depuis uv run"""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    run_server()
