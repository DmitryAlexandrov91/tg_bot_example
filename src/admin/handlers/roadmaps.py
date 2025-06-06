from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from admin.constants import (
    FIELDS_ROADMAP_TEMPLATES,
    FIELDS_RT_PLURAL,
)
from admin.keyboards import (
    build_confirm_keyboard,
    build_restaurant_select_keyboard,
    build_roadmap_template_select_keyboard,
    fields_template_roadmap_keyboard,
    roadmap_edit_fields_keyboard,
)
from admin.services.roadmap_templates import (
    maybe_confirm_edit_roadmap_template,
    show_summary_and_confirm_roadmap_template,
)
from admin.states.roadmap_templates import (
    RoadmapTemplateEditForm,
    RoadmapTemplateForm,
)
from crud import restaurant_crud, template_roadmap_crud

router = Router(name='roadmap_templates')


@router.message(Command('create_roadmap_template'))
async def cmd_create_roadmap_template(
    message: Message,
    state: FSMContext,
) -> None:
    """Начало создания нового шаблона дорожной карты. Запрашивает название."""
    await state.clear()
    await message.answer('Введите название шаблона дорожной карты:')
    await state.set_state(RoadmapTemplateForm.name)


@router.message(RoadmapTemplateForm.name)
async def proc_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Обработка названия шаблона. Сохраняет его и просит описание."""
    await state.update_data(name=message.text.strip())
    if await maybe_confirm_edit_roadmap_template(message, state):
        return
    await message.answer('Введите описание шаблона:')
    await state.set_state(RoadmapTemplateForm.description)


@router.message(RoadmapTemplateForm.description)
async def proc_description(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Сохранение описания шаблона и запрос подтверждения данных."""
    await state.update_data(description=message.text.strip())
    if await maybe_confirm_edit_roadmap_template(message, state):
        return
    await show_summary_and_confirm_roadmap_template(
        message,
        state,
    )


