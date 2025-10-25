from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""

    secret_key: str = "change_me_to_a_secure_value"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12
    database_url: str = "sqlite:///./casino.db"
    initial_balance: int = 2500
    daily_bonus_amount: int = 500
    loyalty_points_per_game: int = 10


settings = Settings()
