// src/pages/OfferRecommendation.jsx
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Slider,
  FormControl,
  FormControlLabel,
  Radio,
  RadioGroup,
  Divider,
  IconButton,
  Tooltip,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  MonetizationOn as OfferIcon,
  Info as InfoIcon,
  Check as CheckIcon,
  Edit as EditIcon,
  Send as SendIcon,
  SaveAlt as SaveIcon,
  ContentCopy as CopyIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';

// Import services
import { offerService } from '../services/api';

export default function OfferRecommendation() {
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [offers, setOffers] = useState([]);
  const [filteredOffers, setFilteredOffers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedOffer, setSelectedOffer] = useState(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editedOffer, setEditedOffer] = useState(null);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });

  useEffect(() => {
    const fetchOffers = async () => {
      try {
        setLoading(true);
        const offersData = await offerService.getOffers();
        setOffers(offersData);
        setFilteredOffers(offersData);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching offers:', error);
        setNotification({
          open: true,
          message: 'Error loading offers. Please try again later.',
          severity: 'error'
        });
        setLoading(false);
      }
    };

    fetchOffers();
  }, []);

  useEffect(() => {
    // Filter offers based on search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      const filtered = offers.filter(offer => 
        (offer.candidate?.name || '').toLowerCase().includes(query) ||
        (offer.role?.title || '').toLowerCase().includes(query) ||
        (offer.status || '').toLowerCase().includes(query)
      );
      setFilteredOffers(filtered);
    } else {
      setFilteredOffers(offers);
    }
  }, [offers, searchQuery]);

  const handleDetailOpen = async (offer) => {
    try {
      // Get detailed offer info from the API
      const offerDetails = await offerService.getOffer(offer._id);
      setSelectedOffer(offerDetails);
      setDetailDialogOpen(true);
    } catch (error) {
      console.error('Error fetching offer details:', error);
      setNotification({
        open: true,
        message: 'Error loading offer details. Please try again.',
        severity: 'error'
      });
    }
  };

  const handleDetailClose = () => {
    setDetailDialogOpen(false);
  };

  const handleEditOpen = (offer) => {
    setSelectedOffer(offer);
    setEditedOffer({
      ...offer.offer,
    });
    setEditDialogOpen(true);
  };

  const handleEditClose = () => {
    setEditDialogOpen(false);
  };

  const handleSaveEdit = async () => {
    try {
      // Calculate new total CTC
      const newTotalCTC = parseInt(editedOffer.base_salary) + parseInt(editedOffer.bonus || 0);
      
      // Prepare the updated offer data
      const updatedOfferData = {
        offer: {
          ...editedOffer,
          total_ctc: newTotalCTC,
        },
        status: 'Modified',
      };
      
      // Update the offer via API
      const response = await offerService.updateOffer(selectedOffer._id, updatedOfferData);
      
      // Update local state
      setOffers(offers.map(offer => 
        offer._id === response._id ? response : offer
      ));
      
      setNotification({
        open: true,
        message: 'Offer updated successfully!',
        severity: 'success'
      });
      
      setEditDialogOpen(false);
    } catch (error) {
      console.error('Error updating offer:', error);
      setNotification({
        open: true,
        message: 'Error updating offer. Please try again.',
        severity: 'error'
      });
    }
  };

  const handleApproveOffer = async (offerId) => {
    try {
      // Approve the offer via API
      const response = await offerService.approveOffer(offerId);
      
      // Update local state
      setOffers(offers.map(offer => 
        offer._id === offerId ? { ...offer, status: 'Approved' } : offer
      ));
      
      setNotification({
        open: true,
        message: 'Offer approved successfully!',
        severity: 'success'
      });
      
      // If the detail dialog is open, close it
      if (detailDialogOpen && selectedOffer?._id === offerId) {
        handleDetailClose();
      }
    } catch (error) {
      console.error('Error approving offer:', error);
      setNotification({
        open: true,
        message: 'Error approving offer. Please try again.',
        severity: 'error'
      });
    }
  };
  
  const handleGenerateOffers = async () => {
    try {
      setGenerating(true);
      
      // Call the API to generate offers for matches
      const response = await offerService.generateOffers();
      
      setNotification({
        open: true,
        message: 'Offer generation started. This may take a few minutes.',
        severity: 'success'
      });
      
      // Poll for new offers after a delay
      setTimeout(async () => {
        try {
          const updatedOffers = await offerService.getOffers();
          setOffers(updatedOffers);
          setFilteredOffers(updatedOffers);
        } catch (error) {
          console.error('Error fetching updated offers:', error);
        } finally {
          setGenerating(false);
        }
      }, 5000);
    } catch (error) {
      console.error('Error generating offers:', error);
      setNotification({
        open: true,
        message: 'Error starting offer generation. Please try again.',
        severity: 'error'
      });
      setGenerating(false);
    }
  };

  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };

  const formatCurrency = (amount) => {
    if (!amount) return '$0';
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Offer Recommendations
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
          Offer Recommendations
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" paragraph>
          Review and manage AI-generated offer recommendations for matched candidates.
        </Typography>
        
        {/* Actions Bar */}
        <Paper sx={{ p: 2, mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={generating ? <CircularProgress size={20} color="inherit" /> : <OfferIcon />}
              onClick={handleGenerateOffers}
              disabled={generating}
            >
              {generating ? 'Generating...' : 'Generate New Offers'}
            </Button>
            
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Total Recommendations: {offers.length}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Chip 
                  label={`Pending: ${offers.filter(o => o.status === 'Pending Approval').length}`} 
                  size="small" 
                  color="warning" 
                />
                <Chip 
                  label={`Approved: ${offers.filter(o => o.status === 'Approved').length}`} 
                  size="small" 
                  color="success" 
                />
                <Chip 
                  label={`Modified: ${offers.filter(o => o.status === 'Modified').length}`} 
                  size="small" 
                  color="info" 
                />
              </Box>
            </Box>
          </Box>
          
          <TextField
            size="small"
            label="Search Offers"
            variant="outlined"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            sx={{ minWidth: 250 }}
          />
        </Paper>
        
        {/* Offers Table */}
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Candidate</TableCell>
                <TableCell>Role</TableCell>
                <TableCell>Total CTC</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredOffers.length > 0 ? (
                filteredOffers.map((offer) => (
                  <TableRow key={offer._id}>
                    <TableCell>
                      <Typography variant="body1">{offer.candidate?.name || 'Unknown Candidate'}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {offer.candidate?.experience || 'Experience not specified'} | {offer.candidate?.location || 'Location not specified'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body1">{offer.role?.title || 'Unknown Role'}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {offer.role?.department || 'Department not specified'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body1" fontWeight="bold">
                        {formatCurrency(offer.offer?.total_ctc)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Base: {formatCurrency(offer.offer?.base_salary)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={offer.status} 
                        color={
                          offer.status === 'Approved' 
                            ? 'success' 
                            : offer.status === 'Modified' 
                              ? 'info' 
                              : 'warning'
                        } 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1 }}>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => handleDetailOpen(offer)}
                          >
                            <InfoIcon />
                          </IconButton>
                        </Tooltip>
                        
                        <Tooltip title="Edit Offer">
                          <IconButton
                            size="small"
                            onClick={() => handleEditOpen(offer)}
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        
                        {offer.status === 'Pending Approval' && (
                          <Tooltip title="Approve Offer">
                            <IconButton
                              size="small"
                              color="success"
                              onClick={() => handleApproveOffer(offer._id)}
                            >
                              <CheckIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                        
                        {offer.status === 'Approved' && (
                          <Tooltip title="Send Offer">
                            <IconButton
                              size="small"
                              color="primary"
                            >
                              <SendIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    <Typography variant="body1" sx={{ py: 2 }}>
                      No offers found.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        {/* Offer Details Dialog */}
        <Dialog
          open={detailDialogOpen}
          onClose={handleDetailClose}
          maxWidth="md"
          fullWidth
        >
          {selectedOffer && (
            <>
              <DialogTitle>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Typography variant="h6">
                    Offer Details: {selectedOffer.candidate?.name || 'Unknown Candidate'}
                  </Typography>
                  <Chip 
                    label={selectedOffer.status} 
                    color={
                      selectedOffer.status === 'Approved' 
                        ? 'success' 
                        : selectedOffer.status === 'Modified' 
                          ? 'info' 
                          : 'warning'
                    } 
                  />
                </Box>
              </DialogTitle>
              
              <DialogContent dividers>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Card sx={{ height: '100%' }}>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Candidate & Role Info
                        </Typography>
                        
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="subtitle2">Candidate</Typography>
                          <Typography variant="body1">{selectedOffer.candidate?.name || 'Name not specified'}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            {selectedOffer.candidate?.experience || 'Experience not specified'} | {selectedOffer.candidate?.education || 'Education not specified'}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Current CTC: {formatCurrency(selectedOffer.candidate?.current_ctc)}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Location: {selectedOffer.candidate?.location || 'Location not specified'}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Preference: {selectedOffer.candidate?.remote_preference || 'Remote preference not specified'}
                          </Typography>
                        </Box>
                        
                        <Divider sx={{ my: 2 }} />
                        
                        <Box>
                          <Typography variant="subtitle2">Role</Typography>
                          <Typography variant="body1">{selectedOffer.role?.title || 'Title not specified'}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            Department: {selectedOffer.role?.department || 'Department not specified'}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Experience Required: {selectedOffer.role?.experience_required || 'Not specified'}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Location: {selectedOffer.role?.location || 'Location not specified'}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Remote Option: {selectedOffer.role?.remote_option || 'Remote option not specified'}
                          </Typography>
                        </Box>
                        
                        <Box sx={{ mt: 2, display: 'flex', alignItems: 'center' }}>
                          <Typography variant="subtitle2" sx={{ mr: 1 }}>Match Score:</Typography>
                          <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                            <CircularProgress
                              variant="determinate"
                              value={selectedOffer.match_score}
                              color={selectedOffer.match_score >= 90 ? 'success' : 
                                     selectedOffer.match_score >= 70 ? 'primary' : 'warning'}
                              size={30}
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
                              <Typography variant="caption" component="div" fontWeight="bold">
                                {selectedOffer.match_score}%
                              </Typography>
                            </Box>
                          </Box>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Card sx={{ height: '100%' }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Typography variant="h6">
                            Offer Package
                          </Typography>
                          <Tooltip title="Edit Offer">
                            <IconButton
                              size="small"
                              onClick={() => {
                                handleDetailClose();
                                handleEditOpen(selectedOffer);
                              }}
                            >
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
                        
                        <Typography variant="h4" sx={{ mb: 2, color: 'primary.main' }}>
                          {formatCurrency(selectedOffer.offer?.total_ctc)}
                        </Typography>
                        
                        <Grid container spacing={2}>
                          <Grid item xs={6}>
                            <Typography variant="subtitle2">Base Salary</Typography>
                            <Typography variant="body1">{formatCurrency(selectedOffer.offer?.base_salary)}</Typography>
                          </Grid>
                          
                          <Grid item xs={6}>
                            <Typography variant="subtitle2">Annual Bonus</Typography>
                            <Typography variant="body1">{formatCurrency(selectedOffer.offer?.bonus)}</Typography>
                          </Grid>
                          
                          <Grid item xs={6}>
                            <Typography variant="subtitle2">Equity</Typography>
                            <Typography variant="body1">{selectedOffer.offer?.equity || 'None'}</Typography>
                          </Grid>
                          
                          <Grid item xs={6}>
                            <Typography variant="subtitle2">Start Date</Typography>
                            <Typography variant="body1">
                              {selectedOffer.offer?.start_date ? 
                                new Date(selectedOffer.offer.start_date).toLocaleDateString() : 
                                'Not specified'}
                            </Typography>
                          </Grid>
                          
                          <Grid item xs={12}>
                            <Typography variant="subtitle2">Work Arrangement</Typography>
                            <Typography variant="body1">{selectedOffer.offer?.remote || 'Not specified'}</Typography>
                          </Grid>
                          
                          <Grid item xs={12}>
                            <Typography variant="subtitle2">Benefits</Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                              {(selectedOffer.offer?.benefits || []).map((benefit, index) => (
                                <Chip key={index} label={benefit} size="small" />
                              ))}
                              {(!selectedOffer.offer?.benefits || selectedOffer.offer.benefits.length === 0) && (
                                <Typography variant="body2" color="text.secondary">No benefits specified</Typography>
                              )}
                            </Box>
                          </Grid>
                        </Grid>
                        
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>CTC Comparison</Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="body2" color="text.secondary">Current</Typography>
                            <LinearProgress 
                              variant="determinate" 
                              value={100} 
                              sx={{ 
                                flexGrow: 1, 
                                height: 8, 
                                borderRadius: 1,
                                backgroundColor: 'action.hover',
                                '& .MuiLinearProgress-bar': {
                                  backgroundColor: 'text.disabled',
                                },
                              }} 
                            />
                            <Typography variant="body2" color="text.secondary">
                              {formatCurrency(selectedOffer.candidate?.current_ctc)}
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                            <Typography variant="body2" color="primary">Offer</Typography>
                            <LinearProgress 
                              variant="determinate" 
                              value={100} 
                              color="primary"
                              sx={{ flexGrow: 1, height: 8, borderRadius: 1 }} 
                            />
                            <Typography variant="body2" color="primary">
                              {formatCurrency(selectedOffer.offer?.total_ctc)}
                            </Typography>
                          </Box>
                          {selectedOffer.candidate?.current_ctc && selectedOffer.offer?.total_ctc && (
                            <Typography variant="body2" sx={{ mt: 1, textAlign: 'right' }}>
                              {Math.round((selectedOffer.offer.total_ctc / selectedOffer.candidate.current_ctc - 1) * 100)}% Increase
                            </Typography>
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
                          {selectedOffer.explanation || 'No explanation available'}
                        </Typography>
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                          <Button
                            startIcon={<DescriptionIcon />}
                            variant="outlined"
                            size="small"
                          >
                            Generate Offer Letter
                          </Button>
                          <Typography variant="body2" color="text.secondary">
                            Generated on {new Date(selectedOffer.created_at).toLocaleString()}
                          </Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </DialogContent>
              
              <DialogActions>
                <Button onClick={handleDetailClose}>Close</Button>
                
                {selectedOffer.status === 'Pending Approval' && (
                  <Button 
                    variant="contained" 
                    color="success"
                    startIcon={<CheckIcon />}
                    onClick={() => {
                      handleApproveOffer(selectedOffer._id);
                      handleDetailClose();
                    }}
                  >
                    Approve Offer
                  </Button>
                )}
                
                {selectedOffer.status === 'Approved' && (
                  <Button 
                    variant="contained" 
                    color="primary"
                    startIcon={<SendIcon />}
                  >
                    Send Offer
                  </Button>
                )}
              </DialogActions>
            </>
          )}
        </Dialog>
        
        {/* Edit Offer Dialog */}
        <Dialog
          open={editDialogOpen}
          onClose={handleEditClose}
          maxWidth="sm"
          fullWidth
        >
          {selectedOffer && editedOffer && (
            <>
              <DialogTitle>
                Edit Offer for {selectedOffer.candidate?.name || 'Unknown Candidate'}
              </DialogTitle>
              
              <DialogContent dividers>
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="Base Salary"
                      type="number"
                      value={editedOffer.base_salary}
                      onChange={(e) => setEditedOffer({
                        ...editedOffer,
                        base_salary: e.target.value,
                      })}
                      InputProps={{
                        startAdornment: '$',
                      }}
                      fullWidth
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="Annual Bonus"
                      type="number"
                      value={editedOffer.bonus || 0}
                      onChange={(e) => setEditedOffer({
                        ...editedOffer,
                        bonus: e.target.value,
                      })}
                      InputProps={{
                        startAdornment: '$',
                      }}
                      fullWidth
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="Equity"
                      value={editedOffer.equity || ''}
                      onChange={(e) => setEditedOffer({
                        ...editedOffer,
                        equity: e.target.value,
                      })}
                      fullWidth
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="Start Date"
                      type="date"
                      value={editedOffer.start_date ? editedOffer.start_date.substring(0, 10) : ''}
                      onChange={(e) => setEditedOffer({
                        ...editedOffer,
                        start_date: e.target.value,
                      })}
                      fullWidth
                      InputLabelProps={{
                        shrink: true,
                      }}
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom>
                      Work Arrangement
                    </Typography>
                    <FormControl component="fieldset">
                      <RadioGroup
                        value={editedOffer.remote || ''}
                        onChange={(e) => setEditedOffer({
                          ...editedOffer,
                          remote: e.target.value,
                        })}
                      >
                        <FormControlLabel value="Full Remote" control={<Radio />} label="Full Remote" />
                        <FormControlLabel value="Hybrid (3 days in office)" control={<Radio />} label="Hybrid (3 days in office)" />
                        <FormControlLabel value="Hybrid (2 days in office)" control={<Radio />} label="Hybrid (2 days in office)" />
                        <FormControlLabel value="On-site" control={<Radio />} label="On-site" />
                      </RadioGroup>
                    </FormControl>
                  </Grid>
                  
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="subtitle2">
                        New Total CTC:
                      </Typography>
                      <Typography variant="h6" color="primary">
                        {formatCurrency(parseInt(editedOffer.base_salary || 0) + parseInt(editedOffer.bonus || 0))}
                      </Typography>
                    </Box>
                    {selectedOffer.candidate?.current_ctc && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        {Math.round(((parseInt(editedOffer.base_salary || 0) + parseInt(editedOffer.bonus || 0)) / selectedOffer.candidate.current_ctc - 1) * 100)}% increase from current CTC
                      </Typography>
                    )}
                  </Grid>
                </Grid>
              </DialogContent>
              
              <DialogActions>
                <Button onClick={handleEditClose}>Cancel</Button>
                <Button 
                  variant="contained" 
                  onClick={handleSaveEdit}
                  startIcon={<SaveIcon />}
                >
                  Save Changes
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