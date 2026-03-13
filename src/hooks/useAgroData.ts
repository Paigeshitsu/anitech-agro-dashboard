import { useState, useEffect, useCallback } from 'react';
import { CropPrice, CropStat, AgroDataState } from '../types/market';
import type { MarketPricesState } from '../types/market';

const API_BASE = 'http://localhost:8000/market/api';

export interface ExtendedAgroData extends AgroDataState {
  refetch: () => Promise<void>;
}

export const useAgroData = (): ExtendedAgroData => {
  const [marketState, setMarketState] = useState<MarketPricesState>({
    data: [],
    loading: true,
    error: null,
  });

  const [cropStatsData, setCropStatsData] = useState<CropStat[]>([]);
  const [cropLoading, setCropLoading] = useState(true);
  const [cropError, setCropError] = useState<string | null>(null);

  const fetchMarketPrices = async (): Promise<CropPrice[]> => {
    try {
      const response = await fetch(`${API_BASE}/market-prices/`);
      if (!response.ok) throw new Error(`API error: ${response.status}`);
      const data: any[] = await response.json();
      return data.map((item) => ({
        name: item.crop_name || item.name,
        price: parseFloat(item.current_price || item.price),
        unit: item.unit,
        date: item.date_updated,
      }));
    } catch (error) {
      console.error('Market fetch failed:', error);
      return [
        { name: 'Rice', price: 45, unit: 'PHP/kg' },
        { name: 'Corn', price: 32, unit: 'PHP/kg' },
        { name: 'Sugar', price: 85, unit: 'PHP/kg' },
        { name: 'Coconut', price: 12, unit: 'PHP/pc' },
        { name: 'Banana', price: 55, unit: 'PHP/kg' },
      ];
    }
  };

  const fetchCropStats = async (): Promise<CropStat[]> => {
    try {
      const response = await fetch(`${API_BASE}/crop-stats/`);
      if (!response.ok) throw new Error(`API error: ${response.status}`);
      return await response.json();
    } catch {
      return [
        { name: 'Rice', yieldPerHectare: 1200, totalRevenue: 54000, unit: 'kg/ha' },
        { name: 'Corn', yieldPerHectare: 800, totalRevenue: 25600, unit: 'kg/ha' },
        { name: 'Sugar Cane', yieldPerHectare: 6500, totalRevenue: 552500, unit: 'kg/ha' },
        { name: 'Coconut', yieldPerHectare: 4500, totalRevenue: 54000, unit: 'pcs/ha' },
        { name: 'Banana', yieldPerHectare: 20000, totalRevenue: 1100000, unit: 'kg/ha' },
      ];
    }
  };

  const refetch = useCallback(async () => {
    setMarketState((prev: MarketPricesState) => ({ ...prev, loading: true })); 
    setCropLoading(true);

    // 1 second loading simulation for refresh UX
    await new Promise(resolve => setTimeout(resolve, 1000));

    try {
      const [marketData, statsData] = await Promise.all([
        fetchMarketPrices(),
        fetchCropStats(),
      ]);
      setMarketState({ data: marketData, loading: false, error: null });
      setCropStatsData(statsData);
      setCropError(null);
    } catch (error) {
      setMarketState({ data: [], loading: false, error: 'Failed to refetch data' });
      setCropError('Failed to refetch stats');
    }
  }, []);

  useEffect(() => {
    refetch();

    const interval = setInterval(refetch, 30000); // Auto refresh every 30s
    return () => clearInterval(interval);
  }, []);

  return {
    marketPrices: marketState,
    cropStats: {
      data: cropStatsData,
      loading: cropLoading,
      error: cropError,
    },
    refetch,
  } as ExtendedAgroData;
};

