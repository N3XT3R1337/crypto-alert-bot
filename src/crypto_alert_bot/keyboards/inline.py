from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from crypto_alert_bot.models.schemas import Alert, AlertStatus


def exchange_selector() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Binance", callback_data="exchange:binance"),
            InlineKeyboardButton(text="CoinGecko", callback_data="exchange:coingecko"),
            InlineKeyboardButton(text="Kraken", callback_data="exchange:kraken"),
        ]
    ])


def symbol_selector(symbols: list[str] | None = None) -> InlineKeyboardMarkup:
    default_symbols = symbols or ["BTC", "ETH", "SOL", "XRP", "ADA", "DOT", "LINK", "DOGE"]
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for sym in default_symbols:
        row.append(InlineKeyboardButton(text=sym, callback_data=f"symbol:{sym}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def chart_timeframe_selector(symbol: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1D", callback_data=f"chart:{symbol}:1"),
            InlineKeyboardButton(text="7D", callback_data=f"chart:{symbol}:7"),
            InlineKeyboardButton(text="30D", callback_data=f"chart:{symbol}:30"),
            InlineKeyboardButton(text="90D", callback_data=f"chart:{symbol}:90"),
        ]
    ])


def alert_direction_selector(symbol: str, price: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Above", callback_data=f"alert_dir:above:{symbol}:{price}"),
            InlineKeyboardButton(text="Below", callback_data=f"alert_dir:below:{symbol}:{price}"),
        ]
    ])


def alert_list_keyboard(alerts: list[Alert]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for alert in alerts:
        if alert.status == AlertStatus.ACTIVE and alert.id is not None:
            emoji = "\u2b06" if alert.direction.value == "above" else "\u2b07"
            text = f"{emoji} {alert.symbol} {alert.direction.value} ${alert.target_price:,.2f}"
            rows.append([
                InlineKeyboardButton(text=text, callback_data=f"alert_info:{alert.id}"),
                InlineKeyboardButton(text="\u274c", callback_data=f"alert_delete:{alert.id}"),
            ])
    if not rows:
        rows.append([InlineKeyboardButton(text="No active alerts", callback_data="noop")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_delete_keyboard(alert_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Yes, delete", callback_data=f"confirm_delete:{alert_id}"),
            InlineKeyboardButton(text="Cancel", callback_data="cancel_delete"),
        ]
    ])


def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Change Exchange", callback_data="settings:exchange")],
        [InlineKeyboardButton(text="Chart Style", callback_data="settings:chart_style")],
        [InlineKeyboardButton(text="Toggle Notifications", callback_data="settings:notifications")],
    ])


def chart_style_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Dark", callback_data="chart_style:dark"),
            InlineKeyboardButton(text="Light", callback_data="chart_style:light"),
        ]
    ])
