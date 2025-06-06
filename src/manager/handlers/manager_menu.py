from aiogram import F, Router, types

from manager.callbacks import ManagerStartCallback
from manager.keyboards.manager_menu import get_manager_start_menu

router = Router()


async def manager_menu(
    target: types.Message | types.CallbackQuery,
) -> None:
    """Универсальная функция: Стартовое меню Менеджера."""
    text = 'Для начала работы выберите действие.\n\n<b>Доступные действия:</b>'

    if isinstance(target, types.Message):
        await target.answer(
            text,
            parse_mode='HTML',
            reply_markup=get_manager_start_menu(),
        )
    else:
        await target.message.edit_text(
            text,
            parse_mode='HTML',
            reply_markup=get_manager_start_menu(),
        )
        await target.answer()


@router.callback_query(
    ManagerStartCallback.filter(F.action == 'back_to_menu'),
)
async def back_to_menu(callback: types.CallbackQuery) -> None:
    """Обработка кнопки возвращения в Меню."""
    await manager_menu(callback)


@router.callback_query(
    ManagerStartCallback.filter(F.action == 'show_unsaved_alert'),
)
async def show_unsaved_alert_main_menu(
    callback: types.CallbackQuery,
    callback_data: ManagerStartCallback,
) -> None:
    """Показывает alert при несохраненных изменениях (Главное меню)."""
    await callback.answer(
        'Сначала сохраните изменения!',
        show_alert=True,
    )
