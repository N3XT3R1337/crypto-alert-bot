from __future__ import annotations

import io
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from loguru import logger

from crypto_alert_bot.models.schemas import PriceHistory
from crypto_alert_bot.utils.exceptions import ChartGenerationError

DARK_STYLE = {
    "bg_color": "#1a1a2e",
    "text_color": "#e0e0e0",
    "line_color": "#00d4aa",
    "grid_color": "#2a2a4a",
    "fill_color": "#00d4aa",
    "fill_alpha": 0.15,
}

LIGHT_STYLE = {
    "bg_color": "#ffffff",
    "text_color": "#333333",
    "line_color": "#2196F3",
    "grid_color": "#e0e0e0",
    "fill_color": "#2196F3",
    "fill_alpha": 0.1,
}


def _get_style(name: str) -> dict[str, str | float]:
    if name == "light":
        return LIGHT_STYLE
    return DARK_STYLE


class ChartService:
    def __init__(self, default_style: str = "dark") -> None:
        self._default_style = default_style

    def generate_price_chart(
        self,
        history: PriceHistory,
        style: str | None = None,
        width: int = 12,
        height: int = 6,
    ) -> io.BytesIO:
        if not history.prices:
            raise ChartGenerationError(history.symbol, "No price data available")

        chart_style = _get_style(style or self._default_style)

        try:
            timestamps: list[datetime] = []
            prices: list[float] = []
            for ts_str, price in history.prices:
                try:
                    ts_val = int(float(ts_str))
                    if ts_val > 1e12:
                        ts_val = ts_val // 1000
                    timestamps.append(datetime.utcfromtimestamp(ts_val))
                except (ValueError, OSError):
                    timestamps.append(datetime.fromisoformat(ts_str))
                prices.append(price)

            fig, ax = plt.subplots(figsize=(width, height))
            fig.patch.set_facecolor(chart_style["bg_color"])
            ax.set_facecolor(chart_style["bg_color"])

            ax.plot(
                timestamps,
                prices,
                color=chart_style["line_color"],
                linewidth=2,
                antialiased=True,
            )
            ax.fill_between(
                timestamps,
                prices,
                alpha=chart_style["fill_alpha"],
                color=chart_style["fill_color"],
            )

            ax.set_title(
                f"{history.symbol}/USD — {history.exchange.capitalize()}",
                color=chart_style["text_color"],
                fontsize=16,
                fontweight="bold",
                pad=15,
            )
            ax.set_ylabel("Price (USD)", color=chart_style["text_color"], fontsize=12)

            ax.tick_params(colors=chart_style["text_color"], labelsize=10)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
            fig.autofmt_xdate(rotation=30)

            ax.grid(True, color=chart_style["grid_color"], alpha=0.5, linestyle="--")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color(chart_style["grid_color"])
            ax.spines["bottom"].set_color(chart_style["grid_color"])

            min_price = min(prices)
            max_price = max(prices)
            current_price = prices[-1]
            info_text = f"High: ${max_price:,.2f}  |  Low: ${min_price:,.2f}  |  Current: ${current_price:,.2f}"
            ax.text(
                0.5,
                -0.15,
                info_text,
                transform=ax.transAxes,
                ha="center",
                fontsize=11,
                color=chart_style["text_color"],
            )

            plt.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
            buf.seek(0)
            plt.close(fig)

            logger.debug("Chart generated for {}", history.symbol)
            return buf
        except ChartGenerationError:
            raise
        except Exception as e:
            logger.error("Chart generation failed for {}: {}", history.symbol, e)
            raise ChartGenerationError(history.symbol, str(e)) from e
