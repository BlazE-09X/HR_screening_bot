from aiogram.filters import BaseFilter
from aiogram.types import Message


class IsRecruiter(BaseFilter):
    def __init__(self, recruiter_ids: list[int]):
        self.recruiter_ids = recruiter_ids

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.recruiter_ids