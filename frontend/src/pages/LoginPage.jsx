import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import Navbar from '@/components/Navbar';
import { AuthContext, API } from '@/App';
import { toast } from 'sonner';
import axios from 'axios';
import { LogIn } from 'lucide-react';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useContext(AuthContext);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.target);
    
    try {
      const response = await axios.post(`${API}/auth/login`, {
        email: formData.get('email'),
        password: formData.get('password')
      });
      
      login(response.data.access_token, response.data.user);
      toast.success('Logged in successfully!');
      
      // Redirect based on role
      if (response.data.user.roles?.includes('admin')) {
        navigate('/admin');
      } else {
        navigate('/campaigns');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Navbar />
      
      <div className="container mx-auto px-6 py-16 flex items-center justify-center min-h-[calc(100vh-80px)]">
        <Card className="w-full max-w-md border-0 shadow-2xl" data-testid="login-card">
          <CardHeader className="space-y-1 text-center">
            <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
              <LogIn className="w-8 h-8 text-blue-600" />
            </div>
            <CardTitle className="text-3xl font-bold" style={{ fontFamily: 'Space Grotesk' }}>
              Welcome Back
            </CardTitle>
            <CardDescription className="text-base">
              Login to continue making a difference
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4" data-testid="login-form">
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <Input 
                  id="email" 
                  name="email" 
                  type="email" 
                  placeholder="your.email@example.com"
                  required 
                  data-testid="login-email"
                  className="h-12"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input 
                  id="password" 
                  name="password" 
                  type="password" 
                  placeholder="Enter your password"
                  required 
                  data-testid="login-password"
                  className="h-12"
                />
              </div>

              <Button 
                type="submit" 
                className="w-full h-12 text-base bg-blue-600 hover:bg-blue-700" 
                disabled={loading}
                data-testid="login-submit"
              >
                {loading ? 'Logging in...' : 'Login'}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                Don't have an account?{' '}
                <span 
                  onClick={() => navigate('/register')} 
                  className="text-blue-600 hover:text-blue-700 font-semibold cursor-pointer"
                  data-testid="go-to-register"
                >
                  Register here
                </span>
              </p>
            </div>

            <div className="mt-6 pt-6 border-t">
              <p className="text-xs text-center text-gray-500">
                <strong>Test Credentials:</strong><br />
                Admin: admin@weforyou.org / admin123<br />
                Donor: priya.sharma@example.com / donor123
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default LoginPage;