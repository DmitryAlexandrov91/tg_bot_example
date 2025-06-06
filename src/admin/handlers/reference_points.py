
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from admin.keyboards import (
    build_restaurant_select_keyboard,
    build_roadmap_template_select_keyboard,
    point_type_keyboard,
)
from admin.services.reference_points import update_ref_point_state
from admin.states.reference_points import RefPointTemplateForm
from crud import (
    restaurant_crud,
    template_reference_point_crud,
    template_roadmap_crud,
)

router = Router(name='reference_points')


@router.message(Command('create_ref_point_template'))
async def cmd_create_reference_point_template(
    message: Message,
    state: FSMContext,
) -> None:
    """Ref point create."""
    await state.clear()
    await message.answer('Введите название шаблона контрольной точки:')
    await state.set_state(RefPointTemplateForm.name)


@router.message(RefPointTemplateForm.name)
async def ref_point_name(
    message: Message,
    state: FSMContext,
) -> None:
    """."""
    if await update_ref_point_state(
        state=state,
        key='name',
        value=message.text,
        next_state=RefPointTemplateForm.point_type,
        message=message,
        prompt='Выберите тип контрольной точки: ',
        reply_markup=point_type_keyboard,
    ):
        return


@router.callback_query(
    F.data.startswith('point_type:'),
    RefPointTemplateForm.point_type,
)
async def point_type_callback(
    call: CallbackQuery,
    state: FSMContext,
) -> None:
    """."""
    point_type = call.data.split(':')[1]
    await state.update_data(point_type=point_type)
    await call.message.edit_reply_markup()
    await call.message.answer(
        'Введите порядковый номер контрольной точки в дорожной карте:',
    )
    await state.set_state(RefPointTemplateForm.order_execution)


@router.message(RefPointTemplateForm.order_execution)
async def ref_point_order_execution(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    ) -> None:
    """Обработка порядкового номера контрольной точки в дорожной карте."""
    if not message.text.isdigit():
        await message.answer(
            'Порядковый номер должен быть числом. Введите ещё раз:',
        )
        return
    rest_list = await restaurant_crud.get_multi(session)
    if await update_ref_point_state(
        state=state,
        key='order_execution',
        value=int(message.text),
        next_state=RefPointTemplateForm.restaurant_id,
        message=message,
        prompt='Выберите ресторан:',
        reply_markup=build_restaurant_select_keyboard(
            rest_list,
            prefix='assign_rest_for_refpoint',
        ),
    ):
        return


@router.callback_query(
    F.data.startswith('assign_rest_for_refpoint:'),
    RefPointTemplateForm.restaurant_id,
)
async def process_restaurant_callback(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Привязка шаблона контрольной точки к ресторану."""
    roadmaps_list = await template_roadmap_crud.get_multi(session)
    rest_id = int(call.data.split(':', 1)[1])
    if await update_ref_point_state(
        state=state,
        key='restaurant_id',
        value=rest_id,
        next_state=RefPointTemplateForm.templateroadmap_id,
        message=call.message,
        prompt='Выберите шаблон дорожной карты:',
        reply_markup=build_roadmap_template_select_keyboard(
            roadmaps_list,
            prefix='assign_roadmap',
        ),
    ):
        return


@router.callback_query(
    F.data.startswith('assign_roadmap:'),
    RefPointTemplateForm.templateroadmap_id,
)
async def process_roadmap_template_callback(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Привязка шаблона контрольной точки к шаблону дорожной карты."""
    roadmap = call.data.split(':')[1]
    await state.update_data(templateroadmap_id=int(roadmap))
    data = await state.get_data()
    try:
        template_ref_point = await template_reference_point_crud.create(
            data,
            session,
        )
    except IntegrityError as error:
        await call.message.answer(
            'Конфликт данных при сохранении.',
            {error},
        )
        return
    await call.message.answer(
        f'Создан шаблон контрольной точки {template_ref_point.name}',
    )
    await state.clear()


@router.message(F.text == 'Создать шаблон контрольной точки')
async def alias_create_ref_point_template(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """"Кнопка генерации ссылки-приглашения."""
    await cmd_create_reference_point_template(message, state)
