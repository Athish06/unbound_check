import { useState } from 'react';
import { Terminal, Key, AlertCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Alert, AlertDescription } from './ui/alert';
import { api } from '../services/api';

export default function Login({ onLogin }) {
  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!apiKey.trim()) {
      setError('Please enter an API key');
      return;
    }

    setLoading(true);
    
    try {
      const response = await api.verifyApiKey(apiKey);
      // Extract user data from response (backend returns { status, user: {...} })
      const userData = response.user || response;
      onLogin(apiKey, userData);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 relative overflow-hidden">
      {/* Animated background grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_50%,#000_70%,transparent_110%)]" />
      
      {/* Glowing orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />

      <div className="relative w-full max-w-md">
        {/* Logo Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="relative">
              <div className="absolute inset-0 bg-cyan-500/20 blur-xl" />
              <Terminal size={48} className="relative text-cyan-400" strokeWidth={1.5} />
            </div>
          </div>
          <h1 className="text-4xl font-bold tracking-wider mb-2">
            UNBOUND<span className="text-cyan-400">_GATEWAY</span>
          </h1>
          <p className="text-slate-400 font-mono text-sm tracking-wider">COMMAND ACCESS CONTROL</p>
        </div>

        {/* Login Card */}
        <div className="relative group">
          {/* Glow effect */}
          <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-500" />
          
          <div className="relative bg-slate-900/80 backdrop-blur-xl rounded-2xl border border-slate-800 p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-mono text-slate-400 uppercase tracking-wider flex items-center gap-2">
                  <Key size={14} />
                  API Key
                </label>
                <div className="relative">
                  <Input
                    type="text"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="Enter your API key..."
                    className="bg-slate-950/50 border-slate-700 text-white font-mono placeholder:text-slate-600 focus:border-cyan-500 focus:ring-cyan-500/20 h-12 px-4"
                    disabled={loading}
                  />
                </div>
              </div>

              {error && (
                <Alert className="bg-red-950/30 border-red-900/50 text-red-400">
                  <AlertCircle size={16} />
                  <AlertDescription className="font-mono text-sm">{error}</AlertDescription>
                </Alert>
              )}

              <Button
                type="submit"
                disabled={loading}
                className="w-full h-12 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white font-mono font-bold tracking-wider uppercase transition-all duration-300"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Authenticating...
                  </span>
                ) : (
                  'Access Gateway'
                )}
              </Button>
            </form>

            {/* Demo Keys Info */}
            <div className="mt-6 pt-6 border-t border-slate-800">
              <p className="text-xs text-slate-500 font-mono mb-3 uppercase tracking-wider">Seed Admin Key:</p>
              <div className="space-y-2">
                <div className="flex items-center justify-between bg-slate-950/50 rounded px-3 py-2 border border-slate-800">
                  <span className="text-xs text-slate-400 font-mono">Admin:</span>
                  <code className="text-xs text-cyan-400 font-mono">admin_key_2025</code>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
