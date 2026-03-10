# ANITECH Django Test Suite Documentation

## Test Summary
**Total Tests: 42**
**Status: ALL PASSING ✓**

## Test Coverage by Module

### Users Module (11 tests)
- **User Model Tests** (3 tests)
  - `test_user_creation` - Verify user creation with account type
  - `test_user_account_types` - Test all account type variations (admin, secretary, farmer, buyer)
  - `test_user_phone_and_carrier` - Test optional phone and carrier fields

- **User View Tests** (8 tests)
  - `test_signup_view` - Verify signup flow and OTP redirection
  - `test_signup_duplicate_username` - Prevent duplicate usernames
  - `test_signup_invalid_email` - Validate email format
  - `test_login_view_valid_credentials` - Successful login with correct credentials
  - `test_login_view_invalid_password` - Reject wrong password
  - `test_login_view_wrong_account_type` - Reject mismatched account type
  - `test_logout_view` - Verify logout and activity logging
  - `test_otp_token_creation` - Verify OTP token generation

### Crops Module (5 tests)
- **Crop Model Tests** (5 tests)
  - `test_crop_creation` - Basic crop creation with required fields
  - `test_crop_status_defaults_to_available` - Default status verification
  - `test_multiple_crops_per_user` - Users can have multiple crops
  - `test_crop_status_transitions` - Status change from available to reserved/sold
  - `test_crop_with_grade_and_description` - Optional grade and description fields

### Market Module (10 tests)
- **Market Price Tests** (3 tests)
  - `test_market_price_creation` - Create market price entry
  - `test_multiple_prices_for_same_crop` - Track price history
  - `test_market_price_auto_date` - Auto-populate date field

- **Buyer Offer Tests** (4 tests)
  - `test_buyer_offer_creation` - Create buyer offers
  - `test_buyer_offer_with_contact` - Optional contact number
  - `test_offer_status_transitions` - Status transitions (Pending → Accepted/Rejected)
  - `test_offer_status_choices` - All valid status choices

- **Schedule Distribution Tests** (3 tests)
  - `test_schedule_distribution_creation` - Create distribution schedules
  - `test_multiple_schedules` - Multiple scheduling support
  - `test_schedule_created_at` - Auto-populate creation timestamp

### Notifications Module (16 tests)
- **Notification Tests** (3 tests)
  - `test_notification_creation` - Create notifications with types
  - `test_notification_types` - All notification types (info, warning, error, success)
  - `test_notification_mark_as_read` - Mark notifications as read

- **Activity Log Tests** (3 tests)
  - `test_activity_log_creation` - Log user activities with IP
  - `test_activity_log_without_ip` - Optional IP address
  - `test_multiple_activities_per_user` - Track multiple activities per user

- **Admin Announcement Tests** (3 tests)
  - `test_announcement_creation` - Create admin announcements
  - `test_announcement_without_expiry` - Optional expiry date
  - `test_multiple_announcements` - Multiple announcements support

- **OTP Token Tests** (4 tests)
  - `test_otp_token_creation` - Generate OTP tokens
  - `test_otp_token_expiration` - Verify token expiration
  - `test_otp_token_expired` - Test expired tokens
  - `test_multiple_otp_tokens_per_user` - Track multiple tokens

- **Translation Cache Tests** (3 tests)
  - `test_translation_cache_creation` - Cache translations
  - `test_translation_cache_uniqueness` - Prevent duplicate translations
  - `test_multiple_translations_same_source` - Multiple language translations

## Running Tests

### Run All Tests
```bash
python manage.py test
```

### Run Tests for Specific Module
```bash
python manage.py test users
python manage.py test crops
python manage.py test market
python manage.py test notifications
```

### Run Specific Test Class
```bash
python manage.py test users.tests.UserModelTest
python manage.py test users.tests.UserViewTest
```

### Run with Verbose Output
```bash
python manage.py test --verbosity=2
```

## Test Results

All tests execute successfully with the following test database:
- **Database**: SQLite (in-memory for tests)
- **Migrations**: All migrations applied successfully before testing
- **Execution Time**: ~12-13 seconds for full suite

## Test Features

✓ **User Authentication**: Signup, login, logout, OTP verification
✓ **Role-based Access**: Admin, Secretary, Farmer, Buyer accounts
✓ **Crop Management**: Create, update, and track crop inventory
✓ **Market Operations**: Price tracking, buyer offers, distribution scheduling
✓ **Notification System**: Create, track, and manage notifications
✓ **Activity Logging**: User activity tracking with IP addresses
✓ **OTP Security**: One-time password generation and validation
✓ **Translation Cache**: Multi-language support with caching
✓ **Data Validation**: Email validation, duplicate prevention, status transitions

## Notes

- All tests use Django TestCase for database transactions
- Each test is isolated and independent
- No external dependencies or fixtures required (all test data created in setup)
- Password validation enforces Django's default validators (minimum complexity)
- Database state is rolled back after each test

## Future Test Enhancements

- API endpoint tests for REST Framework views
- ML service prediction tests
- Integration tests for cross-module workflows
- Performance tests for large datasets
- Selenium tests for frontend workflows
