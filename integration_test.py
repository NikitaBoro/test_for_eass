import pytest
import sys
from fastapi.testclient import TestClient

# Add the project directory to the system path
sys.path.append('./backend')

from backend.main import app, appointments, current_id
import backend.auth as auth

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_and_teardown():
    global current_id
    current_id = 1
    appointments.clear()
    auth.db.clear()
    auth.db.update({
        "admin": {
            "phone": "admin",
            "full_name": "admin admin",
            "email": "admin@email.com",
            "hashed_password": auth.pwd_context.hash("admin"),  # The password is admin
            "disabled": False,
            "role": "admin"
        }
    })
    yield

# Helper functions
def register_user(phone: str, full_name: str, email: str, password: str, role: str = "user"):
    response = client.post("/v1/register", json={
        "phone": phone,
        "full_name": full_name,
        "email": email,
        "role": role
    }, params={"password": password})
    return response

def login_user(phone: str, password: str):
    response = client.post("/v1/token", data={"username": phone, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def create_appointment(token_headers: dict, appointment_data: dict):
    response = client.post("/v1/appointments", json=appointment_data, headers=token_headers)
    return response

# Integration tests
def test_user_workflow():
    response = register_user(phone="1234567890", full_name="Test User", email="test@example.com", password="password123", role="user")
    assert response.status_code == 200

    headers = login_user("1234567890", "password123")
    response = create_appointment(headers, {
        "id": current_id,
        "name": "Test User",
        "phone": "1234567890",
        "date": "17-10-2024",
        "time": "10:00",
        "service": "Manicure"
    })
    assert response.status_code == 200

    response = client.get("/v1/appointments", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["phone"] == "1234567890"
    assert data[0]["name"] == "Test User"
    assert data[0]["date"] == "17-10-2024"
    assert data[0]["time"] == "10:00"
    assert data[0]["service"] == "Manicure"

def test_admin_workflow():
    # Register users
    register_user(phone="1111111111", full_name="Test User", email="test@example.com", password="password123", role="user")
    register_user(phone="2222222222", full_name="Test User2", email="test2@example.com", password="password123", role="user")

    # Login as admin
    admin_headers = login_user("admin", "admin")

    # Get all users
    response = client.get("/v1/admin/users", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    
    # Debugging output
    print("User Data:", data)
    
    assert len(data) == 4

    # Delete a user
    delete_response = client.delete("/v1/admin/users/1111111111", headers=admin_headers)
    assert delete_response.status_code == 200

    # Verify user deletion
    get_users_response = client.get("/v1/admin/users", headers=admin_headers)
    assert get_users_response.status_code == 200
    users_data = get_users_response.json()
    assert not any(user["phone"] == "1111111111" for user in users_data)

    # Create appointments for testing
    user_headers = login_user("2222222222", "password123")
    create_appointment(user_headers, {
        "id": current_id + 1,
        "name": "Test User2",
        "phone": "2222222222",
        "date": "17-10-2024",
        "time": "10:00",
        "service": "Manicure"
    })
    create_appointment(user_headers, {
        "id": current_id + 1,
        "name": "Test User2",
        "phone": "2222222222",
        "date": "18-10-2024",
        "time": "11:00",
        "service": "Pedicure"
    })

    # Get all appointments as admin
    get_appointments_response = client.get("/v1/admin/appointments/all", headers=admin_headers)
    assert get_appointments_response.status_code == 200
    appointments_data = get_appointments_response.json()
    assert len(appointments_data) == 2  # There should be at least two appointments
