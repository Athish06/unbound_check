import { useState, useEffect } from 'react';
import { Terminal, Shield, Users, ScrollText, LogOut, Zap, Activity } from 'lucide-react';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import TerminalInput from './TerminalInput';
import CommandLog from './CommandLog';
import RuleManager from './RuleManager';
import UserManager from './UserManager';
import { api } from '../services/api';

export default function Dashboard({ apiKey, user, onLogout }) {
  const [credits, setCredits] = useState(user.credits);
  const [commandHistory, setCommandHistory] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const isAdmin = user.role === 'admin';

  useEffect(() => {
    loadCommandHistory();
  }, []);

  const loadCommandHistory = async () => {
    try {
      const history = await api.getCommandHistory(isAdmin);
      setCommandHistory(history);
    } catch (err) {
      console.error('Failed to load command history:', err);
    }
  };

  const handleCommandSubmit = async (commandText) => {
    if (!commandText.trim()) return;

    setIsAnalyzing(true);

    try {
      const result = await api.executeCommand(commandText);
      
      if (result.status === 'INSUFFICIENT_CREDITS') {
        return { error: result.message };
      }

      setCredits(result.remaining_credits);
      
      // Reload command history
      await loadCommandHistory();
      
      return result;
    } catch (err) {
      console.error('Command execution error:', err);
      return { error: err.response?.data?.detail || 'Failed to execute command' };
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCreditsUpdate = (newCredits) => {
    setCredits(newCredits);
  };

  return (
    <div className="min-h-screen p-6 relative overflow-hidden">
      {/* Background grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:4rem_4rem] opacity-30" />
      
      <div className="relative max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <header className="relative group">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-2xl blur opacity-20 group-hover:opacity-30 transition duration-500" />
          <div className="relative bg-slate-900/80 backdrop-blur-xl p-6 rounded-2xl border border-slate-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="relative">
                  <div className="absolute inset-0 bg-cyan-500/20 blur-xl" />
                  <Terminal size={32} className="relative text-cyan-400" strokeWidth={1.5} />
                </div>
                <div>
                  <h1 className="text-2xl font-bold tracking-wider">
                    UNBOUND<span className="text-cyan-400">_GATEWAY</span>
                  </h1>
                  <p className="text-sm text-slate-400 font-mono">
                    {user.name} • {isAdmin ? 'ADMIN' : 'MEMBER'}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="flex items-center gap-3 bg-slate-950/50 px-4 py-2 rounded-xl border border-slate-800">
                  <Zap size={20} className="text-yellow-400" />
                  <div>
                    <p className="text-xs text-slate-500 font-mono uppercase">Credits</p>
                    <p className="text-xl font-bold font-mono text-white">{credits}</p>
                  </div>
                </div>
                <Button
                  onClick={onLogout}
                  variant="ghost"
                  className="text-slate-400 hover:text-white hover:bg-slate-800"
                >
                  <LogOut size={18} />
                </Button>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        {isAdmin ? (
          <Tabs defaultValue="terminal" className="space-y-6">
            <TabsList className="bg-slate-900/50 border border-slate-800 p-1 backdrop-blur-xl">
              <TabsTrigger value="terminal" className="font-mono data-[state=active]:bg-slate-800 data-[state=active]:text-cyan-400">
                <Terminal size={16} className="mr-2" />
                Terminal
              </TabsTrigger>
              <TabsTrigger value="rules" className="font-mono data-[state=active]:bg-slate-800 data-[state=active]:text-cyan-400">
                <Shield size={16} className="mr-2" />
                Rules
              </TabsTrigger>
              <TabsTrigger value="users" className="font-mono data-[state=active]:bg-slate-800 data-[state=active]:text-cyan-400">
                <Users size={16} className="mr-2" />
                Users
              </TabsTrigger>
              <TabsTrigger value="audit" className="font-mono data-[state=active]:bg-slate-800 data-[state=active]:text-cyan-400">
                <ScrollText size={16} className="mr-2" />
                Audit Log
              </TabsTrigger>
            </TabsList>

            <TabsContent value="terminal" className="space-y-6">
              <TerminalInput onSubmit={handleCommandSubmit} isAnalyzing={isAnalyzing} />
              <CommandLog commands={commandHistory} isAdmin={false} />
            </TabsContent>

            <TabsContent value="rules">
              <RuleManager />
            </TabsContent>

            <TabsContent value="users">
              <UserManager onCreditsUpdate={handleCreditsUpdate} currentUser={user} />
            </TabsContent>

            <TabsContent value="audit">
              <CommandLog commands={commandHistory} isAdmin={true} />
            </TabsContent>
          </Tabs>
        ) : (
          <div className="space-y-6">
            <TerminalInput onSubmit={handleCommandSubmit} isAnalyzing={isAnalyzing} />
            <CommandLog commands={commandHistory} isAdmin={false} />
          </div>
        )}
      </div>
    </div>
  );
}
