// src/pages/RoleMatching.jsx
import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Grid,
  Typography,
  LinearProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  TextField,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

// Import services
import { matchService, roleService, offerService } from '../services/api';

export default function RoleMatching() {
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [matches, setMatches] = useState([]);
  const [filteredMatches, setFilteredMatches] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRole, setFilterRole] = useState('');
  const [filterMatchScore, setFilterMatchScore] = useState('');
  const [roles, setRoles] = useState([]);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch matches and roles in parallel
        const [matchesData, rolesData] = await Promise.all([
          matchService.getMatches(),
          roleService.getRoles()
        ]);
        
        setMatches(matchesData);
        setFilteredMatches(matchesData);
        setRoles(rolesData);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setNotification({
          open: true,
          message: 'Error loading matches. Please try again later.',
          severity: 'error'
        });
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  useEffect(() => {
    // Filter matches based on search and filters
    let filtered = [...matches];
    
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(match => 
        match.candidate_name?.toLowerCase().includes(query) ||
        match.role_title?.toLowerCase().includes(query)
      );
    }
    
    if (filterRole) {
      filtered = filtered.filter(match => match.role_id === filterRole);
    }
    
    if (filterMatchScore) {
      switch (filterMatchScore) {
        case 'excellent':
          filtered = filtered.filter(match => match.match_score >= 90);
          break;
        case 'good':
          filtered = filtered.filter(match => match.match_score >= 70 && match.match_score < 90);
          break;
        case 'fair':
          filtered = filtered.filter(match => match.match_score >= 50 && match.match_score < 70);
          break;
        case 'poor':
          filtered = filtered.filter(match => match.match_score < 50);
          break;
        default:
          break;
      }
    }
    
    setFilteredMatches(filtered);
  }, [matches, searchQuery, filterRole, filterMatchScore]);

  const handleDetailOpen = async (match) => {
    try {
      // Get detailed match info from the API
      const matchDetails = await matchService.getMatch(match._id);
      setSelectedMatch(matchDetails);
      setDetailDialogOpen(true);
    } catch (error) {
      console.error('Error fetching match details:', error);
      setNotification({
        open: true,
        message: 'Error loading match details. Please try again.',
        severity: 'error'
      });
    }
  };

  const handleDetailClose = () => {
    setDetailDialogOpen(false);
  };

  const runMatchingProcess = async () => {
    try {
      setProcessing(true);
      
      // Call the API to run the matching process
      const response = await matchService.processMatches();
      
      setNotification({
        open: true,
        message: 'Matching process started successfully. This may take a few minutes.',
        severity: 'success'
      });
      
      // Poll for new matches after a delay
      setTimeout(async () => {
        try {
          const updatedMatches = await matchService.getMatches();
          setMatches(updatedMatches);
        } catch (error) {
          console.error('Error fetching updated matches:', error);
        } finally {
          setProcessing(false);
        }
      }, 5000);
    } catch (error) {
      console.error('Error running matching process:', error);
      setNotification({
        open: true,
        message: 'Error starting the matching process. Please try again.',
        severity: 'error'
      });
      setProcessing(false);
    }
  };

  const generateOffer = async (matchId) => {
    try {
      // Call the API to generate an offer for this match
      const response = await offerService.generateOffers([matchId]);
      
      setNotification({
        open: true,
        message: 'Offer generation started. You can view it in the Offers tab when ready.',
        severity: 'success'
      });
      
      handleDetailClose();
    } catch (error) {
      console.error('Error generating offer:', error);
      setNotification({
        open: true,
        message: 'Error generating offer. Please try again.',
        severity: 'error'
      });
    }
  };

  const getMatchScoreColor = (score) => {
    if (score >= 90) return 'success';
    if (score >= 70) return 'primary';
    if (score >= 50) return 'warning';
    return 'error';
  };
  
  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Role Matching
          </Typography>
          <LinearProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Role Matching
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" paragraph>
          View and manage AI-generated role matches for your candidates.
        </Typography>
        
        {/* Actions Bar */}
        <Paper sx={{ p: 2, mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Button
            variant="contained"
            color="primary"
            onClick={runMatchingProcess}
            disabled={processing}
            startIcon={processing ? <CircularProgress size={20} color="inherit" /> : null}
          >
            {processing ? 'Processing...' : 'Run Matching Process'}
          </Button>
          
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <TextField
              size="small"
              label="Search"
              variant="outlined"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
            
            <TextField
              select
              size="small"
              label="Role"
              variant="outlined"
              value={filterRole}
              onChange={(e) => setFilterRole(e.target.value)}
              sx={{ minWidth: 200 }}
            >
              <MenuItem value="">All Roles</MenuItem>
              {roles.map((role) => (
                <MenuItem key={role._id} value={role._id}>
                  {role.title}
                </MenuItem>
              ))}
            </TextField>
            
            <TextField
              select
              size="small"
              label="Match Score"
              variant="outlined"
              value={filterMatchScore}
              onChange={(e) => setFilterMatchScore(e.target.value)}
              sx={{ minWidth: 150 }}
            >
              <MenuItem value="">All Scores</MenuItem>
              <MenuItem value="excellent">Excellent (90%+)</MenuItem>
              <MenuItem value="good">Good (70-89%)</MenuItem>
              <MenuItem value="fair">Fair (50-69%)</MenuItem>
              <MenuItem value="poor">Poor (0-50%)</MenuItem>
            </TextField>
          </Box>
        </Paper>
        
        {/* Matches Table */}
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Candidate</TableCell>
                <TableCell>Role</TableCell>
                <TableCell align="center">Match Score</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredMatches.length > 0 ? (
                filteredMatches.map((match) => (
                  <TableRow key={match._id}>
                    <TableCell>
                      <Typography variant="body1">{match.candidate?.name || 'Unknown Candidate'}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {match.candidate?.experience || 'Experience not specified'} | {match.candidate?.education || 'Education not specified'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body1">{match.role?.title || 'Unknown Role'}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {match.role?.department || 'Department not specified'}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                        <Box 
                          sx={{ 
                            position: 'relative', 
                            display: 'inline-flex',
                            mb: 1
                          }}
                        >
                          <CircularProgress
                            variant="determinate"
                            value={match.match_score}
                            color={getMatchScoreColor(match.match_score)}
                            size={40}
                          />
                          <Box
                            sx={{
                              top: 0,
                              left: 0,
                              bottom: 0,
                              right: 0,
                              position: 'absolute',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                            }}
                          >
                            <Typography
                              variant="caption"
                              component="div"
                              fontWeight="bold"
                            >
                              {match.match_score}%
                            </Typography>
                          </Box>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={match.status} 
                        color={match.status === 'Matched' ? 'success' : 'warning'} 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<InfoIcon />}
                        onClick={() => handleDetailOpen(match)}
                      >
                        Details
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    <Typography variant="body1" sx={{ py: 2 }}>
                      No matches found.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        {/* Match Detail Dialog */}
        <Dialog
          open={detailDialogOpen}
          onClose={handleDetailClose}
          maxWidth="md"
          fullWidth
        >
          {selectedMatch && (
            <>
              <DialogTitle>
                Match Details: {selectedMatch.candidate?.name || 'Unknown Candidate'} → {selectedMatch.role?.title || 'Unknown Role'}
              </DialogTitle>
              <DialogContent dividers>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Card sx={{ height: '100%' }}>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Candidate Profile
                        </Typography>
                        <Typography variant="body1">
                          <strong>Name:</strong> {selectedMatch.candidate?.name || 'Not specified'}
                        </Typography>
                        <Typography variant="body1">
                          <strong>Email:</strong> {selectedMatch.candidate?.email || 'Not specified'}
                        </Typography>
                        <Typography variant="body1">
                          <strong>Experience:</strong> {selectedMatch.candidate?.experience || 'Not specified'}
                        </Typography>
                        <Typography variant="body1">
                          <strong>Education:</strong> {selectedMatch.candidate?.education || 'Not specified'}
                        </Typography>
                        <Typography variant="body1" sx={{ mt: 2, mb: 1 }}>
                          <strong>Skills:</strong>
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                          {(selectedMatch.candidate?.skills || []).map((skill, index) => (
                            <Chip
                              key={index}
                              label={skill}
                              size="small"
                              color={selectedMatch.skill_match.matched.includes(skill) ? 'primary' : 'default'}
                            />
                          ))}
                          {(!selectedMatch.candidate?.skills || selectedMatch.candidate.skills.length === 0) && (
                            <Typography variant="body2" color="text.secondary">No skills specified</Typography>
                          )}
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Card sx={{ height: '100%' }}>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Role Requirements
                        </Typography>
                        <Typography variant="body1">
                          <strong>Title:</strong> {selectedMatch.role?.title || 'Not specified'}
                        </Typography>
                        <Typography variant="body1">
                          <strong>Department:</strong> {selectedMatch.role?.department || 'Not specified'}
                        </Typography>
                        <Typography variant="body1">
                          <strong>Experience Required:</strong> {selectedMatch.role?.experience_required || 'Not specified'}
                        </Typography>
                        
                        <Typography variant="body1" sx={{ mt: 2, mb: 1 }}>
                          <strong>Required Skills:</strong>
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                          {(selectedMatch.role?.required_skills || []).map((skill, index) => (
                            <Chip
                              key={index}
                              label={skill}
                              size="small"
                              color={selectedMatch.skill_match.matched.includes(skill) ? 'success' : 'error'}
                              icon={selectedMatch.skill_match.matched.includes(skill) ? <CheckIcon /> : <CloseIcon />}
                            />
                          ))}
                          {(!selectedMatch.role?.required_skills || selectedMatch.role.required_skills.length === 0) && (
                            <Typography variant="body2" color="text.secondary">No required skills specified</Typography>
                          )}
                        </Box>
                        
                        <Typography variant="body1" sx={{ mt: 2, mb: 1 }}>
                          <strong>Preferred Skills:</strong>
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                          {(selectedMatch.role?.preferred_skills || []).map((skill, index) => (
                            <Chip
                              key={index}
                              label={skill}
                              size="small"
                              variant="outlined"
                              color={selectedMatch.skill_match.matched.includes(skill) ? 'success' : 'default'}
                              icon={selectedMatch.skill_match.matched.includes(skill) ? <CheckIcon /> : null}
                            />
                          ))}
                          {(!selectedMatch.role?.preferred_skills || selectedMatch.role.preferred_skills.length === 0) && (
                            <Typography variant="body2" color="text.secondary">No preferred skills specified</Typography>
                          )}
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          AI Explanation
                        </Typography>
                        <Typography variant="body1" paragraph>
                          {selectedMatch.explanation || 'No explanation available'}
                        </Typography>
                        
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 2 }}>
                          <Chip 
                            label={`Match Score: ${selectedMatch.match_score}%`} 
                            color={getMatchScoreColor(selectedMatch.match_score)} 
                          />
                          <Typography variant="body2" color="text.secondary">
                            Generated on {new Date(selectedMatch.created_at).toLocaleString()}
                          </Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </DialogContent>
              <DialogActions>
                <Button onClick={handleDetailClose}>Close</Button>
                <Button 
                  variant="contained" 
                  color="primary"
                  onClick={() => generateOffer(selectedMatch._id)}
                >
                  Generate Offer
                </Button>
              </DialogActions>
            </>
          )}
        </Dialog>
        
        {/* Notification Snackbar */}
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
      </Box>
    </Container>
  );
}