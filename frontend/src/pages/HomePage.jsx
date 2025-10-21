import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import Navbar from '@/components/Navbar';
import { Heart, Users, Target, TrendingUp, ArrowRight, Shield, Receipt } from 'lucide-react';

const HomePage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen">
      <Navbar />
      
      {/* Hero Section */}
      <div className="relative min-h-[85vh] flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-white to-purple-50" />
        
        {/* Decorative blobs */}
        <div className="absolute top-20 left-10 w-72 h-72 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob" />
        <div className="absolute top-40 right-10 w-72 h-72 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000" />
        <div className="absolute -bottom-8 left-1/2 w-72 h-72 bg-pink-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000" />

        <div className="relative z-10 container mx-auto px-6 text-center">
          <div className="animate-fadeIn">
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6" style={{ fontFamily: 'Space Grotesk' }}>
              Make a Difference
              <br />
              <span className="text-blue-600">One Donation at a Time</span>
            </h1>
            <p className="text-lg sm:text-xl text-gray-600 mb-12 max-w-2xl mx-auto">
              Join thousands of donors supporting meaningful causes. Track your impact, get tax benefits, and change lives.
            </p>
            <div className="flex gap-4 justify-center flex-wrap">
              <Button 
                onClick={() => navigate('/campaigns')} 
                size="lg" 
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-6 text-lg rounded-full"
                data-testid="hero-donate-btn"
              >
                Start Donating <ArrowRight className="ml-2" />
              </Button>
              <Button 
                onClick={() => navigate('/about')} 
                size="lg" 
                variant="outline"
                className="px-8 py-6 text-lg rounded-full"
                data-testid="hero-learn-btn"
              >
                Learn More
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-24 bg-white">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4" style={{ fontFamily: 'Space Grotesk' }}>
              Why Choose WeForYou?
            </h2>
            <p className="text-gray-600 text-lg max-w-2xl mx-auto">
              A transparent, secure, and impactful way to support causes you care about
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              {
                icon: <Heart className="w-8 h-8 text-blue-600" />,
                title: 'Verified Campaigns',
                description: 'All campaigns are verified and monitored for transparency'
              },
              {
                icon: <Users className="w-8 h-8 text-purple-600" />,
                title: 'Track Your Impact',
                description: 'See exactly where your donations go and the impact they create'
              },
              {
                icon: <Receipt className="w-8 h-8 text-pink-600" />,
                title: '80G Tax Benefits',
                description: 'Get tax deduction certificates instantly for eligible donations'
              },
              {
                icon: <TrendingUp className="w-8 h-8 text-green-600" />,
                title: 'Recurring Donations',
                description: 'Set up monthly donations and manage them easily'
              }
            ].map((feature, index) => (
              <Card key={index} className="border-0 shadow-lg hover:shadow-xl transition-all duration-300">
                <CardHeader>
                  <div className="mb-4 w-14 h-14 bg-gray-50 rounded-full flex items-center justify-center">
                    {feature.icon}
                  </div>
                  <CardTitle className="text-xl">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-24 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="container mx-auto px-6 text-center">
          <h2 className="text-4xl font-bold mb-6" style={{ fontFamily: 'Space Grotesk' }}>
            Ready to Make an Impact?
          </h2>
          <p className="text-xl mb-8 opacity-90 max-w-2xl mx-auto">
            Join our community of donors and start supporting causes that matter to you
          </p>
          <Button 
            onClick={() => navigate('/register')} 
            size="lg" 
            className="bg-white text-blue-600 hover:bg-gray-100 px-8 py-6 text-lg rounded-full"
            data-testid="cta-register-btn"
          >
            Get Started Today
          </Button>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="container mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-xl font-bold mb-4" style={{ fontFamily: 'Space Grotesk' }}>
                WeForYou Foundation
              </h3>
              <p className="text-gray-400">Making a difference through transparent and impactful donations.</p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Quick Links</h4>
              <div className="space-y-2">
                <div className="text-gray-400 hover:text-white cursor-pointer" onClick={() => navigate('/campaigns')}>Campaigns</div>
                <div className="text-gray-400 hover:text-white cursor-pointer" onClick={() => navigate('/about')}>About Us</div>
                <div className="text-gray-400 hover:text-white cursor-pointer" onClick={() => navigate('/contact')}>Contact</div>
              </div>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <div className="space-y-2">
                <div className="text-gray-400">Privacy Policy</div>
                <div className="text-gray-400">Terms of Service</div>
                <div className="text-gray-400">Refund Policy</div>
              </div>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Contact</h4>
              <div className="space-y-2 text-gray-400">
                <div>Email: donations@weforyou.org</div>
                <div>Phone: +91-11-12345678</div>
              </div>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            © 2024 WeForYou Foundation. All rights reserved.
          </div>
        </div>
      </footer>

      <style jsx>{`
        @keyframes blob {
          0%, 100% { transform: translate(0, 0) scale(1); }
          25% { transform: translate(20px, -50px) scale(1.1); }
          50% { transform: translate(-20px, 20px) scale(0.9); }
          75% { transform: translate(50px, 50px) scale(1.05); }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
};

export default HomePage;