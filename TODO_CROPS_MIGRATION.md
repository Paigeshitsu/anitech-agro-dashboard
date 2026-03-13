# Crops Migration - Available Crops Flow

## Approved Plan Steps
1. [x] Add crop_purchase view in crops/views.py (direct buy for buyers, full qty, set status='sold').
2. [x] Update templates/crop_detail.html with Buy Now button/form for buyers.
3. [x] Add URL in crops/urls.py for purchase.
4. [ ] Ensure market offer acceptance updates Crop status.
5. [x] Test end-to-end: add crop → view available → buy → verify removed.

## Progress
Direct buy flow complete. Crops disappear from available_crops after purchase. URLs fixed.

**Next:** Market offer integration.
