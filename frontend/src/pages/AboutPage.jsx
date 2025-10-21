import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import Navbar from '@/components/Navbar';
import { Target, Heart, Users, Award } from 'lucide-react';

const AboutPage = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Navbar />
      
      <div className="container mx-auto px-6 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold mb-6" style={{ fontFamily: 'Space Grotesk' }}>
            About <span className="text-blue-600">WeForYou</span> Foundation
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            We are a registered non-profit organization dedicated to creating positive change through transparent and impactful donations.
          </p>
        </div>

        {/* Mission & Vision */}
        <div className="grid md:grid-cols-2 gap-8 mb-16">
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <Target className="w-6 h-6 text-blue-600" />
              </div>
              <CardTitle className="text-2xl">Our Mission</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700 leading-relaxed">
                To empower communities and individuals by facilitating transparent, efficient, and impactful donations that address critical social issues including education, healthcare, and poverty alleviation.
              </p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardHeader>
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mb-4">
                <Heart className="w-6 h-6 text-purple-600" />
              </div>
              <CardTitle className="text-2xl">Our Vision</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700 leading-relaxed">
                A world where every individual has access to basic necessities and opportunities to thrive, and where generosity and compassion drive positive social change.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Values */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-center mb-10" style={{ fontFamily: 'Space Grotesk' }}>
            Our Core Values
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <Card className="border-0 shadow-lg text-center">
              <CardContent className="pt-8">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Users className="w-8 h-8 text-blue-600" />
                </div>
                <h3 className="text-xl font-bold mb-3">Transparency</h3>
                <p className="text-gray-600">
                  Every donation is tracked and donors can see exactly where their money goes.
                </p>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg text-center">
              <CardContent className="pt-8">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Award className="w-8 h-8 text-green-600" />
                </div>
                <h3 className="text-xl font-bold mb-3">Accountability</h3>
                <p className="text-gray-600">
                  We are committed to responsible stewardship of every rupee donated.
                </p>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg text-center">
              <CardContent className="pt-8">
                <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Heart className="w-8 h-8 text-purple-600" />
                </div>
                <h3 className="text-xl font-bold mb-3">Impact</h3>
                <p className="text-gray-600">
                  We focus on creating measurable, lasting change in the communities we serve.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Stats */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-12 text-white">
          <h2 className="text-3xl font-bold text-center mb-10" style={{ fontFamily: 'Space Grotesk' }}>
            Our Impact
          </h2>
          <div className="grid md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold mb-2">₹10M+</div>
              <div className="text-blue-100">Total Donations</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">50+</div>
              <div className="text-blue-100">Active Campaigns</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">5,000+</div>
              <div className="text-blue-100">Happy Donors</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">100+</div>
              <div className="text-blue-100">Lives Changed</div>
            </div>
          </div>
        </div>

        {/* Registration Details */}
        <div className="mt-16">
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="text-2xl">Registration Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-6 text-gray-700">
                <div>
                  <p className="font-semibold mb-2">Organization Name:</p>
                  <p>WeForYou Foundation</p>
                </div>
                <div>
                  <p className="font-semibold mb-2">Registration Number:</p>
                  <p>U85100DL2020NPL123456</p>
                </div>
                <div>
                  <p className="font-semibold mb-2">12A Registration:</p>
                  <p>AAATW1234E</p>
                </div>
                <div>
                  <p className="font-semibold mb-2">80G Registration:</p>
                  <p>AAATW1234EF20214</p>
                </div>
                <div>
                  <p className="font-semibold mb-2">PAN:</p>
                  <p>AAATW1234E</p>
                </div>
                <div>
                  <p className="font-semibold mb-2">FCRA Registration:</p>
                  <p>Available on request</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AboutPage;