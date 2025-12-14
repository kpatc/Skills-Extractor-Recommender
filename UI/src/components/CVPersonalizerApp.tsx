import { useState, useEffect } from 'react';
import styled from 'styled-components';
import { 
  Card, 
  CardContent, 
  Typography, 
  TextField, 
  Button, 
  Box, 
  Grid, 
  Drawer, 
  List, 
  ListItem, 
  ListItemText, 
  ListItemIcon,
  IconButton,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  Snackbar
} from '@mui/material';
import { 
  Description as DescriptionIcon, 
  History as HistoryIcon, 
  Download as DownloadIcon,
  Menu as MenuIcon,
  Send as SendIcon,
  GitHub as GitHubIcon,
  Work as WorkIcon
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { cvAPI, CVResponse, HistoryItem } from '../services/cvAPI';

const AppContainer = styled.div`
  display: flex;
  height: 100%;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
`;

const MainContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
`;

const ContentArea = styled.div`
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;

  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
    gap: 1rem;
    padding: 1rem;
  }
`;

const FormCard = styled(Card)`
  && {
    height: fit-content;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  }
`;

const CVDisplayCard = styled(Card)`
  && {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    max-height: 700px;
    overflow-y: auto;
  }
`;

const StyledDrawer = styled(Drawer)`
  && .MuiDrawer-paper {
    width: 300px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
  }
