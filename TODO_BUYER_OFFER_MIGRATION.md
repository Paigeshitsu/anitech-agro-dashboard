# Buyer Offer Legacy Implementation Plan
## Status: In Progress

1. [x] Update market/models.py - Add quantity, expiry_date, FK to Crop/User; create SellerOffer model
2. [x] Update market/forms.py - Update BuyerOfferForm, add SellerOfferForm
3. [x] Execute: python manage.py makemigrations market
4. [x] Update market/views.py - Add filters/search, buyer_dashboard view, seller offer CRUD, notifications
5. [x] Create templates/buyer_dashboard.html
6. [x] Create templates/sell_offer_list.html, sell_offer_form.html, sell_offer_confirm_delete.html
7. [x] Update templates/market_offer_list.html - Add filters form
8. [x] Update templates/market_offer_form.html - New fields
9. [x] Update market/urls.py - Add new URLs
10. [ ] Update notifications/views.py - Offer status notification trigger
11. [x] Execute: python manage.py migrate
12. [ ] Test: Buyer create offer, farmer accept/reject, filters work, notifications sent
13. [ ] Update static/js/market.js - Dynamic filtering if needed
14. [ ] Mark complete, update TODO_MARKET.md

**Current Step: 11**

