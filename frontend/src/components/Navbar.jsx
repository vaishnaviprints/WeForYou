import React, { useContext } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { AuthContext } from '@/App';
import { LogOut, User, LayoutDashboard } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

const Navbar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useContext(AuthContext);

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="bg-white border-b sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div 
            className="text-2xl font-bold cursor-pointer" 
            style={{ fontFamily: 'Space Grotesk' }}
            onClick={() => navigate('/')}
            data-testid="logo"
          >
            <span className="text-blue-600">WeForYou</span> Foundation
          </div>

          {/* Nav Links */}
          <div className="hidden md:flex items-center gap-6">
            <Button 
              variant="ghost" 
              onClick={() => navigate('/')} 
              className={isActive('/') ? 'text-blue-600' : ''}
              data-testid="nav-home"
            >
              Home
            </Button>
            <Button 
              variant="ghost" 
              onClick={() => navigate('/campaigns')} 
              className={isActive('/campaigns') ? 'text-blue-600' : ''}
              data-testid="nav-campaigns"
            >
              Campaigns
            </Button>
            <Button 
              variant="ghost" 
              onClick={() => navigate('/events')} 
              className={isActive('/events') ? 'text-blue-600' : ''}
              data-testid="nav-events"
            >
              Events
            </Button>
            <Button 
              variant="ghost" 
              onClick={() => navigate('/blood-donors/search')} 
              className={isActive('/blood-donors') ? 'text-blue-600' : ''}
              data-testid="nav-blood-donors"
            >
              Blood Donors
            </Button>
            <Button 
              variant="ghost" 
              onClick={() => navigate('/about')} 
              className={isActive('/about') ? 'text-blue-600' : ''}
              data-testid="nav-about"
            >
              About Us
            </Button>
            <Button 
              variant="ghost" 
              onClick={() => navigate('/contact')} 
              className={isActive('/contact') ? 'text-blue-600' : ''}
              data-testid="nav-contact"
            >
              Contact
            </Button>
          </div>

          {/* Auth Buttons */}
          <div className="flex items-center gap-3">
            {user ? (
              <>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" className="gap-2" data-testid="user-menu">
                      <User className="w-4 h-4" />
                      {user.full_name}
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56">
                    <DropdownMenuItem onClick={() => navigate('/my-donations')} data-testid="menu-donations">
                      My Donations
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate('/my-pledges')} data-testid="menu-pledges">
                      My Pledges
                    </DropdownMenuItem>
                    {user.roles?.includes('volunteer') && (
                      <>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => navigate('/volunteer/members')} data-testid="menu-volunteer-members">
                          My Members
                        </DropdownMenuItem>
                      </>
                    )}
                    {user.roles?.includes('admin') && (
                      <>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => navigate('/admin')} data-testid="menu-admin">
                          <LayoutDashboard className="w-4 h-4 mr-2" />
                          Admin Dashboard
                        </DropdownMenuItem>
                      </>
                    )}
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={logout} className="text-red-600" data-testid="menu-logout">
                      <LogOut className="w-4 h-4 mr-2" />
                      Logout
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            ) : (
              <>
                <Button 
                  variant="ghost" 
                  onClick={() => navigate('/login')} 
                  data-testid="nav-login"
                >
                  Login
                </Button>
                <Button 
                  onClick={() => navigate('/register')} 
                  className="bg-blue-600 hover:bg-blue-700"
                  data-testid="nav-register"
                >
                  Register
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;