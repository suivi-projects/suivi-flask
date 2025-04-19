import uuid
from datetime import datetime, timedelta
import random

# Sample data
sender_id = "86210023-881f-4f7c-9a0f-33a54544e177"
rider_id = "07d2857d-2de1-4178-bd55-9889954191cb"
locations = [
    ("Utawala", "Umoja, Nairobi", -1.2843808, 36.9680714, -1.2834369, 36.8928409),
    ("Embakasi, Nairobi", "Lavington Nairobi", -1.2946971, 36.9316253, -1.2740678, 36.7762269),
    ("Westlands, Nairobi", "Kileleshwa, Nairobi", -1.265590, 36.808350, -1.270000, 36.800000),
    ("Karen, Nairobi", "Runda, Nairobi", -1.319240, 36.711670, -1.210000, 36.820000),
    ("Thika, Kiambu", "Juja, Kiambu", -1.033330, 37.083330, -1.100000, 37.010000),
]
statuses = ["pending", "allocated", "in_progress", "shipped", "arrived"]
payment_statuses = ["paid", "unpaid"]
receiver_names = ["Paul", "Mark", "Alice", "John", "Mary", "Peter", "Jane", "David", "Grace", "James"]
receiver_contacts = ["0711470120", "0719210347", "0722123456", "0733123456", "0744123456", "0755123456"]

# Generate parcels
parcels = []
for i in range(50):  # Generate 50 parcels
    pickup_location, delivery_location, pickup_lat, pickup_lng, delivery_lat, delivery_lng = random.choice(locations)
    parcel = {
        "id": i + 1,  # Start from 1
        "sender_id": sender_id,
        "receiver_name": random.choice(receiver_names),
        "receiver_contact": random.choice(receiver_contacts),
        "pickup_location": pickup_location,
        "delivery_location": delivery_location,
        "description": "",
        "rider_id": rider_id,
        "status": random.choice(statuses),
        "expected_arrival": (datetime.now() + timedelta(days=random.randint(1, 7))).strftime("%B %d, %Y, %I:%M %p"),
        "tracking_number": ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=10)),
        "created_at": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d %H:%M:%S"),
        "pickup_lat": pickup_lat,
        "pickup_lng": pickup_lng,
        "delivery_lat": delivery_lat,
        "delivery_lng": delivery_lng,
        "payment_status": random.choice(payment_statuses),
        "stripe_charge_id": f"ch_{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=24))}",
    }
    parcels.append(parcel)

# Print SQL INSERT statements
for parcel in parcels:
    print(f"""
    INSERT INTO parcel (
        id, sender_id, receiver_name, receiver_contact, pickup_location, delivery_location, 
        description, rider_id, status, expected_arrival, tracking_number, created_at, 
        updated_at, pickup_lat, pickup_lng, delivery_lat, delivery_lng, payment_status, 
        stripe_charge_id
    ) VALUES (
        {parcel['id']}, '{parcel['sender_id']}', '{parcel['receiver_name']}', '{parcel['receiver_contact']}', 
        '{parcel['pickup_location']}', '{parcel['delivery_location']}', '{parcel['description']}', 
        '{parcel['rider_id']}', '{parcel['status']}', '{parcel['expected_arrival']}', 
        '{parcel['tracking_number']}', '{parcel['created_at']}', '{parcel['updated_at']}', 
        {parcel['pickup_lat']}, {parcel['pickup_lng']}, {parcel['delivery_lat']}, 
        {parcel['delivery_lng']}, '{parcel['payment_status']}', '{parcel['stripe_charge_id']}'
    );
    """)

