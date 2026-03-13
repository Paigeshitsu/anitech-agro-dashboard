export interface CropPrice {
  name: string;
  price: number;
  unit?: string;
  date?: string;
}

export interface MarketPricesState {
  data: CropPrice[];
  loading: boolean;
  error: string | null;
}

export interface CropStat {
  name: string;
  yieldPerHectare: number;
  totalRevenue: number;
  unit: string;
}

export interface AgroDataState {
  marketPrices: MarketPricesState;
  cropStats: {
    data: CropStat[];
    loading: boolean;
    error: string | null;
  };
}

export interface ExtendedAgroData extends AgroDataState {
  refetch: () => Promise<void>;
}

