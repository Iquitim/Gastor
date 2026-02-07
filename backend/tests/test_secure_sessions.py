
# import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os

# Add backend directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from core.database import Base, get_db
from core.models import User, PaperSession
from api.routes.auth import get_current_user

# Setup in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Create tables
Base.metadata.create_all(bind=engine)

# Override dependencies
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Mocked users
def mock_get_current_user_1():
    return User(id=1, email="user1@example.com", username="User One")

def mock_get_current_user_2():
    return User(id=2, email="user2@example.com", username="User Two")

def test_create_session_secure():
    # Authenticate as User 1
    app.dependency_overrides[get_current_user] = mock_get_current_user_1
    
    response = client.post("/api/live/start", json={
        "strategy_slug": "example_strategy",
        "coin": "BTCUSDT",
        "timeframe": "1h",
        "initial_balance": 10000,
        "slot": 1
    })
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Sessão iniciada com sucesso"
    session_id_1 = data["session_id"]
    
    # Verify User 1 can see the session
    response = client.get("/api/live/sessions")
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) == 1
    assert sessions[0]["id"] == session_id_1
    assert sessions[0]["slot"] == 1

def test_session_isolation():
    # User 1 created a session in previous test (or needs to create one here if tests are independent)
    # Re-create for independence
    app.dependency_overrides[get_current_user] = mock_get_current_user_1
    client.post("/api/live/start", json={
        "strategy_slug": "strat1", 
        "coin": "ETHUSDT", 
        "timeframe": "15m", 
        "initial_balance": 5000, 
        "slot": 1
    })
    
    # Switch to User 2
    app.dependency_overrides[get_current_user] = mock_get_current_user_2
    
    # User 2 should see NO sessions
    response = client.get("/api/live/sessions")
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) == 0

    # User 2 tries to access User 1's session (assuming ID 1 or we need to find it)
    # We can query DB directly or just try ID 1 if we reset DB between tests.
    # Since we use same engine/metadata across tests in this simple setup, state persists unless cleared.
    # But usually pytest runs isolate better. Here, it's one script.
    
    # Let's find User 1's session ID by peeking as User 1
    app.dependency_overrides[get_current_user] = mock_get_current_user_1
    sessions_1 = client.get("/api/live/sessions").json()
    session_id_1 = sessions_1[0]["id"]

    # Switch back to User 2
    app.dependency_overrides[get_current_user] = mock_get_current_user_2
    
    # Try to stop User 1's session
    response = client.post(f"/api/live/sessions/{session_id_1}/stop")
    assert response.status_code == 404 # Should be Not Found securely (or 403)

def test_slot_replacement():
    app.dependency_overrides[get_current_user] = mock_get_current_user_1
    
    # Start session in Slot 2
    response = client.post("/api/live/start", json={
        "strategy_slug": "strat_slot2_v1", 
        "coin": "SOLUSDT", 
        "timeframe": "1h", 
        "initial_balance": 1000, 
        "slot": 2
    })
    assert response.status_code == 200
    
    # Start ANOTHER session in Slot 2
    response = client.post("/api/live/start", json={
        "strategy_slug": "strat_slot2_v2", 
        "coin": "SOLUSDT", 
        "timeframe": "1h", 
        "initial_balance": 1000, 
        "slot": 2
    })
    assert response.status_code == 200
    
    # List sessions
    response = client.get("/api/live/sessions")
    sessions = response.json()
    
    # Should only have one ACTIVE session in slot 2 logic
    # The API implementation logic was: "se existir sessão rodando no slot, para ela".
    # And specifically "running" sessions.
    
    active_slot_2 = [s for s in sessions if s["slot"] == 2 and s["status"] == "running"]
    assert len(active_slot_2) == 1
    assert active_slot_2[0]["strategy_slug"] == "strat_slot2_v2"

if __name__ == "__main__":
    # Run tests manually if executed as script
    # This minimal runner allows running without pytest installed globally
    try:
        test_create_session_secure()
        print("test_create_session_secure passed")
        test_session_isolation()
        print("test_session_isolation passed")
        test_slot_replacement()
        print("test_slot_replacement passed")
    except AssertionError as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
