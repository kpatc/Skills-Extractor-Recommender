import { useState } from 'react';
import styled from 'styled-components';
import {
  Card,
  CardContent,
  TextField,
  Button,
  Box,
  Stepper,
  Step,
  StepLabel,
  Alert,
  CircularProgress,
  Typography,
  Divider,
  Paper,
  Chip,
  Grid,
  Tab,
  Tabs
} from '@mui/material';
import {
  GitHub as GitHubIcon,
  Upload as UploadIcon,
  ManualInput as ManualInputIcon,
  ArrowForward as ArrowForwardIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';

const FormContainer = styled(motion.div)`
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
`;

const StepCard = styled(Card)`
  margin-bottom: 20px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
`;

const InputTabs = styled(Box)`
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
`;

const TabButton = styled(Button)<{ active: boolean }>`
  flex: 1;
  padding: 12px 16px;
  background: ${props => props.active ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : '#f0f0f0'};
  color: ${props => props.active ? 'white' : '#333'};
  border-radius: 8px;
  text-transform: none;
  font-weight: 600;
  transition: all 0.3s ease;
  border: none;
  cursor: pointer;

  &:hover {
    background: ${props => props.active ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : '#e0e0e0'};
  }

  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
`;

const FileUploadBox = styled(Paper)`
  border: 2px dashed #667eea;
  border-radius: 12px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(102, 126, 234, 0.05);

  &:hover {
    border-color: #764ba2;
    background: rgba(102, 126, 234, 0.1);
  }
`;

const SkillChip = styled(Chip)`
  margin: 4px;
`;

const SuccessMessage = styled(Box)`
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #e8f5e9;
  border-radius: 8px;
  color: #2e7d32;
  margin-bottom: 16px;
`;

interface CandidateProfileFormProps {
  onProfileSubmit: (profile: CandidateProfile) => void;
  isLoading?: boolean;
}

export interface CandidateProfile {
  name: string;
  githubUsername?: string;
  linkedinUrl?: string;
  cvContent?: string;
  currentSkills: string[];
  input_method: 'github' | 'cv_upload' | 'manual';
}

type InputMethod = 'github' | 'cv_upload' | 'manual';

export const CandidateProfileForm: React.FC<CandidateProfileFormProps> = ({
  onProfileSubmit,
  isLoading = false
}) => {
  const [inputMethod, setInputMethod] = useState<InputMethod>('github');
  const [fullName, setFullName] = useState('');
  const [githubUsername, setGithubUsername] = useState('');
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [manualSkills, setManualSkills] = useState('');
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [extractedSkills, setExtractedSkills] = useState<string[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [successMessage, setSuccessMessage] = useState('');
  const [githubLoading, setGithubLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  const steps = ['Identify Yourself', 'Choose Input Method', 'Provide Data', 'Review & Submit'];

  const validateStep = (step: number): boolean => {
    setErrors([]);

    switch (step) {
      case 0:
        if (!fullName.trim()) {
          setErrors(['Please enter your full name']);
          return false;
        }
        if (fullName.length < 3) {
          setErrors(['Name must be at least 3 characters']);
          return false;
        }
        return true;

      case 1:
        return true;

      case 2:
        if (inputMethod === 'github') {
          if (!githubUsername.trim()) {
            setErrors(['Please enter your GitHub username']);
            return false;
          }
        } else if (inputMethod === 'cv_upload') {
          if (!cvFile) {
            setErrors(['Please upload a CV file']);
            return false;
          }
        } else if (inputMethod === 'manual') {
          if (!manualSkills.trim()) {
            setErrors(['Please enter at least one skill']);
            return false;
          }
        }
        return true;

      case 3:
        if (extractedSkills.length === 0) {
          setErrors(['No skills found. Please provide skills.']);
          return false;
        }
        return true;

      default:
        return true;
    }
  };

  const handleGithubAuth = async () => {
    if (!validateStep(2)) return;

    setGithubLoading(true);
    setErrors([]);
    setSuccessMessage('');

    try {
      // Appel à l'API backend pour récupérer les skills depuis GitHub
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/github-profile/${githubUsername}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          }
        }
      );

      if (!response.ok) {
        throw new Error(`GitHub user not found: ${response.statusText}`);
      }

      const data = await response.json();
      const skills = data.skills || data.extracted_skills || [];

      setExtractedSkills(Array.isArray(skills) ? skills : Object.keys(skills));
      setSuccessMessage(`✓ Found ${skills.length} skills from your GitHub repositories`);
      setCurrentStep(3);
    } catch (error) {
      setErrors([
        `Failed to fetch GitHub profile: ${error instanceof Error ? error.message : 'Unknown error'}`,
        'Make sure your GitHub username is correct and your account is public'
      ]);
      setGithubLoading(false);
    }
  };

  const handleCVUpload = async (file: File) => {
    setCvFile(file);
    setGithubLoading(true);
    setErrors([]);
    setSuccessMessage('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/extract-cv-skills`,
        {
          method: 'POST',
          body: formData
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to process CV: ${response.statusText}`);
      }

      const data = await response.json();
      const skills = data.skills || data.extracted_skills || [];

      setExtractedSkills(Array.isArray(skills) ? skills : Object.keys(skills));
      setSuccessMessage(`✓ Extracted ${skills.length} skills from your CV`);
      setCurrentStep(3);
    } catch (error) {
      setErrors([
        `Failed to process CV: ${error instanceof Error ? error.message : 'Unknown error'}`,
        'Supported formats: PDF, DOCX, TXT'
      ]);
      setCvFile(null);
    } finally {
      setGithubLoading(false);
    }
  };

  const handleManualSkills = () => {
    if (!validateStep(2)) return;

    const skills = manualSkills
      .split(/[,;\n]/)
      .map(s => s.trim())
      .filter(s => s.length > 0);

    if (skills.length === 0) {
      setErrors(['Please enter at least one skill']);
      return;
    }

    setExtractedSkills(skills);
    setSuccessMessage(`✓ Added ${skills.length} skills manually`);
    setCurrentStep(3);
  };

  const handleAddSkill = (skill: string) => {
    if (skill.trim() && !extractedSkills.includes(skill.trim())) {
      setExtractedSkills([...extractedSkills, skill.trim()]);
    }
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    setExtractedSkills(extractedSkills.filter(s => s !== skillToRemove));
  };

  const handleSubmit = () => {
    if (!validateStep(3)) return;

    const profile: CandidateProfile = {
      name: fullName,
      githubUsername: inputMethod === 'github' ? githubUsername : undefined,
      linkedinUrl,
      cvContent: inputMethod === 'cv_upload' ? cvFile?.name : undefined,
      currentSkills: extractedSkills,
      input_method: inputMethod
    };

    onProfileSubmit(profile);
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    setCurrentStep(Math.max(0, currentStep - 1));
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <StepCard>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Tell us about yourself
              </Typography>
              <TextField
                fullWidth
                label="Full Name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="John Doe"
                variant="outlined"
                margin="normal"
                sx={{ marginTop: 2 }}
              />
              <TextField
                fullWidth
                label="LinkedIn Profile (Optional)"
                value={linkedinUrl}
                onChange={(e) => setLinkedinUrl(e.target.value)}
                placeholder="https://linkedin.com/in/your-profile"
                variant="outlined"
                margin="normal"
              />
              <Typography variant="caption" color="textSecondary" sx={{ marginTop: 1, display: 'block' }}>
                We'll use this to enrich your profile with additional context
              </Typography>
            </CardContent>
          </StepCard>
        );

      case 1:
        return (
          <StepCard>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                How would you like to provide your skills?
              </Typography>
              <InputTabs>
                <TabButton
                  active={inputMethod === 'github'}
                  onClick={() => setInputMethod('github')}
                  startIcon={<GitHubIcon />}
                >
                  GitHub
                </TabButton>
                <TabButton
                  active={inputMethod === 'cv_upload'}
                  onClick={() => setInputMethod('cv_upload')}
                  startIcon={<UploadIcon />}
                >
                  Upload CV
                </TabButton>
                <TabButton
                  active={inputMethod === 'manual'}
                  onClick={() => setInputMethod('manual')}
                  startIcon={<ManualInputIcon />}
                >
                  Manual Input
                </TabButton>
              </InputTabs>
              <Typography variant="body2" color="textSecondary">
                {inputMethod === 'github' && 'We\'ll analyze your GitHub repositories to extract your technical skills.'}
                {inputMethod === 'cv_upload' && 'Upload your CV to automatically extract skills and experience.'}
                {inputMethod === 'manual' && 'Manually enter your skills one by one.'}
              </Typography>
            </CardContent>
          </StepCard>
        );

      case 2:
        return (
          <StepCard>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {inputMethod === 'github' && 'Connect your GitHub Account'}
                {inputMethod === 'cv_upload' && 'Upload Your CV'}
                {inputMethod === 'manual' && 'Enter Your Skills'}
              </Typography>

              {inputMethod === 'github' && (
                <Box sx={{ marginTop: 2 }}>
                  <TextField
                    fullWidth
                    label="GitHub Username"
                    value={githubUsername}
                    onChange={(e) => setGithubUsername(e.target.value)}
                    placeholder="octocat"
                    variant="outlined"
                    disabled={githubLoading}
                  />
                  <Typography variant="caption" color="textSecondary" sx={{ marginTop: 1, display: 'block' }}>
                    We'll analyze your public repositories to extract skills
                  </Typography>
                  <Button
                    fullWidth
                    variant="contained"
                    startIcon={githubLoading ? <CircularProgress size={20} /> : <GitHubIcon />}
                    onClick={handleGithubAuth}
                    disabled={githubLoading || !githubUsername.trim()}
                    sx={{ marginTop: 2 }}
                  >
                    {githubLoading ? 'Fetching Skills...' : 'Fetch from GitHub'}
                  </Button>
                </Box>
              )}

              {inputMethod === 'cv_upload' && (
                <Box sx={{ marginTop: 2 }}>
                  <FileUploadBox
                    component="label"
                    onDrop={(e) => {
                      e.preventDefault();
                      const file = e.dataTransfer.files[0];
                      if (file) handleCVUpload(file);
                    }}
                    onDragOver={(e) => e.preventDefault()}
                  >
                    <input
                      hidden
                      accept=".pdf,.docx,.doc,.txt"
                      type="file"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) handleCVUpload(file);
                      }}
                    />
                    <UploadIcon sx={{ fontSize: 48, color: '#667eea', marginBottom: 1 }} />
                    <Typography variant="h6">
                      Drop your CV here or click to upload
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      Supported: PDF, DOCX, TXT (Max 10MB)
                    </Typography>
                  </FileUploadBox>
                </Box>
              )}

              {inputMethod === 'manual' && (
                <Box sx={{ marginTop: 2 }}>
                  <TextField
                    fullWidth
                    label="Your Skills"
                    value={manualSkills}
                    onChange={(e) => setManualSkills(e.target.value)}
                    placeholder="React, TypeScript, Node.js, MongoDB"
                    variant="outlined"
                    multiline
                    rows={4}
                    helperText="Separate skills with commas, semicolons, or new lines"
                  />
                  <Button
                    fullWidth
                    variant="contained"
                    onClick={handleManualSkills}
                    sx={{ marginTop: 2 }}
                  >
                    Add Skills
                  </Button>
                </Box>
              )}
            </CardContent>
          </StepCard>
        );

      case 3:
        return (
          <StepCard>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Review Your Skills
              </Typography>
              {successMessage && (
                <SuccessMessage>
                  <CheckCircleIcon />
                  <Typography variant="body2">{successMessage}</Typography>
                </SuccessMessage>
              )}
              <Typography variant="body2" color="textSecondary" sx={{ marginBottom: 2 }}>
                We found {extractedSkills.length} skills. You can add or remove skills below:
              </Typography>
              <Box sx={{ marginBottom: 2 }}>
                {extractedSkills.map((skill) => (
                  <SkillChip
                    key={skill}
                    label={skill}
                    onDelete={() => handleRemoveSkill(skill)}
                    color="primary"
                    variant="outlined"
                  />
                ))}
              </Box>
              <TextField
                fullWidth
                label="Add more skills"
                placeholder="Type skill name and press Enter"
                variant="outlined"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    const input = e.currentTarget.value.trim();
                    if (input) {
                      handleAddSkill(input);
                      e.currentTarget.value = '';
                    }
                  }
                }}
              />
            </CardContent>
          </StepCard>
        );

      default:
        return null;
    }
  };

  return (
    <FormContainer
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Stepper activeStep={currentStep} sx={{ marginBottom: 3 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {errors.length > 0 && (
        <Alert severity="error" sx={{ marginBottom: 2 }}>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {errors.map((error, idx) => (
              <li key={idx}>{error}</li>
            ))}
          </ul>
        </Alert>
      )}

      {renderStepContent()}

      <Box sx={{ display: 'flex', gap: 2, marginTop: 3, justifyContent: 'space-between' }}>
        <Button
          disabled={currentStep === 0 || isLoading}
          onClick={handleBack}
          variant="outlined"
        >
          Back
        </Button>
        <Box sx={{ display: 'flex', gap: 2 }}>
          {currentStep < steps.length - 1 ? (
            <Button
              variant="contained"
              onClick={handleNext}
              endIcon={<ArrowForwardIcon />}
              disabled={isLoading}
            >
              Next
            </Button>
          ) : (
            <Button
              variant="contained"
              color="success"
              onClick={handleSubmit}
              disabled={isLoading}
              startIcon={isLoading ? <CircularProgress size={20} /> : <CheckCircleIcon />}
            >
              {isLoading ? 'Processing...' : 'Analyze My Profile'}
            </Button>
          )}
        </Box>
      </Box>
    </FormContainer>
  );
};
