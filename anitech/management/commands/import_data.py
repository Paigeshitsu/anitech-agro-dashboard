from django.core.management.base import BaseCommand
import mysql.connector
from users.models import User
from crops.models import Crop
from market.models import MarketPrice, BuyerOffer, ScheduleDistribution
from notifications.models import Notification, ActivityLog, AdminAnnouncement, OTPToken, TranslationCache

class Command(BaseCommand):
    help = 'Import data from MySQL to Django'

    def handle(self, *args, **options):
        # Connect to MySQL
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='anitech'
        )
        cursor = conn.cursor(dictionary=True)

        # Import users
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        for u in users:
            User.objects.get_or_create(
                id=u['id'],
                defaults={
                    'username': u['email'],
                    'email': u['email'],
                    'first_name': u['name'],
                    'account_type': u['account_type'],
                    'phone': u['phone'],
                    'carrier': u['carrier'],
                    'is_verified': u['is_verified'],
                    'language': u['language'],
                    'password': u['password'],  # Assuming hashed
                    'date_joined': u['created_at']
                }
            )

        # Import crops
        cursor.execute("SELECT * FROM crops")
        crops = cursor.fetchall()
        for c in crops:
            Crop.objects.get_or_create(
                id=c['id'],
                defaults={
                    'user_id': c['user_id'],
                    'crop_name': c['crop_name'],
                    'grade': c['grade'],
                    'price': c['price'],
                    'wholesale_price': c['wholesale_price'],
                    'retail_price': c['retail_price'],
                    'quantity': c['quantity'],
                    'harvest_date': c['harvest_date'],
                    'available_until': c['available_until'],
                    'description': c['description'],
                    'image': c['image'],
                    'status': c['status'],
                    'created_at': c['created_at']
                }
            )

        # Import market_prices
        cursor.execute("SELECT * FROM market_prices")
        prices = cursor.fetchall()
        for p in prices:
            MarketPrice.objects.get_or_create(
                id=p['id'],
                defaults={
                    'crop_name': p['crop_name'],
                    'price': p['price'],
                    'date': p['date']
                }
            )

        # Import buyer_offers
        cursor.execute("SELECT * FROM buyer_offers")
        offers = cursor.fetchall()
        for o in offers:
            BuyerOffer.objects.get_or_create(
                id=o['id'],
                defaults={
                    'buyer_name': o['buyer_name'],
                    'contact_number': o['contact_number'],
                    'crop_name': o['crop_name'],
                    'offer_price': o['offer_price'],
                    'status': o['status'],
                    'date_offered': o['date_offered']
                }
            )

        # Import schedule_distribution
        cursor.execute("SELECT * FROM schedule_distribution")
        schedules = cursor.fetchall()
        for s in schedules:
            ScheduleDistribution.objects.get_or_create(
                id=s['id'],
                defaults={
                    'title': s['title'],
                    'description': s['description'],
                    'scheduled_date': s['scheduled_date'],
                    'location': s['location'],
                    'created_at': s['created_at']
                }
            )

        # Import notifications
        cursor.execute("SELECT * FROM notifications")
        notifs = cursor.fetchall()
        for n in notifs:
            Notification.objects.get_or_create(
                id=n['id'],
                defaults={
                    'user_id': n['user_id'],
                    'type': n['type'],
                    'title': n['title'],
                    'message': n['message'],
                    'is_read': n['is_read'],
                    'created_at': n['created_at']
                }
            )

        # Import activity_logs
        cursor.execute("SELECT * FROM activity_logs")
        logs = cursor.fetchall()
        for l in logs:
            ActivityLog.objects.get_or_create(
                id=l['id'],
                defaults={
                    'user_id': l['user_id'],
                    'activity': l['activity'],
                    'details': l['details'],
                    'ip_address': l['ip_address'],
                    'created_at': l['created_at']
                }
            )

        # Import admin_announcements
        cursor.execute("SELECT * FROM admin_announcements")
        anns = cursor.fetchall()
        for a in anns:
            AdminAnnouncement.objects.get_or_create(
                id=a['id'],
                defaults={
                    'title': a['title'],
                    'message': a['message'],
                    'created_at': a['created_at'],
                    'expiry_date': a['expiry_date']
                }
            )

        # Import otp_tokens
        cursor.execute("SELECT * FROM otp_tokens")
        otps = cursor.fetchall()
        for o in otps:
            OTPToken.objects.get_or_create(
                id=o['id'],
                defaults={
                    'user_id': o['user_id'],
                    'otp_code': o['otp_code'],
                    'expires_at': o['expires_at'],
                    'created_at': o['created_at']
                }
            )

        # Import translations_cache
        cursor.execute("SELECT * FROM translations_cache")
        trans = cursor.fetchall()
        for t in trans:
            TranslationCache.objects.get_or_create(
                id=t['id'],
                defaults={
                    'source_text': t['source_text'],
                    'source_lang': t['source_lang'],
                    'target_lang': t['target_lang'],
                    'translated_text': t['translated_text'],
                    'created_at': t['created_at']
                }
            )

        cursor.close()
        conn.close()
        self.stdout.write(self.style.SUCCESS('Data imported successfully'))