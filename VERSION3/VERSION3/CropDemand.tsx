import { motion } from "framer-motion";
import { TrendingUp, ArrowUp, ArrowDown, Minus } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, PieChart, Pie, Cell } from "recharts";

const demandData = [
  { crop: "Rice", demand: 92, trend: "up", season: "Wet", recommendation: "Highly Recommended" },
  { crop: "Corn", demand: 78, trend: "up", season: "Dry", recommendation: "Recommended" },
  { crop: "Sugarcane", demand: 65, trend: "stable", season: "All Year", recommendation: "Moderate" },
  { crop: "Coconut", demand: 55, trend: "down", season: "All Year", recommendation: "Low Priority" },
  { crop: "Banana", demand: 70, trend: "up", season: "All Year", recommendation: "Recommended" },
  { crop: "Mango", demand: 85, trend: "up", season: "Dry", recommendation: "Highly Recommended" },
];

const chartData = demandData.map((d) => ({ name: d.crop, Demand: d.demand }));
const COLORS = ["hsl(142,55%,35%)", "hsl(38,80%,55%)", "hsl(200,70%,50%)", "hsl(25,50%,40%)", "hsl(270,50%,55%)", "hsl(15,80%,55%)"];

const trendIcon = (t: string) => {
  if (t === "up") return <ArrowUp className="w-4 h-4 text-primary" />;
  if (t === "down") return <ArrowDown className="w-4 h-4 text-destructive" />;
  return <Minus className="w-4 h-4 text-muted-foreground" />;
};

const CropDemand = () => (
  <div>
    <div className="mb-8">
      <h1 className="text-3xl font-heading font-bold text-foreground">📈 Crop Demand Prediction</h1>
      <p className="text-muted-foreground mt-1">AI-predicted crop demand based on weather, season, and market trends</p>
    </div>

    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
      {demandData.map((d, i) => (
        <motion.div
          key={d.crop}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.05 }}
          className="bg-card rounded-2xl border border-border p-5 card-shadow"
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-heading font-bold text-foreground">{d.crop}</h3>
            {trendIcon(d.trend)}
          </div>
          <div className="flex items-end gap-2 mb-2">
            <span className="text-3xl font-heading font-bold text-foreground">{d.demand}%</span>
            <span className="text-xs text-muted-foreground mb-1">demand index</span>
          </div>
          <div className="w-full bg-muted rounded-full h-2 mb-3">
            <div className="h-2 rounded-full bg-primary transition-all" style={{ width: `${d.demand}%` }} />
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Season: {d.season}</span>
            <span className={d.recommendation.includes("High") ? "text-primary font-medium" : ""}>{d.recommendation}</span>
          </div>
        </motion.div>
      ))}
    </div>

    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-card rounded-2xl border border-border p-6 card-shadow">
        <h3 className="text-sm font-heading font-bold text-foreground mb-4">Demand Index by Crop</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} />
            <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
            <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid hsl(var(--border))", fontSize: 12 }} />
            <Bar dataKey="Demand" radius={[8, 8, 0, 0]}>
              {chartData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="bg-card rounded-2xl border border-border p-6 card-shadow">
        <h3 className="text-sm font-heading font-bold text-foreground mb-4">Demand Distribution</h3>
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie data={chartData} dataKey="Demand" nameKey="name" cx="50%" cy="50%" outerRadius={100} label={({ name, value }) => `${name}: ${value}%`} labelLine={false}>
              {chartData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  </div>
);

export default CropDemand;
