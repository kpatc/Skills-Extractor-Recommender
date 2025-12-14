import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Configuration axios par défaut
axios.defaults.timeout = 300000; // 5 minutes timeout pour la génération de CV

export interface JobDescriptionRequest {
  job_description: string;
  github_profile_url: string;
}

export interface CVResponse {
  id: string;
  cv_content: string;
  job_description: string;
  github_profile_url: string;
  created_at: string;
  filename: string;
}

export interface HistoryItem {
  id: string;
  job_description: string;
  created_at: string;
}

export const cvAPI = {
  // Générer un nouveau CV
  generateCV: async (job_description: string, github_profile_url: string): Promise<{ data: CVResponse }> => {
    const response = await axios.post(`${API_BASE_URL}/generate-cv`, {
      job_description,
      github_profile_url
    });
    return { data: response.data };
  },

  // Récupérer l'historique des CVs
  getHistory: async (): Promise<{ data: HistoryItem[] }> => {
    const response = await axios.get(`${API_BASE_URL}/history`);
    return { data: response.data };
  },

  // Récupérer un CV spécifique
  getCV: async (id: string): Promise<{ data: CVResponse }> => {
    const response = await axios.get(`${API_BASE_URL}/cv/${id}`);
    return { data: response.data };
  },

  // Télécharger un CV
  downloadCV: async (id: string): Promise<{ data: Blob }> => {
    const response = await axios.get(`${API_BASE_URL}/download/${id}`, {
      responseType: 'blob'
    });
    return { data: response.data };
  },

  // Test de connexion à l'API
  healthCheck: async (): Promise<any> => {
    const response = await axios.get(`${API_BASE_URL}/`);
    return response.data;
  }
};

export default cvAPI;
