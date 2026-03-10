# TODO - Fix Django FieldError at /auth/dashboard/

## Issues to Fix:
1. [x] Fix notifications/models.py - change `self.user.name` to `self.user.first_name`
2. [ ] Fix users/views.py - fix SaleRecord reference (undefined model)
3. [ ] Fix templates/dashboard.html - fix offer.crop.crop_name to offer.crop_name  
4. [ ] Fix templates/dashboard.html - fix notifications_count (not passed to context)

