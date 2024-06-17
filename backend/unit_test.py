import pytest
from fastapi.testclient import TestClient
from main import app
from data import appointments,current_id,db
import auth as auth



client = TestClient(app)

# Reset data between tests
@pytest.fixture(autouse=True)
def setup_and_teardown():
    global current_id
    current_id = 1
    appointments.clear()
    db.clear()
    db.update({
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

#Helper functions---------------------------------------------------------------------------------------

# Helper function to register a user
def register_user(phone: str, full_name: str, email: str, password: str, role: str = "user"):
    response = client.post("/v1/register", json={
        "phone": phone,
        "full_name": full_name,
        "email": email,
        "role": role
    }, params={"password": password})
    return response

# Helper function to login and get token
def login_user(phone: str, password: str):
    response = client.post("/v1/token", data={"username": phone, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# Helper function to create an appointment
def create_appointment(token_headers: dict, appointment_data: dict):
    response = client.post("/v1/appointments", json=appointment_data, headers=token_headers)
    return response


# User Tests -----------------------------------------------------------------------------------------------------

# Test registration
def test_register_user():
    response = register_user(phone="1234567890", full_name="Test User", email="test@example.com", password="password123", role="user")
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "1234567890"
    assert data["full_name"] == "Test User"
    assert data["email"] == "test@example.com"
    assert data["role"] == "user"


# Test login for access token
def test_login_for_access_token():
    register_user(phone="1234567890", full_name="Test User", email="test@example.com", password="password123", role="user")
    response = client.post("/v1/token", data={"username": "1234567890", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


# Test get current user info
def test_read_users_me():
    #Register and login user:
    register_user(phone="1234567890", full_name="Test User", email="test@example.com", password="password123", role="user")
    headers = login_user("1234567890", "password123")

    response = client.get("/v1/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "1234567890"
    assert data["full_name"] == "Test User"


# Test create appointment
def test_create_appointment():
    #Register and login user:
    register_user(phone="1234567890", full_name="Test User", email="test@example.com", password="password123", role="user")
    headers = login_user("1234567890", "password123")

    #Create an appointmnet:
    response = create_appointment(headers, {
        "id": current_id,
        "name": "Test User",
        "phone": "1234567890",
        "date": "17-10-2024",
        "time": "10:00",
        "service": "Manicure"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "1234567890"
    assert data["name"] == "Test User"
    assert data["date"] == "17-10-2024"
    assert data["time"] == "10:00"
    assert data["service"] == "Manicure"


# Test get appointments
def test_get_appointments():
    #Register and login user:
    register_user(phone="1234567890", full_name="Test User", email="test@example.com", password="password123", role="user")
    headers = login_user("1234567890", "password123")

    #Create an appointmnet: 
    create_appointment(headers, {
        "id": current_id,
        "name": "Test User",
        "phone": "1234567890",
        "date": "17-10-2024",
        "time": "10:00",
        "service": "Manicure"
    })

    response = client.get("/v1/appointments", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["phone"] == "1234567890"
    assert data[0]["name"] == "Test User"
    assert data[0]["date"] == "17-10-2024"
    assert data[0]["time"] == "10:00"
    assert data[0]["service"] == "Manicure"


# Test to update appointment
def test_update_appointment():
    #Register and login user::
    register_user(phone="1234567890", full_name="Test User", email="test@example.com", password="password123", role="user")
    headers = login_user("1234567890", "password123")

    #Create an appointmnet: 
    create_response = create_appointment(headers, {
        "id": current_id,
        "name": "Test User",
        "phone": "1234567890",
        "date": "17-10-2024",
        "time": "10:00",
        "service": "Manicure"
    })
    assert create_response.status_code == 200
    appointment_id = create_response.json()["id"]

    #Update appointment
    update_response = client.put(f"/v1/appointments/{appointment_id}", json={
        "id": appointment_id,
        "name": "Test User",
        "phone": "1234567890",
        "date": "18-10-2024",
        "time": "11:00",
        "service": "Pedicure"
    }, headers=headers)
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["name"] == "Test User"
    assert data["date"] == "18-10-2024"
    assert data["time"] == "11:00"
    assert data["service"] == "Pedicure"


# Test to delete appointment
def test_delete_appointment():
    # Register and login user:
    register_user(phone="1234567890", full_name="Test User", email="test@example.com", password="password123", role="user")
    headers = login_user("1234567890", "password123")

    # Create an appointment:
    create_response = create_appointment(headers, {
        "id": current_id,
        "name": "Test User",
        "phone": "1234567890",
        "date": "17-10-2024",
        "time": "10:00",
        "service": "Manicure"
    })
    assert create_response.status_code == 200
    create_data = create_response.json()
    appointment_id = create_data["id"]

    # Delete the appointment:
    delete_response = client.delete(f"/v1/appointments/{appointment_id}", headers=headers)
    assert delete_response.status_code == 200
    delete_data = delete_response.json()
    assert delete_data["id"] == appointment_id

    # Verify the appointment is deleted:
    get_response = client.get("/v1/appointments", headers=headers)
    assert get_response.status_code == 404


#Admin Tests -------------------------------------------------------------------------------------------------

# Test admin login
def test_admin_login():
    response = client.post("/v1/token", data={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


# Test admin get all users
def test_admin_get_all_users():
    register_user(phone="1111111111", full_name="Test User", email="test@example.com", password="password123", role="user")
    register_user(phone="2222222222", full_name="Test User2", email="test2@example.com", password="password123", role="user")
    # Login as admin
    admin_headers = login_user("admin", "admin")
    response = client.get("/v1/admin/users", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

# Test admin delete user
def test_admin_delete_user():
    # Register a new user
    register_user(phone="1234567890", full_name="Test User", email="test@example.com", password="password123", role="user")
    # Login as admin
    admin_headers = login_user("admin", "admin")
    response = client.delete("/v1/admin/users/1234567890", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "1234567890"
    assert data["full_name"] == "Test User"
    user_response = client.delete("/v1/admin/users/1234567890", headers=admin_headers)
    assert user_response.status_code == 404  # Expecting 404 Not Found

# Test admin get all appointments
def test_admin_get_appointments():
    # Register and login user to create appointments
    register_user(phone="1234567890", full_name="Test User", email="test@example.com", password="password123", role="user")
    user_headers = login_user("1234567890", "password123")

    # Create the first appointment
    create_appointment(user_headers, {
        "id": current_id,
        "name": "Test User",
        "phone": "1234567890",
        "date": "17-10-2024",
        "time": "10:00",
        "service": "Manicure"
    })

    # Create the second appointment
    create_appointment(user_headers, {
        "id": current_id + 1,
        "name": "Test User",
        "phone": "1234567890",
        "date": "18-10-2024",
        "time": "11:00",
        "service": "Pedicure"
    })

    # Login as admin
    admin_headers = login_user("admin", "admin")

    # Get all appointments as admin
    response = client.get("/v1/admin/appointments/all", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # There should be at least two appointments


# Test admin get appointments by phone
def test_admin_get_appointments_by_phone():
    # Register and login user to create appointments
    register_user(phone="1234567890", full_name="Test User", email="test@example.com", password="password123", role="user")
    user_headers = login_user("1234567890", "password123")
    
    # Create the first appointment
    create_appointment(user_headers, {
        "id": current_id,
        "name": "Test User",
        "phone": "1234567890",
        "date": "17-10-2024",
        "time": "10:00",
        "service": "Manicure"
    })

    # Login as admin
    admin_headers = login_user("admin", "admin")
    response = client.get("/v1/admin/appointments/phone/1234567890", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["phone"] == "1234567890"


# Test admin get appointments by month
def test_admin_get_appointments_by_month():
    # Register and login user to create appointments
    register_user(phone="1234567890", full_name="Test User", email="test@example.com", password="password123", role="user")
    user_headers = login_user("1234567890", "password123")
    
    # Create the first appointment
    create_appointment(user_headers, {
        "id": current_id,
        "name": "Test User",
        "phone": "1234567890",
        "date": "17-10-2024",
        "time": "10:00",
        "service": "Manicure"
    })

    admin_headers = login_user("admin", "admin")
    response = client.get("/v1/admin/appointments/month/10", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["date"].split("-")[1] == "10"


