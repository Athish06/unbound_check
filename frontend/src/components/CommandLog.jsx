import { CheckCircle, ShieldAlert, HelpCircle, User, Clock, Terminal } from 'lucide-react';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';

export default function CommandLog({ commands, isAdmin }) {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'EXECUTED':
        return <CheckCircle size={18} className="text-green-500" />;
      case 'BLOCKED':
        return <ShieldAlert size={18} className="text-red-500" />;
      default:
        return <HelpCircle size={18} className="text-yellow-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'EXECUTED':
        return 'border-green-500';
      case 'BLOCKED':
        return 'border-red-500';
      default:
        return 'border-yellow-500';
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <section className="relative group">
      <div className="absolute -inset-0.5 bg-gradient-to-r from-slate-700 to-slate-800 rounded-2xl blur opacity-20" />

      <div className="relative bg-slate-900/80 backdrop-blur-xl rounded-2xl border border-slate-800 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Clock size={20} className="text-cyan-400" />
          <h2 className="font-mono text-sm uppercase tracking-wider text-slate-400">
            {isAdmin ? 'System Audit Log' : 'Command History'}
          </h2>
          <Badge variant="outline" className="ml-auto font-mono text-xs">
            {commands.length} {commands.length === 1 ? 'Entry' : 'Entries'}
          </Badge>
        </div>

        <ScrollArea className="h-[400px] pr-4">
          {commands.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-500">
              <Terminal size={48} className="mb-4 opacity-30" />
              <p className="font-mono text-sm">No commands executed yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {commands.map((cmd) => (
                <div
                  key={cmd.id}
                  className={`flex flex-col gap-2 p-4 rounded-xl border-l-4 bg-slate-950/40 backdrop-blur-sm hover:bg-slate-950/60 transition-colors ${getStatusColor(cmd.status)}`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3 flex-1">
                      <div className="mt-0.5">{getStatusIcon(cmd.status)}</div>
                      <div className="flex-1 min-w-0">
                        <code className="text-slate-200 font-mono text-sm block break-all">
                          {cmd.command_text}
                        </code>
                        <div className="flex items-center gap-3 mt-2">
                          {cmd.verdict_source && (
                            <Badge variant="secondary" className="font-mono text-[10px] h-5">
                              {cmd.verdict_source}
                            </Badge>
                          )}
                          {cmd.risk_score > 0 && (
                            <span className={`text-xs font-mono ${cmd.risk_score >= 100 ? 'text-red-400' : 'text-yellow-400'}`}>
                              Risk: {cmd.risk_score}
                            </span>
                          )}
                          {isAdmin && cmd.user_name && (
                            <div className="flex items-center gap-1 text-xs text-slate-500 ml-auto">
                              <User size={12} />
                              <span className="font-mono">{cmd.user_name}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-2">
                      <Badge
                        variant="outline"
                        className={`font-mono text-xs whitespace-nowrap
                          ${cmd.status === 'EXECUTED'
                            ? 'bg-green-500/10 text-green-400 border-green-500/50'
                            : cmd.status === 'BLOCKED'
                              ? 'bg-red-500/10 text-red-400 border-red-500/50'
                              : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/50'
                          }`}
                      >
                        {cmd.status}
                      </Badge>
                      <span className="text-xs text-slate-500 font-mono">
                        {formatTimestamp(cmd.timestamp)}
                      </span>
                      {cmd.credits_used > 0 && (
                        <span className="text-xs text-yellow-400 font-mono">
                          -{cmd.credits_used} credit
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>
    </section>
  );
}
