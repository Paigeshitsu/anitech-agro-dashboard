import React from 'react';
import { sampleLogs } from '@/data/mockData';
import { useAuth } from '@/contexts/AuthContext';
import { FileText } from 'lucide-react';

const ActivityLog: React.FC = () => {
  const { user } = useAuth();
  const logs = user?.role === 'admin' || user?.role === 'agri-officer'
    ? sampleLogs
    : sampleLogs.filter(l => l.username === user?.username || l.role.toLowerCase() === user?.role);

  return (
    <div className="agri-card">
      <h4 className="text-heading text-foreground mb-4 flex items-center gap-2">
        <FileText className="w-5 h-5 text-primary" /> Activity Log
      </h4>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              {['Username', 'Role', 'Action', 'Module', 'Date/Time'].map(h => (
                <th key={h} className="text-left py-3 px-3 text-muted-foreground font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {logs.map(log => (
              <tr key={log.id} className="border-b border-border last:border-0 hover:bg-muted/50">
                <td className="py-3 px-3 text-foreground font-medium">{log.username}</td>
                <td className="py-3 px-3"><span className="text-xs px-2 py-0.5 rounded-full bg-accent text-accent-foreground">{log.role}</span></td>
                <td className="py-3 px-3 text-foreground">{log.action}</td>
                <td className="py-3 px-3 text-muted-foreground">{log.module}</td>
                <td className="py-3 px-3 text-muted-foreground">{log.dateTime}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ActivityLog;
