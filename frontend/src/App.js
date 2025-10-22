import { useEffect, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import FloatingDonateButton from "@/components/FloatingDonateButton";

// Pages
import HomePage from "@/pages/HomePage";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";
import AboutPage from "@/pages/AboutPage";
import ContactPage from "@/pages/ContactPage";
import CampaignsPage from "@/pages/CampaignsPage";
import CampaignDetailPage from "@/pages/CampaignDetailPage";
import MyDonationsPage from "@/pages/MyDonationsPage";
import MyPledgesPage from "@/pages/MyPledgesPage";
import AdminDashboard from "@/pages/AdminDashboard";

// Delta feature pages
import VolunteerMembersPage from "@/pages/VolunteerMembersPage";
import OnBehalfDonationPage from "@/pages/OnBehalfDonationPage";
import BloodDonorSearchPage from "@/pages/BloodDonorSearchPage";
import BloodDonorRegisterPage from "@/pages/BloodDonorRegisterPage";
import EventsPage from "@/pages/EventsPage";
import AdminSettingsPage from "@/pages/AdminSettingsPage";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Axios interceptor for auth
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const AuthContext = React.createContext(null);

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const response = await axios.get(`${API}/auth/me`);
        setUser(response.data);
      } catch (error) {
        localStorage.removeItem('token');
      }
    }
    setLoading(false);
  };

  const login = (token, userData) => {
    localStorage.setItem('token', token);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    toast.success('Logged out successfully');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      <div className="App">
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/contact" element={<ContactPage />} />
            <Route path="/campaigns" element={<CampaignsPage />} />
            <Route path="/campaigns/:id" element={<CampaignDetailPage />} />
            <Route path="/my-donations" element={user ? <MyDonationsPage /> : <Navigate to="/login" />} />
            <Route path="/my-pledges" element={user ? <MyPledgesPage /> : <Navigate to="/login" />} />
            <Route path="/admin" element={user?.roles?.includes('admin') ? <AdminDashboard /> : <Navigate to="/" />} />
            
            {/* Delta Features - Blood Donors */}
            <Route path="/blood-donors/search" element={<BloodDonorSearchPage />} />
            <Route path="/blood-donors/register" element={<BloodDonorRegisterPage />} />
            
            {/* Delta Features - Events */}
            <Route path="/events" element={<EventsPage />} />
            
            {/* Delta Features - Volunteer */}
            <Route path="/volunteer/members" element={user?.roles?.includes('volunteer') ? <VolunteerMembersPage /> : <Navigate to="/" />} />
            <Route path="/volunteer/donate-on-behalf/:memberId" element={user?.roles?.includes('volunteer') ? <OnBehalfDonationPage /> : <Navigate to="/" />} />
          </Routes>
          
          {/* Floating Donate Button on All Pages */}
          <FloatingDonateButton />
        </BrowserRouter>
        <Toaster position="top-right" richColors />
      </div>
    </AuthContext.Provider>
  );
}

export default App;

import React from 'react';