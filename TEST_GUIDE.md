# Django Test Execution Guide

## Quick Start

### Run All Tests
```bash
python manage.py test
```

### Expected Output
```
Found 42 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
........................................................ (42 dots)
----------------------------------------------------------------------
Ran 42 tests in ~12s

OK
Destroying test database for alias 'default'...
```

## Detailed Test Execution

### By Module

#### Users Module (11 tests)
```bash
python manage.py test users
# Tests: Authentication, signup, login, logout, OTP
```

#### Crops Module (5 tests)
```bash
python manage.py test crops
# Tests: Crop creation, status transitions, relationships
```

#### Market Module (10 tests)
```bash
python manage.py test market
# Tests: Prices, buyer offers, distribution schedules
```

#### Notifications Module (16 tests)
```bash
python manage.py test notifications
# Tests: Notifications, activity logs, announcements, OTP tokens, translations
```

### By Test Class

```bash
# User Model Tests
python manage.py test users.tests.UserModelTest

# User View Tests (login, signup, logout)
python manage.py test users.tests.UserViewTest

# Crop Model Tests
python manage.py test crops.tests.CropModelTest

# Market Price Tests
python manage.py test market.tests.MarketPriceModelTest

# Buyer Offer Tests
python manage.py test market.tests.BuyerOfferModelTest

# Schedule Distribution Tests
python manage.py test market.tests.ScheduleDistributionModelTest

# Notification Tests
python manage.py test notifications.tests.NotificationModelTest

# Activity Log Tests
python manage.py test notifications.tests.ActivityLogModelTest

# Admin Announcement Tests
python manage.py test notifications.tests.AdminAnnouncementModelTest

# OTP Token Tests
python manage.py test notifications.tests.OTPTokenModelTest

# Translation Cache Tests
python manage.py test notifications.tests.TranslationCacheModelTest
```

### By Individual Test

```bash
# Example: test_signup_view
python manage.py test users.tests.UserViewTest.test_signup_view

# Example: test_crop_creation
python manage.py test crops.tests.CropModelTest.test_crop_creation
```

## Verbose Output

### Standard Verbosity
```bash
python manage.py test --verbosity=1
```

### Detailed Verbosity
```bash
python manage.py test --verbosity=2
```

### No Output (quiet mode)
```bash
python manage.py test --verbosity=0
```

## Test Output Options

### Parallel Test Execution
```bash
python manage.py test --parallel 4
```

### Keep Test Database
```bash
python manage.py test --keepdb
```
(Useful for debugging; reuses test database from previous run)

### Run with Coverage Report
```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generates HTML report in htmlcov/
```

## Test Database Configuration

Tests use an in-memory SQLite database:
- Isolated from production/development databases
- Automatically created and destroyed per test run
- All migrations applied automatically
- No manual setup required

## Debugging Tests

### Print Statements
```bash
python manage.py test --verbosity=2
# Shows all test names and results
```

### Run Single Test with Output
```bash
python manage.py test users.tests.UserViewTest.test_signup_view --verbosity=2
```

### Run Tests with PDB Debugger
Add this to your test:
```python
import pdb; pdb.set_trace()
```

Then run:
```bash
python manage.py test --pdb
```

### Capture Logs During Tests
```bash
python manage.py test -v 3  # Maximum verbosity
```

## Common Test Scenarios

### Test Authentication Flow
```bash
python manage.py test users.tests.UserViewTest
```
Tests:
- User signup with validation
- Login with correct credentials
- Login failure scenarios
- Logout and activity logging

### Test Crop Inventory
```bash
python manage.py test crops.tests.CropModelTest
```
Tests:
- Create new crops
- Multiple crops per user
- Status transitions (available → reserved → sold)
- Optional fields (grade, description)

### Test Market Operations
```bash
python manage.py test market.tests
```
Tests:
- Track market prices
- Create buyer offers
- Manage distribution schedules
- Status tracking

### Test Data Integrity
```bash
python manage.py test notifications.tests.TranslationCacheModelTest
```
Tests:
- Unique constraints
- Data validation
- Relationships

## Test Environment Variables

Set test-specific variables in `.env.test`:
```
DEBUG=True
TESTING=True
SECRET_KEY=test-secret-key
DATABASE_URL=sqlite:///:memory:
```

Load with:
```bash
export $(cat .env.test | xargs)
python manage.py test
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.13
      - run: pip install -r requirements.txt
      - run: python manage.py test
```

## Test Failures & Solutions

### Import Errors
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # Unix
.venv\Scripts\activate     # Windows
```

### Database Locked
```bash
# Remove test database if stuck
rm db.sqlite3
python manage.py migrate
```

### Missing Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Module Not Found
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

## Performance Optimization

### Use --keepdb for Faster Iteration
```bash
python manage.py test --keepdb
```

### Run Tests in Parallel
```bash
python manage.py test --parallel
```

### Focus on Failing Tests
```bash
# Run only previously failed tests
python manage.py test --failfast
```

## Test Best Practices

1. **Isolation**: Each test is independent
2. **Clarity**: Test names describe what they test
3. **Setup/Teardown**: Use setUp() for test data
4. **Assertions**: Use specific assertions (assertEqual, assertTrue, etc.)
5. **No Side Effects**: Tests don't affect each other

## Test File Locations

All tests stored in `tests.py`:
- `users/tests.py` - User authentication tests
- `crops/tests.py` - Crop management tests
- `market/tests.py` - Market operation tests
- `notifications/tests.py` - Notification system tests

## Running Tests in Production-Like Environment

```bash
# Use PostgreSQL instead of SQLite
export DATABASE_URL=postgresql://user:password@localhost/test_db
python manage.py test

# Use settings for production testing
python manage.py test --settings=agro.settings.production
```

## Troubleshooting Common Issues

### "No module named 'django'"
```bash
pip install Django==4.2.29
```

### "can't open file 'manage.py'"
```bash
cd /path/to/agro/  # Navigate to project root
python manage.py test
```

### "SQLite database is locked"
```bash
# Delete test database
rm db.sqlite3
python manage.py migrate --run-syncdb
python manage.py test
```

### Tests pass locally but fail in CI
- Check Python version compatibility
- Verify all dependencies in requirements.txt
- Check environment variables
- Ensure database setup is correct

## Additional Resources

- Django Testing Documentation: https://docs.djangoproject.com/en/4.2/topics/testing/
- Python unittest: https://docs.python.org/3/library/unittest.html
- Coverage.py: https://coverage.readthedocs.io/

## Test Maintenance

### When to Add Tests
- When adding new features
- When fixing bugs
- When refactoring code
- For critical paths

### Test Review Checklist
- [ ] All tests pass
- [ ] Test names are descriptive
- [ ] Tests are independent
- [ ] No hardcoded values
- [ ] Proper setup/teardown
- [ ] Appropriate assertions

## Support

For test-related issues or questions:
1. Check Django documentation
2. Review existing test examples in codebase
3. Run tests with --verbosity=2 for details
4. Check logs for error messages
