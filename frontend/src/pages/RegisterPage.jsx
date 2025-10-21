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
import { UserPlus } from 'lucide-react';

const RegisterPage = () => {
  const navigate = useNavigate();
  const { login } = useContext(AuthContext);
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.target);
    
    try {
      const response = await axios.post(`${API}/auth/register`, {
        email: formData.get('email'),
        password: formData.get('password'),
        full_name: formData.get('full_name'),
        phone: formData.get('phone') || null,
        roles: ['donor']
      });
      
      login(response.data.access_token, response.data.user);
      toast.success('Account created successfully!');
      navigate('/campaigns');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Navbar />
      
      <div className="container mx-auto px-6 py-16 flex items-center justify-center min-h-[calc(100vh-80px)]">
        <Card className="w-full max-w-md border-0 shadow-2xl" data-testid="register-card">
          <CardHeader className="space-y-1 text-center">
            <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
              <UserPlus className="w-8 h-8 text-blue-600" />
            </div>
            <CardTitle className="text-3xl font-bold" style={{ fontFamily: 'Space Grotesk' }}>
              Join WeForYou
            </CardTitle>
            <CardDescription className="text-base">
              Create an account to start making a difference
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleRegister} className="space-y-4" data-testid="register-form">
              <div className="space-y-2">
                <Label htmlFor="full_name">Full Name</Label>
                <Input 
                  id="full_name" 
                  name="full_name" 
                  placeholder="John Doe"
                  required 
                  data-testid="register-name"
                  className="h-12"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <Input 
                  id="email" 
                  name="email" 
                  type="email" 
                  placeholder="your.email@example.com"
                  required 
                  data-testid="register-email"
                  className="h-12"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number (Optional)</Label>
                <Input 
                  id="phone" 
                  name="phone" 
                  type="tel" 
                  placeholder="+91-9876543210"
                  data-testid="register-phone"
                  className="h-12"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input 
                  id="password" 
                  name="password" 
                  type="password" 
                  placeholder="Create a strong password"
                  required 
                  data-testid="register-password"
                  className="h-12"
                  minLength={6}
                />
              </div>

              <Button 
                type="submit" 
                className="w-full h-12 text-base bg-blue-600 hover:bg-blue-700" 
                disabled={loading}
                data-testid="register-submit"
              >
                {loading ? 'Creating Account...' : 'Create Account'}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                Already have an account?{' '}
                <span 
                  onClick={() => navigate('/login')} 
                  className="text-blue-600 hover:text-blue-700 font-semibold cursor-pointer"
                  data-testid="go-to-login"
                >
                  Login here
                </span>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default RegisterPage;