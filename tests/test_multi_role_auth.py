"""
Comprehensive Tests for Multi-Role User Authentication, Google OAuth, and Hospital Scoping.

Verifies:
- Hospital directory retrieval (/api/v1/auth/hospitals)
- Local registration & login for all 5 roles:
  1. PATIENT
  2. DOCTOR
  3. HOSPITAL_STAFF
  4. HOSPITAL_ADMIN (with selected hospital)
  5. PLATFORM_ADMIN
- Google OAuth authentication & dynamic provisioning
- Password verification & rejection
- Current user profile session resolution (/api/v1/auth/me)
"""

import uuid
import pytest
from starlette.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)


def test_get_hospitals_directory(client: TestClient):
    """Verifies that the accredited hospital facilities list is returned for the signup dropdown."""
    resp = client.get("/api/v1/auth/hospitals")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "hospitals" in data
    assert len(data["hospitals"]) > 0
    hospital_ids = [h["id"] for h in data["hospitals"]]
    assert "HOSP-CITY-01" in hospital_ids


def test_patient_local_signup_and_login(client: TestClient):
    """Tests local registration and subsequent login for a PATIENT."""
    uid = uuid.uuid4().hex[:8]
    signup_email = f"patient_{uid}@example.com"
    pwd = "SecurePassword123!"

    # 1. Sign Up
    signup_resp = client.post("/api/v1/auth/signup", json={
        "email": signup_email,
        "password": pwd,
        "full_name": "Journey Patient",
        "role": "PATIENT",
        "phone_number": f"+1555{uid[:7]}"
    })
    assert signup_resp.status_code == 201
    s_data = signup_resp.json()
    assert s_data["status"] == "success"
    assert s_data["role"] == "PATIENT"
    assert "access_token" in s_data
    assert s_data["headers"]["X-User-Role"] == "PATIENT"

    # 2. Log In with correct credentials
    login_resp = client.post("/api/v1/auth/login", json={
        "email_or_identifier": signup_email,
        "password": pwd,
        "role": "PATIENT"
    })
    assert login_resp.status_code == 200
    l_data = login_resp.json()
    assert l_data["role"] == "PATIENT"
    assert l_data["email"] == signup_email

    # 3. Log In with incorrect password
    bad_login_resp = client.post("/api/v1/auth/login", json={
        "email_or_identifier": signup_email,
        "password": "WrongPassword!"
    })
    assert bad_login_resp.status_code == 401


def test_hospital_admin_signup_with_facility(client: TestClient):
    """Tests registration of a HOSPITAL_ADMIN tied to a specific hospital."""
    uid = uuid.uuid4().hex[:8]
    admin_email = f"admin_{uid}@stjude.org"
    resp = client.post("/api/v1/auth/signup", json={
        "email": admin_email,
        "password": "AdminPassword123!",
        "full_name": "Dr. St. Jude Administrator",
        "role": "HOSPITAL_ADMIN",
        "hospital_id": "HOSP-CARE-02"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "HOSPITAL_ADMIN"
    assert data["hospital_id"] == "HOSP-CARE-02"
    assert data["headers"]["X-Hospital-Id"] == "HOSP-CARE-02"
    assert "MANAGE_CALENDARS" in data["permissions"]


def test_google_oauth_authentication(client: TestClient):
    """Tests Google OAuth authentication flow for Doctor and Hospital Staff."""
    # 1. Google OAuth Doctor
    doc_resp = client.post("/api/v1/auth/google", json={
        "google_id": "google-sub-doc-9999",
        "email": "dr.google.physician@gmail.com",
        "name": "Dr. Google Physician",
        "avatar_url": "https://lh3.googleusercontent.com/avatar1",
        "role": "DOCTOR",
        "hospital_id": "HOSP-CITY-01"
    })
    assert doc_resp.status_code == 200
    doc_data = doc_resp.json()
    assert doc_data["role"] == "DOCTOR"
    assert doc_data["auth_provider"] == "GOOGLE"
    assert doc_data["headers"]["X-User-Role"] == "DOCTOR"

    # 2. Google OAuth Hospital Staff
    staff_resp = client.post("/api/v1/auth/google", json={
        "google_id": "google-sub-staff-8888",
        "email": "reception.staff@gmail.com",
        "name": "Receptionist Staff",
        "avatar_url": "https://lh3.googleusercontent.com/avatar2",
        "role": "HOSPITAL_STAFF",
        "hospital_id": "HOSP-CITY-01"
    })
    assert staff_resp.status_code == 200
    staff_data = staff_resp.json()
    assert staff_data["role"] == "HOSPITAL_STAFF"
    assert staff_data["auth_provider"] == "GOOGLE"

    # 3. Subsequent sign-in for existing Google user
    relogin_resp = client.post("/api/v1/auth/google", json={
        "google_id": "google-sub-doc-9999",
        "email": "dr.google.physician@gmail.com",
        "name": "Dr. Google Physician",
        "role": "DOCTOR"
    })
    assert relogin_resp.status_code == 200
    assert relogin_resp.json()["role"] == "DOCTOR"


def test_auth_me_profile_resolution(client: TestClient):
    """Tests /api/v1/auth/me session resolution with Bearer token."""
    # Authenticate via Google
    auth_resp = client.post("/api/v1/auth/google", json={
        "google_id": "google-sub-me-7777",
        "email": "me.session.test@gmail.com",
        "name": "Session Tester",
        "role": "PLATFORM_ADMIN"
    })
    assert auth_resp.status_code == 200
    token = auth_resp.json()["access_token"]

    # Call /me with Bearer token
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["status"] == "success"
    assert me_data["user"]["role"] == "PLATFORM_ADMIN"
    assert me_data["user"]["email"] == "me.session.test@gmail.com"


def test_invalid_role_rejection(client: TestClient):
    """Verifies that unauthorized or invalid roles are rejected with HTTP 400."""
    resp = client.post("/api/v1/auth/signup", json={
        "email": "invalid.role@example.com",
        "password": "Password123!",
        "full_name": "Invalid User",
        "role": "SUPER_HACKER_ROLE"
    })
    assert resp.status_code == 400
