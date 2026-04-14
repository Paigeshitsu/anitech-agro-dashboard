import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { DollarSign, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { MARKET_PRICES } from '@/data/mockData';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const TREND_ICONS = { up: TrendingUp, down: TrendingDown, stable: Minus };
const TREND_COLORS = { up: 'text-success', down: 'text-destructive', stable: 'text-muted-foreground' };

const MarketPrices: React.FC = () => {
  const [selected, setSelected] = useState(MARKET_PRICES[0].crop);
  const selectedData = MARKET_PRICES.find(p => p.crop === selected)!;
  const chartData = selectedData.history.map((price, i) => ({
    week: `Week ${i + 1}`,
    price,
  }));
  chartData.push({ week: 'Next', price: selectedData.predicted });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold text-foreground">Market Price Predictions</h1>
        <p className="text-muted-foreground text-sm mt-1">Multiple Linear Regression model for price forecasting</p>
      </div>

      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="stat-card flex items-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center">
          <DollarSign className="w-6 h-6 text-accent" />
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Model: Multiple Linear Regression</p>
          <p className="text-2xl font-bold text-foreground">91% Accuracy</p>
        </div>
      </motion.div>

      {/* Crop selector */}
      <div>
        <label className="text-sm font-medium text-foreground mb-2 block">Select Crop</label>
        <div className="flex flex-wrap gap-2">
          {MARKET_PRICES.map(p => (
            <button
              key={p.crop}
              onClick={() => setSelected(p.crop)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                selected === p.crop ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:text-foreground'
              }`}
            >
              {p.crop}
            </button>
          ))}
        </div>
      </div>

      {/* Selected crop detail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <motion.div key={selected + '-current'} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="stat-card text-center">
          <p className="text-sm text-muted-foreground">Current Price</p>
          <p className="text-3xl font-bold text-foreground mt-1">₱{selectedData.current}</p>
          <p className="text-xs text-muted-foreground mt-1">per kilo</p>
        </motion.div>
        <motion.div key={selected + '-predicted'} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="stat-card text-center">
          <p className="text-sm text-muted-foreground">Predicted Next Week</p>
          <p className="text-3xl font-bold text-primary mt-1">₱{selectedData.predicted}</p>
          <p className="text-xs text-muted-foreground mt-1">per kilo</p>
        </motion.div>
        <motion.div key={selected + '-trend'} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="stat-card flex flex-col items-center justify-center">
          {React.createElement(TREND_ICONS[selectedData.trend], { className: `w-8 h-8 ${TREND_COLORS[selectedData.trend]}` })}
          <p className="text-sm font-semibold text-foreground mt-2 capitalize">{selectedData.trend === 'up' ? 'Increasing' : selectedData.trend === 'down' ? 'Decreasing' : 'Stable'}</p>
        </motion.div>
      </div>

      {/* Price chart */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="stat-card">
        <h3 className="font-heading text-sm font-semibold text-foreground mb-4">{selected} - Price History & Prediction</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="week" tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: 8, fontSize: 12 }} />
              <Line type="monotone" dataKey="price" stroke="hsl(var(--primary))" strokeWidth={2} dot={{ fill: 'hsl(var(--primary))', r: 4 }} name="Price (₱/kg)" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* All crops table */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="stat-card overflow-x-auto">
        <h3 className="font-heading text-sm font-semibold text-foreground mb-4">All Crop Prices</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-2 px-3 text-muted-foreground font-medium">Crop</th>
              <th className="text-right py-2 px-3 text-muted-foreground font-medium">Current (₱)</th>
              <th className="text-right py-2 px-3 text-muted-foreground font-medium">Predicted (₱)</th>
              <th className="text-right py-2 px-3 text-muted-foreground font-medium">Trend</th>
            </tr>
          </thead>
          <tbody>
            {MARKET_PRICES.map(p => {
              const TrendIcon = TREND_ICONS[p.trend];
              return (
                <tr key={p.crop} className="border-b border-border/50">
                  <td className="py-2.5 px-3 font-medium text-foreground">{p.crop}</td>
                  <td className="py-2.5 px-3 text-right text-foreground">₱{p.current}</td>
                  <td className="py-2.5 px-3 text-right text-primary font-medium">₱{p.predicted}</td>
                  <td className="py-2.5 px-3 text-right">
                    <TrendIcon className={`w-4 h-4 inline ${TREND_COLORS[p.trend]}`} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </motion.div>
    </div>
  );
};

export default MarketPrices;
