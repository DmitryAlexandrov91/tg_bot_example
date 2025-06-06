from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from admin.constants import FIELDS_RESTAURANT, FIELD_LABLES
from admin.keyboards import (
    build_confirm_keyboard,
    build_restaurant_select_keyboard,
    build_user_select_keyboard,
    edit_fields_keyboard,
    fields_rest_keyboard,
)
from admin.services.restaurants import (
    show_summary_and_confirm_restaurant,
    update_restaurant_state,
)
from admin.states.restaurants import (
    EditRestaurantForm,
    RestaurantForm,
)
from crud import restaurant_crud, user_crud
from models.models import User

router = Router(name='restaurants')


@router.message(Command('create_restaurant'))
async def cmd_create_restaurant(
    message: Message,
    state: FSMContext,
) -> None:
    """Начало создания нового ресторана.Запрашивает название."""
    await state.clear()
    await message.answer('Введите название ресторана:')
    await state.set_state(RestaurantForm.name)


@router.message(RestaurantForm.name)
async def proc_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Обработка названия ресторана. Сохраняет его и просит полный адрес."""
    if await update_restaurant_state(
        state=state,
        key='name',
        value=message.text.strip(),
        next_state=RestaurantForm.full_address,
        message=message,
        prompt='Введите полный адрес:',
    ):
        return


@router.message(RestaurantForm.full_address)
async def proc_full_addr(
    message: Message,
    state: FSMContext,
) -> None:
    """Сохраняет полный адрес и запрашивает короткий (для стажёров)."""
    if await update_restaurant_state(
        state=state,
        key='full_address',
        value=message.text.strip(),
        next_state=RestaurantForm.short_address,
        message=message,
        prompt='Введите короткий адрес (для стажёров):',
    ):
        return


@router.message(RestaurantForm.short_address)
async def proc_short_addr(
    message: Message,
    state: FSMContext,
) -> None:
    """Сохраняет короткий адрес и запрашивает контактную информацию."""
    if await update_restaurant_state(
        state=state,
        key='short_address',
        value=message.text.strip(),
        next_state=RestaurantForm.contact_information,
        message=message,
        prompt='Введите контактную информацию:',
    ):
        return


@router.message(RestaurantForm.contact_information)
async def proc_contact(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Сохраняет контактную информацию и просит подтверждение."""
    await state.update_data(contact_information=message.text.strip())
    await show_summary_and_confirm_restaurant(message, state)


@router.callback_query(
    lambda c: c.data == 'create_rest:confirm_yes',
    RestaurantForm.confirm,
)
async def callback_confirm_yes(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Подтверждение создания."""
    data = await state.get_data()
    if 'editing' in data:
        del data['editing']
    try:
        rest = await restaurant_crud.create(data, session)
        await callback.message.edit_reply_markup()
        await callback.message.answer(
            f'Ресторан создан:\n'
            f'Название - {rest.name}, адрес - {rest.short_address}',
        )
        await state.clear()
    except IntegrityError as error:
        await callback.message.answer(f'Ошибка при сохранении: {error}')


@router.callback_query(
    lambda c: c.data == 'create_rest:redact_field',
    RestaurantForm.confirm,
)
async def callback_redact_field(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Выводим инлайн-клавиатуру с полями для редактирования."""
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        'Выберите поле, которое хотите изменить:',
        reply_markup=edit_fields_keyboard,
    )


