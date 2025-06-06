from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.models import Question


class QuestionCRUD(CRUDBase):
    """CRUD модели вопросов."""

    async def get_by_id(
        self, question_id: int, session: AsyncSession,
    ) -> Question | None:
        """Получить вопрос по их ID."""
        return await session.get(Question, question_id)

    async def update_user_answer(
        self, question_id: int, answer_index: int, session: AsyncSession,
    ) -> Question | None:
        """Добавление ответов юзера в модель вопроса."""
        question = await self.get_by_id(question_id, session)
        if question is None:
            return None
        question.user_answer = answer_index
        await session.commit()
        await session.refresh(question)
        return question


question_crud = QuestionCRUD(Question)
