# Запуск

```bash
docker compose up
```

# Структура проекта

| Файл | Назначение |
| --- | --- |
| main.py | backend и frontend на Streamlit |
| parser.py | парсер данных с API Мосбиржи |
| Dockerfile | Dockerfile для сервиса backend |
| Dockerfile.parser | Dockerfile для сервиса parser |
| docker-compose.yml | файл настроек многоконтейнерного приложения |
| requirements.txt | зависимости приложения |
| quotes.csv | пример данных, полученных парсером |
