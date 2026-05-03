from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_base_url: str = "https://api.proxyapi.ru/openai/v1"
    openai_model: str = "gpt-4o-mini"
    openai_ssl_verify: bool = True
    use_url_directly: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
