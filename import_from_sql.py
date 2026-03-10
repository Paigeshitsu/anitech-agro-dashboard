import os
import django
import ast
import re
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anitech.settings')
django.setup()

from users.models import User
from crops.models import Crop
from market.models import MarketPrice, BuyerOffer, ScheduleDistribution
from notifications.models import Notification, ActivityLog, AdminAnnouncement, OTPToken, TranslationCache

def parse_insert_values(insert_text):
    # Extract the VALUES part
    start = insert_text.find('VALUES') + 6
    end = insert_text.rfind(';')
    values_text = insert_text[start:end].strip()
    
    # Remove outer ()
    if values_text.startswith('(') and values_text.endswith(')'):
        values_text = values_text[1:-1]
    
    # Split by '), ('
    rows_text = re.split(r'\),\s*\(', values_text)
    
    parsed_rows = []
    for i, row_text in enumerate(rows_text):
        row_text = row_text.strip('();')
        # Replace NULL with None, ' with "
        row_text = row_text.replace("NULL", "None").replace("'", '"')
        try:
            parsed = ast.literal_eval(f"({row_text})")
            parsed_rows.append(parsed)
        except Exception as e:
            print(f"Failed to parse row {i}: {row_text}, error: {e}")
    return parsed_rows

def import_users(rows):
    for row in rows:
        id, name, email, phone, carrier, password, account_type, is_verified, created_at, language = row
        # Parse created_at to datetime
        try:
            date_joined = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
        except:
            date_joined = None
        is_staff = account_type == 'admin'
        User.objects.get_or_create(
            id=id,
            defaults={
                'username': email,
                'email': email,
                'first_name': name,
                'account_type': account_type,
                'phone': phone,
                'carrier': carrier,
                'is_verified': bool(is_verified),
                'language': language,
                'password': password,
                'date_joined': date_joined,
                'is_staff': is_staff,
                'is_superuser': is_staff,
            }
        )
    print(f"Imported {len(rows)} users")

def import_crops(rows):
    for row in rows:
        if not isinstance(row, tuple) or len(row) != 14:
            continue
        id, user_id, crop_name, grade, price, wholesale_price, retail_price, quantity, harvest_date, available_until, description, image, status, created_at = row
        if not User.objects.filter(id=user_id).exists():
            continue
        try:
            harvest_date = datetime.strptime(harvest_date, '%Y-%m-%d') if harvest_date else None
            available_until = datetime.strptime(available_until, '%Y-%m-%d') if available_until else None
            created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S') if created_at else None
        except:
            pass
        Crop.objects.get_or_create(
            id=id,
            defaults={
                'user_id': user_id,
                'crop_name': crop_name,
                'grade': grade,
                'price': price,
                'wholesale_price': wholesale_price,
                'retail_price': retail_price,
                'quantity': quantity,
                'harvest_date': harvest_date,
                'available_until': available_until,
                'description': description,
                'image': image,
                'status': status,
                'created_at': created_at,
            }
        )
    print(f"Imported {len([r for r in rows if isinstance(r, tuple) and len(r) == 14 and User.objects.filter(id=r[1]).exists()])} crops")

def import_buyer_offers(rows):
    for row in rows:
        id, buyer_name, contact_number, crop_name, offer_price, status, date_offered = row
        try:
            date_offered = datetime.strptime(date_offered, '%Y-%m-%d') if date_offered else None
        except:
            pass
        BuyerOffer.objects.get_or_create(
            id=id,
            defaults={
                'buyer_name': buyer_name,
                'contact_number': contact_number,
                'crop_name': crop_name,
                'offer_price': offer_price,
                'status': status,
                'date_offered': date_offered,
            }
        )
    print(f"Imported {len(rows)} buyer offers")

def import_notifications(rows):
    for row in rows:
        if not isinstance(row, tuple) or len(row) != 7:
            continue
        id, user_id, type, title, message, is_read, created_at = row
        if not User.objects.filter(id=user_id).exists():
            continue
        try:
            created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S') if created_at else None
        except:
            pass
        Notification.objects.get_or_create(
            id=id,
            defaults={
                'user_id': user_id,
                'type': type,
                'title': title,
                'message': message,
                'is_read': bool(is_read),
                'created_at': created_at,
            }
        )
    print(f"Imported {len([r for r in rows if isinstance(r, tuple) and len(r) == 7 and User.objects.filter(id=r[1]).exists()])} notifications")

def import_otp_tokens(rows):
    for row in rows:
        if not isinstance(row, tuple) or len(row) != 6:
            continue
        id, user_id, otp_code, expires_at, used, created_at = row
        if not User.objects.filter(id=user_id).exists():
            continue
        try:
            expires_at = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S') if expires_at else None
        except:
            pass
        OTPToken.objects.get_or_create(
            id=id,
            defaults={
                'user_id': user_id,
                'otp_code': otp_code,
                'expires_at': expires_at,
            }
        )
    print(f"Imported {len([r for r in rows if isinstance(r, tuple) and len(r) == 6 and User.objects.filter(id=r[1]).exists()])} OTP tokens")

def import_schedule_distribution(rows):
    for row in rows:
        id, distribution_type, quantity, recipient, status, officer, distribution_date, created_at = row
        try:
            distribution_date = datetime.strptime(distribution_date, '%Y-%m-%d') if distribution_date else None
            created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S') if created_at else None
        except:
            pass
        ScheduleDistribution.objects.get_or_create(
            id=id,
            defaults={
                'distribution_type': distribution_type,
                'quantity': quantity,
                'recipient': recipient,
                'status': status,
                'officer': officer,
                'distribution_date': distribution_date,
                'created_at': created_at,
            }
        )
    print(f"Imported {len(rows)} schedule distributions")

def import_activity_logs(rows):
    for row in rows:
        if not isinstance(row, tuple) or len(row) != 6:
            continue
        id, user_id, activity, details, ip_address, created_at = row
        if not User.objects.filter(id=user_id).exists():
            continue
        try:
            created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S') if created_at else None
        except:
            pass
        ActivityLog.objects.get_or_create(
            id=id,
            defaults={
                'user_id': user_id,
                'activity': activity,
                'details': details,
                'ip_address': ip_address,
                'created_at': created_at,
            }
        )
    print(f"Imported {len([r for r in rows if isinstance(r, tuple) and len(r) == 6 and User.objects.filter(id=r[1]).exists()])} activity logs")

if __name__ == "__main__":
    with open('agro/anitech.sql', 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    tables = [
        ('users', import_users),
        ('crops', import_crops),
        ('buyer_offers', import_buyer_offers),
        ('notifications', import_notifications),
        ('otp_tokens', import_otp_tokens),
        ('activity_logs', import_activity_logs),
    ]
    
    for table_name, import_func in tables:
        print(f"Importing {table_name}...")
        start = sql_content.find(f"INSERT INTO `{table_name}`")
        if start == -1:
            print(f"No INSERT for {table_name}")
            continue
        end = sql_content.find("INSERT INTO", start + 1)
        if end == -1:
            end = sql_content.find("--", start + 1)
        insert = sql_content[start:end]
        rows = parse_insert_values(insert)
        import_func(rows)
    
    print("Import completed!")