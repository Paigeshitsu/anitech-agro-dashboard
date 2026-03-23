# Clean File Structure TODO

## [x] 1. Delete junk files/dirs
- [ ] wee.jfif
- [ ] users_list.txt  
- [ ] __MACOSX/
- [ ] redundant_temp/
- [ ] agro/
- [ ] accounts/

## [ ] 2. Move data scripts to management/commands
- [ ] import_data.py → anitech/management/commands/
- [ ] import_from_sql.py → anitech/management/commands/
- [ ] import_prices.py → anitech/management/commands/

## [ ] 3. Move Docker files
- [ ] docker-compose.yml, Dockerfile → docker/

## [ ] 4. Move frontend to frontend/
- [ ] src/, package.json, vite.config.ts, tailwind.config.js, postcss.config.js, index.html

## [ ] 5. Consolidate docs
- [ ] Merge all TODO*.md → TODO.md
- [ ] Merge README* → README.md
- [ ] Delete duplicates: ARCHITECTURE_REVIEW.md, FINAL_STATUS.md, etc.

## [ ] 6. Organize templates by app
- [ ] Create templates/users/, templates/market/ etc.
- [ ] Move relevant templates

## [ ] 7. Update .gitignore
- [ ] Add frontend/node_modules/, *.pyc etc.

## [ ] 8. Test
- [ ] python manage.py runserver
- [ ] cd frontend && npm install && npm run dev

## [ ] 9. Complete
