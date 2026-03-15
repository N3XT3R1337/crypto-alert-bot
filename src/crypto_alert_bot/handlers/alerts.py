from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from loguru import logger

from crypto_alert_bot.keyboards.inline import (
    alert_direction_selector,
    alert_list_keyboard,
    confirm_delete_keyboard,
    symbol_selector,
)
from crypto_alert_bot.models.database import Database
from crypto_alert_bot.models.schemas import Alert, AlertDirection, AlertStatus
from crypto_alert_bot.utils.exceptions import AlertLimitExceededError

router = Router(name="alerts")

MAX_ALERTS = 20


class AlertCreation(StatesGroup):
    waiting_for_symbol = State()
    waiting_for_price = State()


@router.message(Command("alerts"))
@router.message(F.text == "\U0001f514 My Alerts")
async def cmd_alerts(message: Message, db: Database) -> None:
    if message.from_user is None:
        return
    alerts = await db.get_user_alerts(message.from_user.id, status=AlertStatus.ACTIVE)
    if not alerts:
        await message.answer("\U0001f514 You have no active alerts.\nUse /alert to create one!")
        return
    await message.answer(
        f"\U0001f514 <b>Your active alerts ({len(alerts)}):</b>",
        parse_mode="HTML",
        reply_markup=alert_list_keyboard(alerts),
    )


@router.message(Command("alert"))
@router.message(F.text == "\u2795 New Alert")
async def cmd_new_alert(message: Message, db: Database, state: FSMContext) -> None:
    if message.from_user is None:
        return
    if message.text and len(message.text.strip().split()) >= 3:
        parts = message.text.strip().split()
        symbol = parts[1].upper()
        try:
            price = float(parts[2])
        except ValueError:
            await message.answer("\u274c Invalid price. Usage: /alert BTC 50000")
            return
        await message.answer(
            f"\U0001f514 Alert for <b>{symbol}</b> at <code>${price:,.2f}</code>\n\nTrigger when price goes:",
            parse_mode="HTML",
            reply_markup=alert_direction_selector(symbol, str(price)),
        )
        return

    count = await db.count_user_alerts(message.from_user.id)
    if count >= MAX_ALERTS:
        await message.answer(f"\u274c You have reached the maximum of {MAX_ALERTS} active alerts.")
        return

    await state.set_state(AlertCreation.waiting_for_symbol)
    await message.answer(
        "\u2795 <b>Create New Alert</b>\n\nSelect or type a cryptocurrency symbol:",
        parse_mode="HTML",
        reply_markup=symbol_selector(),
    )


@router.message(AlertCreation.waiting_for_symbol)
async def on_alert_symbol_text(message: Message, state: FSMContext) -> None:
    if message.text is None:
        return
    symbol = message.text.strip().upper()
    await state.update_data(symbol=symbol)
    await state.set_state(AlertCreation.waiting_for_price)
    await message.answer(
        f"\U0001f4b0 Enter target price for <b>{symbol}</b> (in USD):",
        parse_mode="HTML",
    )


@router.message(AlertCreation.waiting_for_price)
async def on_alert_price_text(message: Message, state: FSMContext) -> None:
    if message.text is None:
        return
    try:
        price = float(message.text.strip().replace(",", "").replace("$", ""))
    except ValueError:
        await message.answer("\u274c Please enter a valid number.")
        return

    data = await state.get_data()
    symbol = data.get("symbol", "BTC")
    await state.clear()
    await message.answer(
        f"\U0001f514 Alert for <b>{symbol}</b> at <code>${price:,.2f}</code>\n\nTrigger when price goes:",
        parse_mode="HTML",
        reply_markup=alert_direction_selector(symbol, str(price)),
    )


