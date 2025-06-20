// src/components/Navigation.jsx
import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  AppBar,
  Box,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Divider,
  Badge,
  Avatar,
  Button,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Upload as UploadIcon,
  CompareArrows as MatchingIcon,
  AttachMoney as OffersIcon,
  Work as RolesIcon,
  Notifications as NotificationIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useAppContext } from '../context/AppContext';

// Import logo (use your actual logo path)
import Logo from '../assets/react.svg';

const drawerWidth = 240;

export default function Navigation() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  
  // Get counts from context
  const { candidates, roles, matches, offers } = useAppContext();
  
  const pendingMatchesCount = matches.filter(m => m.status === 'Review Needed').length;
  const pendingOffersCount = offers.filter(o => o.status === 'Pending Approval').length;

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Upload Candidates', icon: <UploadIcon />, path: '/upload', count: candidates.length },
    { text: 'Role Management', icon: <RolesIcon />, path: '/roles', count: roles.length },
    { text: 'Role Matching', icon: <MatchingIcon />, path: '/matching', count: pendingMatchesCount },
    { text: 'Offer Recommendations', icon: <OffersIcon />, path: '/offers', count: pendingOffersCount },
  ];

  const drawer = (
    <div>
      <Toolbar sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <img src={Logo} alt="Logo" style={{ width: 36, height: 36, marginRight: 8 }} />
        <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 700, letterSpacing: 1 }}>
          AI Role Matcher
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <ListItem 
          key={item.text} 
          component={Link} 
          to={item.path}
          selected={location.pathname === item.path}
          sx={{
            borderRadius: 2,
            mb: 0.5,
            mx: 1,
            cursor: 'pointer',  // Add cursor pointer instead of using button prop
            '&.Mui-selected': {
              backgroundColor: 'primary.main',
              color: 'white',
              '& .MuiListItemIcon-root': { color: 'white' },
            },
            '&:hover': {
              backgroundColor: 'primary.light',
              color: 'primary.contrastText',
              '& .MuiListItemIcon-root': { color: 'primary.contrastText' },
            },
          }}
        >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
            {item.count > 0 && (
              <Badge 
                badgeContent={item.count} 
                color={item.path === '/matching' || item.path === '/offers' ? 'error' : 'primary'}
                sx={{ ml: 1 }}
              />
            )}
          </ListItem>
        ))}
      </List>
      
      <Box sx={{ position: 'absolute', bottom: 0, width: '100%' }}>
        <Divider />
        <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Avatar sx={{ width: 40, height: 40 }}>A</Avatar>
          <Box sx={{ ml: 2, flex: 1 }}>
            <Typography variant="body2" fontWeight={600} noWrap>
              Admin User
            </Typography>
            <Typography variant="caption" color="text.secondary" noWrap>
              HR Manager
            </Typography>
          </Box>
          <IconButton size="small">
            <SettingsIcon fontSize="small" />
          </IconButton>
        </Box>
      </Box>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
          boxShadow: 3,
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1, fontWeight: 700, letterSpacing: 1 }}>
            {menuItems.find(item => item.path === location.pathname)?.text || 'AI Role Matcher'}
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <IconButton color="inherit" sx={{ mr: 1 }}>
              <Badge badgeContent={pendingMatchesCount + pendingOffersCount} color="error">
                <NotificationIcon />
              </Badge>
            </IconButton>
            
            <Button 
              variant="contained" 
              color="secondary" 
              sx={{ 
                bgcolor: 'rgba(255,255,255,0.2)', 
                '&:hover': { 
                  bgcolor: 'rgba(255,255,255,0.3)' 
                } 
              }}
            >
              Help
            </Button>
          </Box>
        </Toolbar>
      </AppBar>
      
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              background: 'linear-gradient(180deg, #f5f5f5 0%, #e3e6f3 100%)',
              borderRight: '1px solid #e0e0e0',
              boxShadow: 2,
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      
      <Box
        component="main"
        sx={{ flexGrow: 1, p: 3, width: { sm: `calc(100% - ${drawerWidth}px)` } }}
      >
        <Toolbar />
        {/* Page content will be rendered here */}
      </Box>
    </Box>
  );
}