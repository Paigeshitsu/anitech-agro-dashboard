# Deep Django Monolith Reconstruction TODO

## Phase 1: Critical Cleanup ✅
- [x] Create this TODO.md
- [x] Edit anitech/settings.py: Remove 'rest_framework'
- [x] Delete market/serializers.py
- [x] Edit market/urls.py: Pure Django paths
- [x] Edit market/views.py: Remove DRF, add market_prices_view
- [x] Edit templates/base.html: Add Tailwind CDN
- [x] Create templates/market/prices.html from PHP blueprint
- [x] Fix anitech/views.py indentation if needed

## Phase 2: React Cleanup ✅
- [x] Delete src/, package.json, vite.config.ts, tailwind.config.js, postcss.config.js, index.html, package-lock.json
- [x] Update .gitignore

## Phase 3: Test & Polish 
- [ ] python manage.py makemigrations && migrate
- [ ] python manage.py runserver
- [ ] Test /market/prices/ page (grid, chart, trends)
- [ ] Populate data via import_prices.py
- [x] Git commit/push with PR (blackboxai/market-prices-fix → main)

Updated: $(date)
