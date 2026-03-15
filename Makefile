.PHONY: install run test lint clean docker-build docker-run

install:
	pip install -r requirements.txt

run:
	python -m crypto_alert_bot.bot

test:
	PYTHONPATH=src pytest tests/ -v

lint:
	ruff check src/ tests/
	mypy src/ --ignore-missing-imports

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info

docker-build:
	docker build -t crypto-alert-bot .

docker-run:
	docker run --env-file .env --name crypto-alert-bot crypto-alert-bot
