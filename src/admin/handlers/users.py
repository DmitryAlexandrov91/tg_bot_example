from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from admin.constants import FIELDS_USER, PROMPT_MAP
from admin.keyboards import (
    build_confirm_keyboard,
    build_user_select_keyboard,
    fields_keyboard,
    fields_keyboard_edit,
    role_keyboard,
    timezone_keyboard,
)
from admin.services.users import (
    maybe_confirm_edit,
    show_summary_and_confirm,
    update_user_state,
)
from admin.states.users import EditUserForm, UserForm
from admin.validators import is_valid_email, is_valid_phone_number
from crud import user_crud
from models.models import User

router = Router(name='users')


@router.message(Command('create_user'))
async def cmd_create_user(
    message: Message,
    state: FSMContext,
) -> None:
    """Начало создания нового пользователя.Запускает FSM, запрашивая имя."""
    await state.clear()
    await message.answer('Введите имя пользователя:')
    await state.set_state(UserForm.first_name)


@router.message(UserForm.first_name)
async def proc_first_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Обработка имени пользователя."""
    if await update_user_state(
        state=state,
        key='first_name',
        value=message.text,
        next_state=UserForm.last_name,
        message=message,
        prompt='Введите фамилию:',
    ):
        return


@router.message(UserForm.last_name)
async def proc_last_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Обработка фамилии пользователя. Сохраняет её и просит отчество."""
    if await update_user_state(
        state=state,
        key='last_name',
        value=message.text,
        next_state=UserForm.patronymic,
        message=message,
        prompt='Введите отчество (или «-» если нет):',
    ):
        return


@router.message(UserForm.patronymic)
async def proc_patronymic(
    message: Message,
    state: FSMContext,
) -> None:
    """Обработка отчества. Если введён «-», сохраняется пустота."""
    text = message.text.strip()
    patronymic_value = ' ' if text == '-' else text
    if await update_user_state(
        state=state,
        key='patronymic',
        value=patronymic_value,
        next_state=UserForm.role,
        message=message,
        prompt='Выберите роль: ',
        reply_markup=role_keyboard,
    ):
        return


