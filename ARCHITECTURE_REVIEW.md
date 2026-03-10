# 🏗️ ANITECH PROJECT - ARCHITECTURE OVERVIEW

## 📁 TREE-STYLE FILE STRUCTURE (Excluding node_modules, build, .git)

```
agro/
├── manage.py                          # Django entry point
├── requirements.txt                   # Python dependencies
├── db.sqlite3                         # SQLite database
├── docker-compose.yml                  # Docker configuration
├── Dockerfile                         # Container definition
│
├── anitech/                          # Main Django project
│   ├── __init__.py
│   ├── settings.py                    # ⚙️ CORE: Django configuration
│   ├── urls.py                        # ⚙️ CORE: Root URL routing
│   ├── views.py                       # Home view
│   ├── wsgi.py
│   └── asgi.py
│
├── users/                            # User authentication app
│   ├── models.py                      # ⚙️ CORE: Custom User model with account types
│   ├── views.py                      # ⚙️ CORE: Auth & dashboard views
│   ├── forms.py
│   ├── urls.py                        # Auth URL patterns
│   ├── admin.py
│   └── migrations/
│
├── crops/                            # Crop management app
│   ├── models.py                     # ⚙️ CORE: Crop model with pricing
│   ├── views.py                      # (Currently empty - placeholder)
│   ├── admin.py
│   └── migrations/
│
├── market/                           # Market & offers app
│   ├── models.py                     # ⚙️ CORE: MarketPrice, BuyerOffer, ScheduleDistribution
│   ├── views.py                      # (Currently empty - placeholder)
│   ├── admin.py
│   └── migrations/
│
├── ml_service/                       # ML crop prediction service
│   ├── model.py                      # ⚙️ CORE: ML prediction logic
│   ├── views.py                      # ⚙️ CORE: ML API endpoint
│   ├── urls.py                       # ML API routes
│   ├── admin.py
│   ├── apps.py
│   ├── models/
│   │   ├── crop_model.joblib         # Trained crop recommendation model
│   │   └── price_model.joblib        # Trained price prediction model
│   └── migrations/
│
├── notifications/                    # Notifications & activity logging
│   ├── models.py                     # ⚙️ CORE: Notification, ActivityLog, OTPToken models
│   ├── views.py
│   ├── admin.py
│   └── migrations/
│
├── templates/                        # HTML templates
│   ├── base.html
│   ├── home.html
│   ├── login.html
│   ├── signup.html
│   ├── verify_otp.html
│   ├── dashboard.html
│   ├── crops.html
│   ├── market.html
│   ├── notifications.html
│   └── profile.html
│
└── static/                           # Static assets
    ├── css/style.css
    ├── js/notifications.js
    └── images/ (icons, logos)
```

---

## 🔧 TECH STACK SUMMARY

| Layer | Technology |
|-------|-------------|
| **Backend** | Django 4.2.29 (Python) |
| **API** | Django REST Framework 3.14.0 |
| **Database** | SQLite3 (default), MySQL compatible |
| **ML/AI** | scikit-learn 1.4.2, pandas 2.2.2, joblib 1.4.2 |
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla) |
| **Auth** | Custom JWT-like OTP system with session auth |
| **Deployment** | Docker-ready |

### Main Entry Points:
1. **`manage.py`** - Django CLI entry point
2. **`anitech/urls.py`** - Root URL dispatcher (routes `/auth/`, `/ml/`, `/`)
3. **`users/views.py`** - Authentication views (login, signup, OTP verification)
4. **`users/views.py::dashboard_view()`** - Role-based dashboard router
5. **`ml_service/views.py::predict_crops()`** - ML prediction API endpoint (`/)

---

##ml/predict/` 🎯 CORE LOGIC FILES (Critical for Performance & Optimization)

| Priority | File Path | Why It's Critical |
|----------|-----------|-------------------|
| 🔴 **HIGH** | `users/views.py` | Handles all auth, OTP, role-based routing, dashboard aggregation with N+1 query risks |
| 🔴 **HIGH** | `ml_service/model.py` | ML inference logic - predictive algorithm performance |
| 🔴 **HIGH** | `ml_service/views.py` | ML API endpoint - needs caching & async optimization |
| 🔴 **HIGH** | `users/models.py` | Custom User model - underpins all auth & permissions |
| 🟠 **MEDIUM** | `crops/models.py` | Core business data - needs indexing on `status`, `user`, `harvest_date` |
| 🟠 **MEDIUM** | `market/models.py` | Market prices & offers - high query volume |
| 🟠 **MEDIUM** | `notifications/models.py` | Activity logging, OTP tokens - can grow large, needs cleanup |
| 🟠 **MEDIUM** | `anitech/settings.py` | Database config, middlewares, caching settings |
| 🟠 **MEDIUM** | `users/urls.py` | Auth route definitions |
| 🟡 **LOW** | `templates/*.html` | Frontend - lower performance impact |

---

## 🚨 OPTIMIZATION OPPORTUNITIES (For AI)

1. **Database Query Optimization**
   - `users/views.py::dashboard_view()` - Multiple `select_related()` but uses slicing `[:10]` without ordering - add `.order_by('-created_at')`
   - Add database indexes on: `Crop.status`, `Crop.harvest_date`, `Notification.is_read`, `ActivityLog.created_at`

2. **ML Service Performance**
   - Model is loaded globally (good) but could use Redis caching for predictions
   - Consider async processing for heavy ML inference

3. **Authentication**
   - OTP tokens need automatic cleanup (cron job)
   - ActivityLog can grow unbounded - implement cleanup

4. **Caching**
   - Add Django cache framework for market prices
   - Cache dashboard context per user role

5. **Security**
   - Currently `DEBUG=True` by default in settings
   - Email backend is console-only (dev mode)

