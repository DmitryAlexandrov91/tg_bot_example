import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Базовый сеттинг с константами проекта."""

    WELCOME_MESSAGE: str = 'Привет! Я - твой помощник для онбординга.'

    TOKEN: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_NAME: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    REDIS_HOST: str
    REDIS_PORT: str
    REDIS_PASSWORD: str
    LOG_FORMAT: str = '%(asctime)s | %(levelname)s | %(message)s'
    DATETIME_FORMAT: str = '%Y-%m-%d  %H-%M-%S'

    TG_ID: int
    FIRST_NAME: str = 'admin'
    LAST_NAME: str = 'admin'
    PATRONYMIC: str = 'admin'
    EMAIL: str = 'email'
    PHONE_NUMBER: str = '+79997776655'

    @property
    def database_url(self) -> str:
        """Свойство возвращает url базы данных."""
        return (
            f'postgresql+asyncpg://{self.POSTGRES_USER}:'
            f'{self.POSTGRES_PASSWORD}@'
            f'{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/'
            f'{self.POSTGRES_NAME}'
        )

    @property
    def redis_url(self) -> str:
        """Настройка redis для dev и prod режимов."""
        if self.REDIS_PASSWORD:
            return (
                f'redis://:{self.REDIS_PASSWORD}@'
                f'{self.REDIS_HOST}:{self.REDIS_PORT}/0'
            )
        return f'redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0'

    class Config:
        """Класс настройки подключения .env файла в проект."""

        env_file = '.env'


settings = Settings()


def configure_logging() -> None:
    """Создание конфигурации логгера."""
    logs_dir = os.path.join(BASE_DIR, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    rotating_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'bot_log.log'),
        backupCount=5,
        encoding='utf-8',
    )
    logging.basicConfig(
        datefmt=settings.DATETIME_FORMAT,
        format=settings.LOG_FORMAT,
        level=logging.INFO,
        handlers=(rotating_handler, logging.StreamHandler()),
    )


def example_exc() -> None:
    """Пример использования логгера."""
    try:
        return '1' + 1
    except TypeError as e:
        configure_logging()
        logging.exception(
            f'\nВозникло исключение {str(e)}\n',
            stack_info=False,
        )
