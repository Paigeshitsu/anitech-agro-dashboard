# ANITECH - Agricultural Management System (Django Edition)

## Overview
ANITECH is a comprehensive agricultural management system that has been migrated from PHP/MySQL to Python Django. It provides a complete platform for farmers, buyers, secretaries, and administrators to manage crop inventory, market prices, buyer offers, and distribution schedules.

## Features
- **User Management**: Multi-role support (Admin, Secretary, Farmer, Buyer) with OTP verification
- **Crop Management**: Track crops with status, grades, pricing information
- **Market Operations**: Monitor market prices, manage buyer offers, schedule distributions
- **Notification System**: Real-time notifications and activity logging
- **ML Integration**: Crop recommendations and price predictions (integrated with ML service)
- **Multi-language Support**: Translation caching for multiple languages
- **Email/OTP Authentication**: Secure authentication with one-time passwords

## Technology Stack
- **Framework**: Django 4.2.29
- **Language**: Python 3.13.1
- **Database**: SQLite (development), MySQL (production)
- **APIs**: Django REST Framework
- **ML**: scikit-learn, pandas, joblib
- **Containerization**: Docker & Docker Compose
- **Email**: SMTP with PHPMailer (legacy) or Django Mail Backend

## Project Structure
```
agro/
├── users/              # User authentication and management
├── crops/              # Crop inventory management
├── market/             # Market prices and buyer offers
├── notifications/      # Notifications and activity logging
├── ml_service/         # Machine learning predictions
├── accounts/           # Account management
├── agro/               # Django settings and configuration
├── templates/          # HTML templates
├── static/             # CSS, JS, images
└── migrations/         # Database migrations
```

## Installation & Setup

### Prerequisites
- Python 3.13+
- pip or conda
- MySQL/PostgreSQL (for production) or SQLite (development)

### Local Development Setup
```bash
# Clone repository
git clone <repo-url>
cd agro

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Docker Setup
```bash
# Build and run with Docker Compose
docker-compose up --build

# Access application at http://localhost:8000
```

## Configuration

### Environment Variables
Create a `.env` file in the project root:
```
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Database Setup
For development (SQLite):
```bash
python manage.py migrate
```

For production (MySQL):
```bash
# Update DATABASE_URL in .env
mysql -u root -p < anitech.sql  # If using provided SQL file
python manage.py migrate
```

## Testing

### Run All Tests
```bash
python manage.py test
```

### Run Tests by Module
```bash
python manage.py test users
python manage.py test crops
python manage.py test market
python manage.py test notifications
```

### Test Coverage
- **42 Total Tests**: All passing ✓
- **User Authentication**: 11 tests
- **Crop Management**: 5 tests
- **Market Operations**: 10 tests
- **Notifications**: 16 tests

See [TESTING.md](TESTING.md) for detailed test documentation.

## API Endpoints

### Authentication
- `POST /auth/signup/` - Register new user
- `POST /auth/login/` - User login
- `POST /auth/verify-otp/` - Verify OTP
- `GET /auth/logout/` - User logout
- `GET /auth/dashboard/` - User dashboard

### Crops
- `GET/POST /api/crops/` - List and create crops
- `GET/PUT /api/crops/<id>/` - Retrieve and update crop

### Market
- `GET /api/market-prices/` - Market prices
- `GET/POST /api/buyer-offers/` - Buyer offers
- `GET/POST /api/distributions/` - Distribution schedules

### ML Service
- `POST /api/ml/predict/` - Get crop recommendations
- `POST /api/ml/predict-price/` - Predict crop prices

## Data Migration from PHP/MySQL

### Using Migration Script
```bash
python import_data.py
```

This script:
- Connects to existing MySQL database
- Imports users with proper role mapping
- Migrates crop data with all metadata
- Transfers market prices and buyer offers
- Maps schedules to distributions

## Email Configuration

### Gmail Setup
1. Enable 2-factor authentication on Gmail
2. Generate app password
3. Add to `.env`:
```
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### OTP Delivery
- OTPs sent via email for verification
- 5-minute expiration by default
- Configurable in settings

## Admin Panel
Access Django admin at `/admin/`:
- User management
- Crop inventory
- Market prices
- Notifications
- Activity logs

## Production Deployment

### Using Docker
```bash
docker-compose -f docker-compose.yml up -d
```

### Using Gunicorn + Nginx
```bash
# Install Gunicorn
pip install gunicorn

# Run Gunicorn
gunicorn agro.wsgi:application --bind 0.0.0.0:8000

# Configure Nginx as reverse proxy
# See deployment guides in docs/
```

### Database
- Use MySQL 8.0+ for production
- Enable SSL connections
- Regular backups recommended

## Maintenance

### Database Backup
```bash
# MySQL
mysqldump -u root -p agro > backup.sql

# SQLite
cp db.sqlite3 db.backup.sqlite3
```

### Static Files
```bash
python manage.py collectstatic
```

### Logs
- Application logs: `logs/app.log`
- Error logs: `logs/error.log`
- Activity logs: Database table `notifications_activitylog`

## Troubleshooting

### Migration Issues
```bash
python manage.py makemigrations
python manage.py migrate --fake-initial
```

### Database Connection
```bash
python manage.py dbshell  # Test database connection
```

### Email Not Sending
- Verify credentials in `.env`
- Check SMTP settings
- View logs for detailed errors

### Static Files Not Loading
```bash
python manage.py collectstatic --noinput
```

## Support & Contact
For issues, questions, or contributions:
- Create issue on repository
- Contact development team

## License
[Specify License]

## Changelog

### Version 1.0.0 (Current)
- Complete migration from PHP to Django
- All original features preserved
- 42 comprehensive tests added
- Production-ready deployment configuration
- Docker support
- Email/OTP authentication

### Previous (PHP Version)
- Original ANITECH system
- Features all migrated to Django

## Contributing
1. Fork repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

Please ensure all tests pass before submitting PR.
