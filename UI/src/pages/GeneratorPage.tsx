import { useState } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import {
  Box,
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Chip,
  Paper,
  CircularProgress,
  Alert,
  Divider,
} from '@mui/material';
import {
  Send as SendIcon,
  Description as DescriptionIcon,
  GitHub as GitHubIcon,
  AutoAwesome as AutoAwesomeIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { cvAPI, CVResponse } from '../services/cvAPI';

interface OutletContext {
  refreshHistory: () => void;
}

const GeneratorPage = () => {
  const [jobDescription, setJobDescription] = useState('');
  const [githubProfile, setGithubProfile] = useState('https://github.com/kpatc');
  const [loading, setLoading] = useState(false);
  const [generatedCV, setGeneratedCV] = useState<CVResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { refreshHistory } = useOutletContext<OutletContext>();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    console.log('Form submitted!', { jobDescription, githubProfile });
    
    if (!jobDescription.trim()) {
      setError('Please provide a job description');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      console.log('Calling API...');
      const response = await cvAPI.generateCV(jobDescription, githubProfile);
      console.log('API Response:', response);
      setGeneratedCV(response.data);
      refreshHistory();
      
      // Ne plus rediriger automatiquement - laisser l'utilisateur décider
    } catch (err: any) {
      console.error('Error generating CV:', err);
      if (err.code === 'ECONNABORTED' || err.message.includes('timeout')) {
        setError('⏱️ Generation is taking longer than expected. The backend is still processing your request. Please wait or try again in a few minutes.');
      } else if (err.response?.status === 500) {
        setError('🔧 Server error during generation. Please check that the backend is running and try again.');
      } else {
        setError('❌ Error generating CV. Please check your connection and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const exampleJobs = [
    'Front-End Engineer, React/TypeScript',
    'Full-Stack Developer, Node.js',
    'Data Scientist, Python/ML',
    'DevOps Engineer, AWS/Docker',
  ];

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography
          variant="h4"
          component="h1"
          gutterBottom
          sx={{
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontWeight: 700,
          }}
        >
          Personalized CV Generator
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Describe the job position to generate an optimized CV based on your LinkedIn and GitHub profiles
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap' }}>
          {exampleJobs.map((job) => (
            <Chip
              key={job}
              label={job}
              variant="outlined"
              size="small"
              onClick={() => setJobDescription(`We are looking for a ${job}...`)}
              sx={{ cursor: 'pointer' }}
            />
          ))}
        </Box>
      </Box>

      <Grid container spacing={4}>
        {/* Panneau de gauche - Formulaire comme dans l'image */}
        <Grid size={{ xs: 12, lg: 6 }}>
          <Card
            sx={{
              borderRadius: 3,
              border: '1px solid rgba(99, 102, 241, 0.2)',
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              color: 'white',
              mb: 2,
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <DescriptionIcon sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight="bold">
                  Review and Edit Before Submission
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                Review and edit your application form responses before submission
              </Typography>
            </CardContent>
          </Card>

          <Paper 
            component="form" 
            onSubmit={handleSubmit}
            sx={{ 
              p: 3, 
              borderRadius: 3,
              border: '1px solid rgba(0, 0, 0, 0.1)',
              background: 'rgba(248, 250, 252, 0.8)',
            }}
          >
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
                <GitHubIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                GitHub Profile
              </Typography>
              <TextField
                fullWidth
                value={githubProfile}
                onChange={(e) => setGithubProfile(e.target.value)}
                placeholder="https://github.com/your-profile"
                variant="outlined"
                size="small"
                sx={{ mb: 2 }}
              />
            </Box>

            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
                Job Description
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={8}
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="We are looking for a Front-End Developer to join our team...

Include:
• Required technologies (React, Node.js, Python...)
• Desired experience level
• Company type and industry
• Main responsibilities
• Specific skills required

The more details you provide, the more personalized your CV will be!"
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    '&:hover fieldset': {
                      borderColor: 'primary.main',
                    },
                  },
                }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {jobDescription.length}/5000 characters • More details = More precise CV ✨
              </Typography>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={loading || !jobDescription.trim()}
              startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
              sx={{
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                borderRadius: 2,
                py: 1.5,
                fontSize: '1rem',
                fontWeight: 600,
                textTransform: 'none',
                '&:hover': {
                  background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                },
              }}
            >
              {loading ? 'Generating...' : 'Generate my CV with AI'}
            </Button>

            {loading && (
              <Box sx={{ mt: 2, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  🤖 Analyzing your LinkedIn and GitHub profiles...
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  ⏱️ This may take 2-5 minutes - AI is analyzing your projects and generating a personalized CV
                </Typography>
                <Typography variant="caption" color="primary.main" sx={{ display: 'block', mt: 1 }}>
                  ✨ Please be patient, quality is worth the wait!
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Panneau de droite - CV personnalisé comme dans l'image */}
        <Grid size={{ xs: 12, lg: 6 }}>
          <Card
            sx={{
              height: 'fit-content',
              borderRadius: 3,
              border: '1px solid rgba(0, 0, 0, 0.1)',
            }}
          >
            <Box
              sx={{
                p: 2,
                background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
                borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <Typography variant="h6" fontWeight="bold">
                Personalized CV
              </Typography>
              {generatedCV && (
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Chip
                    icon={<CheckCircleIcon />}
                    label="CV Generated"
                    color="success"
                    variant="outlined"
                    size="small"
                  />
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => navigate(`/view/${generatedCV.id}`)}
                    sx={{ ml: 1 }}
                  >
                    View & Download
                  </Button>
                </Box>
              )}
            </Box>

            <CardContent sx={{ p: 3, minHeight: 400, maxHeight: 600, overflow: 'auto' }}>
              {loading ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 300 }}>
                  <CircularProgress size={60} sx={{ mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    <AutoAwesomeIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                    AI in action...
                  </Typography>
                  <Typography variant="body2" color="text.secondary" textAlign="center">
                    Analyzing your LinkedIn and GitHub data<br />
                    Generating personalized CV in progress
                  </Typography>
                </Box>
              ) : generatedCV ? (
                <Box>
                  <Alert severity="success" sx={{ mb: 3 }}>
                    CV generated successfully! You can now review it below and click "View & Download" when ready.
                  </Alert>
                  <Box
                    sx={{
                      '& h1, & h2, & h3': { color: 'primary.main', fontWeight: 'bold' },
                      '& h1': { fontSize: '1.5rem', mb: 2 },
                      '& h2': { fontSize: '1.3rem', mb: 1.5, mt: 3 },
                      '& h3': { fontSize: '1.1rem', mb: 1, mt: 2 },
                      '& p': { mb: 1, lineHeight: 1.6 },
                      '& ul': { pl: 3, mb: 2 },
                      '& li': { mb: 0.5 },
                    }}
                  >
                    <ReactMarkdown>{generatedCV.cv_content}</ReactMarkdown>
                  </Box>
                </Box>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 300, textAlign: 'center' }}>
                  <DescriptionIcon sx={{ fontSize: 80, color: 'action.disabled', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    Your personalized CV will appear here
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Fill in the job description and click "Generate" to start
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default GeneratorPage;