`;

interface CVData {
  id: string;
  content: string;
  job_description: string;
  created_at: string;
  filename?: string;
}

export const CVPersonalizerApp: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [jobDescription, setJobDescription] = useState('');
  const [githubProfile, setGithubProfile] = useState('https://github.com/kpatc');
  const [loading, setLoading] = useState(false);
  const [generatedCV, setGeneratedCV] = useState<CVResponse | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  useEffect(() => {
    fetchHistory();
    // Test de connexion à l'API au démarrage
    testAPIConnection();
  }, []);

  const testAPIConnection = async () => {
    try {
      await cvAPI.healthCheck();
      console.log('API connexion établie');
    } catch (error) {
      console.error('Erreur de connexion API:', error);
      setSnackbar({
        open: true,
        message: 'Erreur de connexion au backend. Vérifiez que le serveur est démarré.',
        severity: 'error'
      });
    }
  };

  const fetchHistory = async () => {
    try {
      const historyData = await cvAPI.getHistory();
      setHistory(historyData);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!jobDescription.trim()) {
      setSnackbar({
        open: true,
        message: 'Veuillez fournir une description de poste',
        severity: 'error'
      });
      return;
    }
    
    setLoading(true);
    try {
      const response = await cvAPI.generateCV({
        job_description: jobDescription,
        github_profile_url: githubProfile
      });
      
      setGeneratedCV(response);
      fetchHistory();
      setSnackbar({
        open: true,
        message: 'CV généré avec succès!',
        severity: 'success'
      });
    } catch (error) {
      console.error('Error generating CV:', error);
      setSnackbar({
        open: true,
        message: 'Échec de la génération du CV. Vérifiez que le backend est démarré.',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleHistoryItemClick = async (item: HistoryItem) => {
    try {
      const cvData = await cvAPI.getCV(item.id);
      setGeneratedCV(cvData);
      setSidebarOpen(false);
    } catch (error) {
      console.error('Error fetching CV:', error);
      setSnackbar({
        open: true,
        message: 'Erreur lors du chargement du CV',
        severity: 'error'
      });
    }
  };

  const handleDownload = async () => {
    if (!generatedCV) return;
    
    try {
      const blob = await cvAPI.downloadCV(generatedCV.id);
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', generatedCV.filename || 'cv.md');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setSnackbar({
        open: true,
        message: 'CV téléchargé avec succès!',
        severity: 'success'
      });
    } catch (error) {
      console.error('Error downloading CV:', error);
      setSnackbar({
        open: true,
        message: 'Échec du téléchargement du CV',
        severity: 'error'
      });
    }
  };

  return (
    <AppContainer>
      <StyledDrawer
        variant="temporary"
        anchor="left"
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ color: 'white', mb: 2, display: 'flex', alignItems: 'center' }}>
            <HistoryIcon sx={{ mr: 1 }} />
            Historique des CVs
          </Typography>
          <List>
            {history.map((item) => (
              <ListItem 
                key={item.id}
                button
                onClick={() => handleHistoryItemClick(item)}
                sx={{ 
                  borderRadius: 2, 
                  mb: 1,
                  '&:hover': { 
                    backgroundColor: 'rgba(255, 255, 255, 0.1)' 
                  }
                }}
              >
                <ListItemIcon>
                  <DescriptionIcon sx={{ color: 'white' }} />
                </ListItemIcon>
                <ListItemText 
                  primary={item.job_description.substring(0, 50) + '...'}
                  secondary={new Date(item.created_at).toLocaleDateString()}
                  sx={{ 
                    '& .MuiListItemText-primary': { color: 'white' },
                    '& .MuiListItemText-secondary': { color: 'rgba(255, 255, 255, 0.7)' }
                  }}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      </StyledDrawer>

      <MainContent>
        <Header>
          <Box display="flex" alignItems="center">
            <IconButton onClick={() => setSidebarOpen(true)} sx={{ mr: 2 }}>
              <MenuIcon />
            </IconButton>
            <Typography variant="h5" sx={{ fontWeight: 600 }}>
              AI CV Personalizer
            </Typography>
          </Box>
          {generatedCV && (
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={handleDownload}
              sx={{
                background: 'linear-gradient(45deg, #667eea 30%, #764ba2 90%)',
                boxShadow: '0 3px 5px 2px rgba(102, 126, 234, .3)',
              }}
            >
              Télécharger CV
            </Button>
          )}
        </Header>

        <ContentArea>
          {/* Formulaire de génération */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <FormCard>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
                  <WorkIcon sx={{ mr: 1, color: '#667eea' }} />
                  Générer un CV personnalisé
                </Typography>
                
                <form onSubmit={handleSubmit}>
                  <Box sx={{ mb: 3 }}>
                    <TextField
                      fullWidth
                      label="Profil GitHub"
                      value={githubProfile}
                      onChange={(e) => setGithubProfile(e.target.value)}
                      variant="outlined"
                      InputProps={{
                        startAdornment: <GitHubIcon sx={{ mr: 1, color: '#666' }} />
                      }}
                      sx={{ mb: 2 }}
                    />
                    
                    <TextField
                      fullWidth
                      multiline
                      rows={8}
                      label="Description du poste"
                      value={jobDescription}
                      onChange={(e) => setJobDescription(e.target.value)}
                      variant="outlined"
                      placeholder="Décrivez le poste cible, les compétences requises, l'entreprise..."
                      required
                    />
                    
                    <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                      Plus de détails = CV plus précis ✨
                    </Typography>
                  </Box>
                  
                  <Button
                    type="submit"
                    variant="contained"
                    size="large"
                    disabled={loading}
                    startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
                    sx={{
                      width: '100%',
                      background: 'linear-gradient(45deg, #667eea 30%, #764ba2 90%)',
                      boxShadow: '0 3px 5px 2px rgba(102, 126, 234, .3)',
                      py: 1.5
                    }}
                  >
                    {loading ? 'Génération en cours...' : 'Générer avec l\'IA'}
                  </Button>
                </form>
              </CardContent>
            </FormCard>
          </motion.div>

          {/* Affichage du CV */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <CVDisplayCard>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
                  <DescriptionIcon sx={{ mr: 1, color: '#667eea' }} />
                  CV Personnalisé
                </Typography>
                
                {loading ? (
                  <Box display="flex" flexDirection="column" alignItems="center" py={8}>
                    <CircularProgress size={60} sx={{ mb: 2 }} />
                    <Typography variant="body1" color="textSecondary">
                      Analyse des données LinkedIn et GitHub...
                    </Typography>
                    <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                      Cela peut prendre quelques minutes
                    </Typography>
                  </Box>
                ) : generatedCV ? (
                  <Box>
                    <Box sx={{ mb: 2 }}>
                      <Chip 
                        label={`Généré le ${new Date(generatedCV.created_at).toLocaleDateString()}`}
                        size="small"
                        sx={{ mr: 1 }}
                      />
                    </Box>
                    <Paper 
                      elevation={0} 
                      sx={{ 
                        p: 2, 
                        backgroundColor: '#f8f9fa',
                        borderRadius: 2,
                        maxHeight: '500px',
                        overflow: 'auto'
                      }}
                    >
                      <Typography 
                        component="pre" 
                        sx={{ 
                          whiteSpace: 'pre-wrap',
                          fontFamily: 'monospace',
                          fontSize: '0.9rem',
                          lineHeight: 1.6
                        }}
                      >
                        {generatedCV.content}
                      </Typography>
                    </Paper>
                  </Box>
                ) : (
                  <Box display="flex" flexDirection="column" alignItems="center" py={8}>
                    <DescriptionIcon sx={{ fontSize: 80, color: '#ddd', mb: 2 }} />
                    <Typography variant="h6" color="textSecondary">
                      Votre CV personnalisé apparaîtra ici
                    </Typography>
                    <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                      Remplissez le formulaire et cliquez sur Générer
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </CVDisplayCard>
          </motion.div>
        </ContentArea>
      </MainContent>

      {/* Snackbar pour les notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert 
          onClose={() => setSnackbar({ ...snackbar, open: false })} 
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </AppContainer>
  );
};
