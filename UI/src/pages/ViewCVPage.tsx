import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  Chip,
  Paper,
  Divider,
  Alert,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import {
  Download as DownloadIcon,
  Share as ShareIcon,
  Edit as EditIcon,
  ArrowBack as ArrowBackIcon,
  AutoAwesome as AutoAwesomeIcon,
  CalendarToday as CalendarIcon,
  Assignment as AssignmentIcon,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { cvAPI, CVResponse } from '../services/cvAPI';

const ViewCVPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [cv, setCv] = useState<CVResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    const fetchCV = async () => {
      if (!id) {
        setError('CV ID not provided');
        setLoading(false);
        return;
      }

      try {
        const response = await cvAPI.getCV(id);
        setCv(response.data);
      } catch (err: any) {
        console.error('Error fetching CV:', err);
        setError('Error loading CV');
      } finally {
        setLoading(false);
      }
    };

    fetchCV();
  }, [id]);

  const handleDownload = async () => {
    if (!id) return;
    
    setDownloading(true);
    try {
      const response = await cvAPI.downloadCV(id);
      
      // Create download link
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `CV_${cv?.job_title || 'personalise'}_${new Date().toISOString().split('T')[0]}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error('Error downloading CV:', err);
      alert('Download error. Please try again.');
    } finally {
      setDownloading(false);
    }
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: `Personalized CV - ${cv?.job_title}`,
        text: 'Discover my AI-generated personalized CV',
        url: window.location.href,
      });
    } else {
      // Fallback: copy URL
      navigator.clipboard.writeText(window.location.href);
      alert('Link copied to clipboard!');
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
          <Box sx={{ textAlign: 'center' }}>
            <CircularProgress size={60} sx={{ mb: 2 }} />
            <Typography variant="h6">Chargement du CV...</Typography>
          </Box>
        </Box>
      </Container>
    );
  }

  if (error || !cv) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error || 'CV not found'}
        </Alert>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/generator')}
        >
          Back to Generator
        </Button>
      </Container>
    );
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      {/* En-tête avec actions */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <IconButton
            onClick={() => navigate('/generator')}
            sx={{ mr: 2 }}
          >
            <ArrowBackIcon />
          </IconButton>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h4" fontWeight="bold" gutterBottom>
              {cv.job_title || 'Personalized CV'}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
              <Chip
                icon={<CalendarIcon />}
                label={`Generated on ${formatDate(cv.created_at)}`}
                variant="outlined"
                size="small"
              />
              <Chip
                icon={<AutoAwesomeIcon />}
                label="IA Générée"
                color="primary"
                variant="outlined"
                size="small"
              />
            </Box>
          </Box>
        </Box>

        {/* Barre d'actions */}
        <Paper
          sx={{
            p: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
            border: '1px solid rgba(0, 0, 0, 0.1)',
            borderRadius: 2,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AssignmentIcon color="primary" />
            <Typography variant="subtitle1" fontWeight="medium">
              CV ready to download
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Edit">
              <Button
                variant="outlined"
                startIcon={<EditIcon />}
                onClick={() => navigate('/generator')}
                size="small"
              >
                Edit
              </Button>
            </Tooltip>
            
            <Tooltip title="Share">
              <IconButton onClick={handleShare} color="primary">
                <ShareIcon />
              </IconButton>
            </Tooltip>
            
            <Button
              variant="contained"
              startIcon={downloading ? <CircularProgress size={16} color="inherit" /> : <DownloadIcon />}
              onClick={handleDownload}
              disabled={downloading}
              sx={{
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                },
              }}
            >
              {downloading ? 'Downloading...' : 'Download PDF'}
            </Button>
          </Box>
        </Paper>
      </Box>

      {/* CV Content */}
      <Card
        sx={{
          borderRadius: 3,
          border: '1px solid rgba(0, 0, 0, 0.1)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
        }}
      >
        <CardContent sx={{ p: 4 }}>
          {/* Job metadata */}
          {cv.job_description && (
            <Paper
              sx={{
                p: 3,
                mb: 4,
                background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
                border: '1px solid rgba(245, 158, 11, 0.2)',
                borderRadius: 2,
              }}
            >
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                📋 Target job description
              </Typography>
              <Typography
                variant="body2"
                sx={{
                  maxHeight: 120,
                  overflow: 'auto',
                  lineHeight: 1.6,
                  fontSize: '0.9rem',
                }}
              >
                {cv.job_description.substring(0, 300)}
                {cv.job_description.length > 300 && '...'}
              </Typography>
            </Paper>
          )}

          <Divider sx={{ mb: 4 }} />

          {/* Contenu du CV avec style */}
          <Box
            sx={{
              '& h1': {
                color: 'primary.main',
                fontWeight: 'bold',
                fontSize: '2rem',
                mb: 3,
                textAlign: 'center',
                pb: 2,
                borderBottom: '2px solid',
                borderColor: 'primary.main',
              },
              '& h2': {
                color: 'primary.main',
                fontWeight: 'bold',
                fontSize: '1.5rem',
                mb: 2,
                mt: 4,
                pb: 1,
                borderBottom: '1px solid',
                borderColor: 'primary.light',
              },
              '& h3': {
                color: 'primary.dark',
                fontWeight: 'semibold',
                fontSize: '1.2rem',
                mb: 1.5,
                mt: 3,
              },
              '& h4': {
                color: 'text.primary',
                fontWeight: 'medium',
                fontSize: '1.1rem',
                mb: 1,
                mt: 2,
              },
              '& p': {
                mb: 1.5,
                lineHeight: 1.7,
                color: 'text.secondary',
                fontSize: '1rem',
              },
              '& ul': {
                pl: 3,
                mb: 2,
                '& li': {
                  mb: 0.5,
                  lineHeight: 1.6,
                  color: 'text.secondary',
                },
              },
              '& ol': {
                pl: 3,
                mb: 2,
                '& li': {
                  mb: 0.5,
                  lineHeight: 1.6,
                  color: 'text.secondary',
                },
              },
              '& strong': {
                color: 'text.primary',
                fontWeight: 'bold',
              },
              '& em': {
                color: 'primary.main',
                fontStyle: 'italic',
              },
              '& code': {
                backgroundColor: 'grey.100',
                padding: '2px 6px',
                borderRadius: 1,
                fontFamily: 'monospace',
                fontSize: '0.9rem',
              },
            }}
          >
                                <ReactMarkdown>{cv.cv_content}</ReactMarkdown>
          </Box>
        </CardContent>
      </Card>

      {/* Footer with information */}
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          CV generated with AI • Based on your LinkedIn and GitHub profiles
        </Typography>
        <Typography variant="caption" color="text.secondary">
          ID: {cv.id} • Created on {formatDate(cv.created_at)}
        </Typography>
      </Box>
    </Container>
  );
};

export default ViewCVPage;