@router.callback_query(F.data.startswith('role:'), UserForm.role)
async def process_role_callback(
    call: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработка роли пользователя."""
    role = call.data.split(':')[1]
    await state.update_data(role=role)
    if await maybe_confirm_edit(call.message, state):
        return
    await call.message.edit_reply_markup()
    await call.message.answer('Введите TG ID (целое число):')
    await state.set_state(UserForm.tg_id)


@router.message(UserForm.tg_id)
async def proc_tg_id(
    message: Message,
    state: FSMContext,
) -> None:
    """Сохраняет TG ID и запрашивает email."""
    if not message.text.isdigit():
        await message.answer('TG ID должен быть числом. Введите ещё раз:')
        return
    if await update_user_state(
        state=state,
        key='tg_id',
        value=int(message.text),
        next_state=UserForm.email,
        message=message,
        prompt='Введите email:',
    ):
        return


@router.message(UserForm.email)
async def proc_email(
    message: Message,
    state: FSMContext,
) -> None:
    """Сохраняет email и запрашивает номер телефона."""
    email = message.text.strip()
    if not is_valid_email(email):
        await message.answer('Некорректный email! Попробуйте ещё раз.')
        return
    if await update_user_state(
        state=state,
        key='email',
        value=email,
        next_state=UserForm.phone_number,
        message=message,
        prompt='Введите номер телефона:',
    ):
        return


@router.message(UserForm.phone_number)
async def proc_phone(
    message: Message,
    state: FSMContext,
) -> None:
    """Сохраняет номер телефона и запрашивает часовой пояс."""
    phone = message.text.strip()
    if not is_valid_phone_number(phone):
        await message.answer(
            'Некорректный номер телефона. '
            'Введите номер в формате +71234567890 или 81234567890.',
        )
        return
    if await update_user_state(
        state=state,
        key='phone_number',
        value=phone,
        next_state=UserForm.timezone,
        message=message,
        prompt='Выберите часовой пояс: ',
        reply_markup=timezone_keyboard,
    ):
        return


@router.callback_query(F.data.startswith('timezone:'), UserForm.timezone)
async def process_timezone_callback(
    call: CallbackQuery,
    state: FSMContext,
) -> None:
    """Сохраняет часовой пояс и запрашивает дополнительную информацию."""
    tz = call.data.split(':', 1)[1]
    await state.update_data(timezone=tz)
    await call.message.edit_reply_markup()
    if await maybe_confirm_edit(call.message, state):
        return
    await call.message.answer(
        'Введите дополнительную информацию или «-» если нет:',
    )
    await state.set_state(UserForm.additional_info)


@router.message(UserForm.additional_info)
async def proc_additional_info(
    message: Message,
    state: FSMContext,
) -> None:
    """Записывает дополнительную информацию и показывает сводку."""
    text = message.text.strip()
    await state.update_data(additional_info=None if text == '-' else text)
    await show_summary_and_confirm(message, state)


@router.callback_query(
    lambda c: c.data == 'create_user:confirm_yes',
    UserForm.confirm,
)
async def callback_confirm_yes(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Подтверждение создания."""
    data = await state.get_data()
    if 'editing' in data:
        del data['editing']
    try:
        user = await user_crud.create(data, session)
        await call.message.edit_reply_markup()
        await call.message.answer(
            f'Пользователь создан:\n'
            f'{user.first_name} {user.last_name} ({user.role})',
        )
        await state.clear()
    except IntegrityError as error:
        await call.message.answer(f'Не удалось создать: {error}')


@router.callback_query(
    lambda c: c.data == 'create_user:redact_field',
    UserForm.confirm,
)
async def callback_redact_field(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Выводим инлайн-клавиатуру с полями для редактирования."""
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        'Выберите поле, которое хотите изменить:',
        reply_markup=fields_keyboard_edit,
    )


@router.callback_query(F.data.startswith('edit_fields_user_before:'))
async def callback_edit_specific_field(
    call: CallbackQuery,
    state: FSMContext,
) -> None:
    """Переход к редактированию конкретного поля."""
    field_key = call.data.split(':')[1]
    fsm_states = {
        'first_name': UserForm.first_name,
        'last_name': UserForm.last_name,
        'patronymic': UserForm.patronymic,
        'role': UserForm.role,
        'tg_id': UserForm.tg_id,
        'email': UserForm.email,
        'phone_number': UserForm.phone_number,
        'timezone': UserForm.timezone,
        'additional_info': UserForm.additional_info,
    }
    if field_key not in fsm_states:
        await call.message.answer('Ошибка: неизвестное поле.')
        return
    await state.update_data(editing=True)
    await call.message.edit_reply_markup()
    if field_key == 'role':
        await call.message.answer(
            PROMPT_MAP[field_key],
            reply_markup=role_keyboard,
        )
    elif field_key == 'timezone':
        await call.message.answer(
            PROMPT_MAP[field_key],
            reply_markup=timezone_keyboard,
        )
    else:
        await call.message.answer(PROMPT_MAP[field_key])
    await state.set_state(fsm_states[field_key])


@router.message(Command('edit_user'))
async def cmd_edit_user_start(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Начинаем редактирование."""
    await state.clear()
    users = await user_crud.get_multi(
        session,
        options=[selectinload(User.restaurant)],
    )
    if not users:
        await message.answer('Пользователи не найдены!')
        return
    await message.answer(
        'Выберите пользователя, которого хотите редактировать:',
        reply_markup=build_user_select_keyboard(
            users,
            prefix='edit_user_select',
        ),
    )


@router.callback_query(F.data.startswith('edit_user_select:'))
async def process_user_selected_for_edit(
    call: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработка выбора пользователя через кнопку."""
    tg_id = int(call.data.split(':')[1])
    await state.update_data(tg_id=tg_id)
    await call.message.edit_reply_markup()
    await call.message.answer(
        'Какое поле хотите изменить?',
        reply_markup=fields_keyboard,
    )


@router.callback_query(F.data.startswith('edit_field:'))
async def proc_edit_user_field(
    call: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработали выбор поля — спрашиваем новое значение."""
    field = call.data.split(':', 1)[1]
    await state.update_data(field=field)
    await call.message.edit_reply_markup()
    if field == 'role':
        await call.message.answer(
            PROMPT_MAP[field],
            reply_markup=role_keyboard,
        )
    elif field == 'timezone':
        await call.message.answer(
            PROMPT_MAP[field],
            reply_markup=timezone_keyboard,
        )
    else:
        await call.message.answer(PROMPT_MAP[field])
    await state.set_state(EditUserForm.value)


@router.callback_query(F.data.startswith('role:'), EditUserForm.value)
async def on_new_role(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка новой роли."""
    new_role = call.data.split(':', 1)[1]
    data = await state.get_data()
    user = await user_crud.get_user_by_tg_id(session, data['tg_id'])
    if not user:
        await call.message.answer('Пользователь не найден.')
        return
    await user_crud.update(user, {'role': new_role}, session)
    await call.message.answer(
        f'У {user.first_name} роль обновлена на {new_role}',
    )
    await call.message.edit_reply_markup()
    await state.clear()


@router.callback_query(F.data.startswith('timezone:'), EditUserForm.value)
async def on_new_timezone(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка нового часового пояса."""
    new_tz = call.data.split(':', 1)[1]
    data = await state.get_data()
    user = await user_crud.get_user_by_tg_id(session, data['tg_id'])
    if not user:
        await call.message.answer('Пользователь не найден.')
        return
    await user_crud.update(user, {'timezone': new_tz}, session)
    await call.message.answer(
        f'У {user.first_name} часовой пояс обновлён на {new_tz}',
    )
    await call.message.edit_reply_markup()
    await state.clear()


@router.message(EditUserForm.value)
async def proc_edit_user_value(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Запрос ввода значения."""
    data = await state.get_data()
    tg_id = data['tg_id']
    field = data['field']
    value = message.text.strip()
    if field in ('tg_id',):
        if not value.isdigit():
            await message.answer(
                'Значение должно быть числом. Попробуйте ещё раз:',
            )
            return
        value = int(value)
    user = await user_crud.get_user_by_tg_id(session, tg_id)
    if not user:
        await message.answer('Пользователь не найден.')
        await state.clear()
        return
    updated = await user_crud.update(user, {field: value}, session)
    await message.answer(
        f'Пользователь - {updated.first_name} обновлён!\n'
        f'Новое значение {FIELDS_USER[field]} - {getattr(updated, field)}',
    )
    await state.clear()


@router.message(Command('block_user'))
async def cmd_block_user_start(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Начинаем блокировку."""
    await state.clear()
    users = await user_crud.get_multi(
        session,
        options=[selectinload(User.restaurant)],
    )
    if not users:
        await message.answer('Пользователи не найдены!')
        return
    await message.answer(
        'Выберите пользователя, которого хотите заблокировать:',
        reply_markup=build_user_select_keyboard(
            users,
            prefix='block_user_select',
        ),
    )


@router.callback_query(F.data.startswith('block_user_select:'))
async def process_user_selected_for_block(
    call: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработка выбора пользователя через кнопку."""
    tg_id = int(call.data.split(':')[1])
    await state.update_data(tg_id=tg_id)
    await call.message.edit_reply_markup()
    await call.message.answer(
        'Уверены, что хотите заблокировать пользователя?',
        reply_markup=build_confirm_keyboard(tg_id, entity='user'),
    )


@router.callback_query(F.data.startswith('confirm_block_user'))
async def handle_confirm_block(
    call: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Блокировка сотрудника."""
    user_tg_id = int(call.data.split(':')[1])
    user = await user_crud.get_user_by_tg_id(session, user_tg_id)
    await call.message.edit_reply_markup()
    if not user:
        await call.message.answer('Пользователь не найден.')
        return
    updated = await user_crud.update(user, {'is_active': False}, session)
    await call.message.answer(
        f'Пользователь {updated.first_name} - успешно заблокирован.',
    )


@router.callback_query(F.data == 'cancel_block_user')
async def handle_cancel_block(
    call: CallbackQuery,
) -> None:
    """Отмена бллокировки."""
    await call.message.edit_reply_markup()
    await call.message.answer('Блокировка отменена')
    return


@router.message(F.text == 'Создать пользователя')
async def alias_create_user(
    message: Message,
    state: FSMContext,
) -> None:
    """Кнопка создания юзера."""
    await cmd_create_user(message, state)


@router.message(F.text == 'Редактировать пользователя')
async def alias_edit_user(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Кнопка рефреш юзера."""
    await cmd_edit_user_start(message, state, session)


@router.message(F.text == 'Заблокировать пользователя')
async def alias_block_user(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Кнопка блока юзера."""
    await cmd_block_user_start(message, state, session)
