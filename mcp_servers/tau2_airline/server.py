# server.py
import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

DB_PATH = Path(__file__).parent / "db.json"
global_db = None

def load_db():
    global global_db
    if global_db is None:
        with open(DB_PATH, "r") as f:
            global_db = json.load(f)
    return global_db

def save_db(db):
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)

mcp = FastMCP("airline_assistant", description="An assistant for airline management tasks.")

@mcp.tool()
def list_flights() -> list:
    """모든 항공편 목록을 반환합니다."""
    db = load_db()
    return list(db["flights"].keys())

@mcp.tool()
def get_flight(flight_number: str) -> dict:
    """특정 항공편 정보를 반환합니다."""
    db = load_db()
    return db["flights"].get(flight_number, {})

@mcp.tool()
def list_users() -> list:
    """모든 사용자 목록을 반환합니다."""
    db = load_db()
    return list(db["users"].keys())

@mcp.tool()
def get_user(user_id: str) -> dict:
    """특정 사용자 정보를 반환합니다."""
    db = load_db()
    return db["users"].get(user_id, {})

@mcp.tool()
def list_reservations() -> list:
    """모든 예약 목록을 반환합니다."""
    db = load_db()
    return list(db["reservations"].keys())

@mcp.tool()
def get_reservation(reservation_id: str) -> dict:
    """특정 예약 정보를 반환합니다."""
    db = load_db()
    return db["reservations"].get(reservation_id, {})

@mcp.tool()
def search_direct_flight(origin: str, destination: str, date: str) -> list:
    """직항 항공편을 검색합니다."""
    db = load_db()
    results = []
    for flight in db["flights"].values():
        if flight.get("origin") == origin and flight.get("destination") == destination:
            # 날짜 및 status 등 추가 필터링 필요
            results.append(flight)
    return results

# 필요에 따라 예약 생성, 예약 취소, 결제 등 추가 함수 구현 가능

if __name__ == "__main__":
    mcp.run(transport='stdio')