import random

from sqlalchemy import event, exists, select
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapper


class HumanReadablePKMixin:
    """
    Mixin class for models requiring a human readable primary key generator.
    """

    PK_MAX_RETRIES = 15  # Maximum number of retries to avoid collisions
    PK_PREFIX = "DEF"  # Default prefix (override in subclasses)
    PK_NUM_LENGTH = 12  # Default numeric length (override in subclasses)
    PK_GROUP_SIZE = 4  # Default group size (override in subclasses)

    @classmethod
    def generate_human_readable_pk(cls) -> str:
        """
        Generate a primary key with a given prefix, numeric length, and grouping size.

        :param prefix: The prefix string (uppercase letters).
        :param num_length: The total length of the numeric part.
        :param group_size: The size of each group in the numeric part (default: 4).
        :return: A formatted primary key string.
        """

        random_number = (
            f"{random.randint(10 ** (cls.PK_NUM_LENGTH - 1), 10**cls.PK_NUM_LENGTH - 1)}"  # nosec: B311
        )
        grouped_number = "-".join(
            random_number[i : i + cls.PK_GROUP_SIZE]
            for i in range(0, len(random_number), cls.PK_GROUP_SIZE)
        )

        return f"{cls.PK_PREFIX}-{grouped_number}"

    @classmethod
    def build_id_regex(cls) -> str:
        prefix_part = f"^{cls.PK_PREFIX}"
        groups_count = (cls.PK_NUM_LENGTH + cls.PK_GROUP_SIZE - 1) // cls.PK_GROUP_SIZE
        group_part = (r"-\d{" + str(cls.PK_GROUP_SIZE) + r"}") * groups_count

        return f"{prefix_part}{group_part}$"


@event.listens_for(HumanReadablePKMixin, "before_insert", propagate=True)
def on_before_insert(mapper: Mapper, connection: Connection, obj: HumanReadablePKMixin) -> None:
    from app.db.models import Base

    if not isinstance(obj, Base):  # pragma: no cover
        return

    model_cls = obj.__class__

    for _ in range(model_cls.PK_MAX_RETRIES):
        pk = obj.generate_human_readable_pk()
        # Check for collision
        stmt = select(exists().where(model_cls.id == pk))
        result = connection.scalar(stmt)
        if not result:  # No collision found
            obj.id = pk
            return

    raise ValueError(
        f"Unable to generate unique primary key after {model_cls.PK_MAX_RETRIES} attempts."
    )
