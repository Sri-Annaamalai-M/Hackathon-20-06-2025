// src/context/AppContext.jsx
import { createContext, useContext, useState, useEffect } from 'react';
import { candidateService, roleService, matchService, offerService } from '../services/api';

// Create context
const AppContext = createContext();

// Custom hook for using the context
export const useAppContext = () => useContext(AppContext);

// Mock data for fallback
const mockData = {
  candidates: [
    { _id: 'mock1', name: 'Alex Johnson', email: 'alex@example.com', skills: ['React', 'Node.js'], experience: '5 years' },
    { _id: 'mock2', name: 'Maria Garcia', email: 'maria@example.com', skills: ['Python', 'Data Science'], experience: '3 years' },
  ],
  roles: [
    { _id: 'mock1', title: 'Frontend Developer', department: 'Engineering', required_skills: ['JavaScript', 'React'], is_active: true },
    { _id: 'mock2', title: 'Data Scientist', department: 'Analytics', required_skills: ['Python', 'Machine Learning'], is_active: true },
  ],
  matches: [
    { _id: 'mock1', candidate_id: 'mock1', role_id: 'mock1', match_score: 85, status: 'Matched' },
    { _id: 'mock2', candidate_id: 'mock2', role_id: 'mock2', match_score: 92, status: 'Matched' },
  ],
  offers: [
    { 
      _id: 'mock1', 
      candidate_id: 'mock1', 
      role_id: 'mock1', 
      match_score: 85, 
      status: 'Pending Approval',
      offer: {
        base_salary: 100000,
        bonus: 10000,
        equity: '1%',
        total_ctc: 110000
      }
    },
  ]
};

