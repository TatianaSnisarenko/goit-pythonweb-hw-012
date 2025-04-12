from tests.conftest import TestingSessionLocal
import uuid
from src.services.auth import Hash
from src.database.models import User
from src.utils.utils import to_dict


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
