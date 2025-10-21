import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import Navbar from '@/components/Navbar';
import { toast } from 'sonner';
import { Mail, Phone, MapPin, Send } from 'lucide-react';

const ContactPage = () => {
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    // Simulate form submission
    setTimeout(() => {
      toast.success('Message sent successfully! We\'ll get back to you soon.');
      e.target.reset();
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Navbar />
      
      <div className="container mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4" style={{ fontFamily: 'Space Grotesk' }}>
            Get in <span className="text-blue-600">Touch</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Have questions? We'd love to hear from you. Send us a message and we'll respond as soon as possible.
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8 mb-12">
          {/* Contact Info Cards */}
          <Card className="border-0 shadow-lg text-center">
            <CardContent className="pt-8">
              <div className="w-14 h-14 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Mail className="w-7 h-7 text-blue-600" />
              </div>
              <h3 className="font-semibold text-lg mb-2">Email Us</h3>
              <p className="text-gray-600">donations@weforyou.org</p>
              <p className="text-gray-600">support@weforyou.org</p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg text-center">
            <CardContent className="pt-8">
              <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Phone className="w-7 h-7 text-green-600" />
              </div>
              <h3 className="font-semibold text-lg mb-2">Call Us</h3>
              <p className="text-gray-600">+91-11-12345678</p>
              <p className="text-gray-600 text-sm">Mon-Fri, 9AM-6PM IST</p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg text-center">
            <CardContent className="pt-8">
              <div className="w-14 h-14 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <MapPin className="w-7 h-7 text-purple-600" />
              </div>
              <h3 className="font-semibold text-lg mb-2">Visit Us</h3>
              <p className="text-gray-600">123 Charity Street</p>
              <p className="text-gray-600">New Delhi, 110001</p>
            </CardContent>
          </Card>
        </div>

        {/* Contact Form */}
        <Card className="max-w-3xl mx-auto border-0 shadow-2xl" data-testid="contact-form-card">
          <CardHeader>
            <CardTitle className="text-2xl">Send us a Message</CardTitle>
            <CardDescription>
              Fill out the form below and we'll get back to you within 24 hours
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6" data-testid="contact-form">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <Input 
                    id="name" 
                    name="name" 
                    placeholder="John Doe" 
                    required 
                    data-testid="contact-name"
                    className="h-12"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <Input 
                    id="email" 
                    name="email" 
                    type="email" 
                    placeholder="john@example.com" 
                    required 
                    data-testid="contact-email"
                    className="h-12"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="subject">Subject</Label>
                <Input 
                  id="subject" 
                  name="subject" 
                  placeholder="How can we help you?" 
                  required 
                  data-testid="contact-subject"
                  className="h-12"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="message">Message</Label>
                <Textarea 
                  id="message" 
                  name="message" 
                  placeholder="Tell us more about your inquiry..." 
                  rows={6} 
                  required 
                  data-testid="contact-message"
                />
              </div>

              <Button 
                type="submit" 
                className="w-full h-12 text-base bg-blue-600 hover:bg-blue-700" 
                disabled={loading}
                data-testid="contact-submit"
              >
                {loading ? 'Sending...' : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Send Message
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* FAQ Section */}
        <div className="mt-16 max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-8" style={{ fontFamily: 'Space Grotesk' }}>
            Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            {[
              {
                q: 'How do I get my 80G tax receipt?',
                a: 'Tax receipts are automatically generated and available for download after successful donation. Make sure to provide your PAN details during donation.'
              },
              {
                q: 'Can I cancel my recurring donation?',
                a: 'Yes, you can pause or cancel your recurring pledge anytime from your "My Pledges" page.'
              },
              {
                q: 'Is my donation secure?',
                a: 'Absolutely! We use Razorpay for secure payment processing with industry-standard encryption.'
              },
              {
                q: 'How can I track my donations?',
                a: 'Login to your account and visit "My Donations" to see your complete donation history with receipts.'
              }
            ].map((faq, index) => (
              <Card key={index} className="border-0 shadow-md">
                <CardContent className="pt-6">
                  <h3 className="font-semibold text-lg mb-2">{faq.q}</h3>
                  <p className="text-gray-600">{faq.a}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContactPage;