"""
Translation utilities for AniTech
Based on the old PHP system translations
"""

# Crop name translations from old PHP system - Expanded
CROP_TRANSLATIONS = {
    'Rice': {'en': 'Rice', 'tl': 'Palay'},
    'Corn': {'en': 'Corn', 'tl': 'Mais'},
    'Eggplant': {'en': 'Eggplant', 'tl': 'Talong'},
    'Bitter Gourd': {'en': 'Bitter Gourd', 'tl': 'Ampalaya'},
    'Tomato': {'en': 'Tomato', 'tl': 'Kamatis'},
    'Sweet Potato': {'en': 'Sweet Potato', 'tl': 'Kamote'},
    'Okra': {'en': 'Okra', 'tl': 'Okra'},
    'Peanut': {'en': 'Peanut', 'tl': 'Mani'},
    'Melon': {'en': 'Melon', 'tl': 'Melon'},
    'Watermelon': {'en': 'Watermelon', 'tl': 'Pakwan'},
    'Cucumber': {'en': 'Cucumber', 'tl': 'Pipino'},
    'Carrot': {'en': 'Carrot', 'tl': 'Karot'},
    'Chili': {'en': 'Chili', 'tl': 'Siling Labuyo'},
    'Potato': {'en': 'Potato', 'tl': 'Patatas'},
    'Cabbage': {'en': 'Cabbage', 'tl': 'Repolyo'},
    'Onion': {'en': 'Onion', 'tl': 'Sibuyas'},
    'Garlic': {'en': 'Garlic', 'tl': 'Bawang'},
    'Squash': {'en': 'Squash', 'tl': 'Kalabasa'},
    'Beans': {'en': 'Beans', 'tl': 'Sitaw'},
    'Mung Bean': {'en': 'Mung Bean', 'tl': 'Munggo'},
    'Pea': {'en': 'Pea', 'tl': 'Gisantes'},
    'Bell Pepper': {'en': 'Bell Pepper', 'tl': 'Pimiento'},
    'Ginger': {'en': 'Ginger', 'tl': 'Luya'},
    'Turmeric': {'en': 'Turmeric', 'tl': 'Luyang Dilaw'},
    'Lemongrass': {'en': 'Lemongrass', 'tl': 'Cymbopogon'},
    'Kangkong': {'en': 'Kangkong', 'tl': 'Kangkong'},
    'Pechay': {'en': 'Pechay', 'tl': 'Pechay'},
    'Mustard': {'en': 'Mustard', 'tl': 'Mustasa'},
    'Lettuce': {'en': 'Lettuce', 'tl': 'Litsugas'},
    'Celery': {'en': 'Celery', 'tl': 'Kintsay'},
    'Radish': {'en': 'Radish', 'tl': 'Labanos'},
    'White Radish': {'en': 'White Radish', 'tl': 'Labanos'},
    'Bottle Gourd': {'en': 'Bottle Gourd', 'tl': 'Kalabasa'},
    'Snake Gourd': {'en': 'Snake Gourd', 'tl': 'Patola'},
    'Luffa': {'en': 'Luffa', 'tl': 'Lufa'},
}


def get_crop_name(crop_name, lang='en'):
    """
    Translate crop name to the specified language.
    Based on old PHP system getCropName() function.
    
    Args:
        crop_name: The crop name in English
        lang: Language code ('en' for English, 'tl' for Tagalog)
    
    Returns:
        Translated crop name or original if not found
    """
    if lang == 'en':
        return crop_name
    
    translations = CROP_TRANSLATIONS.get(crop_name, {})
    return translations.get(lang, crop_name)


def get_current_lang(request):
    """
    Get current language from session.
    Based on old PHP system language handling.
    
    Args:
        request: Django request object
    
    Returns:
        Language code ('en' or 'tl')
    """
    return request.session.get('lang', 'en')


def set_language(request, lang):
    """
    Set language in session.
    Based on old PHP system update_language action.
    
    Args:
        request: Django request object
        lang: Language code ('en' or 'tl')
    """
    request.session['lang'] = lang
    if lang == 'tl':
        request.session['language'] = 'Tagalog'
    else:
        request.session['language'] = 'English'


def get_season():
    """
    Get current season based on month.
    Based on old PHP system seasonality logic.
    
    Returns:
        'Wet' or 'Dry' season
    """
    from datetime import datetime
    month = datetime.now().month
    # Wet season: June to November (months 6-11)
    is_wet = (month >= 6 and month <= 11)
    return "Wet" if is_wet else "Dry"


def check_crop_seasonality():
    """
    Check crop seasonality based on current date.
    Based on old PHP system checkCropSeasonality() function.
    
    Returns:
        List of seasonality alerts
    """
    from datetime import datetime
    
    alerts = []
    md = datetime.now().strftime('%m-%d')
    
    # High Demand Periods (from JS logic)
    # December 15 to January 5
    if (md >= '12-15' and md <= '12-31') or (md >= '01-01' and md <= '01-05'):
        alerts.append({
            'crop': 'All Crops',
            'message': 'High demand period for holiday season.',
            'type': 'high-demand'
        })
    
    # Planting: March - April 15
    if md >= '03-01' and md <= '04-15':
        alerts.append({
            'crop': 'Seasonal',
            'message': 'Best time for planting rice and corn.',
            'type': 'planting'
        })
    
    # Harvest: August 15 - September 15
    if md >= '08-15' and md <= '09-15':
        alerts.append({
            'crop': 'Seasonal',
            'message': 'Harvest season approaching.',
            'type': 'harvest'
        })
    
    return alerts


def get_seasonal_dates():
    """
    Get seasonal planting/harvest/high-demand date ranges.
    Used for calendar highlighting.
    
    Returns:
        Dictionary with planting, harvest, and high-demand date strings
    """
    return {
        'planting': [
            "03-01", "03-02", "03-03", "03-04", "03-05", "03-06", "03-07", "03-08", "03-09", "03-10",
            "03-11", "03-12", "03-13", "03-14", "03-15", "03-16", "03-17", "03-18", "03-19", "03-20",
            "03-21", "03-22", "03-23", "03-24", "03-25", "03-26", "03-27", "03-28", "03-29", "03-30", "03-31",
            "04-01", "04-02", "04-03", "04-04", "04-05", "04-06", "04-07", "04-08", "04-09", "04-10",
            "04-11", "04-12", "04-13", "04-14", "04-15"
        ],
        'harvest': [
            "08-15", "08-16", "08-17", "08-18", "08-19", "08-20", "08-21", "08-22", "08-23", "08-24",
            "08-25", "08-26", "08-27", "08-28", "08-29", "08-30", "08-31",
            "09-01", "09-02", "09-03", "09-04", "09-05", "09-06", "09-07", "09-08", "09-09", "09-10",
            "09-11", "09-12", "09-13", "09-14", "09-15"
        ],
        'highDemand': [
            "12-15", "12-16", "12-17", "12-18", "12-19", "12-20", "12-21", "12-22", "12-23", "12-24",
            "12-25", "12-26", "12-27", "12-28", "12-29", "12-30", "12-31",
            "01-01", "01-02", "01-03", "01-04", "01-05"
        ]
    }


def get_translations(lang='en'):
    """
    Get all translations for the specified language.
    
    Args:
        lang: Language code ('en' or 'tl')
    
    Returns:
        Dictionary of translations
    """
    if lang == 'en':
        return {
            'Overview': 'Overview',
            'Weather Forecast': 'Weather Forecast',
            'Crop Management': 'Crop Management',
            'Available Crops': 'Available Crops',
            'Market Prices': 'Market Prices',
            'Schedule Distribution': 'Schedule Distribution',
            'Buyer Offers': 'Buyer Offers',
            'Activity Log': 'Activity Log',
            'Profile': 'Profile',
            'Logout': 'Logout',
            'Language': 'Language',
            'English': 'English',
            'Tagalog': 'Tagalog',
            'Dashboard': 'Dashboard',
            'Search': 'Search',
            'Seasonal Crops': 'Seasonal Crops',
            'High Demand Crops': 'High Demand Crops',
            'All Crops': 'All Crops',
            'Suitability': 'Suitability',
            'Best Season': 'Best Season',
            'Profit': 'Profit',
            'Water Need': 'Water Need',
            'Est. Price': 'Est. Price',
            'View All': 'View All',
            'Type': 'Type',
            'Status': 'Status',
            'Date': 'Date',
            'Buyer': 'Buyer',
            'Offer': 'Offer',
            'Price': 'Price',
            'Quantity': 'Quantity',
            'Pending': 'Pending',
            'Accepted': 'Accepted',
            'Rejected': 'Rejected',
            'No notifications': 'No notifications',
            'Mark all as read': 'Mark all as read',
            'Weather Update': 'Weather Update',
            'Crop Status': 'Crop Status',
            'Market Price Update': 'Market Price Update',
            'Admin Update': 'Admin Update',
            'Agri-Extension Offer': 'Agri-Extension Offer',
            'Saved Successfully': 'Saved Successfully',
            'Action completed': 'Action completed',
            'Logout Confirm': 'Are you sure you want to log out?',
            'Loading': 'Loading...',
            'Not Set': 'Not Set',
            'Invalid Date': 'Invalid Date',
            'Click for details': 'Click for details',
            'Sun': 'Sun',
            'Mon': 'Mon',
            'Tue': 'Tue',
            'Wed': 'Wed',
            'Thu': 'Thu',
            'Fri': 'Fri',
            'Sat': 'Sat',
            'January': 'January',
            'February': 'February',
            'March': 'March',
            'April': 'April',
            'May': 'May',
            'June': 'June',
            'July': 'July',
            'August': 'August',
            'September': 'September',
            'October': 'October',
            'November': 'November',
            'December': 'December',
            'Planting': 'Planting',
            'Harvest': 'Harvest',
            'High Demand': 'High Demand',
            'Previous Month': 'Previous Month',
            'Next Month': 'Next Month',
            'Farmer Dashboard': 'Farmer Dashboard',
            'Price Trackings': 'Price Trackings',
            'All Trends': 'All Trends',
            'Real-time condition for your crops': 'Real-time condition for your crops',
            'Prediction for optimal crops this season': 'Prediction for optimal crops this season',
            'Search...': 'Search...',
            'Seasonal': 'Seasonal',
            'Demand': 'Demand',
            'Manage crops listed and ready for sale': 'Manage crops listed and ready for sale',
            'View and manage distribution schedules for farm supplies': 'View and manage distribution schedules for farm supplies',
            'Manage and track crop price offers from buyers': 'Manage and track crop price offers from buyers',
            'No available crops at the moment': 'No available crops at the moment',
            'No data available': 'No data available',
            'Live market data will be updated soon': 'Live market data will be updated soon',
        }
    else:
        return {
            'Overview': 'Pangkalahatang View',
            'Weather Forecast': 'Forecast ng Panahon',
            'Crop Management': 'Pamamahala ng Pananim',
            'Available Crops': 'Mga Available na Pananim',
            'Market Prices': 'Presyo sa Market',
            'Schedule Distribution': 'Iskedyul ng Distribusyon',
            'Buyer Offers': 'Mga Offer ng Buyer',
            'Activity Log': 'Log ng Aktibidad',
            'Profile': 'Profile',
            'Logout': 'Mag-logout',
            'Language': 'Wika',
            'English': 'English',
            'Tagalog': 'Tagalog',
            'Dashboard': 'Dashboard',
            'Search': 'Hanapin',
            'Seasonal Crops': 'Mga Seasonal na Pananim',
            'High Demand Crops': 'Mga High Demand na Pananim',
            'All Crops': 'Lahat ng Pananim',
            'Suitability': 'Kaugnayan',
            'Best Season': 'Best Season',
            'Profit': 'Profit',
            'Water Need': 'Kailangan ng Tubig',
            'Est. Price': 'Presyo',
            'View All': 'Tingnan Lahat',
            'Type': 'Uri',
            'Status': 'Katayuan',
            'Date': 'Petsa',
            'Buyer': 'Buyer',
            'Offer': 'Offer',
            'Price': 'Presyo',
            'Quantity': 'Dami',
            'Pending': 'Pending',
            'Accepted': 'Accepted',
            'Rejected': 'Rejected',
            'No notifications': 'Walang notifications',
            'Mark all as read': 'Markahan lahat ng nabasa',
            'Weather Update': 'Update ng Panahon',
            'Crop Status': 'Katayuan ng Pananim',
            'Market Price Update': 'Update ng Presyo sa Market',
            'Admin Update': 'Admin Update',
            'Agri-Extension Offer': 'Agri-Extension Offer',
            'Saved Successfully': 'Matagumpay na Na-save',
            'Action completed': 'Nakompleto ang action',
            'Logout Confirm': 'Sigurado ka bang gusto mag-logout?',
            'Loading': 'Loading...',
            'Not Set': 'Hindi Naka-set',
            'Invalid Date': 'Invalid na Petsa',
            'Click for details': 'Pindutin para sa details',
            'Sun': 'Lin',
            'Mon': 'Lun',
            'Tue': 'Mar',
            'Wed': 'Mier',
            'Thu': 'Hue',
            'Fri': 'Bie',
            'Sat': 'Sab',
            'January': 'Enero',
            'February': 'Pebrero',
            'March': 'Marso',
            'April': 'Abril',
            'May': 'Mayo',
            'June': 'Hunyo',
            'July': 'Hulyo',
            'August': 'Agosto',
            'September': 'Setyembre',
            'October': 'Oktubre',
            'November': 'Nobyembre',
            'December': 'Disyembre',
            'Planting': 'Pagbubunga',
            'Harvest': 'Pag-aani',
            'High Demand': 'Mataas na Demand',
            'Previous Month': 'Nakaraang Buwan',
            'Next Month': 'Susunod na Buwan',
            'Farmer Dashboard': 'Farmer Dashboard',
            'Price Trackings': 'Price Trackings',
            'All Trends': 'Lahat ng Trends',
            'Real-time condition for your crops': 'Real-time na kalagayan ng iyong mga pananim',
            'Prediction for optimal crops this season': 'Prediction para sa optimal na pananim sa season na ito',
            'Search...': 'Hanapin...',
            'Seasonal': 'Seasonal',
            'Demand': 'Demand',
            'Manage crops listed and ready for sale': 'Pamamahala ng mga pananim na listed at ready for sale',
            'View and manage distribution schedules for farm supplies': 'Tingnan at pamahalaan ang distribution schedules para sa farm supplies',
            'Manage and track crop price offers from buyers': 'Pamamahala at track ng crop price offers mula sa buyers',
            'No available crops at the moment': 'Walang available na pananim sa ngayon',
            'No data available': 'Walang data available',
            'Live market data will be updated soon': 'Live market data ay ma-update sa lalong madaling panahon',
        }


def create_notification(user, notification_type, title, message):
    """
    Create a notification for a user.
    Based on old PHP system createNotification() function.
    
    Args:
        user: User object
        notification_type: Type of notification (warning, market, offer, info, urgent)
        title: Notification title
        message: Notification message
    
    Returns:
        Notification object or None
    """
    from notifications.models import Notification
    
    try:
        notification = Notification.objects.create(
            user=user,
            type=notification_type,
            title=title,
            message=message,
            is_read=False
        )
        return notification
    except Exception as e:
        print(f"Notification Error: {e}")
        return None


def get_unread_notifications_count(user):
    """
    Get count of unread notifications for a user.
    
    Args:
        user: User object
    
    Returns:
        Integer count of unread notifications
    """
    from notifications.models import Notification
    
    try:
        return Notification.objects.filter(user=user, is_read=False).count()
    except Exception:
        return 0


def get_recent_notifications(user, limit=5):
    """
    Get recent notifications for a user.
    
    Args:
        user: User object
        limit: Maximum number of notifications to return
    
    Returns:
        QuerySet of Notification objects
    """
    from notifications.models import Notification
    
    try:
        return Notification.objects.filter(user=user).order_by('-created_at')[:limit]
    except Exception:
        return []

