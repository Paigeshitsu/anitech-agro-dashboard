import { useState } from "react";
import { motion } from "framer-motion";
import { useAuth } from "@/contexts/AuthContext";
import { useActivityLog } from "@/contexts/ActivityLogContext";
import {
  Cloud, Sprout, TrendingUp, DollarSign, ShoppingCart, Users, Activity,
  MoreVertical, Send, Scale, MapPin, Phone, User
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { useToast } from "@/hooks/use-toast";

interface CropListing {
  id: number;
  name: string;
  seller: string;
  quantity: number;
  price: number;
  location: string;
  sellerContact: string;
}

const cropListings: CropListing[] = [
  { id: 1, name: "Rice (Palay)", seller: "Juan Dela Cruz", quantity: 500, price: 22, location: "Nueva Ecija", sellerContact: "09171234567" },
  { id: 2, name: "Corn", seller: "Maria Santos", quantity: 300, price: 18, location: "Isabela", sellerContact: "09181234567" },
  { id: 3, name: "Banana", seller: "Luis Garcia", quantity: 600, price: 25, location: "Davao", sellerContact: "09191234567" },
  { id: 4, name: "Mango", seller: "Rosa Tan", quantity: 200, price: 60, location: "Guimaras", sellerContact: "09201234567" },
  { id: 5, name: "Sugarcane", seller: "Pedro Reyes", quantity: 800, price: 15, location: "Tarlac", sellerContact: "09211234567" },
  { id: 6, name: "Coconut", seller: "Ana Lim", quantity: 400, price: 30, location: "Quezon", sellerContact: "09221234567" },
];

const statCards = [
  { label: "Weather Status", value: "Sunny, 28°C", icon: <Cloud className="w-6 h-6" />, color: "bg-sky/10 text-sky" },
  { label: "Active Crops", value: "24", icon: <Sprout className="w-6 h-6" />, color: "bg-primary/10 text-primary" },
  { label: "Crop Demand", value: "High", icon: <TrendingUp className="w-6 h-6" />, color: "bg-harvest/10 text-harvest" },
  { label: "Avg Market Price", value: "₱45.20/kg", icon: <DollarSign className="w-6 h-6" />, color: "bg-earth/10 text-earth" },
  { label: "Pending Offers", value: "8", icon: <ShoppingCart className="w-6 h-6" />, color: "bg-accent/10 text-accent" },
  { label: "Total Users", value: "156", icon: <Users className="w-6 h-6" />, color: "bg-wind/10 text-wind" },
];

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } },
};

const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0 },
};

