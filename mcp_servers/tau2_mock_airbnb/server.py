# server.py
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Database path
DB_PATH = Path(__file__).parent / "db.json"

def load_db() -> Dict[str, Any]:
    """Load the database from JSON file."""
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"properties": {}, "users": {}, "bookings": {}, "reviews": {}}

def save_db(db: Dict[str, Any]) -> None:
    """Save the database to JSON file."""
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def get_next_booking_id(db: Dict[str, Any]) -> str:
    """Generate next booking ID."""
    existing_ids = [int(bid.replace("BOOK", "")) for bid in db["bookings"].keys()]
    next_id = max(existing_ids, default=0) + 1
    return f"BOOK{next_id:03d}"

# Create the MCP server
mcp = FastMCP("airbnb_assistant", description="An assistant for Airbnb-like property booking and management.")

@mcp.tool()
def search_properties(
    city: Optional[str] = None,
    check_in_date: Optional[str] = None,
    check_out_date: Optional[str] = None,
    guests: Optional[int] = None,
    property_type: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Search for properties based on criteria.
    
    Args:
        city: City to search in
        check_in_date: Check-in date in YYYY-MM-DD format
        check_out_date: Check-out date in YYYY-MM-DD format  
        guests: Number of guests
        property_type: Type of property (apartment, house, villa, etc.)
        min_price: Minimum price per night
        max_price: Maximum price per night
    
    Returns:
        List of matching properties
    """
    db = load_db()
    results = []
    
    for prop_id, prop in db["properties"].items():
        # City filter
        if city and city.lower() not in prop["location"]["city"].lower():
            continue
            
        # Guest capacity filter
        if guests and prop["capacity"]["guests"] < guests:
            continue
            
        # Property type filter
        if property_type and prop["property_type"] != property_type:
            continue
            
        # Date availability filter
        if check_in_date and check_out_date:
            available = True
            current_date = datetime.strptime(check_in_date, "%Y-%m-%d")
            end_date = datetime.strptime(check_out_date, "%Y-%m-%d")
            total_price = 0
            
            while current_date < end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                if date_str not in prop["availability"]:
                    available = False
                    break
                day_info = prop["availability"][date_str]
                if day_info["status"] != "available":
                    available = False
                    break
                total_price += day_info["price_per_night"]
                current_date += timedelta(days=1)
                
            if not available:
                continue
                
            # Price filter
            nights = (datetime.strptime(check_out_date, "%Y-%m-%d") - datetime.strptime(check_in_date, "%Y-%m-%d")).days
            avg_price = total_price / nights if nights > 0 else total_price
            
            if min_price and avg_price < min_price:
                continue
            if max_price and avg_price > max_price:
                continue
                
            # Add pricing info to result
            prop_result = prop.copy()
            prop_result["search_total_price"] = total_price
            prop_result["search_avg_price"] = avg_price
        else:
            prop_result = prop.copy()
            
        results.append(prop_result)
    
    return results

@mcp.tool()
def get_property_details(property_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific property.
    
    Args:
        property_id: The property ID
        
    Returns:
        Property details
    """
    db = load_db()
    return db["properties"].get(property_id, {})

@mcp.tool()
def get_user_profile(user_id: str) -> Dict[str, Any]:
    """
    Get user profile information.
    
    Args:
        user_id: The user ID
        
    Returns:
        User profile data
    """
    db = load_db()
    return db["users"].get(user_id, {})

@mcp.tool()
def create_booking(
    user_id: str,
    property_id: str,
    check_in_date: str,
    check_out_date: str,
    guest_count: int,
    payment_method_id: str,
    special_requests: Optional[str] = ""
) -> Dict[str, Any]:
    """
    Create a new booking.
    
    Args:
        user_id: ID of the user making the booking
        property_id: ID of the property to book
        check_in_date: Check-in date in YYYY-MM-DD format
        check_out_date: Check-out date in YYYY-MM-DD format
        guest_count: Number of guests
        payment_method_id: Payment method to use
        special_requests: Any special requests
        
    Returns:
        Created booking details
    """
    db = load_db()
    
    # Validate user exists
    if user_id not in db["users"]:
        raise ValueError(f"User {user_id} not found")
        
    # Validate property exists
    if property_id not in db["properties"]:
        raise ValueError(f"Property {property_id} not found")
        
    user = db["users"][user_id]
    property_data = db["properties"][property_id]
    
    # Validate payment method
    if payment_method_id not in user["payment_methods"]:
        raise ValueError(f"Payment method {payment_method_id} not found for user")
        
    # Validate guest capacity
    if guest_count > property_data["capacity"]["guests"]:
        raise ValueError(f"Property can only accommodate {property_data['capacity']['guests']} guests")
        
    # Check availability and calculate price
    current_date = datetime.strptime(check_in_date, "%Y-%m-%d")
    end_date = datetime.strptime(check_out_date, "%Y-%m-%d")
    nights = (end_date - current_date).days
    total_price = 0
    
    # Validate dates
    if nights <= 0:
        raise ValueError("Check-out date must be after check-in date")
        
    # Check availability for each night
    while current_date < end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        if date_str not in property_data["availability"]:
            raise ValueError(f"Property not available on {date_str}")
        day_info = property_data["availability"][date_str]
        if day_info["status"] != "available":
            raise ValueError(f"Property not available on {date_str}")
        total_price += day_info["price_per_night"]
        current_date += timedelta(days=1)
    
    # Create booking
    booking_id = get_next_booking_id(db)
    booking = {
        "booking_id": booking_id,
        "user_id": user_id,
        "property_id": property_id,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "nights": nights,
        "guest_count": guest_count,
        "status": "confirmed",
        "total_price": total_price,
        "booking_date": datetime.now().strftime("%Y-%m-%d"),
        "payment_method_id": payment_method_id,
        "special_requests": special_requests,
        "cancellation_policy": "moderate",
        "host_notes": ""
    }
    
    # Update database
    db["bookings"][booking_id] = booking
    user["bookings"].append(booking_id)
    
    # Mark dates as booked
    current_date = datetime.strptime(check_in_date, "%Y-%m-%d")
    while current_date < end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        property_data["availability"][date_str]["status"] = "booked"
        current_date += timedelta(days=1)
    
    save_db(db)
    return booking

@mcp.tool()
def get_booking_details(booking_id: str) -> Dict[str, Any]:
    """
    Get booking details.
    
    Args:
        booking_id: The booking ID
        
    Returns:
        Booking details
    """
    db = load_db()
    return db["bookings"].get(booking_id, {})

@mcp.tool()
def get_user_bookings(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all bookings for a user.
    
    Args:
        user_id: The user ID
        
    Returns:
        List of user's bookings
    """
    db = load_db()
    if user_id not in db["users"]:
        return []
    
    user_booking_ids = db["users"][user_id]["bookings"]
    bookings = []
    for booking_id in user_booking_ids:
        if booking_id in db["bookings"]:
            bookings.append(db["bookings"][booking_id])
    
    return bookings

@mcp.tool()
def cancel_booking(booking_id: str, reason: str = "") -> Dict[str, Any]:
    """
    Cancel a booking.
    
    Args:
        booking_id: The booking ID to cancel
        reason: Reason for cancellation
        
    Returns:
        Updated booking details
    """
    db = load_db()
    
    if booking_id not in db["bookings"]:
        raise ValueError(f"Booking {booking_id} not found")
        
    booking = db["bookings"][booking_id]
    
    if booking["status"] == "cancelled":
        raise ValueError("Booking is already cancelled")
        
    if booking["status"] == "completed":
        raise ValueError("Cannot cancel completed booking")
    
    # Update booking status
    booking["status"] = "cancelled"
    booking["cancellation_reason"] = reason
    booking["cancellation_date"] = datetime.now().strftime("%Y-%m-%d")
    
    # Free up the dates
    property_data = db["properties"][booking["property_id"]]
    current_date = datetime.strptime(booking["check_in_date"], "%Y-%m-%d")
    end_date = datetime.strptime(booking["check_out_date"], "%Y-%m-%d")
    
    while current_date < end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        if date_str in property_data["availability"]:
            property_data["availability"][date_str]["status"] = "available"
        current_date += timedelta(days=1)
    
    save_db(db)
    return booking

@mcp.tool()
def add_review(
    booking_id: str,
    rating: int,
    comment: str
) -> Dict[str, Any]:
    """
    Add a review for a completed booking.
    
    Args:
        booking_id: The booking ID
        rating: Rating from 1-5
        comment: Review comment
        
    Returns:
        Created review
    """
    db = load_db()
    
    if booking_id not in db["bookings"]:
        raise ValueError(f"Booking {booking_id} not found")
        
    booking = db["bookings"][booking_id]
    
    if booking["status"] != "completed":
        raise ValueError("Can only review completed bookings")
        
    if not (1 <= rating <= 5):
        raise ValueError("Rating must be between 1 and 5")
    
    # Generate review ID
    existing_review_ids = [int(rid.replace("REV", "")) for rid in db["reviews"].keys()]
    next_id = max(existing_review_ids, default=0) + 1
    review_id = f"REV{next_id:03d}"
    
    review = {
        "review_id": review_id,
        "booking_id": booking_id,
        "user_id": booking["user_id"],
        "property_id": booking["property_id"],
        "rating": rating,
        "comment": comment,
        "review_date": datetime.now().strftime("%Y-%m-%d"),
        "helpful_votes": 0
    }
    
    db["reviews"][review_id] = review
    save_db(db)
    
    return review

@mcp.tool()
def get_property_reviews(property_id: str) -> List[Dict[str, Any]]:
    """
    Get all reviews for a property.
    
    Args:
        property_id: The property ID
        
    Returns:
        List of reviews for the property
    """
    db = load_db()
    reviews = []
    
    for review in db["reviews"].values():
        if review["property_id"] == property_id:
            reviews.append(review)
    
    return sorted(reviews, key=lambda x: x["review_date"], reverse=True)

@mcp.tool()
def calculate_booking_cost(
    property_id: str,
    check_in_date: str,
    check_out_date: str
) -> Dict[str, Any]:
    """
    Calculate the total cost for a booking.
    
    Args:
        property_id: The property ID
        check_in_date: Check-in date in YYYY-MM-DD format
        check_out_date: Check-out date in YYYY-MM-DD format
        
    Returns:
        Cost breakdown
    """
    db = load_db()
    
    if property_id not in db["properties"]:
        raise ValueError(f"Property {property_id} not found")
        
    property_data = db["properties"][property_id]
    
    current_date = datetime.strptime(check_in_date, "%Y-%m-%d")
    end_date = datetime.strptime(check_out_date, "%Y-%m-%d")
    nights = (end_date - current_date).days
    
    if nights <= 0:
        raise ValueError("Check-out date must be after check-in date")
    
    nightly_costs = []
    total_price = 0
    
    while current_date < end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        if date_str not in property_data["availability"]:
            raise ValueError(f"Property not available on {date_str}")
        day_info = property_data["availability"][date_str]
        if day_info["status"] != "available":
            raise ValueError(f"Property not available on {date_str}")
        nightly_costs.append({
            "date": date_str,
            "price": day_info["price_per_night"]
        })
        total_price += day_info["price_per_night"]
        current_date += timedelta(days=1)
    
    # Calculate fees (simplified)
    service_fee = int(total_price * 0.12)  # 12% service fee
    cleaning_fee = 50  # Fixed cleaning fee
    taxes = int((total_price + service_fee + cleaning_fee) * 0.08)  # 8% tax
    
    return {
        "property_id": property_id,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "nights": nights,
        "nightly_costs": nightly_costs,
        "subtotal": total_price,
        "service_fee": service_fee,
        "cleaning_fee": cleaning_fee,
        "taxes": taxes,
        "total": total_price + service_fee + cleaning_fee + taxes
    }

@mcp.tool()
def list_cities() -> List[Dict[str, str]]:
    """
    Get list of all cities with available properties.
    
    Returns:
        List of cities
    """
    db = load_db()
    cities = set()
    
    for prop in db["properties"].values():
        cities.add((prop["location"]["city"], prop["location"]["country"]))
    
    return [{"city": city, "country": country} for city, country in sorted(cities)]

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
