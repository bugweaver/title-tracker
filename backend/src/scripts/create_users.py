import argparse
import asyncio
import sys
import os

sys.path.append(os.path.join(os.getcwd(), "src"))

from sqlalchemy import select
from core.models.db_helper import db_helper
from core.models.user import User
from core.security import get_password_hash


async def create_user(
    login: str,
    email: str,
    name: str,
    password: str,
    is_private: bool = False,
):
    async with db_helper.session_factory() as session:
        stmt = select(User).where(User.login == login)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            print(f"User '{login}' already exists, skipping.")
            return

        new_user = User(
            login=login,
            email=email,
            password=get_password_hash(password),
            name=name,
            is_active=True,
            is_private=is_private,
        )
        session.add(new_user)
        await session.commit()
        print(f"User '{login}' created successfully.")


def main():
    parser = argparse.ArgumentParser(description="Create a new user")
    parser.add_argument("--login", required=True, help="User login (unique)")
    parser.add_argument("--email", required=True, help="User email (unique)")
    parser.add_argument("--name", required=True, help="Display name")
    parser.add_argument("--password", required=True, help="User password")
    parser.add_argument(
        "--private",
        action="store_true",
        default=False,
        help="Make profile private",
    )

    args = parser.parse_args()

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(
        create_user(
            login=args.login,
            email=args.email,
            name=args.name,
            password=args.password,
            is_private=args.private,
        )
    )


if __name__ == "__main__":
    main()
