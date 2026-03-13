import { useState, useCallback } from 'react';
import { CropPrice, MarketPricesState } from '../types/market';

const API_URL = 'http://localhost:8000/market/api/market-prices/';

export const useMarketPrices = () => {
  const [state, setState] = useState<MarketPricesState>({
    data: [],
    loading: false,
    error: null,
  });

  const fetchPrices = useCallback(async () => {
    setState((prev: MarketPricesState) => ({ ...prev, loading: true, error: null })); 
    try {
      const response = await fetch(API_URL);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setState({
        data: data.map((item: any) => ({
          name: item.name || item.crop_name,
          price: Number(item.price || item.current_price),
          unit: item.unit,
        })),
        loading: false,
        error: null,
      });
    } catch (error) {
      console.error('Fetch error:', error);
      // Mock fallback
      setState({
        data: [
          { name: 'Rice', price: 45, unit: 'PHP/kg' },
          { name: 'Corn', price: 32, unit: 'PHP/kg' },
          { name: 'Sugar', price: 85, unit: 'PHP/kg' },
          { name: 'Coconut', price: 12, unit: 'PHP/pc' },
          { name: 'Banana', price: 55, unit: 'PHP/kg' },
        ],
        loading: false,
        error: 'Using mock data (API unavailable)',
      });
    }
  }, []);

  const refetch = useCallback(async () => {
    await new Promise(r => setTimeout(r, 1000)); // 1s loading
    await fetchPrices();
  }, [fetchPrices]);

  return {
    ...state,
    refetch,
    fetchPrices,
  };
};

