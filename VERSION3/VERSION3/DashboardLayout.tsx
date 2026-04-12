import { ReactNode } from "react";
import { useAuth, UserRole } from "@/contexts/AuthContext";
import { useNavigate, useLocation, Link } from "react-router-dom";
import {
  LayoutDashboard, Cloud, Sprout, TrendingUp, DollarSign, Truck,
  ShoppingCart, ScrollText, LogOut, Leaf, Package, Users
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface MenuItem {
  label: string;
  icon: ReactNode;
  path: string;
}

const menuByRole: Record<UserRole, MenuItem[]> = {
  admin: [
    { label: "Overview", icon: <LayoutDashboard className="w-5 h-5" />, path: "/dashboard" },
    { label: "Weather Forecast", icon: <Cloud className="w-5 h-5" />, path: "/dashboard/weather" },
    { label: "Available Crops", icon: <Sprout className="w-5 h-5" />, path: "/dashboard/crops" },
    { label: "Crop Demand", icon: <TrendingUp className="w-5 h-5" />, path: "/dashboard/demand" },
    { label: "Market Prices", icon: <DollarSign className="w-5 h-5" />, path: "/dashboard/prices" },
    { label: "Schedule Distribution", icon: <Truck className="w-5 h-5" />, path: "/dashboard/distribution" },
    { label: "Buyer Offers", icon: <ShoppingCart className="w-5 h-5" />, path: "/dashboard/offers" },
    { label: "Activity Log", icon: <ScrollText className="w-5 h-5" />, path: "/dashboard/logs" },
  ],
  farmer: [
    { label: "Overview", icon: <LayoutDashboard className="w-5 h-5" />, path: "/dashboard" },
    { label: "Weather Forecast", icon: <Cloud className="w-5 h-5" />, path: "/dashboard/weather" },
    { label: "Available Crops", icon: <Sprout className="w-5 h-5" />, path: "/dashboard/crops" },
    { label: "Crop Demand", icon: <TrendingUp className="w-5 h-5" />, path: "/dashboard/demand" },
    { label: "Market Prices", icon: <DollarSign className="w-5 h-5" />, path: "/dashboard/prices" },
    { label: "Schedule Distribution", icon: <Truck className="w-5 h-5" />, path: "/dashboard/distribution" },
    { label: "Buyer Offers", icon: <ShoppingCart className="w-5 h-5" />, path: "/dashboard/offers" },
    { label: "Activity Log", icon: <ScrollText className="w-5 h-5" />, path: "/dashboard/logs" },
  ],
  "agri-officer": [
    { label: "Overview", icon: <LayoutDashboard className="w-5 h-5" />, path: "/dashboard" },
    { label: "Schedule Distribution", icon: <Truck className="w-5 h-5" />, path: "/dashboard/distribution" },
    { label: "Activity Log", icon: <ScrollText className="w-5 h-5" />, path: "/dashboard/logs" },
  ],
  buyer: [
    { label: "Overview", icon: <LayoutDashboard className="w-5 h-5" />, path: "/dashboard" },
    { label: "Activity Log", icon: <ScrollText className="w-5 h-5" />, path: "/dashboard/logs" },
  ],
};

const DashboardLayout = ({ children }: { children: ReactNode }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  if (!user) return null;

  const menu = menuByRole[user.role];

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const roleBadgeColor: Record<UserRole, string> = {
    admin: "bg-primary/20 text-primary",
    farmer: "bg-accent/20 text-accent",
    "agri-officer": "bg-harvest/20 text-harvest",
    buyer: "bg-sky/20 text-sky",
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className="w-64 bg-sidebar flex flex-col border-r border-sidebar-border shrink-0">
        <div className="p-5 flex items-center gap-3 border-b border-sidebar-border">
          <div className="w-10 h-10 rounded-xl bg-sidebar-primary flex items-center justify-center">
            <Leaf className="w-6 h-6 text-sidebar-primary-foreground" />
          </div>
          <div>
            <h2 className="text-sm font-heading font-bold text-sidebar-foreground">ANITECH</h2>
            <p className="text-[10px] text-sidebar-foreground/60 tracking-wider">AgriTech System</p>
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {menu.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? "bg-sidebar-accent text-sidebar-primary"
                    : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
                }`}
              >
                {item.icon}
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-sidebar-border space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-sidebar-accent flex items-center justify-center text-sidebar-foreground text-xs font-bold">
              {user.username[0]?.toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-sidebar-foreground truncate">{user.username}</p>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${roleBadgeColor[user.role]}`}>
                {user.role}
              </span>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="w-full justify-start text-sidebar-foreground/60 hover:text-sidebar-foreground hover:bg-sidebar-accent/50"
          >
            <LogOut className="w-4 h-4 mr-2" />
            Sign Out
          </Button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-6 lg:p-8">
          {children}
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;
