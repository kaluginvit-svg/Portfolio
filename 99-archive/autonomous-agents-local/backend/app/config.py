from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    """Ключ API (OpenAI или ProxyAPI)."""
    openai_base_url: str = ""
    """URL прокси-API. Если задан — запросы идут через прокси, а не напрямую в OpenAI."""
    openai_model: str = "gpt-4o-mini"
    openai_ssl_verify: bool = True
    """Проверять ли SSL-сертификат при запросах к API (для прокси с самоподписанным сертификатом — false)."""
    use_url_directly: bool = False  # если True — передаём ссылку в промпты; иначе подставляем HTML

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
