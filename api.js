// src/services/api.js - Alternative configuration

import axios from 'axios';

// Environment-based API URL
const API_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.DEV ? 'http://localhost:8000/api' : '/api');

// Create axios instance with interceptors for better error handling
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // Increased timeout for file uploads
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log the error for debugging
    console.error('API Error:', error);
    
    // Create a more user-friendly error message
    let errorMessage = 'An unexpected error occurred';
    
    if (error.response) {
      // The request was made and the server responded with a status code
      const status = error.response.status;
      const detail = error.response.data?.detail || '';
      
      switch (status) {
        case 400:
          errorMessage = `Bad Request: ${detail}`;
          break;
        case 401:
          errorMessage = 'Unauthorized: Please log in again';
          break;
        case 403:
          errorMessage = 'Forbidden: You do not have permission';
          break;
        case 404:
          errorMessage = `Not Found: ${detail || 'The requested resource was not found'}`;
          break;
        case 500:
          errorMessage = `Server Error: ${detail || 'Internal server error'}`;
          break;
        default:
          errorMessage = `Error ${status}: ${detail || 'Something went wrong'}`;
      }
    } else if (error.request) {
      // The request was made but no response was received
      if (error.code === 'ECONNABORTED') {
        errorMessage = 'Request timed out. Please try again.';
      } else if (error.code === 'ERR_NETWORK') {
        errorMessage = 'Network error. Please check if the backend server is running on http://localhost:8000';
      } else {
        errorMessage = 'Network error. Please check your connection.';
      }
    }
    
    // Attach the user-friendly message to the error
    error.userMessage = errorMessage;
    
    return Promise.reject(error);
  }
);

// Candidate services
export const candidateService = {
  // Get all candidates
  getCandidates: async () => {
    try {
      const response = await apiClient.get('/candidates/');
      return response.data;
    } catch (error) {
      console.error('Error fetching candidates:', error);
      throw error;
    }
  },
  
  // Upload candidate files
  uploadCandidateFiles: async (files) => {
    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });
      
      const response = await apiClient.post('/candidates/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 60000 // 1 minute timeout for file uploads
      });
      return response.data;
    } catch (error) {
      console.error('Error uploading candidate files:', error);
      throw error;
    }
  },
  
  // Get candidate by ID
  getCandidate: async (id) => {
    try {
      const response = await apiClient.get(`/candidates/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching candidate ${id}:`, error);
      throw error;
    }
  }
};

// Role services
export const roleService = {
  // Get all roles
  getRoles: async (activeOnly = true) => {
    try {
      const response = await apiClient.get('/roles/', { 
        params: { active_only: activeOnly } 
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching roles:', error);
      throw error;
    }
  },
  
  // Get role by ID
  getRole: async (id) => {
    try {
      const response = await apiClient.get(`/roles/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching role ${id}:`, error);
      throw error;
    }
  },
  
  // Create a new role
  createRole: async (roleData) => {
    try {
      const response = await apiClient.post('/roles/', roleData);
      return response.data;
    } catch (error) {
      console.error('Error creating role:', error);
      throw error;
    }
  },
  
  // Update a role
  updateRole: async (id, roleData) => {
    try {
      const response = await apiClient.put(`/roles/${id}`, roleData);
      return response.data;
    } catch (error) {
      console.error(`Error updating role ${id}:`, error);
      throw error;
    }
  },
  
  // Delete a role (soft delete)
  deleteRole: async (id) => {
    try {
      const response = await apiClient.delete(`/roles/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error deleting role ${id}:`, error);
      throw error;
    }
  }
};

// Match services
export const matchService = {
  // Get all matches with optional filters
  getMatches: async (filters = {}) => {
    try {
      const response = await apiClient.get('/matches/', { params: filters });
      return response.data;
    } catch (error) {
      console.error('Error fetching matches:', error);
      throw error;
    }
  },
  
  // Get match by ID
  getMatch: async (id) => {
    try {
      const response = await apiClient.get(`/matches/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching match ${id}:`, error);
      throw error;
    }
  },
  
  // Run matching process
  processMatches: async (candidateIds = [], roleIds = []) => {
    try {
      // Convert array parameters to query string
      let params = new URLSearchParams();
      candidateIds.forEach(id => params.append('candidate_ids', id));
      roleIds.forEach(id => params.append('role_ids', id));
      
      const response = await apiClient.post(`/matches/process?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Error processing matches:', error);
      throw error;
    }
  },
  
  // Regenerate explanation for a match
  regenerateExplanation: async (id) => {
    try {
      const response = await apiClient.post(`/matches/${id}/regenerate-explanation`);
      return response.data;
    } catch (error) {
      console.error(`Error regenerating explanation for match ${id}:`, error);
      throw error;
    }
  }
};

// Offer services
export const offerService = {
  // Get all offers with optional filters
  getOffers: async (filters = {}) => {
    try {
      const response = await apiClient.get('/offers/', { params: filters });
      return response.data;
    } catch (error) {
      console.error('Error fetching offers:', error);
      throw error;
    }
  },
  
  // Get offer by ID
  getOffer: async (id) => {
    try {
      const response = await apiClient.get(`/offers/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching offer ${id}:`, error);
      throw error;
    }
  },
  
  // Generate offers for matches
  generateOffers: async (matchIds = []) => {
    try {
      // Convert array parameters to query string
      let params = new URLSearchParams();
      matchIds.forEach(id => params.append('match_ids', id));
      
      const response = await apiClient.post(`/offers/generate?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Error generating offers:', error);
      throw error;
    }
  },
  
  // Update an offer
  updateOffer: async (id, offerData) => {
    try {
      const response = await apiClient.put(`/offers/${id}`, offerData);
      return response.data;
    } catch (error) {
      console.error(`Error updating offer ${id}:`, error);
      throw error;
    }
  },
  
  // Approve an offer
  approveOffer: async (id) => {
    try {
      const response = await apiClient.post(`/offers/${id}/approve`);
      return response.data;
    } catch (error) {
      console.error(`Error approving offer ${id}:`, error);
      throw error;
    }
  },
  
  // Reject an offer
  rejectOffer: async (id, comments = '') => {
    try {
      const response = await apiClient.post(`/offers/${id}/reject`, { comments });
      return response.data;
    } catch (error) {
      console.error(`Error rejecting offer ${id}:`, error);
      throw error;
    }
  }
};