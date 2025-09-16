# make_db.py
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List
from litellm import completion
import os
from pydantic import BaseModel
from tqdm.auto import tqdm, trange

# 가짜 데이터 생성용 상수들
CITIES = [
    {"code": "NYC", "name": "New York", "country": "USA", "region": "North America"},
    {"code": "LAX", "name": "Los Angeles", "country": "USA", "region": "North America"},
    {"code": "CHI", "name": "Chicago", "country": "USA", "region": "North America"},
    {"code": "MIA", "name": "Miami", "country": "USA", "region": "North America"},
    {"code": "SFO", "name": "San Francisco", "country": "USA", "region": "North America"},
    {"code": "LON", "name": "London", "country": "UK", "region": "Europe"},
    {"code": "PAR", "name": "Paris", "country": "France", "region": "Europe"},
    {"code": "BER", "name": "Berlin", "country": "Germany", "region": "Europe"},
    {"code": "ROM", "name": "Rome", "country": "Italy", "region": "Europe"},
    {"code": "AMS", "name": "Amsterdam", "country": "Netherlands", "region": "Europe"},
    {"code": "BCN", "name": "Barcelona", "country": "Spain", "region": "Europe"},
    {"code": "TOK", "name": "Tokyo", "country": "Japan", "region": "Asia"},
    {"code": "SEO", "name": "Seoul", "country": "South Korea", "region": "Asia"},
    {"code": "BKK", "name": "Bangkok", "country": "Thailand", "region": "Asia"},
    {"code": "SIN", "name": "Singapore", "country": "Singapore", "region": "Asia"},
    {"code": "HKG", "name": "Hong Kong", "country": "Hong Kong", "region": "Asia"},
    {"code": "SYD", "name": "Sydney", "country": "Australia", "region": "Oceania"},
    {"code": "MEL", "name": "Melbourne", "country": "Australia", "region": "Oceania"},
    {"code": "DUB", "name": "Dubai", "country": "UAE", "region": "Middle East"},
    {"code": "IST", "name": "Istanbul", "country": "Turkey", "region": "Europe/Asia"},
]

PROPERTY_TYPES = ["apartment", "house", "villa", "studio", "loft", "condo", "townhouse", "cabin", "chalet", "castle"]
AMENITIES = [
    "wifi", "kitchen", "parking", "pool", "gym", "air_conditioning", 
    "heating", "tv", "washer", "dryer", "hot_tub", "fireplace",
    "balcony", "garden", "pets_allowed", "smoking_allowed", "elevator",
    "workspace", "iron", "hair_dryer", "shampoo", "breakfast", "laptop_friendly"
]

# Pydantic models for structured LLM output
class PropertyDescription(BaseModel):
    title: str
    description: str
    neighborhood_description: str

class UserProfile(BaseModel):
    first_name: str
    last_name: str
    bio: str
    interests: List[str]

class ReviewContent(BaseModel):
    comment: str
    pros: List[str]
    cons: List[str]

def generate_property_description_with_llm(city: Dict, prop_type: str) -> PropertyDescription:
    """Generate realistic property description using LLM."""
    try:
        response = completion(
            model="gpt-4.1-nano",
            messages=[{
                "role": "user", 
                "content": f"""Generate a realistic Airbnb property listing for a {prop_type} in {city['name']}, {city['country']}. 
                
                Create:
                1. A catchy title (max 60 chars)
                2. A detailed description (100-200 words) highlighting unique features
                3. A neighborhood description (50-100 words) mentioning local attractions
                
                Make it sound authentic and appealing to travelers."""
            }],
            response_format=PropertyDescription
        )
        return PropertyDescription.model_validate(json.loads(response.choices[0].message.content))
    except Exception as e:
        print(f"LLM generation failed: {e}, using fallback")
        return PropertyDescription(
            title=f"Beautiful {prop_type} in {city['name']}",
            description=f"A lovely {prop_type} located in the heart of {city['name']}. Perfect for your stay with modern amenities and great location access to local attractions.",
            neighborhood_description=f"Located in a vibrant neighborhood of {city['name']} with easy access to restaurants, shops, and public transportation."
        )