@router.callback_query(
    lambda c: c.data == 'create_temp:confirm_yes',
    RoadmapTemplateForm.confirm,
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
        template = await template_roadmap_crud.create(data, session)
        await callback.message.edit_reply_markup()
        await callback.message.answer(
            f'Шаблон дорожной карты создан:\n'
            f'Название - {template.name}, описание - {template.description}',
        )
        await state.clear()
    except IntegrityError as error:
        await callback.message.answer(f'Ошибка при сохранении: {error}')


@router.callback_query(
    lambda c: c.data == 'create_temp:redact_field',
    RoadmapTemplateForm.confirm,
)
async def callback_redact_field(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Выводим инлайн-клавиатуру с полями для редактирования."""
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        'Выберите поле, которое хотите изменить:',
        reply_markup=roadmap_edit_fields_keyboard,
    )


@router.callback_query(F.data.startswith('edit_field_roadmap_before:'))
async def callback_edit_specific_field(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Переход к редактированию конкретного поля."""
    field_key = callback.data.split(':')[1]
    fsm_states = {
        'name': RoadmapTemplateForm.name,
        'description': RoadmapTemplateForm.description,
    }
    if field_key not in fsm_states:
        await callback.message.answer('Ошибка: неизвестное поле.')
        return
    await state.update_data(editing=True)
    await callback.message.edit_reply_markup()
    await callback.message.answer(FIELDS_ROADMAP_TEMPLATES[field_key])
    await state.set_state(fsm_states[field_key])


@router.message(Command('edit_roadmap_template'))
async def cmd_edit_roadmap_template_start(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Старт для редактирования шаблона дорожной карты."""
    await state.clear()
    roadmap_templates = await template_roadmap_crud.get_multi(session)
    if not roadmap_templates:
        await message.answer('Шаблоны дорожных карт не найдены!')
        return
    await message.answer(
        'Выберите шаблон для редактирования:',
        reply_markup=build_roadmap_template_select_keyboard(
            roadmap_templates,
            prefix='edit_roadmap_template_select',
        ),
    )


@router.callback_query(F.data.startswith('edit_roadmap_template_select:'))
async def process_roadmap_template_selected_for_edit(
    call: CallbackQuery,
    state: FSMContext,
) -> None:
    """Показывает все шаблоны дорожных карт."""
    template_id = int(call.data.split(':')[1])
    await state.update_data(roadmap_template_id=template_id)
    await call.message.edit_reply_markup()
    await call.message.answer(
        'Какое поле хотите изменить?',
        reply_markup=fields_template_roadmap_keyboard,
    )


@router.callback_query(F.data.startswith('edit_roadmap_template_field:'))
async def proc_edit_roadmap_template_field(
    call: CallbackQuery,
    state: FSMContext,
) -> None:
    """Показывает поля."""
    field = call.data.split(':')[1]
    await state.update_data(field=field)
    await call.message.edit_reply_markup()
    await call.message.answer(FIELDS_ROADMAP_TEMPLATES[field])
    await state.set_state(RoadmapTemplateEditForm.value)


@router.message(RoadmapTemplateEditForm.value)
async def proc_edit_roadmap_template_value(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Ввод значения."""
    data = await state.get_data()
    template_id = data['roadmap_template_id']
    field = data['field']
    value = message.text.strip()
    roadmap_template = await template_roadmap_crud.get(template_id, session)
    if not roadmap_template:
        await message.answer('Шаблон дорожной карты не найден.')
        await state.clear()
        return
    updated = await template_roadmap_crud.update(
        roadmap_template,
        {field: value},
        session,
    )
    await message.answer(
        f'Шаблон дорожной карты {updated.name} - обновлён!.\n'
        f'Новое значение {FIELDS_RT_PLURAL[field]} - '
        f'{getattr(updated, field)}.',
    )
    await state.clear()


@router.message(Command('block_roadmap_template'))
async def cmd_block_roadmap_template_start(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Начинаем блокировку."""
    await state.clear()
    templates = await template_roadmap_crud.get_multi(session)
    if not templates:
        await message.answer('Шаблоны дорожных карт не найдены!')
        return
    await message.answer(
        'Выберите шаблон для блокировки:',
        reply_markup=build_roadmap_template_select_keyboard(
            templates,
            prefix='block_roadmap_template_select',
        ),
    )


@router.callback_query(F.data.startswith('block_roadmap_template_select:'))
async def process_roadmap_template_selected_for_block(
    call: CallbackQuery,
    state: FSMContext,
) -> None:
    """Показывает все шаблоны дорожных карт."""
    template_id = int(call.data.split(':')[1])
    await state.update_data(roadmap_template_id=template_id)
    await call.message.edit_reply_markup()
    await call.message.answer(
        'Уверены, что хотите заблокировать шаблон дорожной карты?',
        reply_markup=build_confirm_keyboard(
            template_id,
            entity='roadmap_template',
        ),
    )


@router.callback_query(F.data.startswith('confirm_block_roadmap_template'))
async def handle_confirm_block(
    call: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Блокировка шаблона дорожной карты."""
    template_id = int(call.data.split(':')[1])
    template = await template_roadmap_crud.get(template_id, session)
    await call.message.edit_reply_markup()
    if not template:
        await call.message.answer('Шаблон дорожной карты не найден.')
        return
    updated = await template_roadmap_crud.update(
        template,
        {'is_blocked': True},
        session,
    )
    await call.message.answer(
        f'Шаблон дорожной карты {updated.name} - успешно заблокирован.',
    )


@router.callback_query(F.data == 'cancel_block_roadmap_template')
async def handle_cancel_block(
    call: CallbackQuery,
) -> None:
    """Отмена блокировки."""
    await call.message.edit_reply_markup()
    await call.message.answer('Блокировка отменена')
    return


@router.message(Command('adapt_template_for_roadmap'))
async def cmd_adapt_template_for_roadmap_start(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Показывает все шаблоны дорожных карт."""
    await state.clear()
    templates = await template_roadmap_crud.get_multi(session)
    if not templates:
        await message.answer('Шаблоны дорожных карт не найдены!')
        return
    await message.answer(
        'Выберите шаблон дорожной карты:',
        reply_markup=build_roadmap_template_select_keyboard(
            templates,
            prefix='adapt_roadmap_template_select',
        ),
    )


@router.callback_query(F.data.startswith('adapt_roadmap_template_select:'))
async def process_adapt_restaurant_select(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Показывает все рестораны."""
    template_id = int(call.data.split(':')[1])
    await state.update_data(roadmap_template_id=template_id)
    await call.message.edit_reply_markup()
    restaurants = await restaurant_crud.get_multi(session)
    if not restaurants:
        await call.message.answer('Рестораны не найдены!')
        return
    await call.message.answer(
        'Выберите ресторан для адаптации шаблона:',
        reply_markup=build_restaurant_select_keyboard(
            restaurants,
            prefix='adapt_restaurant_select',
        ),
    )


@router.callback_query(F.data.startswith('adapt_restaurant_select:'))
async def adapt_template_for_restaurant(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Привязка шаблона к ресторану."""
    restaurant_id = int(call.data.split(':')[1])
    data = await state.get_data()
    print('here', data)
    template_id = data['roadmap_template_id']
    restaurant = await restaurant_crud.get(restaurant_id, session)
    roadmap_template = await template_roadmap_crud.get(template_id, session)
    if not roadmap_template:
        await call.message.answer('Шаблон не найден в БД.')
    else:
        await template_roadmap_crud.update(
            roadmap_template,
            {'restaurant_id': restaurant_id},
            session,
        )
        await call.message.answer(
            f'Готово!\nШаблон "{roadmap_template.name}" '
            f'привязан к ресторану "{restaurant.name}"!',
        )
    await call.message.edit_reply_markup()
    await state.clear()


# =========================
# Кнопки
# =========================


@router.message(F.text == 'Создать шаблон дорожной карты')
async def alias_create_restaurant(
    message: Message,
    state: FSMContext,
) -> None:
    """Кнопка создания шаблона дорожной карты."""
    await cmd_create_roadmap_template(message, state)


@router.message(F.text == 'Редактировать шаблон дорожной карты')
async def alias_edit_roadmap_template(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Кнопка рефреш шаблона дорожной карты."""
    await cmd_edit_roadmap_template_start(message, state, session)


@router.message(F.text == 'Заблокировать шаблон дорожной карты')
async def alias_block_restaurant(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Кнопка блока шаблона дорожной карты."""
    await cmd_block_roadmap_template_start(message, state, session)


@router.message(F.text == 'Привязать шаблон дорожной карты к ресторану')
async def alias_adapt_template(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Кнопка адаптации шаблона к ресторану."""
    await cmd_adapt_template_for_roadmap_start(message, state, session)
