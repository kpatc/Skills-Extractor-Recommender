import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
} from '@mui/material';
import {
  AutoAwesome as AutoAwesomeIcon,
  GitHub as GitHubIcon,
  LinkedIn as LinkedInIcon,
  Download as DownloadIcon,
  Rocket as RocketIcon,
} from '@mui/icons-material';

const HomePage = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <AutoAwesomeIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'Advanced AI',
      description: 'Uses Gemini 2.0 Flash to analyze your profiles and generate optimized CVs.',
    },
    {
      icon: <GitHubIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'GitHub Integration',
      description: 'Automatic analysis of your repositories to highlight your projects.',
    },
    {
      icon: <LinkedInIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'LinkedIn Data',
      description: 'Syncs with your LinkedIn profile for complete personalization.',
    },
    {
      icon: <DownloadIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'PDF Export',
      description: 'Download your generated CVs in PDF format ready for your applications.',
    },
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box textAlign="center" mb={6}>
        <Typography
          variant="h2"
          component="h1"
          gutterBottom
          sx={{
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontWeight: 800,
            mb: 2,
          }}
        >
          🤖 AI CV Personalizer
        </Typography>
        <Typography
          variant="h5"
          color="text.secondary"
          sx={{ mb: 4, maxWidth: 600, mx: 'auto', lineHeight: 1.6 }}
        >
          Generate personalized CVs using AI to analyze your LinkedIn and GitHub profiles
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap', mb: 4 }}>
          <Chip label="Gemini 2.0 Flash" variant="outlined" color="primary" />
          <Chip label="LinkedIn Integration" variant="outlined" color="secondary" />
          <Chip label="GitHub Analysis" variant="outlined" color="primary" />
          <Chip label="PDF Export" variant="outlined" color="secondary" />
        </Box>

        <Button
          variant="contained"
          size="large"
          startIcon={<RocketIcon />}
          onClick={() => {
            console.log('Button clicked, navigating to /generator');
            navigate('/generator');
          }}
          sx={{
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
            borderRadius: 3,
            py: 1.5,
            px: 4,
            fontSize: '1.1rem',
            fontWeight: 600,
            textTransform: 'none',
            boxShadow: '0 8px 30px rgba(99, 102, 241, 0.3)',
            '&:hover': {
              boxShadow: '0 12px 40px rgba(99, 102, 241, 0.4)',
              transform: 'translateY(-2px)',
            },
            transition: 'all 0.3s ease',
          }}
        >
          Create my personalized CV
        </Button>
      </Box>

      <Grid container spacing={4} sx={{ mt: 4 }}>
        {features.map((feature, index) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={index}>
            <Card
              sx={{
                height: '100%',
                borderRadius: 3,
                border: '1px solid rgba(99, 102, 241, 0.1)',
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: '0 12px 40px rgba(0, 0, 0, 0.1)',
                  borderColor: 'primary.main',
                },
              }}
            >
              <CardContent sx={{ textAlign: 'center', py: 3 }}>
                <Box sx={{ mb: 2 }}>{feature.icon}</Box>
                <Typography variant="h6" component="h3" gutterBottom fontWeight="bold">
                  {feature.title}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                  {feature.description}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Box
        sx={{
          mt: 8,
          p: 4,
          borderRadius: 3,
          background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
          border: '1px solid rgba(99, 102, 241, 0.1)',
          textAlign: 'center',
        }}
      >
        <Typography variant="h4" gutterBottom fontWeight="bold" color="text.primary">
          How does it work?
        </Typography>
        <Grid container spacing={3} sx={{ mt: 2 }}>
          <Grid size={{ xs: 12, md: 4 }}>
            <Box sx={{ p: 2 }}>
              <Typography variant="h6" color="primary.main" fontWeight="bold" gutterBottom>
                1. Describe the position
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Paste the job description that interests you
              </Typography>
            </Box>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Box sx={{ p: 2 }}>
              <Typography variant="h6" color="primary.main" fontWeight="bold" gutterBottom>
                2. AI analyzes
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Our AI analyzes your LinkedIn and GitHub profiles
              </Typography>
            </Box>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Box sx={{ p: 2 }}>
              <Typography variant="h6" color="primary.main" fontWeight="bold" gutterBottom>
                3. Personalized CV
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Receive a CV optimized for the targeted position
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
};

export default HomePage;
