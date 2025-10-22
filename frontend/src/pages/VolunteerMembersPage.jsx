import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Checkbox } from '@/components/ui/checkbox';
import Navbar from '@/components/Navbar';
import { AuthContext, API } from '@/App';
import { toast } from 'sonner';
import axios from 'axios';
import { Plus, Edit2, UserPlus } from 'lucide-react';

const VolunteerMembersPage = () => {
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!user?.roles?.includes('volunteer')) {
      toast.error('Access denied');
      navigate('/');
      return;
    }
    fetchMembers();
  }, []);

  const fetchMembers = async () => {
    try {
      const response = await axios.get(`${API}/volunteer/members`);
      setMembers(response.data);
    } catch (error) {
      toast.error('Failed to load members');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateMember = async (e) => {
    e.preventDefault();
    setCreating(true);
    const formData = new FormData(e.target);

    try {
      await axios.post(`${API}/volunteer/members/create`, {
        full_name: formData.get('full_name'),
        phone: formData.get('phone'),
        email: formData.get('email') || null,
        blood_group: formData.get('blood_group') || null,
        date_of_birth: formData.get('date_of_birth') || null,
        city: formData.get('city') || null,
        state: formData.get('state') || null,
        district: formData.get('district') || null,
        pan: formData.get('pan') || null,
        address: formData.get('address') || null,
        consent_public_donor: false,
        consent_marketing: false
      });

      toast.success('Member created successfully');
      setShowCreateDialog(false);
      fetchMembers();
      e.target.reset();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create member');
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Navbar />

      <div className="bg-white border-b">
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold" style={{ fontFamily: 'Space Grotesk' }}>
                My Members
              </h1>
              <p className="text-gray-600 mt-2">Manage members you've created</p>
            </div>
            <Button
              onClick={() => setShowCreateDialog(true)}
              className="bg-blue-600 hover:bg-blue-700"
              data-testid="create-member-btn"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Member
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-12">
        {members.length === 0 ? (
          <Card className="border-0 shadow-lg">
            <CardContent className="py-20 text-center">
              <UserPlus className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-2xl font-semibold text-gray-600 mb-2">No Members Yet</h3>
              <p className="text-gray-500 mb-6">Start by adding your first member</p>
              <Button onClick={() => setShowCreateDialog(true)}>
                Add Member
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {members.map((member) => (
              <Card key={member.id} className="border-0 shadow-lg hover:shadow-xl transition-shadow" data-testid={`member-card-${member.id}`}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>{member.full_name}</span>
                    <Button variant="ghost" size="sm" onClick={() => navigate(`/volunteer/members/${member.id}/edit`)}>
                      <Edit2 className="w-4 h-4" />
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Phone:</span>
                      <span className="font-medium">{member.phone}</span>
                    </div>
                    {member.email && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">Email:</span>
                        <span className="font-medium">{member.email}</span>
                      </div>
                    )}
                    {member.blood_group && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">Blood Group:</span>
                        <span className="font-medium text-red-600">{member.blood_group}</span>
                      </div>
                    )}
                    {member.city && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">City:</span>
                        <span className="font-medium">{member.city}</span>
                      </div>
                    )}
                  </div>
                  <div className="mt-4 pt-4 border-t">
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() => navigate(`/volunteer/donate-on-behalf/${member.id}`)}
                      data-testid={`donate-behalf-${member.id}`}
                    >
                      Donate On Behalf
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Create Member Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="create-member-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl">Add New Member</DialogTitle>
          </DialogHeader>

          <form onSubmit={handleCreateMember} className="space-y-4" data-testid="create-member-form">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="full_name">Full Name *</Label>
                <Input id="full_name" name="full_name" required data-testid="member-name" />
              </div>
              <div>
                <Label htmlFor="phone">Phone *</Label>
                <Input id="phone" name="phone" type="tel" required data-testid="member-phone" />
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="email">Email</Label>
                <Input id="email" name="email" type="email" data-testid="member-email" />
              </div>
              <div>
                <Label htmlFor="blood_group">Blood Group</Label>
                <Select name="blood_group">
                  <SelectTrigger data-testid="member-blood-group">
                    <SelectValue placeholder="Select..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="A+">A+</SelectItem>
                    <SelectItem value="A-">A-</SelectItem>
                    <SelectItem value="B+">B+</SelectItem>
                    <SelectItem value="B-">B-</SelectItem>
                    <SelectItem value="AB+">AB+</SelectItem>
                    <SelectItem value="AB-">AB-</SelectItem>
                    <SelectItem value="O+">O+</SelectItem>
                    <SelectItem value="O-">O-</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="city">City</Label>
                <Input id="city" name="city" data-testid="member-city" />
              </div>
              <div>
                <Label htmlFor="district">District</Label>
                <Input id="district" name="district" data-testid="member-district" />
              </div>
              <div>
                <Label htmlFor="state">State</Label>
                <Input id="state" name="state" data-testid="member-state" />
              </div>
            </div>

            <div>
              <Label htmlFor="address">Address</Label>
              <Input id="address" name="address" data-testid="member-address" />
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="date_of_birth">Date of Birth</Label>
                <Input id="date_of_birth" name="date_of_birth" type="date" data-testid="member-dob" />
              </div>
              <div>
                <Label htmlFor="pan">PAN (for 80G)</Label>
                <Input id="pan" name="pan" maxLength={10} placeholder="ABCDE1234F" data-testid="member-pan" />
              </div>
            </div>

            <div className="flex gap-4 pt-4">
              <Button type="button" variant="outline" onClick={() => setShowCreateDialog(false)} className="flex-1">
                Cancel
              </Button>
              <Button type="submit" disabled={creating} className="flex-1 bg-blue-600 hover:bg-blue-700" data-testid="submit-member">
                {creating ? 'Creating...' : 'Create Member'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default VolunteerMembersPage;