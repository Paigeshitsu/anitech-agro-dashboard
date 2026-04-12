import { useState } from "react";
import { motion } from "framer-motion";
import { useAuth } from "@/contexts/AuthContext";
import { Sprout, Plus, MapPin, Scale, DollarSign } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";

interface Crop {
  id: number;
  name: string;
  seller: string;
  quantity: number;
  price: number;
  location: string;
  addedBy: string;
}

const initialCrops: Crop[] = [
  { id: 1, name: "Rice (Palay)", seller: "Juan Dela Cruz", quantity: 500, price: 22, location: "Nueva Ecija", addedBy: "admin" },
  { id: 2, name: "Corn", seller: "Maria Santos", quantity: 300, price: 18, location: "Isabela", addedBy: "farmer" },
  { id: 3, name: "Sugarcane", seller: "Pedro Reyes", quantity: 800, price: 12, location: "Tarlac", addedBy: "admin" },
  { id: 4, name: "Coconut", seller: "Ana Lim", quantity: 1200, price: 15, location: "Quezon", addedBy: "farmer" },
  { id: 5, name: "Banana", seller: "Luis Garcia", quantity: 600, price: 25, location: "Davao", addedBy: "farmer" },
  { id: 6, name: "Mango", seller: "Rosa Tan", quantity: 200, price: 60, location: "Guimaras", addedBy: "admin" },
];

const AvailableCrops = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [crops, setCrops] = useState<Crop[]>(initialCrops);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", quantity: "", price: "", location: "" });

  const canAdd = user?.role === "admin" || user?.role === "farmer";

  const handleAdd = () => {
    if (!form.name || !form.quantity || !form.price || !form.location) {
      toast({ title: "Please fill all fields", variant: "destructive" });
      return;
    }
    const newCrop: Crop = {
      id: Date.now(),
      name: form.name,
      seller: user?.username || "",
      quantity: Number(form.quantity),
      price: Number(form.price),
      location: form.location,
      addedBy: user?.role || "",
    };
    setCrops([newCrop, ...crops]);
    setForm({ name: "", quantity: "", price: "", location: "" });
    setOpen(false);
    toast({ title: "Crop added successfully!" });
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-heading font-bold text-foreground">🌱 Available Crops</h1>
          <p className="text-muted-foreground mt-1">Browse and manage crop listings</p>
        </div>
        {canAdd && (
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button><Plus className="w-4 h-4 mr-2" /> Add Crop</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>Add New Crop</DialogTitle></DialogHeader>
              <div className="space-y-4 mt-4">
                <div><Label>Crop Name</Label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. Rice" /></div>
                <div><Label>Quantity (kg)</Label><Input type="number" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} /></div>
                <div><Label>Price (₱/kg)</Label><Input type="number" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} /></div>
                <div><Label>Location</Label><Input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} /></div>
                <Button onClick={handleAdd} className="w-full">Add Crop</Button>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {crops.map((crop, i) => (
          <motion.div
            key={crop.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="bg-card rounded-2xl border border-border p-5 card-shadow hover:card-shadow-hover transition-shadow"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                <Sprout className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h3 className="font-heading font-bold text-foreground">{crop.name}</h3>
                <p className="text-xs text-muted-foreground">by {crop.seller}</p>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Scale className="w-4 h-4" /> {crop.quantity} kg
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <DollarSign className="w-4 h-4" /> ₱{crop.price}/kg
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <MapPin className="w-4 h-4" /> {crop.location}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default AvailableCrops;
