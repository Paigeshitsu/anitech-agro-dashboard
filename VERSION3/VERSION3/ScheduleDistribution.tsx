import { useState } from "react";
import { motion } from "framer-motion";
import { useAuth } from "@/contexts/AuthContext";
import { useActivityLog } from "@/contexts/ActivityLogContext";
import { Truck, Plus, Package, Wrench, Leaf, Tractor } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";

type MaterialType = "Seeds" | "Fertilizer" | "Machinery" | "Tools";

interface Material {
  id: number;
  type: MaterialType;
  name: string;
  quantity: string;
  addedBy: string;
  date: string;
  status: "Pending" | "Received";
}

const typeIcons: Record<MaterialType, React.ReactNode> = {
  Seeds: <Leaf className="w-5 h-5 text-primary" />,
  Fertilizer: <Package className="w-5 h-5 text-harvest" />,
  Machinery: <Tractor className="w-5 h-5 text-earth" />,
  Tools: <Wrench className="w-5 h-5 text-sky" />,
};

const initialMaterials: Material[] = [
  { id: 1, type: "Seeds", name: "Rice Seeds (IR64)", quantity: "50 bags", addedBy: "Officer Jose", date: "2026-04-05", status: "Received" },
  { id: 2, type: "Fertilizer", name: "Urea 46-0-0", quantity: "100 bags", addedBy: "Officer Jose", date: "2026-04-04", status: "Pending" },
  { id: 3, type: "Machinery", name: "Hand Tractor", quantity: "5 units", addedBy: "Officer Maria", date: "2026-04-03", status: "Received" },
  { id: 4, type: "Tools", name: "Sprayers", quantity: "20 units", addedBy: "Officer Jose", date: "2026-04-02", status: "Pending" },
];

const ScheduleDistribution = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const { addLog } = useActivityLog();
  const [materials, setMaterials] = useState<Material[]>(initialMaterials);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ type: "" as MaterialType | "", name: "", quantity: "" });

  const isOfficer = user?.role === "agri-officer";
  const isAdmin = user?.role === "admin";

  const handleAdd = () => {
    if (!form.type || !form.name || !form.quantity) {
      toast({ title: "Fill all fields", variant: "destructive" });
      return;
    }
    setMaterials([{
      id: Date.now(),
      type: form.type as MaterialType,
      name: form.name,
      quantity: form.quantity,
      addedBy: user?.username || "",
      date: new Date().toISOString().split("T")[0],
      status: "Pending",
    }, ...materials]);
    addLog({ username: user?.username || "", role: user?.role || "", action: `Added material: ${form.name}`, module: "Distribution" });
    setForm({ type: "", name: "", quantity: "" });
    setOpen(false);
    toast({ title: "Material added!" });
  };

  const handleReceive = (id: number) => {
    const mat = materials.find((m) => m.id === id);
    setMaterials(materials.map((m) => m.id === id ? { ...m, status: "Received" as const } : m));
    addLog({ username: user?.username || "", role: user?.role || "", action: `Received material: ${mat?.name}`, module: "Distribution" });
    toast({ title: "Material marked as received!" });
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-heading font-bold text-foreground">🚜 Schedule Distribution</h1>
          <p className="text-muted-foreground mt-1">Agricultural materials management</p>
        </div>
        {isOfficer && (
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild><Button><Plus className="w-4 h-4 mr-2" /> Add Material</Button></DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>Add Material</DialogTitle></DialogHeader>
              <div className="space-y-4 mt-4">
                <div>
                  <Label>Type</Label>
                  <Select value={form.type} onValueChange={(v) => setForm({ ...form, type: v as MaterialType })}>
                    <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                    <SelectContent>
                      {(["Seeds", "Fertilizer", "Machinery", "Tools"] as MaterialType[]).map((t) => (
                        <SelectItem key={t} value={t}>{t}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div><Label>Name</Label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
                <div><Label>Quantity</Label><Input value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} placeholder="e.g. 50 bags" /></div>
                <Button onClick={handleAdd} className="w-full">Add Material</Button>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </div>

      <div className="space-y-4">
        {materials.map((mat, i) => (
          <motion.div
            key={mat.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
            className="bg-card rounded-2xl border border-border p-5 card-shadow flex items-center justify-between"
          >
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-muted flex items-center justify-center">
                {typeIcons[mat.type]}
              </div>
              <div>
                <h3 className="font-heading font-bold text-foreground">{mat.name}</h3>
                <p className="text-xs text-muted-foreground">{mat.type} · {mat.quantity} · by {mat.addedBy}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`text-xs px-3 py-1 rounded-full font-medium ${mat.status === "Received" ? "bg-primary/10 text-primary" : "bg-harvest/10 text-harvest"}`}>
                {mat.status}
              </span>
              {isAdmin && mat.status === "Pending" && (
                <Button size="sm" onClick={() => handleReceive(mat.id)}>Receive</Button>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default ScheduleDistribution;