def generate_user_with_llm() -> UserProfile:
    """Generate realistic user profile using LLM."""
    try:
        response = completion(
            model="gpt-4.1-nano",
            messages=[{
                "role": "user",
                "content": """Generate a realistic Airbnb user profile with:
                1. First name (common international name)
                2. Last name (common surname)
                3. Bio (2-3 sentences about their travel style/interests)
                4. List of 3-5 interests/hobbies
                
                Make it diverse and authentic."""
            }],
            response_format=UserProfile
        )
        return UserProfile.model_validate(json.loads(response.choices[0].message.content))
    except Exception as e:
        print(f"LLM generation failed: {e}, using fallback")
        fallback_names = [
            ("Alex", "Johnson"), ("Maria", "Garcia"), ("James", "Smith"), ("Sarah", "Chen"),
            ("David", "Miller"), ("Emma", "Wilson"), ("Chris", "Brown"), ("Lisa", "Davis")
        ]
        first, last = random.choice(fallback_names)
        return UserProfile(
            first_name=first,
            last_name=last,
            bio="Love exploring new places and meeting people from different cultures. Always looking for unique experiences.",
            interests=["travel", "photography", "food", "culture"]
        )

def generate_review_with_llm(property_type: str, city_name: str, rating: int) -> ReviewContent:
    """Generate realistic review using LLM."""
    try:
        sentiment = "positive" if rating >= 4 else "mixed" if rating >= 3 else "negative"
        response = completion(
            model="gpt-4.1-nano",
            messages=[{
                "role": "user",
                "content": f"""Generate a realistic Airbnb review for a {property_type} in {city_name}. 
                Rating: {rating}/5 stars
                Sentiment: {sentiment}
                
                Create:
                1. A natural review comment (50-150 words)
                2. List of 2-4 pros (positive aspects)
                3. List of 1-3 cons (areas for improvement, empty if 5-star review)
                
                Make it sound like a real traveler wrote it."""
            }],
            response_format=ReviewContent
        )
        return ReviewContent.model_validate(json.loads(response.choices[0].message.content))
    except Exception as e:
        print(f"LLM generation failed: {e}, using fallback")
        comments = [
            "Great place to stay! Very clean and comfortable.",
            "Perfect location and amazing host. Highly recommended!",
            "Nice space but could use some updates.",
            "Exactly as described. Would book again.",
            "Beautiful property with great amenities."
        ]
        return ReviewContent(
            comment=random.choice(comments),
            pros=["clean", "good location"],
            cons=[] if rating >= 4 else ["minor issues"]
        )

def generate_property_id(index: int) -> str:
    return f"PROP{index:04d}"

def generate_user_id(index: int) -> str:
    return f"USER{index:04d}"

def generate_booking_id(index: int) -> str:
    return f"BOOK{index:04d}"

