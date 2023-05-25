import factory

from app.db import models


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.User
        sqlalchemy_session = None

    id = factory.Sequence(lambda i: i)
    tg_id = factory.Sequence(lambda i: i)
    tg_username = factory.Sequence(lambda n: f"user{n}")
