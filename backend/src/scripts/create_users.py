import asyncio
import sys
import os

# Add src to path if running directly
sys.path.append(os.path.join(os.getcwd(), "src"))

from sqlalchemy import select
from core.models.db_helper import db_helper
from core.models.user import User
from core.security import get_password_hash

async def create_users():
    async with db_helper.session_factory() as session:
        # Get users from environment variables or use defaults
        user1_login = os.getenv("DEFAULT_USER_LOGIN")
        user1_email = os.getenv("DEFAULT_USER_EMAIL")
        user1_name = os.getenv("DEFAULT_USER_NAME")
        user1_password = os.getenv("DEFAULT_USER_PASSWORD")
        
        user2_login = os.getenv("SECOND_USER_LOGIN")
        user2_email = os.getenv("SECOND_USER_EMAIL")
        user2_name = os.getenv("SECOND_USER_NAME")
        user2_password = os.getenv("SECOND_USER_PASSWORD")

        users_to_create = [
            {
                "login": user1_login,
                "email": user1_email,
                "password": user1_password,
                "name": user1_name,
                "is_active": True,
                "is_private": False
            },
            {
                "login": user2_login,
                "email": user2_email,
                "password": user2_password,
                "name": user2_name,
                "is_active": True,
                "is_private": False
            }
        ]

        for user_data in users_to_create:
            stmt = select(User).where(User.login == user_data["login"])
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"User '{user_data['login']}' already exists.")
            else:
                print(f"Creating user '{user_data['login']}'...")
                new_user = User(
                    login=user_data["login"],
                    email=user_data["email"],
                    password=get_password_hash(user_data["password"]),
                    name=user_data["name"],
                    is_active=user_data["is_active"],
                    is_private=user_data["is_private"]
                )
                session.add(new_user)
                await session.commit()
                print(f"User '{user_data['login']}' created successfully.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(create_users())
