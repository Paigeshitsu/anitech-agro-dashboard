import { motion } from "framer-motion";
import { useAuth } from "@/contexts/AuthContext";
import { useActivityLog } from "@/contexts/ActivityLogContext";
import { ScrollText, LogIn, Sprout, ShoppingCart, Cloud, Truck, Brain } from "lucide-react";

const moduleIcons: Record<string, React.ReactNode> = {
  Auth: <LogIn className="w-4 h-4" />,
  Crops: <Sprout className="w-4 h-4" />,
  Offers: <ShoppingCart className="w-4 h-4" />,
  Distribution: <Truck className="w-4 h-4" />,
  Weather: <Cloud className="w-4 h-4" />,
  "AI Prediction": <Brain className="w-4 h-4" />,
};

const roleBadge: Record<string, string> = {
  admin: "bg-primary/10 text-primary",
  farmer: "bg-accent/10 text-accent",
  "agri-officer": "bg-harvest/10 text-harvest",
  buyer: "bg-sky/10 text-sky",
};

const ActivityLog = () => {
  const { user } = useAuth();
  const { logs } = useActivityLog();

  const isFullAccess = user?.role === "admin" || user?.role === "agri-officer";
  const filtered = isFullAccess ? logs : logs.filter((l) => l.username === user?.username);

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-heading font-bold text-foreground">📜 Activity Log</h1>
        <p className="text-muted-foreground mt-1">
          {isFullAccess ? "All system activities" : "Your activity history"}
        </p>
      </div>

      <div className="bg-card rounded-2xl border border-border card-shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="text-left p-4 font-medium text-muted-foreground">User</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Role</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Action</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Module</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Date/Time</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((log, i) => (
                <motion.tr
                  key={log.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.03 }}
                  className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors"
                >
                  <td className="p-4 font-medium text-foreground">{log.username}</td>
                  <td className="p-4">
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${roleBadge[log.role] || ""}`}>
                      {log.role}
                    </span>
                  </td>
                  <td className="p-4 text-foreground flex items-center gap-2">
                    {moduleIcons[log.module] || <ScrollText className="w-4 h-4" />} {log.action}
                  </td>
                  <td className="p-4 text-muted-foreground">{log.module}</td>
                  <td className="p-4 text-muted-foreground">{log.datetime}</td>
                </motion.tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-muted-foreground">No activity recorded yet</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ActivityLog;
