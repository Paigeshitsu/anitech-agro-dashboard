export const formatPrice = (price: number, currency: string = 'PHP'): string => {
  return new Intl.NumberFormat('en-PH', {
    style: 'currency',
    currency,
  }).format(price);
};

export const formatDate = (dateString: string): string => {
  return new Intl.DateTimeFormat('en-PH').format(new Date(dateString));
};

export const getUnit = (cropName: string): string => {
  const units: Record<string, string> = {
    'Rice': '/kg',
    'Corn': '/kg',
    'Sugar Cane': '/kg',
    'Banana': '/kg',
    'Coconut': '/pc',
    'Tomato': '/kg',
    'Onion': '/kg',
  };
  return units[cropName] || '/kg';
};

export const AGRO_GREEN_COLORS = ['#22c55e', '#16a34a', '#15803d'] as const;
export type AgroGreenColor = typeof AGRO_GREEN_COLORS[number];

// Agro Theme CSS Vars for JS
export const AGRO_THEME = {
  primary: '#1a472a',
  accent: '#22c55e',
  success: '#16a34a',
  green3: '#15803d',
} as const;