export const AppProvider = ({ children }) => {
  // Application state
  const [candidates, setCandidates] = useState([]);
  const [roles, setRoles] = useState([]);
  const [matches, setMatches] = useState([]);
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [useFallbackData, setUseFallbackData] = useState(false);

  // Load initial data
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        let candidatesData = [], rolesData = [], matchesData = [], offersData = [];
        
        try {
          // Try to fetch candidates
          candidatesData = await candidateService.getCandidates();
        } catch (err) {
          console.error('Error fetching candidates:', err);
          if (err.userMessage) {
            setError(prev => prev || err.userMessage);
          }
        }
        
        try {
          // Try to fetch roles
          rolesData = await roleService.getRoles();
        } catch (err) {
          console.error('Error fetching roles:', err);
          if (err.userMessage) {
            setError(prev => prev || err.userMessage);
          }
        }
        
        try {
          // Try to fetch matches
          matchesData = await matchService.getMatches();
        } catch (err) {
          console.error('Error fetching matches:', err);
          if (err.userMessage) {
            setError(prev => prev || err.userMessage);
          }
        }
        
        try {
          // Try to fetch offers
          offersData = await offerService.getOffers();
        } catch (err) {
          console.error('Error fetching offers:', err);
          if (err.userMessage) {
            setError(prev => prev || err.userMessage);
          }
        }
        
        // Check if any data was loaded successfully
        const hasData = candidatesData.length > 0 || rolesData.length > 0 || 
                        matchesData.length > 0 || offersData.length > 0;
        
        if (!hasData) {
          console.warn('No data fetched from API, using fallback data');
          setUseFallbackData(true);
          
          // Use mock data as fallback
          setCandidates(mockData.candidates);
          setRoles(mockData.roles);
          setMatches(mockData.matches);
          setOffers(mockData.offers);
          
          // Show a generic error if none was set
          if (!error) {
            setError('Unable to connect to the backend. Using demo mode with sample data.');
          }
        } else {
          // Use the real data
          setCandidates(candidatesData);
          setRoles(rolesData);
          setMatches(matchesData);
          setOffers(offersData);
        }
      } catch (err) {
        console.error('Error in fetchInitialData:', err);
        setError('Failed to load application data. Please refresh the page.');
        
        // Use mock data as fallback
        setCandidates(mockData.candidates);
        setRoles(mockData.roles);
        setMatches(mockData.matches);
        setOffers(mockData.offers);
        setUseFallbackData(true);
      } finally {
        setLoading(false);
      }
    };

    fetchInitialData();
  }, []);

  // Refresh data functions
  const refreshCandidates = async () => {
    if (useFallbackData) {
      return mockData.candidates;
    }
    
    try {
      const data = await candidateService.getCandidates();
      setCandidates(data);
      return data;
    } catch (err) {
      console.error('Error refreshing candidates:', err);
      setError(err.userMessage || 'Error refreshing candidates');
      throw err;
    }
  };

  const refreshRoles = async () => {
    if (useFallbackData) {
      return mockData.roles;
    }
    
    try {
      const data = await roleService.getRoles();
      setRoles(data);
      return data;
    } catch (err) {
      console.error('Error refreshing roles:', err);
      setError(err.userMessage || 'Error refreshing roles');
      throw err;
    }
  };

  const refreshMatches = async () => {
    if (useFallbackData) {
      return mockData.matches;
    }
    
    try {
      const data = await matchService.getMatches();
      setMatches(data);
      return data;
    } catch (err) {
      console.error('Error refreshing matches:', err);
      setError(err.userMessage || 'Error refreshing matches');
      throw err;
    }
  };

  const refreshOffers = async () => {
    if (useFallbackData) {
      return mockData.offers;
    }
    
    try {
      const data = await offerService.getOffers();
      setOffers(data);
      return data;
    } catch (err) {
      console.error('Error refreshing offers:', err);
      setError(err.userMessage || 'Error refreshing offers');
      throw err;
    }
  };

  // Upload candidates
  const uploadCandidates = async (files) => {
    if (useFallbackData) {
      // Simulate successful upload
      setTimeout(() => {
        setCandidates([
          ...candidates,
          { 
            _id: `mock${candidates.length + 1}`, 
            name: 'New Candidate', 
            email: 'new@example.com', 
            skills: ['JavaScript', 'React'], 
            experience: '2 years' 
          }
        ]);
      }, 1000);
      
      return { message: 'Simulated upload successful in demo mode' };
    }
    
    try {
      const response = await candidateService.uploadCandidateFiles(files);
      // Refresh candidates after successful upload (with a delay to allow processing)
      setTimeout(refreshCandidates, 2000);
      return response;
    } catch (err) {
      console.error('Error uploading candidates:', err);
      setError(err.userMessage || 'Error uploading candidates');
      throw err;
    }
  };

  // Run matching process
  const runMatching = async (candidateIds = [], roleIds = []) => {
    if (useFallbackData) {
      // Simulate successful matching
      setTimeout(() => {
        setMatches([
          ...matches,
          { 
            _id: `mock${matches.length + 1}`, 
            candidate_id: candidates[0]._id, 
            role_id: roles[0]._id, 
            match_score: 75, 
            status: 'Matched' 
          }
        ]);
      }, 1000);
      
      return { message: 'Simulated matching process in demo mode' };
    }
    
    try {
      const response = await matchService.processMatches(candidateIds, roleIds);
      // Refresh matches after processing (with a delay)
      setTimeout(refreshMatches, 3000);
      return response;
    } catch (err) {
      console.error('Error running matching process:', err);
      setError(err.userMessage || 'Error running matching process');
      throw err;
    }
  };

  // Generate offers
  const generateOffers = async (matchIds = []) => {
    if (useFallbackData) {
      // Simulate successful offer generation
      setTimeout(() => {
        setOffers([
          ...offers,
          { 
            _id: `mock${offers.length + 1}`, 
            candidate_id: candidates[0]._id, 
            role_id: roles[0]._id, 
            match_score: 75, 
            status: 'Pending Approval',
            offer: {
              base_salary: 90000,
              bonus: 9000,
              equity: '0.5%',
              total_ctc: 99000
            }
          }
        ]);
      }, 1000);
      
      return { message: 'Simulated offer generation in demo mode' };
    }
    
    try {
      const response = await offerService.generateOffers(matchIds);
      // Refresh offers after generation (with a delay)
      setTimeout(refreshOffers, 3000);
      return response;
    } catch (err) {
      console.error('Error generating offers:', err);
      setError(err.userMessage || 'Error generating offers');
      throw err;
    }
  };

  // Approve offer
  const approveOffer = async (offerId) => {
    if (useFallbackData) {
      // Simulate successful approval
      setOffers(offers.map(offer => 
        offer._id === offerId ? { ...offer, status: 'Approved' } : offer
      ));
      
      return { message: 'Simulated offer approval in demo mode' };
    }
    
    try {
      const response = await offerService.approveOffer(offerId);
      // Update offers in state
      setOffers(offers.map(offer => 
        offer._id === offerId ? { ...offer, status: 'Approved' } : offer
      ));
      return response;
    } catch (err) {
      console.error('Error approving offer:', err);
      setError(err.userMessage || 'Error approving offer');
      throw err;
    }
  };

  // Update offer
  const updateOffer = async (offerId, offerData) => {
    if (useFallbackData) {
      // Simulate successful update
      setOffers(offers.map(offer => 
        offer._id === offerId ? { ...offer, ...offerData, status: 'Modified' } : offer
      ));
      
      return { message: 'Simulated offer update in demo mode' };
    }
    
    try {
      const response = await offerService.updateOffer(offerId, offerData);
      // Update offers in state
      setOffers(offers.map(offer => 
        offer._id === offerId ? response : offer
      ));
      return response;
    } catch (err) {
      console.error('Error updating offer:', err);
      setError(err.userMessage || 'Error updating offer');
      throw err;
    }
  };

  // Clear error
  const clearError = () => {
    setError(null);
  };

  // Provide context value
  const contextValue = {
    // State
    candidates,
    roles,
    matches,
    offers,
    loading,
    error,
    useFallbackData,
    
    // Functions
    refreshCandidates,
    refreshRoles,
    refreshMatches,
    refreshOffers,
    uploadCandidates,
    runMatching,
    generateOffers,
    approveOffer,
    updateOffer,
    clearError
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
};