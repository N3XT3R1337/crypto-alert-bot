from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="\U0001f4b0 Prices"), KeyboardButton(text="\U0001f4ca Chart")],
            [KeyboardButton(text="\U0001f514 My Alerts"), KeyboardButton(text="\u2795 New Alert")],
            [KeyboardButton(text="\u2699\ufe0f Settings"), KeyboardButton(text="\u2753 Help")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