@router.callback_query(F.data.startswith("alert_dir:"))
async def on_alert_direction(callback: CallbackQuery, db: Database) -> None:
    if callback.data is None or callback.message is None:
        return
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer("Invalid data")
        return

    direction_str, symbol, price_str = parts[1], parts[2], parts[3]
    direction = AlertDirection.ABOVE if direction_str == "above" else AlertDirection.BELOW

    try:
        price = float(price_str)
    except ValueError:
        await callback.answer("Invalid price")
        return

    user = await db.get_user(callback.from_user.id)
    exchange_name = user.preferred_exchange if user else "binance"

    count = await db.count_user_alerts(callback.from_user.id)
    if count >= MAX_ALERTS:
        await callback.answer(f"Max {MAX_ALERTS} alerts reached!", show_alert=True)
        return

    alert = Alert(
        id=None,
        user_id=callback.from_user.id,
        symbol=symbol,
        target_price=price,
        direction=direction,
        exchange=exchange_name,
    )
    alert_id = await db.create_alert(alert)
    await callback.answer("Alert created!")

    arrow = "\u2b06" if direction == AlertDirection.ABOVE else "\u2b07"
    await callback.message.answer(
        f"\u2705 <b>Alert #{alert_id} created!</b>\n\n"
        f"{arrow} {symbol} {direction.value} <code>${price:,.2f}</code>\n"
        f"\U0001f3e6 Exchange: {exchange_name.capitalize()}",
        parse_mode="HTML",
    )
    logger.info("Alert created: id={} user={} {}@{}", alert_id, callback.from_user.id, symbol, price)


@router.callback_query(F.data.startswith("alert_delete:"))
async def on_alert_delete(callback: CallbackQuery) -> None:
    if callback.data is None or callback.message is None:
        return
    alert_id = int(callback.data.split(":")[1])
    await callback.answer()
    await callback.message.answer(
        f"\u26a0\ufe0f Delete alert #{alert_id}?",
        reply_markup=confirm_delete_keyboard(alert_id),
    )


@router.callback_query(F.data.startswith("confirm_delete:"))
async def on_confirm_delete(callback: CallbackQuery, db: Database) -> None:
    if callback.data is None or callback.message is None:
        return
    alert_id = int(callback.data.split(":")[1])
    deleted = await db.delete_alert(alert_id, callback.from_user.id)
    if deleted:
        await callback.answer("Alert deleted!")
        await callback.message.edit_text(f"\u2705 Alert #{alert_id} deleted.")
    else:
        await callback.answer("Alert not found", show_alert=True)


@router.callback_query(F.data == "cancel_delete")
async def on_cancel_delete(callback: CallbackQuery) -> None:
    if callback.message is None:
        return
    await callback.answer("Cancelled")
    await callback.message.delete()


@router.callback_query(F.data == "noop")
async def on_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.startswith("settings:exchange"))
async def on_settings_exchange(callback: CallbackQuery) -> None:
    if callback.message is None:
        return
    from crypto_alert_bot.keyboards.inline import exchange_selector
    await callback.answer()
    await callback.message.answer(
        "\U0001f3e6 Select your preferred exchange:",
        reply_markup=exchange_selector(),
    )


@router.callback_query(F.data.startswith("exchange:"))
async def on_exchange_selected(callback: CallbackQuery, db: Database) -> None:
    if callback.data is None:
        return
    exchange_name = callback.data.split(":")[1]
    user = await db.get_user(callback.from_user.id)
    if user:
        user.preferred_exchange = exchange_name
        await db.upsert_user(user)
    await callback.answer(f"Exchange set to {exchange_name.capitalize()}!")


@router.callback_query(F.data.startswith("settings:chart_style"))
async def on_settings_chart_style(callback: CallbackQuery) -> None:
    if callback.message is None:
        return
    from crypto_alert_bot.keyboards.inline import chart_style_keyboard
    await callback.answer()
    await callback.message.answer(
        "\U0001f3a8 Select chart style:",
        reply_markup=chart_style_keyboard(),
    )


@router.callback_query(F.data.startswith("chart_style:"))
async def on_chart_style_selected(callback: CallbackQuery, db: Database) -> None:
    if callback.data is None:
        return
    style = callback.data.split(":")[1]
    prefs = await db.get_preferences(callback.from_user.id)
    prefs.chart_style = style
    await db.save_preferences(prefs)
    await callback.answer(f"Chart style set to {style}!")


@router.callback_query(F.data == "settings:notifications")
async def on_toggle_notifications(callback: CallbackQuery, db: Database) -> None:
    prefs = await db.get_preferences(callback.from_user.id)
    prefs.notification_enabled = not prefs.notification_enabled
    await db.save_preferences(prefs)
    status = "enabled" if prefs.notification_enabled else "disabled"
    await callback.answer(f"Notifications {status}!")
