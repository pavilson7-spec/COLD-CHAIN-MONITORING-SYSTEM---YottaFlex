import React, { useState, useEffect } from 'react';
import Layout from './layouts/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import EntityListView from './pages/EntityListView';
import ReportsPage from './pages/ReportsPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  const [user, setUser] = useState(null);
  const [activePage, setActivePage] = useState('Dashboard');

  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    const token = localStorage.getItem('token');
    if (savedUser && token) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.clear();
      }
    }
  }, []);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  if (!user) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  const renderContent = () => {
    switch (activePage) {
      case 'Dashboard':
        return <DashboardPage onNavigate={setActivePage} />;
      case 'Reports':
        return <ReportsPage />;
      case 'System Settings':
        return <SettingsPage />;
      default:
        return <EntityListView entityType={activePage} />;
    }
  };

  return (
    <Layout
      user={user}
      onLogout={handleLogout}
      activePage={activePage}
      onNavigate={setActivePage}
    >
      {renderContent()}
    </Layout>
  );
}
