import { useState, useEffect } from 'react';
import { Users, Plus, Edit, Zap, UserCircle, Trash2 } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { useToast } from '../hooks/use-toast';
import { api } from '../services/api';

export default function UserManager({ onCreditsUpdate, currentUser }) {
  const [users, setUsers] = useState([]);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isKeyModalOpen, setIsKeyModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [newUserApiKey, setNewUserApiKey] = useState('');
  const [newUser, setNewUser] = useState({
    name: '',
    role: 'member'
  });
  const [creditUpdate, setCreditUpdate] = useState('');
  const { toast } = useToast();

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const usersData = await api.getAllUsers();
      setUsers(usersData);
    } catch (err) {
      console.error('Failed to load users:', err);
    }
  };

  const handleCreateUser = async () => {
    if (!newUser.name.trim()) {
      toast({
        variant: 'destructive',
        title: 'Validation Error',
        description: 'User name is required',
      });
      return;
    }

    try {
      const createdUser = await api.createUser(newUser);
      
      // Store the API key to show in modal (this is the ONLY time we get it)
      setNewUserApiKey(createdUser.api_key);
      
      // Close create dialog and open key reveal modal
      setIsCreateDialogOpen(false);
      setIsKeyModalOpen(true);
      
      // Reset form
      setNewUser({ name: '', role: 'member' });
      
      // Reload users list (won't include API keys)
      await loadUsers();
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: err.response?.data?.detail || 'Failed to create user',
      });
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(newUserApiKey);
      toast({
        title: 'Copied!',
        description: 'API key copied to clipboard',
        className: 'bg-green-950 border-green-900 text-green-400',
      });
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Failed to copy',
        description: 'Please copy manually',
      });
    }
  };

  const handleUpdateCredits = async () => {
    const newCredits = parseInt(creditUpdate);
    if (isNaN(newCredits) || newCredits < 0) {
      toast({
        variant: 'destructive',
        title: 'Invalid Input',
        description: 'Please enter a valid number',
      });
      return;
    }

    try {
      await api.updateUserCredits(selectedUser.id, newCredits);
      setUsers(users.map(u => 
        u.id === selectedUser.id ? { ...u, credits: newCredits } : u
      ));
      setIsEditDialogOpen(false);
      setSelectedUser(null);
      setCreditUpdate('');
      
      toast({
        title: 'Credits Updated',
        description: `${selectedUser.name}'s credits set to ${newCredits}`,
        className: 'bg-green-950 border-green-900 text-green-400',
      });
      
      // Reload to reflect changes
      await loadUsers();
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: err.response?.data?.detail || 'Failed to update credits',
      });
    }
  };

  const handleDeleteUser = async (user) => {
    // Prevent deleting self
    if (currentUser && user.id === currentUser.id) {
      toast({
        variant: 'destructive',
        title: 'Cannot Delete',
        description: 'You cannot delete your own account',
      });
      return;
    }

    if (!window.confirm(`Are you sure you want to delete user "${user.name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await api.deleteUser(user.id);
      setUsers(users.filter(u => u.id !== user.id));
      
      toast({
        title: 'User Deleted',
        description: `${user.name} has been removed`,
        className: 'bg-green-950 border-green-900 text-green-400',
      });
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: err.response?.data?.detail || 'Failed to delete user',
      });
    }
  };

  const openEditDialog = (user) => {
    setSelectedUser(user);
    setCreditUpdate(user.credits.toString());
    setIsEditDialogOpen(true);
  };

  return (
    <div className="relative group">
      <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-2xl blur opacity-20" />
      
      <Card className="relative bg-slate-900/80 backdrop-blur-xl border-slate-800">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Users size={24} className="text-cyan-400" />
              <div>
                <CardTitle className="text-white font-mono tracking-wider">User Management</CardTitle>
                <CardDescription className="font-mono text-xs">Create users and manage credits</CardDescription>
              </div>
            </div>
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 font-mono">
                  <Plus size={18} className="mr-2" />
                  Create User
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-slate-900 border-slate-800 text-white">
                <DialogHeader>
                  <DialogTitle className="font-mono text-cyan-400">Create New User</DialogTitle>
                  <DialogDescription className="font-mono text-xs text-slate-400">
                    Generate a new user with API key and credits
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <label className="text-sm font-mono text-slate-400 uppercase tracking-wider">User Name</label>
                    <Input
                      value={newUser.name}
                      onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                      placeholder="Enter user name"
                      className="bg-slate-950 border-slate-700 text-white font-mono"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-mono text-slate-400 uppercase tracking-wider">Role</label>
                    <Select
                      value={newUser.role}
                      onValueChange={(value) => setNewUser({ ...newUser, role: value })}
                    >
                      <SelectTrigger className="bg-slate-950 border-slate-700 text-white font-mono">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-900 border-slate-800 text-white">
                        <SelectItem value="member" className="font-mono">MEMBER</SelectItem>
                        <SelectItem value="admin" className="font-mono">ADMIN</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="p-3 bg-slate-950/50 rounded border border-slate-800">
                    <p className="text-xs text-slate-400 font-mono">Initial credits: 10</p>
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    onClick={handleCreateUser}
                    className="bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 font-mono w-full"
                  >
                    Generate User
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px] pr-4">
            {users.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-slate-500 py-12">
                <Users size={48} className="mb-4 opacity-30" />
                <p className="font-mono text-sm">No users found</p>
              </div>
            ) : (
              <div className="space-y-4">
                {users.map((user) => (
                  <div
                    key={user.id}
                    className="relative group/item bg-slate-950/40 rounded-xl border border-slate-800 p-4 hover:bg-slate-950/60 transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center">
                          <UserCircle size={24} className="text-white" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="text-white font-mono font-bold">{user.name}</h3>
                            <Badge
                              variant="outline"
                              className={`font-mono text-xs ${user.role === 'admin' ? 'bg-purple-500/20 text-purple-400 border-purple-500/50' : 'bg-slate-700 text-slate-300'}`}
                            >
                              {user.role.toUpperCase()}
                            </Badge>
                          </div>
                          <code className="text-xs text-slate-500 font-mono">ID: {user.id.substring(0, 8)}...</code>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="flex items-center gap-2 bg-slate-950 px-4 py-2 rounded-lg border border-slate-800">
                          <Zap size={16} className="text-yellow-400" />
                          <span className="text-lg font-bold font-mono text-white">{user.credits}</span>
                        </div>
                        <div className="flex items-center gap-1 opacity-0 group-hover/item:opacity-100 transition-opacity">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => openEditDialog(user)}
                            className="text-cyan-400 hover:text-cyan-300 hover:bg-cyan-950/30"
                            title="Edit Credits"
                          >
                            <Edit size={18} />
                          </Button>
                          {currentUser && user.id !== currentUser.id && (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleDeleteUser(user)}
                              className="text-red-400 hover:text-red-300 hover:bg-red-950/30"
                              title="Delete User"
                            >
                              <Trash2 size={18} />
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>

          {/* Edit Credits Dialog */}
          <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
            <DialogContent className="bg-slate-900 border-slate-800 text-white">
              <DialogHeader>
                <DialogTitle className="font-mono text-cyan-400">Update Credits</DialogTitle>
                <DialogDescription className="font-mono text-xs text-slate-400">
                  {selectedUser && `Adjust credits for ${selectedUser.name}`}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <label className="text-sm font-mono text-slate-400 uppercase tracking-wider">New Credit Amount</label>
                  <Input
                    type="number"
                    value={creditUpdate}
                    onChange={(e) => setCreditUpdate(e.target.value)}
                    placeholder="Enter credit amount"
                    className="bg-slate-950 border-slate-700 text-white font-mono"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  onClick={handleUpdateCredits}
                  className="bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 font-mono w-full"
                >
                  Update Credits
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {/* API Key Reveal Modal - SHOWN ONLY ONCE */}
          <Dialog open={isKeyModalOpen} onOpenChange={setIsKeyModalOpen}>
            <DialogContent className="bg-slate-900 border-slate-800 text-white max-w-2xl">
              <DialogHeader>
                <DialogTitle className="font-mono text-green-400 text-xl">✓ User Created Successfully</DialogTitle>
                <DialogDescription className="font-mono text-xs text-slate-400">
                  Save this API key now - it will never be shown again
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4 py-6">
                {/* Warning Banner */}
                <div className="bg-red-900/20 border border-red-500 p-4 rounded-lg">
                  <p className="text-red-400 font-mono text-sm font-bold mb-2 flex items-center gap-2">
                    <span className="text-2xl">⚠</span> 
                    WARNING: KEY SHOWN ONCE
                  </p>
                  <p className="text-red-300/80 font-mono text-xs">
                    This is the only time you will see this API key. Copy it now and store it securely.
                  </p>
                </div>

                {/* API Key Display */}
                <div className="space-y-2">
                  <label className="text-sm font-mono text-slate-400 uppercase tracking-wider">API Key</label>
                  <div className="relative">
                    <code className="block text-xl text-green-400 font-mono select-all bg-black p-4 rounded-lg border border-green-500/30 break-all">
                      {newUserApiKey}
                    </code>
                  </div>
                </div>

                {/* Copy Button */}
                <Button
                  onClick={copyToClipboard}
                  className="w-full bg-gradient-to-r from-green-600 to-green-500 hover:from-green-500 hover:to-green-400 font-mono font-bold text-lg h-14"
                >
                  📋 Copy API Key to Clipboard
                </Button>

                {/* Additional Info */}
                <div className="bg-slate-950/50 border border-slate-800 p-4 rounded-lg">
                  <p className="text-slate-400 font-mono text-xs mb-2">
                    <span className="text-cyan-400 font-bold">Next Steps:</span>
                  </p>
                  <ul className="text-slate-400 font-mono text-xs space-y-1 list-disc list-inside">
                    <li>Copy and save this key in a secure location</li>
                    <li>Share it with the user (via secure channel)</li>
                    <li>The user can use this key to log in</li>
                    <li>Once you close this modal, the key cannot be retrieved</li>
                  </ul>
                </div>
              </div>

              <DialogFooter>
                <Button
                  onClick={() => {
                    setIsKeyModalOpen(false);
                    setNewUserApiKey('');
                  }}
                  variant="outline"
                  className="w-full font-mono border-slate-700 hover:bg-slate-800"
                >
                  I've Saved the Key - Close
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>
    </div>
  );
}