@router.callback_query(F.data.startswith('edit_field_rest_before:'))
async def callback_edit_specific_field(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Переход к редактированию конкретного поля."""
    field_key = callback.data.split(':')[1]
    fsm_states = {
        'name': RestaurantForm.name,
        'full_address': RestaurantForm.full_address,
        'short_address': RestaurantForm.short_address,
        'contact_information': RestaurantForm.contact_information,
    }
    if field_key not in fsm_states:
        await callback.message.answer('Ошибка: неизвестное поле.')
        return
    await state.update_data(editing=True)
    await callback.message.edit_reply_markup()
    await callback.message.answer(FIELDS_RESTAURANT[field_key])
    await state.set_state(fsm_states[field_key])


@router.message(Command('edit_restaurant'))
async def cmd_edit_restaurant_start(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Старт для редактирования ресторана."""
    await state.clear()
    restaurants = await restaurant_crud.get_multi(session)
    if not restaurants:
        await message.answer('Рестораны не найдены!')
        return
    await message.answer(
        'Выберите ресторан для редактирования:',
        reply_markup=build_restaurant_select_keyboard(
            restaurants,
            prefix='edit_restaurant_select',
        ),
    )


@router.callback_query(F.data.startswith('edit_restaurant_select:'))
async def process_restaurant_selected_for_edit(
    call: CallbackQuery,
    state: FSMContext,
) -> None:
    """Показывает все рестораны."""
    rest_id = int(call.data.split(':')[1])
    await state.update_data(restaurant_id=rest_id)
    await call.message.edit_reply_markup()
    await call.message.answer(
        'Какое поле хотите изменить?',
        reply_markup=fields_rest_keyboard,
    )


@router.callback_query(F.data.startswith('edit_rest_field:'))
async def proc_edit_restaurant_field(
    call: CallbackQuery,
    state: FSMContext,
) -> None:
    """Показывает поля."""
    field = call.data.split(':')[1]
    await state.update_data(field=field)
    await call.message.edit_reply_markup()
    await call.message.answer(FIELDS_RESTAURANT[field])
    await state.set_state(EditRestaurantForm.value)


@router.message(EditRestaurantForm.value)
async def proc_edit_restaurant_value(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Ввод значения."""
    data = await state.get_data()
    restaurant_id = data['restaurant_id']
    field = data['field']
    value = message.text.strip()
    restaurant = await restaurant_crud.get(restaurant_id, session)
    if not restaurant:
        await message.answer('Ресторан не найден.')
        await state.clear()
        return
    updated = await restaurant_crud.update(restaurant, {field: value}, session)
    await message.answer(
        f'Ресторан {updated.name} - обновлён!.\n'
        f'Новое значение {FIELD_LABLES[field]} - {getattr(updated, field)}.',
    )
    await state.clear()


@router.message(Command('block_restaurant'))
async def cmd_block_restaurant_start(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Начинаем блокировку."""
    await state.clear()
    restaurants = await restaurant_crud.get_multi(session)
    if not restaurants:
        await message.answer('Рестораны не найдены!')
        return
    await message.answer(
        'Выберите ресторан для блокировки:',
        reply_markup=build_restaurant_select_keyboard(
            restaurants,
            prefix='block_restaurant_select',
        ),
    )


@router.callback_query(
    F.data.startswith('block_restaurant_select:'),
    )
async def process_restaurant_selected_for_edit(
    call: CallbackQuery,
    state: FSMContext,
) -> None:
    """Показывает все рестораны."""
    rest_id = int(call.data.split(':')[1])
    await state.update_data(restaurant_id=rest_id)
    await call.message.edit_reply_markup()
    await call.message.answer(
        'Уверены, что хотите заблокировать ресторан?',
        reply_markup=build_confirm_keyboard(rest_id, entity='restaurant'),
    )


@router.callback_query(F.data.startswith('confirm_block_restaurant'))
async def handle_confirm_block(
    call: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Блокировка сотрудника."""
    rest_id = int(call.data.split(':')[1])
    restaurant = await restaurant_crud.get(rest_id, session)
    await call.message.edit_reply_markup()
    if not restaurant:
        await call.message.answer('Ресторан не найден.')
        return
    updated = await restaurant_crud.update(
        restaurant,
        {'is_blocked': True},
        session,
    )
    await call.message.answer(
        f'Ресторан {updated.name} - успешно заблокирован.',
    )


@router.callback_query(F.data == 'cancel_block_restaurant')
async def handle_cancel_block(
    call: CallbackQuery,
) -> None:
    """Отмена бллокировки."""
    await call.message.edit_reply_markup()
    await call.message.answer('Блокировка отменена')
    return


@router.message(Command('assign_user'))
async def cmd_assign_user_start(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """1) Попросить выбрать пользователя."""
    await state.clear()
    users = await user_crud.get_multi(
        session,
        options=[selectinload(User.restaurant)],
    )
    if not users:
        await message.answer('Нет пользователей для привязки.')
        return
    await message.answer(
        'Выберите пользователя, которого нужно привязать к ресторану:',
        reply_markup=build_user_select_keyboard(users, prefix='assign_user'),
    )


@router.callback_query(F.data.startswith('assign_user:'))
async def on_user_selected(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Пользователь выбран — сохраним и предложим список ресторанов."""
    tg_id = int(call.data.split(':', 1)[1])
    await state.update_data(tg_id=tg_id)
    await call.message.edit_reply_markup()
    rest_list = await restaurant_crud.get_multi(session)
    if not rest_list:
        await call.message.answer('Нет ресторанов для привязки.')
        return
    await call.message.answer(
        'Выберите, к какому ресторану привязать пользователя:',
        reply_markup=build_restaurant_select_keyboard(
            rest_list,
            prefix='assign_rest',
        ),
    )


@router.callback_query(F.data.startswith('assign_rest:'))
async def on_restaurant_selected(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Ресторан выбран — сохраняем привязку."""
    rest_id = int(call.data.split(':', 1)[1])
    data = await state.get_data()
    tg_id = data['tg_id']
    restaurant = await restaurant_crud.get(rest_id, session)
    user = await user_crud.get_user_by_tg_id(session, tg_id)
    if not user:
        await call.message.answer('Пользователь не найден в БД.')
    else:
        await user_crud.update(user, {'restaurant_id': rest_id}, session)
        await call.message.answer(
            f'Готово!\nПользователь {user.first_name} '
            f'привязан к ресторану {restaurant.name}!',
        )
    await call.message.edit_reply_markup()
    await state.clear()


@router.message(F.text == 'Создать ресторан')
async def alias_create_restaurant(
    message: Message,
    state: FSMContext,
) -> None:
    """Кнопка создания ресторана."""
    await cmd_create_restaurant(message, state)


@router.message(F.text == 'Редактировать ресторан')
async def alias_edit_restaurant(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Кнопка рефреш ресторана."""
    await cmd_edit_restaurant_start(message, state, session)


@router.message(F.text == 'Заблокировать ресторан')
async def alias_block_restaurant(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Кнопка блока ресторана."""
    await cmd_block_restaurant_start(message, state, session)


@router.message(F.text == 'Привязать пользователя к ресторану')
async def alias_assign_user(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Кнопка привязки к ресторану."""
    await cmd_assign_user_start(message, state, session)
