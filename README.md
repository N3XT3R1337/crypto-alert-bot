```
   ██████╗██████╗ ██╗   ██╗██████╗ ████████╗ ██████╗      █████╗ ██╗     ███████╗██████╗ ████████╗
  ██╔════╝██╔══██╗╚██╗ ██╔╝██╔══██╗╚══██╔══╝██╔═══██╗    ██╔══██╗██║     ██╔════╝██╔══██╗╚══██╔══╝
  ██║     ██████╔╝ ╚████╔╝ ██████╔╝   ██║   ██║   ██║    ███████║██║     █████╗  ██████╔╝   ██║
  ██║     ██╔══██╗  ╚██╔╝  ██╔═══╝    ██║   ██║   ██║    ██╔══██║██║     ██╔══╝  ██╔══██╗   ██║
  ╚██████╗██║  ██║   ██║   ██║        ██║   ╚██████╔╝    ██║  ██║███████╗███████╗██║  ██║   ██║
   ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝        ╚═╝    ╚═════╝     ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝   ╚═╝
                                          ██████╗  ██████╗ ████████╗
                                          ██╔══██╗██╔═══██╗╚══██╔══╝
                                          ██████╔╝██║   ██║   ██║
                                          ██╔══██╗██║   ██║   ██║
                                          ██████╔╝╚██████╔╝   ██║
                                          ╚═════╝  ╚═════╝    ╚═╝
```

<p align="center">
  <img src="https://img.shields.io/badge/build-passing-brightgreen?style=flat-square" alt="Build Status">
  <img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/aiogram-3.x-blue?style=flat-square" alt="aiogram">
  <img src="https://img.shields.io/badge/code%20style-ruff-000000?style=flat-square" alt="Code Style">
</p>

---

Telegram bot for real-time cryptocurrency price monitoring with customizable alerts, inline charts, and multi-exchange support. Get notified instantly when prices hit your targets.

## Features

- **Multi-Exchange Support** — Fetch prices from Binance, CoinGecko, and Kraken
- **Custom Price Alerts** — Set "above" or "below" alerts for any supported symbol
- **Inline Charts** — Beautiful matplotlib-generated price charts with dark/light themes
- **Redis Caching** — Reduce API calls with configurable TTL cache
- **Scheduled Checks** — APScheduler runs periodic alert checks in the background
- **SQLite Storage** — Persistent user preferences and alert history
- **FSM Workflows** — Step-by-step alert creation with aiogram FSM
- **Structured Logging** — Loguru-based logging with rotation and compression

## Tech Stack

| Component       | Technology                          |
|-----------------|-------------------------------------|
| Bot Framework   | aiogram 3.x                        |
| HTTP Client     | aiohttp                             |
| Database        | SQLite via aiosqlite                |
| Cache           | Redis (optional)                    |
| Scheduler       | APScheduler                         |
| Charts          | matplotlib                          |
| Logging         | loguru                              |
| Testing         | pytest + pytest-asyncio             |
| Containerization| Docker                              |

## Installation

### Prerequisites

- Python 3.11+
- Redis (optional, for caching)
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### Quick Start

```bash
git clone https://github.com/N3XT3R1337/crypto-alert-bot.git
cd crypto-alert-bot

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your bot token
```

### Docker

```bash
docker build -t crypto-alert-bot .
docker run --env-file .env crypto-alert-bot
```

## Usage

### Running the Bot

```bash
PYTHONPATH=src python -m crypto_alert_bot.bot
```

Or use the Makefile:

```bash
make install
make run
```

### Bot Commands

| Command                  | Description                        |
|--------------------------|------------------------------------|
| `/start`                 | Start the bot and register         |
| `/price BTC`             | Get current BTC price              |
| `/chart ETH`             | View ETH price chart               |
| `/alert BTC 50000`       | Create alert for BTC at $50,000    |
| `/alerts`                | List your active alerts            |
| `/settings`              | Configure exchange and preferences |
| `/help`                  | Show help message                  |

### Creating an Alert

```
You: /alert BTC 70000
Bot: 🔔 Alert for BTC at $70,000.00
     Trigger when price goes:
     [Above] [Below]

You: *clicks Above*
Bot: ✅ Alert #1 created!
     ⬆ BTC above $70,000.00
     🏦 Exchange: Binance
```

### Viewing Charts

```
You: /chart SOL
Bot: 📊 Select timeframe for SOL:
     [1D] [7D] [30D] [90D]

You: *clicks 7D*
Bot: *sends inline chart image*
     📊 SOL/USD — 7D chart via Binance
```

## Running Tests

```bash
make test
```

Or directly:

```bash
PYTHONPATH=src pytest tests/ -v
```

## Configuration

All settings are configured via environment variables (`.env` file):

| Variable             | Default      | Description                    |
|----------------------|--------------|--------------------------------|
| `BOT_TOKEN`          | —            | Telegram bot token (required)  |
| `ADMIN_IDS`          | —            | Comma-separated admin user IDs |
| `DATABASE_PATH`      | `data/crypto_alert.db` | SQLite database path  |
| `REDIS_HOST`         | `localhost`  | Redis host                     |
| `REDIS_PORT`         | `6379`       | Redis port                     |
| `REDIS_TTL`          | `60`         | Cache TTL in seconds           |
| `DEFAULT_EXCHANGE`   | `binance`    | Default exchange               |
| `MAX_ALERTS_PER_USER`| `20`         | Alert limit per user           |
| `CHECK_INTERVAL`     | `30`         | Alert check interval (seconds) |

## Project Structure

```
crypto-alert-bot/
├── src/crypto_alert_bot/
│   ├── __init__.py
│   ├── bot.py
│   ├── handlers/
│   │   ├── start.py
│   │   ├── prices.py
│   │   ├── charts.py
│   │   └── alerts.py
│   ├── keyboards/
│   │   ├── inline.py
│   │   └── reply.py
│   ├── services/
│   │   ├── exchange.py
│   │   ├── cache.py
│   │   ├── chart.py
│   │   └── alert_checker.py
│   ├── models/
│   │   ├── database.py
│   │   └── schemas.py
│   └── utils/
│       ├── config.py
│       ├── exceptions.py
│       └── logging.py
├── tests/
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_exchange.py
│   ├── test_alerts.py
│   ├── test_cache.py
│   └── test_chart.py
├── .env.example
├── .gitignore
├── Dockerfile
├── LICENSE
├── Makefile
├── README.md
└── requirements.txt
```

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
