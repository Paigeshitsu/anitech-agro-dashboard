import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { CropPrice } from '../types/market';
import { formatPrice, AGRO_GREEN_COLORS } from '../utils/formatters';

interface PriceChartProps {
  data: CropPrice[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
        <p className="font-bold text-gray-800">{label}</p>
        <p className="text-lg font-semibold text-green-600">{formatPrice(data.price)}</p>
        <p className="text-sm text-gray-500">{data.unit || 'PHP/kg'}</p>
      </div>
    );
  }
  return null;
};

const PriceChart = ({ data }: PriceChartProps) => {
  return (
    <div className="h-[400px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" fontSize={12} label={{ value: 'Crop Name', position: 'insideBottom', offset: -5 }} />
          <YAxis tickFormatter={formatPrice} label={{ value: 'Current Price (PHP)', angle: -90, position: 'insideLeft' }} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: '#f3f4f6' }} />
          <Bar dataKey="price" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={AGRO_GREEN_COLORS[index % AGRO_GREEN_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PriceChart;

