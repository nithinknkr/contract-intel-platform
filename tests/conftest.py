import os
import uuid
from pathlib import Path

from dotenv import load_dotenv

# MUST be the first executable lines in this file. Settings() and the DB
# engine are both constructed at import time (see app/core/config.py and
# app/db/session.py) — if any app.* import happens before this line runs,
# it will silently bind to .env (dev DB) instead of .env.test.
env_test_path = Path(__file__).parent.parent / ".env.test"
load_dotenv(env_test_path, override=True)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app
from app.models.user import User, UserRole
from app.services import queue as queue_module


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(settings.database_url)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_connection(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    yield connection
    transaction.rollback()
    connection.close()


@pytest.fixture()
def db_session(db_connection):
    Session = sessionmaker(bind=db_connection)
    session = Session()

    # Standard SQLAlchemy "join a savepoint" recipe: route handlers call
    # db.commit() freely (see documents.py / auth.py). Each commit ends the
    # SAVEPOINT, not the outer transaction opened in db_connection — this
    # listener immediately reopens a new SAVEPOINT so the test always has one
    # active, while the outer transaction (and everything inside it) is what
    # actually gets rolled back in db_connection's teardown above.
    nested = db_connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = db_connection.begin_nested()

    yield session
    session.close()


@pytest.fixture()
def mock_enqueue(monkeypatch):
    calls = []

    def fake_enqueue(func, *args, **kwargs):
        calls.append((func, args, kwargs))
        return None

    monkeypatch.setattr(queue_module.document_queue, "enqueue", fake_enqueue)
    return calls


@pytest.fixture()
def client(db_session, mock_enqueue):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class AuthedClient:
    def __init__(self, client: TestClient, org_id, user_id, access_token: str):
        self.client = client
        self.org_id = org_id
        self.user_id = user_id
        self.access_token = access_token


@pytest.fixture()
def signed_up_client(client, db_session):
    email = f"test-{uuid.uuid4()}@example.com"
    response = client.post(
        "/auth/signup",
        json={
            "email": email,
            "password": "TestPassword123!",
            "organization_name": f"Test Org {uuid.uuid4()}",
        },
    )
    assert response.status_code == 201, response.text
    tokens = response.json()

    user = db_session.query(User).filter(User.email == email).first()
    assert user is not None

    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"

    return AuthedClient(
        client=client,
        org_id=user.org_id,
        user_id=user.id,
        access_token=tokens["access_token"],
    )


@pytest.fixture()
def second_user_in_org(signed_up_client, db_session):
    admin = db_session.query(User).filter(User.id == signed_up_client.user_id).first()

    viewer = User(
        org_id=admin.org_id,
        email=f"viewer-{uuid.uuid4()}@example.com",
        hashed_password="x",
        role=UserRole.VIEWER,
    )
    db_session.add(viewer)
    db_session.flush()

    token = create_access_token(user_id=viewer.id, org_id=viewer.org_id, role=viewer.role)

    viewer_client = signed_up_client.client
    original_auth_header = viewer_client.headers.get("Authorization")
    viewer_client.headers["Authorization"] = f"Bearer {token}"

    yield viewer, token, viewer_client

    # restore the admin's auth header in case the same client object is reused
    if original_auth_header:
        viewer_client.headers["Authorization"] = original_auth_header