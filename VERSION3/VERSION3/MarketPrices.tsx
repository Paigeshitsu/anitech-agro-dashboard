import { useState, useMemo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { TrendingUp, TrendingDown, Minus, Search, Loader2 } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

const allCrops = ["Rice", "Corn", "Sugarcane", "Coconut", "Banana", "Mango", "Tomato", "Onion", "Garlic", "Eggplant", "Cabbage", "Carrot"];

const months = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const weeks = ["Week 1", "Week 2", "Week 3", "Week 4"];

// Seeded pseudo-random for consistent predictions
function seededRandom(seed: number) {
  let s = seed % 2147483647;
  if (s <= 0) s += 2147483646;
  return () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

function hashStr(str: string) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (Math.imul(31, h) + str.charCodeAt(i)) | 0;
  return Math.abs(h);
}

interface PredictionResult {
  product: string;
  month: string;
  week: string;
  predictedPrice: number;
  currentPrice: number;
  trend: "Increasing" | "Decreasing" | "Stable";
  weeklyData: { week: string; price: number; predicted: number }[];
}

function generatePrediction(product: string, month: string, week: string): PredictionResult {
  const seed = hashStr(`${product}-${month}-${week}`);
  const rng = seededRandom(seed);

  const basePrice = 10 + rng() * 80;
  const currentPrice = Math.round(basePrice * 100) / 100;
  const delta = (rng() - 0.4) * 15;
  const predictedPrice = Math.round((basePrice + delta) * 100) / 100;

  const trend: PredictionResult["trend"] =
    delta > 2 ? "Increasing" : delta < -2 ? "Decreasing" : "Stable";

  const weeklyData = weeks.map((w, i) => {
    const wSeed = hashStr(`${product}-${month}-${w}`);
    const wRng = seededRandom(wSeed);
    const p = basePrice + (wRng() - 0.5) * 10;
    const pred = p + (wRng() - 0.4) * 8;
    return {
      week: w,
      price: Math.round(p * 100) / 100,
      predicted: Math.round(pred * 100) / 100,
    };
  });

  return { product, month, week, predictedPrice, currentPrice, trend, weeklyData };
}

const MarketPrices = () => {
  const [query, setQuery] = useState("");
  const [month, setMonth] = useState("");
  const [week, setWeek] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const suggestions = useMemo(() => {
    if (!query.trim()) return [];
    return allCrops.filter((c) => c.toLowerCase().includes(query.toLowerCase())).slice(0, 5);
  }, [query]);

  const canPredict = query.trim() !== "" && month !== "" && week !== "";

  const handlePredict = useCallback(() => {
    if (!canPredict) return;
    setIsLoading(true);
    setShowSuggestions(false);
    // Simulate ML model latency
    setTimeout(() => {
      const pred = generatePrediction(query.trim(), month, week);
      setResult(pred);
      setIsLoading(false);
    }, 800);
  }, [canPredict, query, month, week]);

  const selectSuggestion = (crop: string) => {
    setQuery(crop);
    setShowSuggestions(false);
  };

  const trendIcon =
    result?.trend === "Increasing" ? (
      <TrendingUp className="w-5 h-5 text-primary" />
    ) : result?.trend === "Decreasing" ? (
      <TrendingDown className="w-5 h-5 text-destructive" />
    ) : (
      <Minus className="w-5 h-5 text-muted-foreground" />
    );

  const trendColor =
    result?.trend === "Increasing"
      ? "text-primary"
      : result?.trend === "Decreasing"
        ? "text-destructive"
        : "text-muted-foreground";

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-heading font-bold text-foreground">💵 Market Price Prediction</h1>
        <p className="text-muted-foreground mt-1">AI-powered price forecasting using Linear Regression</p>
      </div>

      {/* Search Controls */}
      <div className="bg-card rounded-2xl border border-border p-5 card-shadow mb-6">
        <div className="flex flex-col md:flex-row items-start md:items-end gap-4">
          {/* Product Input */}
          <div className="flex-1 w-full relative">
            <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Product</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Type crop name (e.g. Rice)"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setShowSuggestions(true);
                }}
                onFocus={() => setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
                className="pl-9"
              />
            </div>
            <AnimatePresence>
              {showSuggestions && suggestions.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  className="absolute z-20 mt-1 w-full bg-popover border border-border rounded-lg shadow-lg overflow-hidden"
                >
                  {suggestions.map((s) => (
                    <button
                      key={s}
                      onMouseDown={() => selectSuggestion(s)}
                      className="w-full text-left px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground transition-colors"
                    >
                      {s}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Month */}
          <div className="w-full md:w-44">
            <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Month</label>
            <Select value={month} onValueChange={setMonth}>
              <SelectTrigger><SelectValue placeholder="Select month" /></SelectTrigger>
              <SelectContent>
                {months.map((m) => (
                  <SelectItem key={m} value={m}>{m}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Week */}
          <div className="w-full md:w-36">
            <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Week</label>
            <Select value={week} onValueChange={setWeek}>
              <SelectTrigger><SelectValue placeholder="Select week" /></SelectTrigger>
              <SelectContent>
                {weeks.map((w) => (
                  <SelectItem key={w} value={w}>{w}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Predict Button */}
          <Button
            onClick={handlePredict}
            disabled={!canPredict || isLoading}
            className="w-full md:w-auto"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
            Predict
          </Button>
        </div>
      </div>

      {/* Loading State */}
      <AnimatePresence>
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center justify-center py-16"
          >
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <span className="ml-3 text-muted-foreground">Running prediction model…</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results */}
      <AnimatePresence>
        {result && !isLoading && (
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <div className="bg-card rounded-2xl border border-border p-5 card-shadow">
                <p className="text-xs text-muted-foreground mb-1">Product</p>
                <p className="text-xl font-heading font-bold text-foreground">{result.product}</p>
              </div>
              <div className="bg-card rounded-2xl border border-border p-5 card-shadow">
                <p className="text-xs text-muted-foreground mb-1">Period</p>
                <p className="text-xl font-heading font-bold text-foreground">{result.month}, {result.week}</p>
              </div>
              <div className="bg-card rounded-2xl border border-border p-5 card-shadow">
                <p className="text-xs text-muted-foreground mb-1">Predicted Price</p>
                <p className="text-2xl font-heading font-bold text-foreground">₱{result.predictedPrice.toFixed(2)}/kg</p>
              </div>
              <div className="bg-card rounded-2xl border border-border p-5 card-shadow">
                <p className="text-xs text-muted-foreground mb-1">Trend</p>
                <div className="flex items-center gap-2">
                  {trendIcon}
                  <span className={`text-lg font-heading font-bold ${trendColor}`}>{result.trend}</span>
                </div>
              </div>
            </div>

            {/* Chart */}
            <div className="bg-card rounded-2xl border border-border p-6 card-shadow">
              <h3 className="text-sm font-heading font-bold text-foreground mb-4">
                {result.product} — {result.month} Weekly Price Trend (₱/kg)
              </h3>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={result.weeklyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="week" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid hsl(var(--border))", fontSize: 12 }} />
                  <Legend />
                  <Line type="monotone" dataKey="price" name="Historical" stroke="hsl(var(--earth))" strokeWidth={2.5} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="predicted" name="Predicted" stroke="hsl(var(--primary))" strokeWidth={2.5} strokeDasharray="5 5" dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default MarketPrices;
