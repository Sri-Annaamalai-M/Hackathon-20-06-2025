// src/pages/CandidateUpload.jsx
import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Grid,
  LinearProgress,
  Paper,
  Typography,
  Chip,
  Alert,
  Snackbar,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import DescriptionIcon from '@mui/icons-material/Description';

// Import candidate service
import { candidateService } from '../services/api';

export default function CandidateUpload() {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });

  const onDrop = useCallback((acceptedFiles) => {
    // Only accept PDF and DOCX files
    const filteredFiles = acceptedFiles.filter(
      file => file.type === 'application/pdf' || 
              file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    );
    
    if (filteredFiles.length < acceptedFiles.length) {
      setNotification({
        open: true,
        message: 'Some files were rejected. Only PDF and DOCX files are accepted.',
        severity: 'warning'
      });
    }
    
    setFiles(prevFiles => [...prevFiles, ...filteredFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    }
  });

  const handleUpload = async () => {
    if (files.length === 0) {
      setNotification({
        open: true,
        message: 'Please select files to upload',
        severity: 'error'
      });
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    
    // Create a simulated progress interval for better UX
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return prev;
        }
        return prev + 10;
      });
    }, 500);

    try {
      // Use the candidateService to upload files
      const response = await candidateService.uploadCandidateFiles(files);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      setNotification({
        open: true,
        message: `Successfully uploaded ${files.length} files! The AI is now processing your candidates.`,
        severity: 'success'
      });
      
      setFiles([]);
    } catch (error) {
      clearInterval(progressInterval);
      console.error('Upload error:', error);
      
      setNotification({
        open: true,
        message: error.response?.data?.detail || 'Error uploading files. Please try again.',
        severity: 'error'
      });
    } finally {
      setTimeout(() => {
        setUploading(false);
      }, 1000); // Small delay to show 100% progress
    }
  };

  const handleRemoveFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Upload Candidate Profiles
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" paragraph>
          Upload resumes and interview notes to begin the AI analysis process.
          Supported formats: PDF, DOCX
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Paper
              {...getRootProps()}
              sx={{
                p: 3,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
                border: '2px dashed',
                borderColor: isDragActive ? 'primary.main' : 'divider',
                borderRadius: 2,
                minHeight: 200,
                cursor: 'pointer',
              }}
            >
              <input {...getInputProps()} />
              <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" align="center">
                {isDragActive
                  ? 'Drop the files here'
                  : 'Drag & drop candidate files here, or click to select files'}
              </Typography>
              <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 1 }}>
                PDF and DOCX files only
              </Typography>
            </Paper>
          </Grid>

          {files.length > 0 && (
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Selected Files ({files.length})
              </Typography>
              <Box sx={{ mb: 2 }}>
                {files.map((file, index) => (
                  <Card key={index} sx={{ mb: 1 }}>
                    <CardContent sx={{ py: 1, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {file.type === 'application/pdf' ? (
                          <PictureAsPdfIcon color="error" sx={{ mr: 1 }} />
                        ) : (
                          <DescriptionIcon color="primary" sx={{ mr: 1 }} />
                        )}
                        <Typography variant="body2">{file.name}</Typography>
                      </Box>
                      <Button 
                        size="small" 
                        color="error" 
                        onClick={() => handleRemoveFile(index)}
                        disabled={uploading}
                      >
                        Remove
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </Box>
              <Button
                variant="contained"
                color="primary"
                startIcon={<CloudUploadIcon />}
                onClick={handleUpload}
                disabled={uploading}
                fullWidth
              >
                {uploading ? 'Uploading...' : 'Upload Files'}
              </Button>
              {uploading && (
                <Box sx={{ mt: 2 }}>
                  <LinearProgress variant="determinate" value={uploadProgress} />
                  <Typography variant="body2" align="center" sx={{ mt: 1 }}>
                    {uploadProgress}% Uploaded
                  </Typography>
                </Box>
              )}
            </Grid>
          )}

          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  How It Works
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                  <Chip label="1. Upload files" color="primary" />
                  <Chip label="2. AI parses content" />
                  <Chip label="3. Structured profiles created" />
                  <Chip label="4. Ready for role matching" color="success" />
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Our AI agent will process your uploaded files to extract key information such as skills, 
                  experience, education, and certifications. The structured profiles will then be used for
                  role matching and offer recommendations.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      <Snackbar 
        open={notification.open} 
        autoHideDuration={6000} 
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseNotification} severity={notification.severity}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}