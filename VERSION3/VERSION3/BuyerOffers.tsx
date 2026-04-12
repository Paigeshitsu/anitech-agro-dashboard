import { useState } from "react";
import { motion } from "framer-motion";
import { useAuth } from "@/contexts/AuthContext";
import { useActivityLog } from "@/contexts/ActivityLogContext";
import { ShoppingCart, Check, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";

interface Offer {
  id: number;
  buyerName: string;
  cropName: string;
  offerPrice: number;
  quantity: number;
  contact: string;
  date: string;
  sellerName: string;
  sellerContact: string;
}

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
];

const initialOffers: Offer[] = [
  { id: 1, buyerName: "Carlos Buyer", cropName: "Rice", offerPrice: 24, quantity: 200, contact: "09111111111", date: "2026-04-06", sellerName: "Juan Dela Cruz", sellerContact: "09171234567" },
  { id: 2, buyerName: "Diana Shop", cropName: "Corn", offerPrice: 20, quantity: 100, contact: "09222222222", date: "2026-04-05", sellerName: "Maria Santos", sellerContact: "09181234567" },
];

const BuyerOffers = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const { addLog } = useActivityLog();
  const [offers, setOffers] = useState<Offer[]>(initialOffers);

  const isAdminOrFarmer = user?.role === "admin" || user?.role === "farmer";

  // Buyers should not access this page - redirect handled by menu
  if (user?.role === "buyer") {
    return (
      <div className="bg-card rounded-2xl border border-border p-12 text-center card-shadow">
        <ShoppingCart className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
        <p className="text-muted-foreground">Please visit your Overview dashboard to browse crops and make offers.</p>
      </div>
    );
  }

  const handleAccept = (id: number) => {
    const offer = offers.find((o) => o.id === id);
    setOffers(offers.filter((o) => o.id !== id));
    addLog({ username: user?.username || "", role: user?.role || "", action: `Accepted offer from ${offer?.buyerName} for ${offer?.cropName}`, module: "Offers" });
    toast({ title: "Offer accepted! Transaction saved." });
  };

  const handleDelete = (id: number) => {
    const offer = offers.find((o) => o.id === id);
    setOffers(offers.filter((o) => o.id !== id));
    addLog({ username: user?.username || "", role: user?.role || "", action: `Deleted offer from ${offer?.buyerName}`, module: "Offers" });
    toast({ title: "Offer removed." });
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-heading font-bold text-foreground">💰 Buyer Offers</h1>
        <p className="text-muted-foreground mt-1">Manage incoming buyer offers</p>
      </div>
      {offers.length === 0 ? (
        <div className="bg-card rounded-2xl border border-border p-12 text-center card-shadow">
          <ShoppingCart className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">No pending offers</p>
        </div>
      ) : (
        <div className="space-y-4">
          {offers.map((offer, i) => (
            <motion.div
              key={offer.id}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="bg-card rounded-2xl border border-border p-5 card-shadow flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
            >
              <div className="flex-1 grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
                <div><p className="text-muted-foreground text-xs">Buyer</p><p className="font-medium text-foreground">{offer.buyerName}</p></div>
                <div><p className="text-muted-foreground text-xs">Crop</p><p className="font-medium text-foreground">{offer.cropName}</p></div>
                <div><p className="text-muted-foreground text-xs">Offer</p><p className="font-medium text-foreground">₱{offer.offerPrice}/kg × {offer.quantity}kg</p></div>
                <div><p className="text-muted-foreground text-xs">Contact</p><p className="font-medium text-foreground">{offer.contact}</p></div>
                <div><p className="text-muted-foreground text-xs">Date</p><p className="font-medium text-foreground">{offer.date}</p></div>
              </div>
              {isAdminOrFarmer && (
                <div className="flex gap-2">
                  <Button size="sm" onClick={() => handleAccept(offer.id)}><Check className="w-4 h-4 mr-1" /> Accept</Button>
                  <Button size="sm" variant="destructive" onClick={() => handleDelete(offer.id)}><Trash2 className="w-4 h-4" /></Button>
                </div>
              )}
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

export default BuyerOffers;
