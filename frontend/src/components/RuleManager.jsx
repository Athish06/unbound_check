import { useState, useEffect } from 'react';
import { Shield, Plus, Trash2, CheckCircle, XCircle, Edit2 } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
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

export default function RuleManager() {
  const [rules, setRules] = useState([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [formData, setFormData] = useState({
    pattern: '',
    action: 'AUTO_ACCEPT',
    description: '',
    is_active: true
  });
  const { toast } = useToast();

  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    try {
      const rulesData = await api.getRules();
      setRules(rulesData);
    } catch (err) {
      console.error('Failed to load rules:', err);
    }
  };

  const handleOpenDialog = (rule = null) => {
    if (rule) {
      setEditingRule(rule);
      setFormData({
        pattern: rule.pattern,
        action: rule.action,
        description: rule.description || '',
        is_active: rule.is_active !== undefined ? rule.is_active : true
      });
    } else {
      setEditingRule(null);
      setFormData({
        pattern: '',
        action: 'AUTO_ACCEPT',
        description: '',
        is_active: true
      });
    }
    setIsDialogOpen(true);
  };

  const handleSaveRule = async () => {
    if (!formData.pattern.trim()) {
      toast({
        variant: 'destructive',
        title: 'Validation Error',
        description: 'Pattern is required',
      });
      return;
    }

    // Validate regex
    try {
      new RegExp(formData.pattern);
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Invalid Regex',
        description: 'Please provide a valid regular expression pattern',
      });
      return;
    }

    try {
      if (editingRule) {
        // Update existing rule
        const updatedRule = await api.updateRule(editingRule.id, formData);
        setRules(rules.map(r => r.id === editingRule.id ? updatedRule : r));
        toast({
          title: 'Rule Updated',
          description: 'Rule configuration has been updated successfully',
          className: 'bg-green-950 border-green-900 text-green-400',
        });
      } else {
        // Create new rule
        const addedRule = await api.createRule(formData);
        setRules([addedRule, ...rules]); // Add to top, though backend sorts by order
        // Reload to get correct order if needed, but this is fine for now
        toast({
          title: 'Rule Added',
          description: 'New rule has been configured successfully',
          className: 'bg-green-950 border-green-900 text-green-400',
        });
      }
      setIsDialogOpen(false);
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: err.response?.data?.detail || 'Failed to save rule',
      });
    }
  };

  const handleDeleteRule = async (ruleId) => {
    try {
      await api.deleteRule(ruleId);
      setRules(rules.filter(r => r.id !== ruleId));
      toast({
        title: 'Rule Deleted',
        description: 'Rule has been removed from the system',
      });
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: err.response?.data?.detail || 'Failed to delete rule',
      });
    }
  };

  return (
    <div className="relative group">
      <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-2xl blur opacity-20" />

      <Card className="relative bg-slate-900/80 backdrop-blur-xl border-slate-800">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield size={24} className="text-cyan-400" />
              <div>
                <CardTitle className="text-white font-mono tracking-wider">Rule Configuration</CardTitle>
                <CardDescription className="font-mono text-xs">Define command execution policies</CardDescription>
              </div>
            </div>
            <Button
              onClick={() => handleOpenDialog()}
              className="bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 font-mono"
            >
              <Plus size={18} className="mr-2" />
              Add Rule
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px] pr-4">
            {rules.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-slate-500 py-12">
                <Shield size={48} className="mb-4 opacity-30" />
                <p className="font-mono text-sm">No rules configured</p>
              </div>
            ) : (
              <div className="space-y-4">
                {rules.map((rule, index) => (
                  <div
                    key={rule.id}
                    className="relative group/item bg-slate-950/40 rounded-xl border border-slate-800 p-4 hover:bg-slate-950/60 transition-all"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-3">
                          <Badge variant="outline" className="font-mono text-xs text-slate-400">
                            #{index + 1}
                          </Badge>
                          {rule.action === 'AUTO_ACCEPT' ? (
                            <Badge className="bg-green-500/20 text-green-400 border-green-500/50 font-mono text-xs">
                              <CheckCircle size={12} className="mr-1" />
                              AUTO_ACCEPT
                            </Badge>
                          ) : (
                            <Badge className="bg-red-500/20 text-red-400 border-red-500/50 font-mono text-xs">
                              <XCircle size={12} className="mr-1" />
                              AUTO_REJECT
                            </Badge>
                          )}
                          {!rule.is_active && (
                            <Badge variant="secondary" className="font-mono text-xs">Inactive</Badge>
                          )}
                        </div>
                        <code className="block text-cyan-400 font-mono text-sm bg-slate-950 px-3 py-2 rounded border border-slate-800">
                          {rule.pattern}
                        </code>
                        {rule.description && (
                          <p className="text-sm text-slate-400">{rule.description}</p>
                        )}
                        <p className="text-xs text-slate-600 font-mono">
                          Created: {new Date(rule.created_at).toLocaleString()}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 opacity-0 group-hover/item:opacity-100 transition-opacity">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleOpenDialog(rule)}
                          className="text-cyan-400 hover:text-cyan-300 hover:bg-cyan-950/30"
                        >
                          <Edit2 size={18} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDeleteRule(rule.id)}
                          className="text-red-400 hover:text-red-300 hover:bg-red-950/30"
                        >
                          <Trash2 size={18} />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="font-mono text-cyan-400">
              {editingRule ? 'Edit Rule' : 'Create New Rule'}
            </DialogTitle>
            <DialogDescription className="font-mono text-xs text-slate-400">
              Define a regex pattern to match commands and set the action
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-mono text-slate-400 uppercase tracking-wider">Pattern (Regex)</label>
              <Input
                value={formData.pattern}
                onChange={(e) => setFormData({ ...formData, pattern: e.target.value })}
                placeholder="^git (pull|fetch|status)"
                className="bg-slate-950 border-slate-700 text-white font-mono"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-mono text-slate-400 uppercase tracking-wider">Action</label>
              <Select
                value={formData.action}
                onValueChange={(value) => setFormData({ ...formData, action: value })}
              >
                <SelectTrigger className="bg-slate-950 border-slate-700 text-white font-mono">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800 text-white">
                  <SelectItem value="AUTO_ACCEPT" className="font-mono">AUTO_ACCEPT</SelectItem>
                  <SelectItem value="AUTO_REJECT" className="font-mono">AUTO_REJECT</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-mono text-slate-400 uppercase tracking-wider">Description</label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Describe what this rule does..."
                className="bg-slate-950 border-slate-700 text-white font-mono min-h-[80px]"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              onClick={handleSaveRule}
              className="bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 font-mono w-full"
            >
              {editingRule ? 'Update Rule' : 'Create Rule'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
