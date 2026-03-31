"""
This module seeds the database with initial data for testing and demonstration.
"""
import random
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash
from app import create_app
from models import db, User, Donor, BloodInventory, BloodRequest, BLOOD_GROUPS

app = create_app()

# Major cities around the world with coordinates for testing the locator
CITIES = [
    # North America
    {"name": "New York", "lat": 40.7128, "lon": -74.0060},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
    {"name": "Toronto", "lat": 43.6532, "lon": -79.3832},
    # Europe
    {"name": "London", "lat": 51.5074, "lon": -0.1278},
    {"name": "Paris", "lat": 48.8566, "lon": 2.3522},
    {"name": "Berlin", "lat": 52.5200, "lon": 13.4050},
    # Asia
    {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946},
    {"name": "Singapore", "lat": 1.3521, "lon": 103.8198},
    # Australia
    {"name": "Sydney", "lat": -33.8688, "lon": 151.2093},
    # South America
    {"name": "Sao Paulo", "lat": -23.5505, "lon": -46.6333},
]

NAMES = ["Liam", "Olivia", "Noah", "Emma", "Oliver", "Ava", "James", "Isabella", "William", "Sophia",
         "Ben", "Chloe", "Dan", "Elena", "Finn", "Grace", "Hugo", "Iris", "Jack", "Kaia"]


def seed_data():
    """
    Seeds the database with initial data.
    """
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()

        print("Seeding Users...")
        admin = User(username='admin', email='admin@bbms.com', role='admin')
        admin.password_hash = generate_password_hash('admin123')
        staff = User(username='staff', email='staff@bbms.com', role='staff')
        staff.password_hash = generate_password_hash('staff123')
        db.session.add_all([admin, staff])

        print("Seeding Inventory...")
        for bg in BLOOD_GROUPS:
            inv = BloodInventory(
                blood_group=bg,
                units_available=random.randint(2, 25)
            )
            db.session.add(inv)

        print("Seeding Donors with Worldwide Coordinates...")
        now = datetime.now(timezone.utc)
        for i in range(100):
            city = random.choice(CITIES)
            # Add some jitter to coordinates so they don't all stack on top of each other
            lat = city['lat'] + random.uniform(-0.1, 0.1)
            lon = city['lon'] + random.uniform(-0.1, 0.1)

            # Randomize last donation date to test eligibility
            days_ago = random.randint(10, 100)
            last_date = (now - timedelta(days=days_ago)).date()

            donor = Donor(
                name=f"{random.choice(NAMES)} {random.choice(NAMES)}",
                blood_group=random.choice(BLOOD_GROUPS),
                contact=f"+1 {random.randint(100, 999)}-{random.randint(1000, 9999)}",
                email=f"donor{i}@example.com",
                address=f"{city['name']} District",
                latitude=lat,
                longitude=lon,
                last_donation_date=last_date
            )
            db.session.add(donor)

        print("Seeding Historical Requests for Prediction Engine...")
        # Create a trend for A+ (rising) and O- (stable)
        # We'll seed requests over the last 12 weeks
        for week in range(1, 13):
            week_date = now - timedelta(weeks=week)

            # Falling trend for some groups, rising for others
            # A+ Rising trend: 1, 2, 3, 4... requests per group per week
            for _ in range(week // 2 + 1):
                req = BloodRequest(
                    patient_name=f"Patient A+ {week}-{_}",
                    blood_group='A+',
                    units_required=random.randint(1, 4),
                    urgency='normal',
                    status='completed',
                    created_at=week_date
                )
                db.session.add(req)

            # O- Random but slightly higher
            for _ in range(random.randint(2, 5)):
                req = BloodRequest(
                    patient_name=f"Patient O- {week}-{_}",
                    blood_group='O-',
                    units_required=random.randint(1, 3),
                    urgency='urgent' if random.random() > 0.7 else 'normal',
                    status='completed',
                    created_at=week_date
                )
                db.session.add(req)

        # Pending urgent requests to trigger alerts
        pending_urgent = BloodRequest(
            patient_name="John Emergency",
            blood_group="B+",
            units_required=5,
            urgency="critical",
            status="pending"
        )
        db.session.add(pending_urgent)

        db.session.commit()
        print("Database seeded successfully with worldwide data!")


if __name__ == '__main__':
    seed_data()
