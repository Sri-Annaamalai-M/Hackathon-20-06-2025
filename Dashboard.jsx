// src/pages/Dashboard.jsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  List,
  ListItem,
  ListItemText,
  Avatar,
  Chip,
  IconButton,
  useTheme,
  alpha,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  PeopleAlt as CandidateIcon,
  WorkOutline as RoleIcon,
  Assignment as MatchIcon,
  MonetizationOn as OfferIcon,
  Psychology as AIIcon,
  TrendingUp as TrendingUpIcon,
  ArrowForward as ArrowForwardIcon,
  Schedule as ScheduleIcon,
  Analytics as AnalyticsIcon,
} from '@mui/icons-material';
import { Bar, Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Import services
import { candidateService, roleService, matchService, offerService } from '../services/api';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export default function Dashboard() {
  const navigate = useNavigate();
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    candidateCount: 0,
    roleCount: 0,
    matchCount: 0,
    offerCount: 0,
    recentCandidates: [],
    recentMatches: [],
    matchQualityDistribution: {
      labels: ['Excellent (90%+)', 'Good (70-89%)', 'Fair (50-69%)', 'Poor (<50%)'],
      data: [0, 0, 0, 0],
    },
    weeklyActivity: {
      labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      data: [0, 0, 0, 0, 0, 0, 0],
    },
  });

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        
        // Fetch all required data in parallel
        const [candidates, roles, matches, offers] = await Promise.all([
          candidateService.getCandidates(),
          roleService.getRoles(),
          matchService.getMatches(),
          offerService.getOffers()
        ]);
        
        // Process match quality distribution
        const matchDistribution = [0, 0, 0, 0]; // Excellent, Good, Fair, Poor
        
        matches.forEach(match => {
          const score = match.match_score;
          if (score >= 90) matchDistribution[0]++;
          else if (score >= 70) matchDistribution[1]++;
          else if (score >= 50) matchDistribution[2]++;
          else matchDistribution[3]++;
        });
        
        // Get recent candidates and matches
        const recentCandidates = candidates
          .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
          .slice(0, 4)
          .map(candidate => ({
            id: candidate._id,
            name: candidate.name,
            role: candidate.experience || 'Not specified',
            matchScore: matches.find(m => m.candidate_id === candidate._id)?.match_score || 0,
            avatar: candidate.name.split(' ').map(n => n[0]).join(''),
            status: 'active'
          }));
        
        const recentMatches = matches
          .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
          .slice(0, 4)
          .map(match => {
            const candidate = candidates.find(c => c._id === match.candidate_id);
            const role = roles.find(r => r._id === match.role_id);
            const matchTime = new Date(match.created_at);
            const now = new Date();
            const diffHours = Math.floor((now - matchTime) / (1000 * 60 * 60));
            
            let timeDisplay;
            if (diffHours < 1) {
              timeDisplay = 'Just now';
            } else if (diffHours < 24) {
              timeDisplay = `${diffHours} hours ago`;
            } else {
              timeDisplay = `${Math.floor(diffHours / 24)} days ago`;
            }
            
            return {
              id: match._id,
              candidate: candidate?.name || 'Unknown',
              role: role?.title || 'Unknown',
              matchScore: match.match_score,
              offerStatus: offers.find(o => o.match_id === match._id)?.status || 'Pending',
              time: timeDisplay
            };
          });
        
        // Update stats state
        setStats({
          candidateCount: candidates.length,
          roleCount: roles.length,
          matchCount: matches.length,
          offerCount: offers.length,
          recentCandidates,
          recentMatches,
          matchQualityDistribution: {
            labels: ['Excellent (90%+)', 'Good (70-89%)', 'Fair (50-69%)', 'Poor (<50%)'],
            data: matchDistribution,
          },
          weeklyActivity: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            data: [12, 8, 15, 9, 11, 6, 4], // Placeholder data, could be calculated from actual timestamps
          },
        });
        
        setLoading(false);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        setError('Failed to fetch dashboard data. Please try again later.');
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const chartData = {
    labels: stats.matchQualityDistribution.labels,
    datasets: [
      {
        label: 'Number of Matches',
        data: stats.matchQualityDistribution.data,
        backgroundColor: [
          'rgba(76, 175, 80, 0.8)',
          'rgba(33, 150, 243, 0.8)',
          'rgba(255, 152, 0, 0.8)',
          'rgba(244, 67, 54, 0.8)',
        ],
        borderColor: [
          'rgba(76, 175, 80, 1)',
          'rgba(33, 150, 243, 1)',
          'rgba(255, 152, 0, 1)',
          'rgba(244, 67, 54, 1)',
        ],
        borderWidth: 2,
        borderRadius: 8,
      },
    ],
  };

  const lineChartData = {
    labels: stats.weeklyActivity.labels,
    datasets: [
      {
        label: 'Matches Created',
        data: stats.weeklyActivity.data,
        borderColor: 'rgba(102, 126, 234, 1)',
        backgroundColor: 'rgba(102, 126, 234, 0.1)',
        tension: 0.4,
        fill: true,
        pointBackgroundColor: 'rgba(102, 126, 234, 1)',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 6,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          font: {
            size: 14,
            weight: 600,
          },
          padding: 20,
        },
      },
      title: {
        display: true,
        text: 'Match Quality Distribution',
        font: {
          size: 16,
          weight: 700,
        },
        padding: 20,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: alpha('#000', 0.1),
        },
      },
      x: {
        grid: {
          display: false,
        },
      },
    },
  };

  const lineChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'Weekly Activity',
        font: {
          size: 16,
          weight: 700,
        },
        padding: 20,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: alpha('#000', 0.1),
        },
      },
      x: {
        grid: {
          display: false,
        },
      },
    },
  };

  if (loading) {
    return (
      <Container maxWidth="xl">
        <Box sx={{ my: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Dashboard
          </Typography>
          <LinearProgress sx={{ borderRadius: 2, height: 6 }} />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="xl">
        <Box sx={{ my: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Dashboard
          </Typography>
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl">
      <Box sx={{ my: 4 }}>
        {/* Welcome Header */}
        <Paper 
          elevation={0} 
          sx={{ 
            p: 4, 
            mb: 4, 
            borderRadius: 4,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            position: 'relative',
            overflow: 'hidden',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              right: 0,
              width: '200px',
              height: '200px',
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '50%',
              transform: 'translate(50px, -50px)',
            },
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, position: 'relative', zIndex: 1 }}>
            <Avatar sx={{ 
              bgcolor: 'rgba(255,255,255,0.2)', 
              width: 80, 
              height: 80,
              backdropFilter: 'blur(10px)'
            }}>
              <AIIcon sx={{ fontSize: 40 }} />
            </Avatar>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h3" fontWeight={700} gutterBottom>
                Welcome to AI Role Matcher
              </Typography>
              <Typography variant="h6" sx={{ opacity: 0.9, mb: 2 }}>
                Transform your hiring process with intelligent automation and data-driven insights
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={<TrendingUpIcon />}
                  sx={{
                    bgcolor: 'rgba(255,255,255,0.2)',
                    backdropFilter: 'blur(10px)',
                    color: 'white',
                    fontWeight: 600,
                    '&:hover': {
                      bgcolor: 'rgba(255,255,255,0.3)',
                    },
                  }}
                  onClick={() => navigate('/matching')}
                >
                  View Analytics
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  startIcon={<ScheduleIcon />}
                  sx={{
                    borderColor: 'rgba(255,255,255,0.5)',
                    color: 'white',
                    fontWeight: 600,
                    '&:hover': {
                      borderColor: 'white',
                      bgcolor: 'rgba(255,255,255,0.1)',
                    },
                  }}
                >
                  Schedule Demo
                </Button>
              </Box>
            </Box>
          </Box>
        </Paper>

        {/* Enhanced Stats Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ 
              height: '100%',
              borderRadius: 3,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              cursor: 'pointer',
              '&:hover': { 
                transform: 'translateY(-8px) scale(1.02)',
                boxShadow: '0 20px 40px rgba(102, 126, 234, 0.3)'
              }
            }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                  <CandidateIcon sx={{ fontSize: 48, opacity: 0.9 }} />
                  <IconButton 
                    sx={{ color: 'rgba(255,255,255,0.8)' }}
                    onClick={() => navigate('/upload')}
                  >
                    <ArrowForwardIcon />
                  </IconButton>
                </Box>
                <Typography variant="h3" fontWeight={700} gutterBottom>
                  {stats.candidateCount}
                </Typography>
                <Typography variant="body1" sx={{ opacity: 0.9 }}>
                  Active Candidates
                </Typography>
                <Typography variant="caption" sx={{ opacity: 0.7 }}>
                  Ready for matching
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ 
              height: '100%',
              borderRadius: 3,
              background: 'linear-gradient(135deg, #4caf50 0%, #8bc34a 100%)',
              color: 'white',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              cursor: 'pointer',
              '&:hover': { 
                transform: 'translateY(-8px) scale(1.02)',
                boxShadow: '0 20px 40px rgba(76, 175, 80, 0.3)'
              }
            }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                  <RoleIcon sx={{ fontSize: 48, opacity: 0.9 }} />
                  <IconButton 
                    sx={{ color: 'rgba(255,255,255,0.8)' }}
                    onClick={() => navigate('/matching')}
                  >
                    <ArrowForwardIcon />
                  </IconButton>
                </Box>
                <Typography variant="h3" fontWeight={700} gutterBottom>
                  {stats.roleCount}
                </Typography>
                <Typography variant="body1" sx={{ opacity: 0.9 }}>
                  Open Positions
                </Typography>
                <Typography variant="caption" sx={{ opacity: 0.7 }}>
                  Active roles
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ 
              height: '100%',
              borderRadius: 3,
              background: 'linear-gradient(135deg, #ff9800 0%, #ffc107 100%)',
              color: 'white',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              cursor: 'pointer',
              '&:hover': { 
                transform: 'translateY(-8px) scale(1.02)',
                boxShadow: '0 20px 40px rgba(255, 152, 0, 0.3)'
              }
            }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                  <MatchIcon sx={{ fontSize: 48, opacity: 0.9 }} />
                  <IconButton 
                    sx={{ color: 'rgba(255,255,255,0.8)' }}
                    onClick={() => navigate('/matching')}
                  >
                    <ArrowForwardIcon />
                  </IconButton>
                </Box>
                <Typography variant="h3" fontWeight={700} gutterBottom>
                  {stats.matchCount}
                </Typography>
                <Typography variant="body1" sx={{ opacity: 0.9 }}>
                  AI Matches
                </Typography>
                <Typography variant="caption" sx={{ opacity: 0.7 }}>
                  Ready for review
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ 
              height: '100%',
              borderRadius: 3,
              background: 'linear-gradient(135deg, #e91e63 0%, #f06292 100%)',
              color: 'white',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              cursor: 'pointer',
              '&:hover': { 
                transform: 'translateY(-8px) scale(1.02)',
                boxShadow: '0 20px 40px rgba(233, 30, 99, 0.3)'
              }
            }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                  <OfferIcon sx={{ fontSize: 48, opacity: 0.9 }} />
                  <IconButton 
                    sx={{ color: 'rgba(255,255,255,0.8)' }}
                    onClick={() => navigate('/offers')}
                  >
                    <ArrowForwardIcon />
                  </IconButton>
                </Box>
                <Typography variant="h3" fontWeight={700} gutterBottom>
                  {stats.offerCount}
                </Typography>
                <Typography variant="body1" sx={{ opacity: 0.9 }}>
                  Offers Generated
                </Typography>
                <Typography variant="caption" sx={{ opacity: 0.7 }}>
                  Ready for approval
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Charts Section */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={8}>
            <Paper sx={{ 
              p: 3, 
              borderRadius: 3,
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(10px)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.1)'
            }}>
              <Bar data={chartData} options={chartOptions} />
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Paper sx={{ 
              p: 3, 
              borderRadius: 3,
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(10px)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
              height: '100%'
            }}>
              <Line data={lineChartData} options={lineChartOptions} />
            </Paper>
          </Grid>
        </Grid>

        {/* Recent Activity Section */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ 
              p: 3, 
              borderRadius: 3,
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(10px)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
              height: '100%'
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <CandidateIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6" fontWeight={700}>
                    Recent Candidates
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Latest candidate activity
                  </Typography>
                </Box>
              </Box>
              
              <List sx={{ p: 0 }}>
                {stats.recentCandidates.length > 0 ? (
                  stats.recentCandidates.map((candidate, index) => (
                    <ListItem 
                      key={candidate.id} 
                      sx={{ 
                        borderRadius: 2, 
                        mb: 1, 
                        p: 2,
                        background: alpha(theme.palette.primary.main, 0.04),
                        border: '1px solid',
                        borderColor: alpha(theme.palette.primary.main, 0.1),
                        transition: 'all 0.2s ease',
                        '&:hover': {
                          background: alpha(theme.palette.primary.main, 0.08),
                          transform: 'translateX(4px)'
                        }
                      }}
                    >
                      <Avatar 
                        sx={{ 
                          bgcolor: candidate.status === 'active' ? 'success.main' : 
                                  candidate.status === 'interview' ? 'warning.main' : 'info.main',
                          mr: 2,
                          fontWeight: 600
                        }}
                      >
                        {candidate.avatar}
                      </Avatar>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography fontWeight={600}>{candidate.name}</Typography>
                            {candidate.matchScore > 0 && (
                              <Chip 
                                label={`${candidate.matchScore}%`}
                                size="small"
                                color={candidate.matchScore > 85 ? 'success' : 'primary'}
                                sx={{ fontWeight: 600 }}
                              />
                            )}
                          </Box>
                        }
                        secondary={
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 0.5 }}>
                            <Typography variant="body2" color="text.secondary">
                              {candidate.role}
                            </Typography>
                            <Chip 
                              label={candidate.status}
                              size="small"
                              variant="outlined"
                              color={candidate.status === 'active' ? 'success' : 
                                    candidate.status === 'interview' ? 'warning' : 'info'}
                            />
                          </Box>
                        }
                      />
                    </ListItem>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                    No recent candidates
                  </Typography>
                )}
              </List>
              
              <Button 
                fullWidth 
                variant="outlined" 
                sx={{ mt: 2, borderRadius: 2 }}
                onClick={() => navigate('/upload')}
              >
                View All Candidates
              </Button>
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Paper sx={{ 
              p: 3, 
              borderRadius: 3,
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(10px)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
              height: '100%'
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <Avatar sx={{ bgcolor: 'success.main' }}>
                  <MatchIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6" fontWeight={700}>
                    Recent Matches
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    AI-generated recommendations
                  </Typography>
                </Box>
              </Box>
              
              <List sx={{ p: 0 }}>
                {stats.recentMatches.length > 0 ? (
                  stats.recentMatches.map((match, index) => (
                    <ListItem 
                      key={match.id} 
                      sx={{ 
                        borderRadius: 2, 
                        mb: 1, 
                        p: 2,
                        background: alpha(theme.palette.success.main, 0.04),
                        border: '1px solid',
                        borderColor: alpha(theme.palette.success.main, 0.1),
                        transition: 'all 0.2s ease',
                        '&:hover': {
                          background: alpha(theme.palette.success.main, 0.08),
                          transform: 'translateX(4px)'
                        }
                      }}
                    >
                      <Avatar 
                        sx={{ 
                          bgcolor: match.matchScore > 85 ? 'success.main' : 'warning.main',
                          mr: 2,
                          fontWeight: 600
                        }}
                      >
                        {match.candidate[0]}
                      </Avatar>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography fontWeight={600}>{match.candidate}</Typography>
                            <Chip 
                              label={`${match.matchScore}%`}
                              size="small"
                              color={match.matchScore > 85 ? 'success' : 'warning'}
                              sx={{ fontWeight: 600 }}
                            />
                          </Box>
                        }
                        secondary={
                          <Box sx={{ mt: 0.5 }}>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              {match.role}
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <Chip 
                                label={match.offerStatus}
                                size="small"
                                variant="outlined"
                                color={match.offerStatus === 'Approved' ? 'success' : 'warning'}
                              />
                              <Typography variant="caption" color="text.secondary">
                                {match.time}
                              </Typography>
                            </Box>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                    No recent matches
                  </Typography>
                )}
              </List>
              
              <Button 
                fullWidth 
                variant="outlined" 
                sx={{ mt: 2, borderRadius: 2 }}
                onClick={() => navigate('/matching')}
              >
                View All Matches
              </Button>
            </Paper>
          </Grid>
        </Grid>

        {/* Quick Actions */}
        <Paper sx={{ 
          p: 4, 
          mt: 4, 
          borderRadius: 3,
          background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
          border: '1px solid',
          borderColor: alpha(theme.palette.primary.main, 0.2)
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
            <Avatar sx={{ bgcolor: 'primary.main' }}>
              <AnalyticsIcon />
            </Avatar>
            <Box>
              <Typography variant="h6" fontWeight={700}>
                Quick Actions
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Get started with common tasks
              </Typography>
            </Box>
          </Box>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                fullWidth
                variant="contained"
                size="large"
                startIcon={<CandidateIcon />}
                sx={{ 
                  borderRadius: 2, 
                  py: 2,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                }}
                onClick={() => navigate('/upload')}
              >
                Upload Resumes
              </Button>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                fullWidth
                variant="contained"
                size="large"
                startIcon={<MatchIcon />}
                sx={{ 
                  borderRadius: 2, 
                  py: 2,
                  background: 'linear-gradient(135deg, #4caf50 0%, #8bc34a 100%)'
                }}
                onClick={() => navigate('/matching')}
              >
                Run Matching
              </Button>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                fullWidth
                variant="contained"
                size="large"
                startIcon={<OfferIcon />}
                sx={{ 
                  borderRadius: 2, 
                  py: 2,
                  background: 'linear-gradient(135deg, #ff9800 0%, #ffc107 100%)'
                }}
                onClick={() => navigate('/offers')}
              >
                Generate Offers
              </Button>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                fullWidth
                variant="outlined"
                size="large"
                startIcon={<TrendingUpIcon />}
                sx={{ 
                  borderRadius: 2, 
                  py: 2,
                  borderColor: 'primary.main',
                  color: 'primary.main',
                  '&:hover': {
                    background: alpha(theme.palette.primary.main, 0.1)
                  }
                }}
              >
                View Analytics
              </Button>
            </Grid>
          </Grid>
        </Paper>

        {/* Error notification */}
        <Snackbar 
          open={error !== null} 
          autoHideDuration={6000} 
          onClose={() => setError(null)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert onClose={() => setError(null)} severity="error">
            {error}
          </Alert>
        </Snackbar>
      </Box>
    </Container>
  );
}