def generate_properties(count: int = 1000) -> Dict:
    properties = {}
    
    print(f"Generating {count} properties with LLM...")
    for i in trange(1, count + 1):
        if i % 50 == 0:
            print(f"Generated {i}/{count} properties...")
            
        prop_id = generate_property_id(i)
        city = random.choice(CITIES)
        prop_type = random.choice(PROPERTY_TYPES)
        
        # Generate description with LLM
        prop_desc = generate_property_description_with_llm(city, prop_type)
        
        # 가격은 지역과 숙소 타입에 따라 달라짐
        base_price = random.randint(30, 800)
        if city["code"] in ["NYC", "LON", "PAR", "TOK", "SFO", "DUB"]:
            base_price *= random.uniform(1.5, 2.5)
        if prop_type in ["villa", "house", "castle", "chalet"]:
            base_price *= random.uniform(1.3, 2.0)
        base_price = int(base_price)
            
        # 숙소별로 60일치 가격 및 예약 상태 생성
        start_date = datetime(2024, 5, 15)
        availability = {}
        
        for day in trange(60):
            date_str = (start_date + timedelta(days=day)).strftime("%Y-%m-%d")
            is_available = random.random() > 0.4  # 60% 확률로 예약 가능
            
            if is_available:
                # 주말이면 가격 인상, 성수기/비수기 반영
                weekday = (start_date + timedelta(days=day)).weekday()
                month = (start_date + timedelta(days=day)).month
                price = base_price
                
                # 주말 할증
                if weekday >= 5:  # 토요일, 일요일
                    price = int(price * random.uniform(1.2, 1.5))
                
                # 성수기 할증 (여름, 겨울 휴가철)
                if month in [6, 7, 8, 12]:
                    price = int(price * random.uniform(1.1, 1.4))
                    
                availability[date_str] = {
                    "status": "available",
                    "price_per_night": price,
                    "minimum_nights": random.choice([1, 2, 3, 7]),
                    "maximum_nights": random.choice([14, 30, 90])
                }
            else:
                availability[date_str] = {
                    "status": "booked",
                    "price_per_night": 0
                }
        
        properties[prop_id] = {
            "property_id": prop_id,
            "title": prop_desc.title,
            "description": prop_desc.description,
            "property_type": prop_type,
            "location": {
                "city": city["name"],
                "country": city["country"],
                "region": city["region"],
                "address": f"{random.randint(1, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'First', 'Second', 'Park', 'Broadway', 'Market'])} {random.choice(['Street', 'Avenue', 'Boulevard', 'Road'])}",
                "neighborhood": prop_desc.neighborhood_description,
                "latitude": round(random.uniform(-90, 90), 6),
                "longitude": round(random.uniform(-180, 180), 6)
            },
            "host_id": generate_user_id(random.randint(1, min(200, count // 5))),
            "capacity": {
                "guests": random.randint(1, 12),
                "bedrooms": random.randint(0, 6),
                "bathrooms": random.randint(1, 4),
                "beds": random.randint(1, 8)
            },
            "amenities": random.sample(AMENITIES, random.randint(8, 18)),
            "house_rules": {
                "check_in_time": f"{random.randint(14, 17)}:00",
                "check_out_time": f"{random.randint(10, 12)}:00",
                "pets_allowed": random.choice([True, False]),
                "smoking_allowed": random.choice([True, False]),
                "parties_allowed": random.choice([True, False]),
                "quiet_hours": f"{random.randint(22, 23)}:00 - {random.randint(7, 9)}:00"
            },
            "rating": round(random.uniform(3.0, 5.0), 1),
            "review_count": random.randint(0, 300),
            "instant_book": random.choice([True, False]),
            "cancellation_policy": random.choice(["flexible", "moderate", "strict", "super_strict"]),
            "availability": availability
        }
    
    return properties

def generate_users(count: int = 500) -> Dict:
    users = {}
    
    print(f"Generating {count} users with LLM...")
    for i in range(1, count + 1):
        if i % 25 == 0:
            print(f"Generated {i}/{count} users...")
            
        user_id = generate_user_id(i)
        
        # Generate user profile with LLM
        user_profile = generate_user_with_llm()
        
        # 결제 수단 생성
        payment_methods = {}
        
        # 신용카드 1-3개
        for j in range(random.randint(1, 3)):
            card_id = f"card_{i}_{j}"
            payment_methods[card_id] = {
                "type": "credit_card",
                "id": card_id,
                "brand": random.choice(["visa", "mastercard", "amex", "discover"]),
                "last_four": f"{random.randint(1000, 9999)}",
                "expiry_date": f"{random.randint(1, 12):02d}/{random.randint(25, 30)}"
            }
        
        # 기프트카드 0-2개
        if random.random() > 0.6:
            for k in range(random.randint(1, 2)):
                gift_id = f"gift_{i}_{k}"
                payment_methods[gift_id] = {
                    "type": "gift_card",
                    "id": gift_id,
                    "balance": random.randint(25, 1000)
                }
        
        # PayPal/디지털 결제 0-1개
        if random.random() > 0.7:
            digital_id = f"paypal_{i}"
            payment_methods[digital_id] = {
                "type": "digital_wallet",
                "id": digital_id,
                "provider": random.choice(["paypal", "apple_pay", "google_pay"])
            }
        
        users[user_id] = {
            "user_id": user_id,
            "profile": {
                "first_name": user_profile.first_name,
                "last_name": user_profile.last_name,
                "email": f"{user_profile.first_name.lower()}.{user_profile.last_name.lower()}{random.randint(1, 999)}@{random.choice(['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'])}",
                "phone": f"+{random.randint(1, 99)}-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                "date_of_birth": f"{random.randint(1970, 2005)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "profile_picture": f"https://example.com/avatar/{user_id}.jpg",
                "bio": user_profile.bio,
                "interests": user_profile.interests,
                "languages": random.sample(["English", "Spanish", "French", "German", "Italian", "Portuguese", "Japanese", "Korean", "Chinese"], random.randint(1, 3)),
                "join_date": (datetime.now() - timedelta(days=random.randint(30, 1800))).strftime("%Y-%m-%d")
            },
            "address": {
                "street": f"{random.randint(1, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Park', 'Broadway'])} {random.choice(['St', 'Ave', 'Blvd'])}",
                "city": random.choice([c["name"] for c in CITIES]),
                "country": random.choice([c["country"] for c in CITIES]),
                "zip_code": f"{random.randint(10000, 99999)}"
            },
            "payment_methods": payment_methods,
            "membership_level": random.choice(["regular", "plus", "premium"]),
            "host_status": random.choice([True, False]),
            "verification": {
                "email_verified": True,
                "phone_verified": random.choice([True, False]),
                "id_verified": random.choice([True, False]),
                "work_verified": random.choice([True, False])
            },
            "preferences": {
                "currency": random.choice(["USD", "EUR", "GBP", "JPY", "KRW"]),
                "language": random.choice(["en", "es", "fr", "de", "ja", "ko"]),
                "notifications": {
                    "email": random.choice([True, False]),
                    "sms": random.choice([True, False]),
                    "push": random.choice([True, False])
                }
            },
            "bookings": []  # 나중에 예약 생성 시 채워짐
        }
    
    return users

def generate_bookings(users: Dict, properties: Dict, count: int = 300) -> Dict:
    bookings = {}
    user_ids = list(users.keys())
    property_ids = list(properties.keys())
    
    print(f"Generating {count} bookings...")
    for i in range(1, count + 1):
        if i % 25 == 0:
            print(f"Generated {i}/{count} bookings...")
            
        booking_id = generate_booking_id(i)
        user_id = random.choice(user_ids)
        property_id = random.choice(property_ids)
        
        # 체크인/체크아웃 날짜 생성 (더 다양한 기간)
        start_date = datetime(2024, 5, 15) + timedelta(days=random.randint(-30, 40))
        nights = random.choices([1, 2, 3, 4, 5, 6, 7, 10, 14, 21, 28], 
                               weights=[15, 20, 25, 15, 10, 8, 5, 1, 0.5, 0.3, 0.2])[0]
        end_date = start_date + timedelta(days=nights)
        
        # 가격 계산
        total_price = 0
        property_data = properties[property_id]
        for day in range(nights):
            date_str = (start_date + timedelta(days=day)).strftime("%Y-%m-%d")
            if date_str in property_data["availability"]:
                total_price += property_data["availability"][date_str].get("price_per_night", 100)
            else:
                total_price += random.randint(80, 300)
        
        # 수수료 추가
        service_fee = int(total_price * 0.12)
        cleaning_fee = random.randint(25, 100)
        taxes = int((total_price + service_fee + cleaning_fee) * 0.08)
        total_with_fees = total_price + service_fee + cleaning_fee + taxes
        
        # 게스트 수
        max_guests = property_data["capacity"]["guests"]
        guest_count = random.randint(1, min(max_guests, 6))
        
        booking_status = random.choices(
            ["confirmed", "pending", "cancelled", "completed", "checked_in"],
            weights=[40, 5, 15, 35, 5]
        )[0]
        
        # 특별 요청 생성 (가끔씩만)
        special_requests = ""
        if random.random() < 0.3:
            requests = [
                "Late check-in after 10 PM",
                "Early check-in if possible",
                "Need parking space for large vehicle",
                "Traveling with small pet (hypoallergenic)",
                "Celebrating anniversary - any special touches appreciated",
                "Business trip - need strong WiFi and workspace",
                "Traveling with elderly parent - need ground floor",
                "Vegetarian/vegan - any nearby restaurant recommendations?"
            ]
            special_requests = random.choice(requests)
        
        bookings[booking_id] = {
            "booking_id": booking_id,
            "user_id": user_id,
            "property_id": property_id,
            "check_in_date": start_date.strftime("%Y-%m-%d"),
            "check_out_date": end_date.strftime("%Y-%m-%d"),
            "nights": nights,
            "guest_count": guest_count,
            "status": booking_status,
            "base_price": total_price,
            "service_fee": service_fee,
            "cleaning_fee": cleaning_fee,
            "taxes": taxes,
            "total_price": total_with_fees,
            "booking_date": (start_date - timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d"),
            "payment_method_id": random.choice(list(users[user_id]["payment_methods"].keys())),
            "special_requests": special_requests,
            "cancellation_policy": random.choice(["flexible", "moderate", "strict", "super_strict"]),
            "host_notes": random.choice([
                "",
                "Welcome! Keys are in the lockbox - code is 1234.",
                "Please remove shoes inside the apartment.",
                "WiFi password is 'welcome123' - enjoy your stay!",
                "Check-in instructions sent via message.",
                "Looking forward to hosting you!"
            ]),
            "guest_message": random.choice([
                "",
                "Thank you for accepting our booking!",
                "Looking forward to our stay!",
                "Can't wait to explore the neighborhood.",
                "Thanks for the quick response!"
            ])
        }
        
        # 사용자의 예약 목록에 추가
        users[user_id]["bookings"].append(booking_id)
        
        # 해당 날짜들을 예약됨으로 표시 (confirmed/checked_in/completed인 경우)
        if booking_status in ["confirmed", "checked_in", "completed"]:
            for day in range(nights):
                date_str = (start_date + timedelta(days=day)).strftime("%Y-%m-%d")
                if date_str in property_data["availability"]:
                    property_data["availability"][date_str]["status"] = "booked"
    
    return bookings

def generate_reviews(bookings: Dict, properties: Dict, count: int = 200) -> Dict:
    reviews = {}
    completed_bookings = [bid for bid, booking in bookings.items() if booking["status"] == "completed"]
    
    # 완료된 예약보다 리뷰가 많을 수 없음
    actual_count = min(count, len(completed_bookings))
    selected_bookings = random.sample(completed_bookings, actual_count)
    
    print(f"Generating {actual_count} reviews with LLM...")
    for i, booking_id in enumerate(selected_bookings, 1):
        if i % 10 == 0:
            print(f"Generated {i}/{actual_count} reviews...")
            
        review_id = f"REV{i:04d}"
        booking = bookings[booking_id]
        property_data = properties[booking["property_id"]]
        
        # 평점 생성 (대부분 긍정적)
        rating = random.choices([1, 2, 3, 4, 5], weights=[2, 3, 10, 35, 50])[0]
        
        # LLM으로 리뷰 생성
        review_content = generate_review_with_llm(
            property_data["property_type"], 
            property_data["location"]["city"], 
            rating
        )
        
        reviews[review_id] = {
            "review_id": review_id,
            "booking_id": booking_id,
            "user_id": booking["user_id"],
            "property_id": booking["property_id"],
            "rating": rating,
            "comment": review_content.comment,
            "pros": review_content.pros,
            "cons": review_content.cons,
            "review_date": (datetime.strptime(booking["check_out_date"], "%Y-%m-%d") + timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d"),
            "helpful_votes": random.randint(0, 25),
            "response_from_host": random.choice([
                "",
                "Thank you for the lovely review!",
                "So glad you enjoyed your stay!",
                "Thanks for choosing our place - come back anytime!",
                "Appreciate the feedback, hope to host you again!"
            ]) if random.random() < 0.4 else ""
        }
    
    return reviews

def create_db():
    print("Creating comprehensive Airbnb mock database with LLM-generated content...")
    print("=" * 60)
    
    print("Step 1: Generating properties...")
    properties = generate_properties(100)
    
    print("\nStep 2: Generating users...")
    users = generate_users(100)
    
    print("\nStep 3: Generating bookings...")
    bookings = generate_bookings(users, properties, 80)
    
    print("\nStep 4: Generating reviews...")
    reviews = generate_reviews(bookings, properties, 200)
    
    # 통계 계산
    print("\n" + "=" * 60)
    print("DATABASE GENERATION COMPLETE!")
    print("=" * 60)
    
    # 가격 분석
    all_prices = []
    for prop in properties.values():
        for date_info in prop["availability"].values():
            if date_info["status"] == "available":
                all_prices.append(date_info["price_per_night"])
    
    avg_price = sum(all_prices) / len(all_prices) if all_prices else 0
    
    # 지역별 통계
    city_stats = {}
    for prop in properties.values():
        city = prop["location"]["city"]
        if city not in city_stats:
            city_stats[city] = 0
        city_stats[city] += 1
    
    db = {
        "properties": properties,
        "users": users,
        "bookings": bookings,
        "reviews": reviews,
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "generation_method": "LLM-assisted (gpt-4.1-nano)",
            "statistics": {
                "property_count": len(properties),
                "user_count": len(users),
                "booking_count": len(bookings),
                "review_count": len(reviews),
                "average_price_per_night": round(avg_price, 2),
                "cities_covered": len(city_stats),
                "most_popular_city": max(city_stats.keys(), key=city_stats.get) if city_stats else "N/A",
                "booking_statuses": {
                    status: sum(1 for b in bookings.values() if b["status"] == status)
                    for status in ["confirmed", "pending", "cancelled", "completed", "checked_in"]
                },
                "property_types": {
                    ptype: sum(1 for p in properties.values() if p["property_type"] == ptype)
                    for ptype in PROPERTY_TYPES
                }
            }
        }
    }
    
    return db

if __name__ == "__main__":
    print("🏠 Creating comprehensive Airbnb mock database with AI-generated content...")
    print("📊 Scaling up to 10x more data with realistic variety!")
    print("🤖 Using GPT-4.1-nano for content generation...")
    print()
    
    try:
        db = create_db()
        
        print("\n💾 Saving database to disk...")
        with open("db.json", "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        
        print("\n✅ Database created successfully!")
        print(f"📈 Final Statistics:")
        stats = db['metadata']['statistics']
        print(f"   • Properties: {stats['property_count']:,}")
        print(f"   • Users: {stats['user_count']:,}")
        print(f"   • Bookings: {stats['booking_count']:,}")
        print(f"   • Reviews: {stats['review_count']:,}")
        print(f"   • Cities: {stats['cities_covered']}")
        print(f"   • Average price: ${stats['average_price_per_night']:.2f}/night")
        print(f"   • Most popular city: {stats['most_popular_city']}")
        print(f"\n🎯 Ready for realistic Airbnb scenarios!")
        
    except Exception as e:
        print(f"\n❌ Error during generation: {e}")
        print("💡 Make sure you have OPENAI_API_KEY set or check your API quota")
