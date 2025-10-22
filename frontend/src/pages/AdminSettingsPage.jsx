import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import Navbar from '@/components/Navbar';
import { AuthContext, API } from '@/App';
import { toast } from 'sonner';
import axios from 'axios';
import { Settings, Download, Edit2, Trash2, Plus, Users, Calendar } from 'lucide-react';

const AdminSettingsPage = () => {
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);
  const [settings, setSettings] = useState(null);
  const [events, setEvents] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showEventDialog, setShowEventDialog] = useState(false);
  const [editingEvent, setEditingEvent] = useState(null);

  useEffect(() => {
    if (!user?.roles?.includes('admin')) {
      toast.error('Access denied');
      navigate('/');
      return;
    }
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [settingsRes, eventsRes, usersRes] = await Promise.all([
        axios.get(`${API}/admin/settings`),
        axios.get(`${API}/admin/events`),
        axios.get(`${API}/admin/users`)
      ]);
      setSettings(settingsRes.data);
      setEvents(eventsRes.data);
      setUsers(usersRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    try {
      await axios.patch(`${API}/admin/settings`, data);
      toast.success('Settings updated successfully');
    } catch (error) {
      toast.error('Failed to update settings');
    }
  };

  const handleExport = async (type) => {
    try {
      const response = await axios.get(`${API}/admin/export/${type}`);
      const dataStr = JSON.stringify(response.data, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${type}_export_${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      toast.success(`${type} data exported successfully`);
    } catch (error) {
      toast.error(`Failed to export ${type}`);
    }
  };

  const handleCreateEvent = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
      title: formData.get('title'),
      description: formData.get('description'),
      schedule_start: formData.get('schedule_start'),
      venue: formData.get('venue'),
      capacity: parseInt(formData.get('capacity')) || null,
      fee_enabled: formData.get('fee_enabled') === 'on',
      fee_amount: parseFloat(formData.get('fee_amount')) || null,
      image_url: formData.get('image_url') || null
    };

    try {
      if (editingEvent) {
        await axios.patch(`${API}/admin/events/${editingEvent.id}`, data);
        toast.success('Event updated');
      } else {
        await axios.post(`${API}/admin/events`, data);
        toast.success('Event created');
      }
      setShowEventDialog(false);
      setEditingEvent(null);
      fetchData();
    } catch (error) {
      toast.error('Failed to save event');
    }
  };

  const handleDeleteEvent = async (eventId) => {
    if (!confirm('Are you sure you want to delete this event?')) return;

    try {
      await axios.delete(`${API}/admin/events/${eventId}`);
      toast.success('Event deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete event');
    }
  };

  if (loading) {
    return (
      <div className=\"min-h-screen flex items-center justify-center\">
        <div className=\"animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600\"></div>
      </div>
    );
  }

  return (
    <div className=\"min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50\">
      <Navbar />

      <div className=\"bg-white border-b\">
        <div className=\"container mx-auto px-6 py-8\">
          <h1 className=\"text-4xl font-bold\" style={{ fontFamily: 'Space Grotesk' }}>
            Admin Settings & Management
          </h1>
          <p className=\"text-gray-600 mt-2\">Manage all aspects of your foundation</p>
        </div>
      </div>

      <div className=\"container mx-auto px-6 py-12\">
        <Tabs defaultValue=\"settings\" className=\"space-y-6\">
          <TabsList className=\"grid w-full grid-cols-4 max-w-3xl\">
            <TabsTrigger value=\"settings\" data-testid=\"settings-tab\">
              <Settings className=\"w-4 h-4 mr-2\" />
              Site Settings
            </TabsTrigger>
            <TabsTrigger value=\"events\" data-testid=\"events-tab\">
              <Calendar className=\"w-4 h-4 mr-2\" />
              Events
            </TabsTrigger>
            <TabsTrigger value=\"users\" data-testid=\"users-tab\">
              <Users className=\"w-4 h-4 mr-2\" />
              Users
            </TabsTrigger>
            <TabsTrigger value=\"exports\" data-testid=\"exports-tab\">
              <Download className=\"w-4 h-4 mr-2\" />
              Data Exports
            </TabsTrigger>
          </TabsList>

          {/* Site Settings Tab */}
          <TabsContent value=\"settings\">
            <Card className=\"border-0 shadow-lg\">
              <CardHeader>
                <CardTitle>Foundation Details</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSaveSettings} className=\"space-y-4\" data-testid=\"settings-form\">
                  <div className=\"grid md:grid-cols-2 gap-4\">
                    <div>
                      <Label>Foundation Name</Label>
                      <Input name=\"foundation_name\" defaultValue={settings?.foundation_name} />
                    </div>
                    <div>
                      <Label>Phone Number</Label>
                      <Input name=\"phone\" defaultValue={settings?.phone} data-testid=\"settings-phone\" />
                    </div>
                  </div>

                  <div className=\"grid md:grid-cols-2 gap-4\">
                    <div>
                      <Label>Email</Label>
                      <Input name=\"email\" type=\"email\" defaultValue={settings?.email} data-testid=\"settings-email\" />
                    </div>
                    <div>
                      <Label>PAN</Label>
                      <Input name=\"pan\" defaultValue={settings?.pan} />
                    </div>
                  </div>

                  <div>
                    <Label>Address</Label>
                    <Input name=\"address\" defaultValue={settings?.address} />
                  </div>

                  <div>
                    <Label>About Us Content</Label>
                    <Textarea
                      name=\"about_us\"
                      rows={6}
                      defaultValue={settings?.about_us}
                      data-testid=\"settings-about\"
                    />
                  </div>

                  <div>
                    <Label>Registration Number</Label>
                    <Input name=\"registration_number\" defaultValue={settings?.registration_number} />
                  </div>

                  <Button type=\"submit\" className=\"bg-blue-600 hover:bg-blue-700\" data-testid=\"save-settings\">
                    Save Settings
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Events Management Tab */}
          <TabsContent value=\"events\">
            <div className=\"space-y-6\">
              <div className=\"flex justify-between items-center\">
                <h2 className=\"text-2xl font-bold\">Events Management</h2>
                <Button
                  onClick={() => {
                    setEditingEvent(null);
                    setShowEventDialog(true);
                  }}
                  className=\"bg-blue-600 hover:bg-blue-700\"
                  data-testid=\"add-event-btn\"
                >
                  <Plus className=\"w-4 h-4 mr-2\" />
                  Add Event
                </Button>
              </div>

              <div className=\"grid md:grid-cols-2 lg:grid-cols-3 gap-6\">
                {events.map((event) => (
                  <Card key={event.id} className=\"border-0 shadow-lg\">
                    <CardHeader>
                      <CardTitle>{event.title}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className=\"space-y-2 text-sm\">
                        <p><strong>Venue:</strong> {event.venue || 'N/A'}</p>
                        <p><strong>Date:</strong> {new Date(event.schedule_start).toLocaleDateString()}</p>
                        <p><strong>Fee:</strong> {event.fee_enabled ? `₹${event.fee_amount}` : 'FREE'}</p>
                        <p><strong>Registered:</strong> {event.registered_count}</p>
                      </div>
                      <div className=\"flex gap-2 mt-4\">
                        <Button
                          variant=\"outline\"
                          size=\"sm\"
                          onClick={() => {
                            setEditingEvent(event);
                            setShowEventDialog(true);
                          }}
                          data-testid={`edit-event-${event.id}`}
                        >
                          <Edit2 className=\"w-3 h-3\" />
                        </Button>
                        <Button
                          variant=\"outline\"
                          size=\"sm\"
                          onClick={() => handleDeleteEvent(event.id)}
                          className=\"text-red-600\"
                          data-testid={`delete-event-${event.id}`}
                        >
                          <Trash2 className=\"w-3 h-3\" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </TabsContent>

          {/* Users Management Tab */}
          <TabsContent value=\"users\">
            <Card className=\"border-0 shadow-lg\">
              <CardHeader>
                <CardTitle>All Users ({users.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className=\"space-y-2\">
                  {users.slice(0, 20).map((user) => (
                    <div key={user.id} className=\"flex justify-between items-center p-3 bg-gray-50 rounded\">
                      <div>
                        <p className=\"font-semibold\">{user.full_name}</p>
                        <p className=\"text-sm text-gray-600\">{user.email}</p>
                      </div>
                      <div className=\"text-sm\">
                        <span className=\"px-2 py-1 bg-blue-100 text-blue-700 rounded\">{user.roles?.join(', ')}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Data Exports Tab */}
          <TabsContent value=\"exports\">
            <div className=\"grid md:grid-cols-2 gap-6\">
              {[
                { type: 'users', title: 'Users Data', desc: 'Export all registered users' },
                { type: 'volunteers', title: 'Volunteers Data', desc: 'Export volunteer information' },
                { type: 'transactions', title: 'Transactions', desc: 'Export all donation transactions' },
                { type: 'campaigns', title: 'Campaigns', desc: 'Export campaign data' },
                { type: 'blood-donors', title: 'Blood Donors', desc: 'Export blood donor directory' }
              ].map((item) => (
                <Card key={item.type} className=\"border-0 shadow-lg\">
                  <CardContent className=\"pt-6\">
                    <h3 className=\"font-bold text-lg mb-2\">{item.title}</h3>
                    <p className=\"text-sm text-gray-600 mb-4\">{item.desc}</p>
                    <Button
                      onClick={() => handleExport(item.type)}
                      variant=\"outline\"
                      className=\"w-full\"
                      data-testid={`export-${item.type}`}
                    >
                      <Download className=\"w-4 h-4 mr-2\" />
                      Export JSON
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Create/Edit Event Dialog */}
      <Dialog open={showEventDialog} onOpenChange={setShowEventDialog}>
        <DialogContent className=\"sm:max-w-2xl max-h-[90vh] overflow-y-auto\">
          <DialogHeader>
            <DialogTitle>{editingEvent ? 'Edit Event' : 'Create New Event'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateEvent} className=\"space-y-4\" data-testid=\"event-form\">
            <div>
              <Label>Event Title *</Label>
              <Input name=\"title\" defaultValue={editingEvent?.title} required />
            </div>
            <div>
              <Label>Description *</Label>
              <Textarea name=\"description\" rows={4} defaultValue={editingEvent?.description} required />
            </div>
            <div className=\"grid md:grid-cols-2 gap-4\">
              <div>
                <Label>Start Date & Time *</Label>
                <Input
                  name=\"schedule_start\"
                  type=\"datetime-local\"
                  defaultValue={editingEvent?.schedule_start?.slice(0, 16)}
                  required
                />
              </div>
              <div>
                <Label>Venue</Label>
                <Input name=\"venue\" defaultValue={editingEvent?.venue} />
              </div>
            </div>
            <div className=\"grid md:grid-cols-2 gap-4\">
              <div>
                <Label>Capacity (Optional)</Label>
                <Input name=\"capacity\" type=\"number\" defaultValue={editingEvent?.capacity} />
              </div>
              <div>
                <Label>Image URL</Label>
                <Input name=\"image_url\" defaultValue={editingEvent?.image_url} />
              </div>
            </div>
            <div className=\"flex items-center gap-4 p-4 bg-gray-50 rounded\">
              <input type=\"checkbox\" name=\"fee_enabled\" id=\"fee_enabled\" defaultChecked={editingEvent?.fee_enabled} />
              <Label htmlFor=\"fee_enabled\" className=\"font-semibold\">Enable Registration Fee</Label>
              <Input name=\"fee_amount\" type=\"number\" placeholder=\"Amount\" defaultValue={editingEvent?.fee_amount} className=\"w-32\" />
            </div>
            <div className=\"flex gap-4\">
              <Button type=\"button\" variant=\"outline\" onClick={() => setShowEventDialog(false)} className=\"flex-1\">
                Cancel
              </Button>
              <Button type=\"submit\" className=\"flex-1 bg-blue-600 hover:bg-blue-700\">
                {editingEvent ? 'Update Event' : 'Create Event'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminSettingsPage;
