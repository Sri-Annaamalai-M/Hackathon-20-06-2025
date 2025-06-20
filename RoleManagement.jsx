// src/pages/RoleManagement.jsx
import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Container,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  LinearProgress,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Check as CheckIcon,
  Close as CloseIcon,
} from '@mui/icons-material';

// Import services and context
import { roleService } from '../services/api';
import { useAppContext } from '../context/AppContext';

export default function RoleManagement() {
  const { roles, refreshRoles } = useAppContext();
  
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState('add'); // 'add' or 'edit'
  const [selectedRole, setSelectedRole] = useState(null);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });
  
  // Form state
  const [formData, setFormData] = useState({
    title: '',
    department: '',
    description: '',
    required_skills: '',
    preferred_skills: '',
    experience_required: '',
    education_required: '',
    location: '',
    remote_option: '',
    salary_range: { min: 0, max: 0 }
  });

  // Handle opening the dialog for adding a new role
  const handleAddRole = () => {
    setDialogMode('add');
    setFormData({
      title: '',
      department: '',
      description: '',
      required_skills: '',
      preferred_skills: '',
      experience_required: '',
      education_required: '',
      location: '',
      remote_option: '',
      salary_range: { min: 0, max: 0 }
    });
    setDialogOpen(true);
  };

  // Handle opening the dialog for editing an existing role
  const handleEditRole = (role) => {
    setDialogMode('edit');
    setSelectedRole(role);
    
    // Convert arrays to comma-separated strings for the form
    setFormData({
      title: role.title || '',
      department: role.department || '',
      description: role.description || '',
      required_skills: (role.required_skills || []).join(', '),
      preferred_skills: (role.preferred_skills || []).join(', '),
      experience_required: role.experience_required || '',
      education_required: role.education_required || '',
      location: role.location || '',
      remote_option: role.remote_option || '',
      salary_range: role.salary_range || { min: 0, max: 0 }
    });
    
    setDialogOpen(true);
  };

  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    if (name === 'salary_min' || name === 'salary_max') {
      setFormData({
        ...formData,
        salary_range: {
          ...formData.salary_range,
          [name === 'salary_min' ? 'min' : 'max']: parseInt(value) || 0
        }
      });
    } else {
      setFormData({
        ...formData,
        [name]: value
      });
    }
  };

  // Handle form submission
  const handleSubmit = async () => {
    try {
      setLoading(true);
      
      // Convert comma-separated strings to arrays
      const roleData = {
        title: formData.title,
        department: formData.department,
        description: formData.description,
        required_skills: formData.required_skills.split(',').map(skill => skill.trim()).filter(Boolean),
        preferred_skills: formData.preferred_skills.split(',').map(skill => skill.trim()).filter(Boolean),
        experience_required: formData.experience_required,
        education_required: formData.education_required,
        location: formData.location,
        remote_option: formData.remote_option,
        salary_range: formData.salary_range
      };
      
      if (dialogMode === 'add') {
        // Create new role
        await roleService.createRole(roleData);
        setNotification({
          open: true,
          message: 'Role created successfully!',
          severity: 'success'
        });
      } else {
        // Update existing role
        await roleService.updateRole(selectedRole._id, roleData);
        setNotification({
          open: true,
          message: 'Role updated successfully!',
          severity: 'success'
        });
      }
      
      // Refresh roles list
      await refreshRoles();
      
      // Close dialog
      setDialogOpen(false);
    } catch (error) {
      console.error('Error saving role:', error);
      setNotification({
        open: true,
        message: `Error ${dialogMode === 'add' ? 'creating' : 'updating'} role. Please try again.`,
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  // Handle role deletion (soft delete)
  const handleDeleteRole = async (roleId) => {
    try {
      setLoading(true);
      
      // Call API to soft delete the role
      await roleService.deleteRole(roleId);
      
      // Refresh roles list
      await refreshRoles();
      
      setNotification({
        open: true,
        message: 'Role deactivated successfully!',
        severity: 'success'
      });
    } catch (error) {
      console.error('Error deleting role:', error);
      setNotification({
        open: true,
        message: 'Error deactivating role. Please try again.',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Role Management
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" paragraph>
          Manage job roles for AI matching with candidates
        </Typography>
        
        {/* Actions Bar */}
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 3 }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            onClick={handleAddRole}
          >
            Add New Role
          </Button>
        </Box>
        
        {/* Roles Table */}
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Title</TableCell>
                <TableCell>Department</TableCell>
                <TableCell>Skills</TableCell>
                <TableCell>Experience</TableCell>
                <TableCell>Location</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {roles.length > 0 ? (
                roles.map((role) => (
                  <TableRow key={role._id}>
                    <TableCell>
                      <Typography variant="body1">{role.title}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{role.department}</Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {(role.required_skills || []).slice(0, 3).map((skill, index) => (
                          <Chip
                            key={index}
                            label={skill}
                            size="small"
                            color="primary"
                          />
                        ))}
                        {role.required_skills?.length > 3 && (
                          <Chip
                            label={`+${role.required_skills.length - 3}`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{role.experience_required || 'Not specified'}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{role.location || 'Not specified'}</Typography>
                      {role.remote_option && (
                        <Chip 
                          label={role.remote_option} 
                          size="small" 
                          variant="outlined"
                          sx={{ mt: 0.5 }}
                        />
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={role.is_active ? 'Active' : 'Inactive'} 
                        color={role.is_active ? 'success' : 'default'} 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1 }}>
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleEditRole(role)}
                        >
                          <EditIcon />
                        </IconButton>
                        {role.is_active && (
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDeleteRole(role._id)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography variant="body1" sx={{ py: 2 }}>
                      No roles found. Add your first role to get started.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        {/* Role Dialog */}
        <Dialog
          open={dialogOpen}
          onClose={() => setDialogOpen(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            {dialogMode === 'add' ? 'Add New Role' : 'Edit Role'}
          </DialogTitle>
          
          <DialogContent dividers>
            {loading && <LinearProgress sx={{ mb: 2 }} />}
            
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Title"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  fullWidth
                  required
                  margin="normal"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Department"
                  name="department"
                  value={formData.department}
                  onChange={handleInputChange}
                  fullWidth
                  required
                  margin="normal"
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  label="Description"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  fullWidth
                  multiline
                  rows={3}
                  margin="normal"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Required Skills (comma-separated)"
                  name="required_skills"
                  value={formData.required_skills}
                  onChange={handleInputChange}
                  fullWidth
                  required
                  margin="normal"
                  helperText="E.g. React, Node.js, MongoDB"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Preferred Skills (comma-separated)"
                  name="preferred_skills"
                  value={formData.preferred_skills}
                  onChange={handleInputChange}
                  fullWidth
                  margin="normal"
                  helperText="E.g. TypeScript, Docker, AWS"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Experience Required"
                  name="experience_required"
                  value={formData.experience_required}
                  onChange={handleInputChange}
                  fullWidth
                  margin="normal"
                  helperText="E.g. 3+ years"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Education Required"
                  name="education_required"
                  value={formData.education_required}
                  onChange={handleInputChange}
                  fullWidth
                  margin="normal"
                  helperText="E.g. Bachelor's in Computer Science"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Location"
                  name="location"
                  value={formData.location}
                  onChange={handleInputChange}
                  fullWidth
                  margin="normal"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Remote Option"
                  name="remote_option"
                  value={formData.remote_option}
                  onChange={handleInputChange}
                  fullWidth
                  margin="normal"
                  helperText="E.g. Remote, Hybrid, On-site only"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Minimum Salary"
                  name="salary_min"
                  type="number"
                  value={formData.salary_range.min}
                  onChange={handleInputChange}
                  fullWidth
                  margin="normal"
                  InputProps={{
                    startAdornment: '$',
                  }}
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Maximum Salary"
                  name="salary_max"
                  type="number"
                  value={formData.salary_range.max}
                  onChange={handleInputChange}
                  fullWidth
                  margin="normal"
                  InputProps={{
                    startAdornment: '$',
                  }}
                />
              </Grid>
            </Grid>
          </DialogContent>
          
          <DialogActions>
            <Button 
              onClick={() => setDialogOpen(false)} 
              disabled={loading}
              startIcon={<CloseIcon />}
            >
              Cancel
            </Button>
            <Button 
              variant="contained" 
              color="primary" 
              onClick={handleSubmit}
              disabled={loading}
              startIcon={<CheckIcon />}
            >
              {dialogMode === 'add' ? 'Create Role' : 'Update Role'}
            </Button>
          </DialogActions>
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