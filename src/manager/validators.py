from typing import Optional, Tuple

from .constants import MAX_ANSWERS


def validate_question_input(
    message_parts: list,
    max_answers: int = MAX_ANSWERS,
) -> Tuple[bool, Optional[str]]:
    """Валидатор загрузки вопроса."""
    if len(message_parts) <= 1:
        return (
            False,
            'Упс! Кажется, данные не введены.',
        )

    if len(message_parts[0]) < 5:
        return (
            False,
            'Вопрос слишком короткий',
        )

    for part in message_parts:
        if len(part) == 0:
            return (
                False,
                'Нельзя вводить пустые строки в качестве ответов!',
            )

    if len(message_parts) > 5:
        return (
            False,
            f'Допустимо указать не более {max_answers} вариантов ответа!',
        )

    return True, None
