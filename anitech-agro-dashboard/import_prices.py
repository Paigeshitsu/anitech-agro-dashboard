#!/usr/bin/env python
"""
Import sample market prices from CSV into MarketPrice model.
Simulates previous_price and trends.
Run: python manage.py shell < import_prices.py
"""

import csv
import os
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from market.models import MarketPrice
from pathlib import Path

# Full absolute path to CSV666666666
CSV_PATH = r'c:/Users/User/Downloads/agro/redundant_temp/agro/agro/ml_service/data/bantay_presyo_region_v_legazpi_naga_ml.csv'

def load_sample_prices():
    if not os.path.exists(CSV_PATH):
        print(f"CSV not found at {CSV_PATH}")
        return

    print("Loading market prices from CSV...")
    
    # Read CSV
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"Found {len(rows)} price records")
    
    created = 0
    updated = 0
    
    # Sort by date to simulate historical data
    rows.sort(key=lambda x: (x['crop'], x['date']))
    
    crop_prices = {crop: [] for crop in set(r['crop'] for r in rows)}
    
    for row in rows[-100:]:  # Last 100 for demo (trends)
        crop = row['crop']
        date_str = row['date']
        price = float(row['price'])
        
        # Previous price: last entry for this crop
        if crop_prices[crop]:
            prev_price = crop_prices[crop][-1]['price']
        else:
            prev_price = None
        
        # Get or create
        mp, created_new = MarketPrice.objects.get_or_create(
            crop_name=crop,
            date=date_str,
            defaults={
                'current_price': price,
                'previous_price': prev_price,
                'unit': 'per kg',
            }
        )
        
        if not created_new:
            mp.current_price = price
            mp.previous_price = prev_price
            mp.save()
            updated += 1
        else:
            created += 1
        
        # Track history
        crop_prices[crop].append({'date': date_str, 'price': price})
    
    print(f"Created: {created}, Updated: {updated}")
    print(f"Total MarketPrice records: {MarketPrice.objects.count()}")
    latest = MarketPrice.objects.order_by('-last_updated')[:5]
    print("\nLatest 5 prices:")
    for p in latest:
        trend = 'up' if p.previous_price and p.current_price > p.previous_price else ('down' if p.previous_price else 'stable')
        print(f"{p.crop_name}: {p.current_price} {p.unit} (prev: {p.previous_price}, trend: {trend})")

if __name__ == '__main__':
    from django.core.wsgi import get_wsgi_application
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anitech.settings')
    application = get_wsgi_application()
    load_sample_prices()

