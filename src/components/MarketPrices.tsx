import React from 'react';
import { useAgroData, ExtendedAgroData } from '../hooks/useAgroData';
import Card from './ui/Card';
import PriceChart from './PriceChart';
import { formatPrice, getUnit } from '../utils/formatters';
import { CropPrice } from '../types/market';

const MarketPrices = () => {
  const { marketPrices: { data, loading, error }, refetch } = useAgroData() as ExtendedAgroData;

  const handleRefresh = () => {
    refetch();
  };

  if (loading) {
    return (
      <Card title="Market Crop Prices" className="agro-card">
        <div className="flex items-center justify-center h-[400px] bg-gradient-to-br from-gray-50 to-green-50 rounded-xl p-8">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-[var(--agro-accent-dark)] border-t-transparent"></div>
          <span className="ml-4 text-xl text-gray-600 font-medium">Loading live prices...</span>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card title="Market Prices Error" className="agro-card border-2 border-red-200">
        <div className="text-center p-12">
          <div className="text-4xl mb-4">⚠️</div>
          <p className="text-lg text-red-700 mb-4">{error}</p>
          <button 
            onClick={handleRefresh}
            className="px-6 py-2 bg-[var(--agro-accent-dark)] text-white rounded-xl hover:bg-[var(--agro-primary)] font-medium transition-all shadow-md"
          >
            🔄 Retry
          </button>
        </div>
      </Card>
    );
  }

  return (
    <Card title="Live Market Crop Prices" className="agro-card">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <div className="text-sm text-gray-500">Data Source: Anitech Market API | Auto-refreshes every 30s</div>
        <button 
          onClick={handleRefresh}
          className="px-5 py-2 bg-gradient-to-r from-[var(--agro-accent)] to-[var(--agro-success)] text-white rounded-xl hover:shadow-lg transform hover:-translate-y-0.5 transition-all font-medium flex items-center gap-2"
        >
          <span>🔄 Refresh</span>
        </button>
      </div>
      <div className="h-[450px] mb-8">
        <PriceChart data={data} />
      </div>
      <div className="overflow-x-auto rounded-xl border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gradient-to-r from-[var(--agro-primary)] to-[var(--agro-primary-dark)] text-white">
            <tr>
              <th className="px-6 py-4 text-left font-semibold">Crop</th>
              <th className="px-6 py-4 text-left font-semibold">Current Price (PHP)</th>
              <th className="px-6 py-4 text-left font-semibold">Unit</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item, index) => (
              <tr key={item.name || index} className="hover:bg-green-50 border-b border-gray-100 transition-colors">
                <td className="px-6 py-4 font-semibold text-gray-900">{item.name}</td>
                <td className="px-6 py-4">
                  <span className="text-2xl font-bold text-[var(--agro-accent-dark)]">
                    {formatPrice(item.price)}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-xs font-medium">
                    {item.unit || getUnit(item.name)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
};

export default MarketPrices;