const Overview = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const { addLog } = useActivityLog();
  const isBuyer = user?.role === "buyer";

  const [makeOfferOpen, setMakeOfferOpen] = useState(false);
  const [selectedCrop, setSelectedCrop] = useState<CropListing | null>(null);
  const [offerForm, setOfferForm] = useState({ price: "", quantity: "", contact: "" });

  const handleMakeOffer = () => {
    if (!selectedCrop || !offerForm.price || !offerForm.quantity || !offerForm.contact) {
      toast({ title: "Please fill all fields", variant: "destructive" });
      return;
    }
    addLog({ username: user?.username || "", role: user?.role || "", action: `Made offer on ${selectedCrop.name}`, module: "Offers" });
    toast({ title: `Offer sent to ${selectedCrop.seller} for ${selectedCrop.name}!` });
    setOfferForm({ price: "", quantity: "", contact: "" });
    setMakeOfferOpen(false);
    setSelectedCrop(null);
  };

  if (isBuyer) {
    return (
      <div>
        <div className="mb-8">
          <h1 className="text-3xl font-heading font-bold text-foreground">
            Welcome back, {user?.username} 👋
          </h1>
          <p className="text-muted-foreground mt-1">Browse available crops and make offers</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {cropListings.map((crop, i) => (
            <motion.div
              key={crop.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="bg-card rounded-2xl border border-border p-5 card-shadow"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                    <Sprout className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-heading font-bold text-foreground">{crop.name}</h3>
                    <p className="text-xs text-muted-foreground">{crop.seller}</p>
                  </div>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon"><MoreVertical className="w-4 h-4" /></Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent>
                    <DropdownMenuItem><User className="w-4 h-4 mr-2" /> {crop.seller}</DropdownMenuItem>
                    <DropdownMenuItem><Phone className="w-4 h-4 mr-2" /> {crop.sellerContact}</DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
              <div className="space-y-2 mb-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground"><Scale className="w-4 h-4" /> {crop.quantity} kg</div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground"><DollarSign className="w-4 h-4" /> ₱{crop.price}/kg</div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground"><MapPin className="w-4 h-4" /> {crop.location}</div>
              </div>
              <Dialog open={makeOfferOpen && selectedCrop?.id === crop.id} onOpenChange={(open) => { setMakeOfferOpen(open); if (!open) setSelectedCrop(null); }}>
                <DialogTrigger asChild>
                  <Button className="w-full" onClick={() => setSelectedCrop(crop)}>
                    <Send className="w-4 h-4 mr-2" /> Make Offer
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader><DialogTitle>Make Offer for {crop.name}</DialogTitle></DialogHeader>
                  <div className="space-y-4 mt-4">
                    <div><Label>Offer Price (₱/kg)</Label><Input type="number" value={offerForm.price} onChange={(e) => setOfferForm({ ...offerForm, price: e.target.value })} /></div>
                    <div><Label>Quantity (kg)</Label><Input type="number" value={offerForm.quantity} onChange={(e) => setOfferForm({ ...offerForm, quantity: e.target.value })} /></div>
                    <div><Label>Contact Number</Label><Input value={offerForm.contact} onChange={(e) => setOfferForm({ ...offerForm, contact: e.target.value })} placeholder="09XX-XXX-XXXX" /></div>
                    <Button onClick={handleMakeOffer} className="w-full">Submit Offer</Button>
                  </div>
                </DialogContent>
              </Dialog>
            </motion.div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-heading font-bold text-foreground">
          Welcome back, {user?.username} 👋
        </h1>
        <p className="text-muted-foreground mt-1">Here's your agricultural overview for today.</p>
      </div>

      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5"
      >
        {statCards.map((card) => (
          <motion.div
            key={card.label}
            variants={item}
            className="bg-card rounded-2xl border border-border p-5 card-shadow hover:card-shadow-hover transition-shadow duration-300"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-muted-foreground">{card.label}</span>
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${card.color}`}>
                {card.icon}
              </div>
            </div>
            <p className="text-2xl font-heading font-bold text-foreground">{card.value}</p>
          </motion.div>
        ))}
      </motion.div>

      <div className="mt-8 bg-card rounded-2xl border border-border p-6 card-shadow">
        <h2 className="text-lg font-heading font-bold text-foreground mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-primary" />
          AI Prediction Summary
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-leaf-light rounded-xl p-4">
            <p className="text-sm text-muted-foreground mb-1">Weather Prediction</p>
            <p className="font-heading font-bold text-foreground">Partly Cloudy</p>
            <p className="text-xs text-primary mt-1">68% rainfall chance tomorrow</p>
          </div>
          <div className="bg-harvest/10 rounded-xl p-4">
            <p className="text-sm text-muted-foreground mb-1">Top Demand Crop</p>
            <p className="font-heading font-bold text-foreground">Rice (Palay)</p>
            <p className="text-xs text-harvest mt-1">Predicted high demand next week</p>
          </div>
          <div className="bg-sky/10 rounded-xl p-4">
            <p className="text-sm text-muted-foreground mb-1">Price Trend</p>
            <p className="font-heading font-bold text-foreground">↑ Upward</p>
            <p className="text-xs text-sky mt-1">Corn prices rising 12% this month</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Overview;
