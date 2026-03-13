# Anitech Agro Dashboard Refactor TODO

## Plan Steps (Approved)
- [x] 1. Update src/types/market.ts (add CropStats interface)
- [x] 2. Update src/utils/formatters.ts (add Agro-Green theme colors)
- [x] 3. Create src/hooks/useAgroData.ts (central hook for market prices + crop stats, loading/error)
- [x] 4. Update src/components/PriceChart.tsx (solid bar colors, exact axes, responsive fixes)
- [x] 5. Refactor src/components/MarketPrices.tsx (use new hook, bar graph + table, responsive)
- [x] 6. Create src/components/Sidebar.tsx (responsive: drawer mobile, fixed desktop)

- [ ] 7. Verify data flow (hook updates → graph/table sync)
- [ ] 8. Cleanup: Remove src/hooks/useMarketPrices.ts
- [ ] 9. Test responsiveness & types
- [ ] 10. Complete task

Current progress: Starting step 1.

