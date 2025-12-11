import { useState } from 'react';
import { Terminal, Send, Activity } from 'lucide-react';
import { Button } from './ui/button';
import { useToast } from '../hooks/use-toast';

export default function TerminalInput({ onSubmit, isAnalyzing }) {
  const [command, setCommand] = useState('');
  const { toast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!command.trim() || isAnalyzing) return;

    const result = await onSubmit(command);
    
    if (result.error) {
      toast({
        variant: 'destructive',
        title: 'Command Failed',
        description: result.error,
      });
    } else if (result.status === 'EXECUTED') {
      toast({
        title: 'Command Executed',
        description: `Successfully executed: ${command}`,
        className: 'bg-green-950 border-green-900 text-green-400',
      });
    } else if (result.status === 'BLOCKED') {
      toast({
        variant: 'destructive',
        title: 'Command Blocked',
        description: `Security policy prevented execution`,
      });
    } else if (result.status === 'NO_MATCH') {
      toast({
        title: 'No Rule Match',
        description: 'Command did not match any configured rules',
        className: 'bg-yellow-950 border-yellow-900 text-yellow-400',
      });
    }

    setCommand('');
  };

  return (
    <section className="relative group">
      <div className={`absolute -inset-0.5 rounded-2xl blur opacity-30 transition duration-1000 group-hover:opacity-50
        ${isAnalyzing ? 'bg-gradient-to-r from-purple-600 to-pink-600 animate-pulse' : 'bg-gradient-to-r from-cyan-500 to-cyan-600'}`}
      />
      
      <div className="relative bg-slate-900/80 backdrop-blur-xl rounded-2xl border border-slate-800 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Terminal size={20} className="text-cyan-400" />
          <h2 className="font-mono text-sm uppercase tracking-wider text-slate-400">Command Terminal</h2>
          {isAnalyzing && (
            <div className="ml-auto flex items-center gap-2 text-purple-400 animate-pulse">
              <Activity size={16} className="animate-spin" />
              <span className="text-xs font-mono">ANALYZING...</span>
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="flex items-center gap-4">
          <div className="flex-1 relative">
            <div className="flex items-center bg-slate-950/70 rounded-xl border border-slate-800 px-4 py-3 focus-within:border-cyan-500 transition-colors">
              <span className="text-green-500 font-mono mr-3 text-lg select-none">$</span>
              <input
                type="text"
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                placeholder="Enter system command..."
                className="bg-transparent border-none outline-none text-white font-mono text-lg w-full placeholder:text-slate-600"
                disabled={isAnalyzing}
                autoFocus
              />
            </div>
          </div>

          <Button
            type="submit"
            disabled={!command.trim() || isAnalyzing}
            className="h-12 px-6 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed font-mono font-bold"
          >
            <Send size={18} className="mr-2" />
            Execute
          </Button>
        </form>

        <div className="mt-4 flex items-start gap-2 text-xs text-slate-500 font-mono">
          <div className="mt-0.5">ℹ</div>
          <p>
            Commands are matched against configured rules. Safe commands execute automatically.
            Each execution costs 1 credit.
          </p>
        </div>
      </div>
    </section>
  );
}
