"""Test script to verify the consolidated User model."""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import SessionLocal, engine
from src.models.user import User, UserRole

async def test_user_creation():
    """Test user creation and password hashing."""
    db = SessionLocal()
    try:
        # Create a test user
        test_email = "test@example.com"
        test_password = "testpassword123"
        
        user = User(
            email=test_email,
            username="testuser",
            name="Test User",
            role=UserRole.USER,
            is_active=True
        )
        user.set_password(test_password)
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Verify the user was created
        assert user.id is not None
        assert user.email == test_email
        assert user.check_password(test_password)
        assert not user.check_password("wrongpassword")
        assert user.role == UserRole.USER
        assert user.is_active is True
        
        print("✅ User model test passed!")
        
        # Clean up
        await db.delete(user)
        await db.commit()
        
    except Exception as e:
        await db.rollback()
        print(f"❌ Test failed: {e}")
        raise
    finally:
        await db.close()

async def main():
    """Run the test."""
    try:
        await test_user_creation()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
