from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from crud import template_roadmap_crud
from manager.callbacks import (
    ManagerStartCallback,
    ManagerTemplateRoadmapCallback,
)
from manager.keyboards.template_roadmaps import (
    get_templateroadmap_editor_menu_keyboard,
    get_templateroadmap_menu_keyboard,
    select_templateroadmap_keyboard,
    templateroadmap_editor_cancel_keyboard,
)
from manager.states import EditTemplateRoadmapStates
from manager.utils import (
    generate_roadmap_editor_text,
    get_templateroadmap,
    process_templateroadmap_field_update,
    send_or_edit_message,
)
from models.models import TemplateRoadMap, User

router = Router()


@router.callback_query(
    ManagerStartCallback.filter(F.action == 'manager_templateroadmaps'),
)
async def manager_get_templateroadmaps(
    callback: types.CallbackQuery,
    session: AsyncSession,
    user: User,
) -> None:
    """Обработка кнопки Управления Шаблонами дорожных карт.

    Получение доступных Шаблонов дорожных карт, выбор с помощью кнопок.
    """
    templateroadmaps = (
        await template_roadmap_crud.get_multi_filtered(
            session,
            TemplateRoadMap.restaurant_id == user.restaurant_id,
        ))

    if not templateroadmaps:
        text = ('<b>Нет доступных Шаблонов дорожных карт!</b>\n\n'
                'Обратитесь к администратору.')
        templateroadmaps = []
    else:
        text = 'Выберите Шаблон дорожной карты\n\n<b>Доступные шаблоны:</b>'

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': select_templateroadmap_keyboard(
            templateroadmaps,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.callback_query(
    ManagerTemplateRoadmapCallback.filter(F.action == 'select'),
)
async def manager_roadmap_menu(
    callback: types.CallbackQuery,
    callback_data: ManagerTemplateRoadmapCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Меню управления Шаблоном дорожной карты."""
    templateroadmap = await get_templateroadmap(
        callback_data.templateroadmap_id,
        session,
        callback=callback,
    )

    if not templateroadmap or not callback.message:
        return

    state_data = await state.get_data()

    text = generate_roadmap_editor_text(
        roadmap=templateroadmap,
        state_data=state_data,
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': get_templateroadmap_menu_keyboard(
            templateroadmap,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.callback_query(
    ManagerTemplateRoadmapCallback.filter(
        F.action == 'edit_templateroadmap',
    ),
)
async def manager_edit_templateroadmap(
    callback: types.CallbackQuery,
    callback_data: ManagerTemplateRoadmapCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Меню Редактора Шаблона дорожной карты.

    Выбор действий с Шаблоном дорожной картой.
    """
    templateroadmap = await get_templateroadmap(
        callback_data.templateroadmap_id,
        session,
        callback=callback,
    )

    if not templateroadmap or not callback.message:
        return

    await state.update_data(
        templateroadmap_id=templateroadmap.id,
        editor_message_id=callback.message.message_id,
    )
    await state.set_state(EditTemplateRoadmapStates.selecting_action)

    state_data = await state.get_data()
    text = generate_roadmap_editor_text(
        roadmap=templateroadmap,
        state_data=state_data,
        edit_mode=True,
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': get_templateroadmap_editor_menu_keyboard(
            templateroadmap,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.callback_query(
    ManagerTemplateRoadmapCallback.filter(
        F.action == 'edit_templateroadmap_name',
    ),
)
async def manager_edit_templateroadmap_name(
    callback: types.CallbackQuery,
    callback_data: ManagerTemplateRoadmapCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Редактирование названия Шаблона дорожной карты."""
    templateroadmap = await get_templateroadmap(
        callback_data.templateroadmap_id,
        session,
        callback=callback,
    )

    if not templateroadmap:
        return

    await state.set_state(EditTemplateRoadmapStates.editing_name)
    await state.update_data(
        templateroadmap_id=callback_data.templateroadmap_id,
        editor_message_id=callback.message.message_id,
    )

    text = (
        '<i>Текущее название дорожной карты:</i>\n'
        f'<b>{templateroadmap.name}</b>\n\n'
        '<i>Введите новое название Шаблона дорожной карты:</i>'
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': templateroadmap_editor_cancel_keyboard(
            callback_data.templateroadmap_id,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.callback_query(
    ManagerTemplateRoadmapCallback.filter(
        F.action == 'edit_templateroadmap_description',
    ),
)
async def manager_edit_templateroadmap_description(
    callback: types.CallbackQuery,
    callback_data: ManagerTemplateRoadmapCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Редактирование описание Шаблона дорожной карты."""
    templateroadmap = await get_templateroadmap(
        callback_data.templateroadmap_id,
        session,
        callback=callback,
    )
    if not templateroadmap:
        return

    await state.set_state(EditTemplateRoadmapStates.editing_description)
    await state.update_data(
        templateroadmap_id=callback_data.templateroadmap_id,
        editor_message_id=callback.message.message_id,
    )

    text = (
        '<i>Текущее описание дорожной карты:</i>\n'
        f'<b>{templateroadmap.description}</b>\n\n'
        '<i>Введите новое описание Шаблона дорожной карты:</i>'
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': templateroadmap_editor_cancel_keyboard(
            callback_data.templateroadmap_id,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.message(EditTemplateRoadmapStates.editing_name)
async def manager_process_new_templateroadmap_name(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка нового названия Шаблона дорожной карты."""
    data = await state.get_data()

    templateroadmap = await get_templateroadmap(
        data['templateroadmap_id'],
        session,
        message=message,
    )

    if not templateroadmap:
        await state.clear()
        return

    await process_templateroadmap_field_update(
        message=message,
        state=state,
        session=session,
        state_to_set=EditTemplateRoadmapStates.selecting_action,
        obj_field=templateroadmap.name,
        data_field='new_name',
    )


@router.message(EditTemplateRoadmapStates.editing_description)
async def manager_process_new_templateroadmap_description(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка нового описания Шаблона дорожной карты."""
    data = await state.get_data()
    templateroadmap = await get_templateroadmap(
        data['templateroadmap_id'],
        session,
        message=message,
    )
    if not templateroadmap:
        await state.clear()
        return

    await process_templateroadmap_field_update(
        message=message,
        state=state,
        session=session,
        state_to_set=EditTemplateRoadmapStates.selecting_action,
        obj_field=templateroadmap.description,
        data_field='new_description',
    )


@router.callback_query(
    ManagerTemplateRoadmapCallback.filter(
        F.action == 'block_templateroadmap',
    ),
    EditTemplateRoadmapStates.selecting_action,
)
async def manager_block_templateroadmap(
    callback: types.CallbackQuery,
    callback_data: ManagerTemplateRoadmapCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Блокировка Шаблона дорожной карты."""
    templateroadmap = await get_templateroadmap(
        callback_data.templateroadmap_id,
        session,
        callback=callback,
    )
    if not templateroadmap:
        return

    new_block_status = not templateroadmap.is_blocked
    templateroadmap.is_blocked = new_block_status
    await session.commit()

    await state.update_data(is_blocked=new_block_status)
    state_data = await state.get_data()

    text = generate_roadmap_editor_text(
        roadmap=templateroadmap,
        state_data=state_data,
        edit_mode=True,
        changes=True,
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': get_templateroadmap_editor_menu_keyboard(
            templateroadmap=templateroadmap,
            changes=True,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.callback_query(
    ManagerTemplateRoadmapCallback.filter(
        F.action == 'save_templateroadmap',
    ),
    EditTemplateRoadmapStates.selecting_action,
)
async def manager_save_templateroadmap_changes(
    callback: types.CallbackQuery,
    callback_data: ManagerTemplateRoadmapCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Сохранение изменений Шаблона дорожной карты в БД."""
    data = await state.get_data()
    templateroadmap = await template_roadmap_crud.get(
        callback_data.templateroadmap_id,
        session,
        load_relations=True,
    )

    if not templateroadmap:
        await callback.answer(
            'Шаблон дорожной карты не найден!',
            show_alert=True,
        )
        return

    if 'new_name' in data:
        templateroadmap.name = data['new_name']
    if 'new_description' in data:
        templateroadmap.description = data['new_description']
    if 'is_blocked' in data:
        templateroadmap.is_blocked = data['is_blocked']

    await session.commit()
    await state.clear()
    await callback.answer(
        '✅ Изменения сохранены!',
        show_alert=True,
    )

    templateroadmap = await template_roadmap_crud.get(
        callback_data.templateroadmap_id,
        session,
        load_relations=True,
    )

    if not templateroadmap:
        return

    text = generate_roadmap_editor_text(
        roadmap=templateroadmap,
        state_data={},
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': get_templateroadmap_editor_menu_keyboard(
            templateroadmap,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.callback_query(
    ManagerTemplateRoadmapCallback.filter(F.action == 'show_unsaved_alert'),
)
async def show_unsaved_alert_back(
    callback: types.CallbackQuery,
    callback_data: ManagerTemplateRoadmapCallback,
) -> None:
    """Показывает alert при несохраненных изменениях (Назад)."""
    await callback.answer(
        'Сначала сохраните изменения!',
        show_alert=True,
    )
