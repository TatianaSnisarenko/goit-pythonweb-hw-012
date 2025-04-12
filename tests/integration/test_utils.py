from datetime import datetime

from sqlalchemy import select
from tests.integration.conftest import TestingSessionLocal
import uuid
from src.services.auth import Hash
from src.database.models import Contact, User
from src.utils.utils import to_dict

base_contact_data = {
    "first_name": "John",
    "last_name": "Doe",
    "phone": "1234567890",
    "birthday": "1990-01-01",
}


async def create_user(confirmed=False):
    hashed_password = Hash().get_password_hash("Password123!")

    user_name = str(uuid.uuid4()).replace("-", "")
    email = user_name + "@example.com"

    test_user = User(
        username=user_name,
        email=email,
        hashed_password=hashed_password,
        role="user",
        confirmed=confirmed,
        avatar="<https://twitter.com/gravatar>",
    )

    async with TestingSessionLocal() as session:
        session.add(test_user)
        await session.commit()
    return email


async def create_contact(user_email, birthday=datetime.today()):

    async with TestingSessionLocal() as session:
        stmt = select(User).filter_by(email=user_email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            test_contact = generate_contact(user.id, birthday)
            session.add(test_contact)
            await session.commit()
            await session.refresh(test_contact)
    return test_contact


def generate_contact(user_id, birthday):
    email = str(uuid.uuid4()).replace("-", "") + "@example.com"
    test_contact = Contact(
        first_name=base_contact_data["first_name"],
        last_name=base_contact_data["last_name"],
        phone=base_contact_data["phone"],
        birthday=birthday,
        email=email,
        user_id=user_id,
    )

    return test_contact
