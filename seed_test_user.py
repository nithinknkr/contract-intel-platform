import uuid
from app.db.session import SessionLocal
from app.models.organization import Organization
from app.models.user import User, UserRole

db = SessionLocal()
org = Organization(id=uuid.uuid4(), name="Test Org")
db.add(org)
db.flush()

user = User(
    id=uuid.uuid4(), org_id=org.id, email="test@example.com",
    hashed_password="x", role=UserRole.ADMIN,
)
db.add(user)
db.commit()

print(f"org_id: {org.id}")
print(f"user_id: {user.id}")
db.close()