Инструмент для анализа пользовательских отзывов из Яндекс.Карт. Выделяет аспекты, определяет сентимент, находит ключевые мысли и формирует PDF-отчёт. Пользователь взаимодействует через Telegram-бота.

## Установка

1. Установите зависимости:
   ```
   pip install -r requirements.txt
    ```

2. Скачайте модели отсюда:   
    ```
   [https://drive.google.com/drive/folders/13QlDQCyxfOxUR8_QyiJwn4UqZVZWDIty?usp=drive_link](https://drive.google.com/drive/folders/13QlDQCyxfOxUR8_QyiJwn4UqZVZWDIty?usp=drive_link)
    ```
3. Поместите скачанные модели в папку:
   ```
   ./models
    ```

## Использование

1. Вставьте токен Telegram-бота в файл `main.py`.
2. Запустите бота:
   ```
   python main.py
    ```

## Структура

- `main.py` — запуск Telegram-бота
- `parser/` — парсинг отзывов с Яндекс.Карт
- `label_reviews.py` — извлечение аспектов и сентимента
- `summarize.py` — кластеризация ключевых мыслей
- `render_pdf.py` — генерация PDF-отчета

## Результат

На вход — ссылка на заведение.  
На выход — PDF-документ с анализом отзывов.