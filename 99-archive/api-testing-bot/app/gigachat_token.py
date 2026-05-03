import os
import pathlib
from gigachat import GigaChat
from dotenv import load_dotenv


def prepare_gigachat_env(env_path: str = None) -> str:
    """
    Load env, prepare certs and return GIGA_CREDENTIALS string.
    Does not perform network calls.
    """
    # Load .env if path provided or find in project root
    if env_path:
        load_dotenv(env_path)
    else:
        # Try to find .env in project root or parent directories
        current = pathlib.Path(__file__).resolve().parent
        for _ in range(3):  # Search up to 3 levels
            env_file = current.parent / ".env"
            if env_file.exists():
                load_dotenv(env_file)
                break
            current = current.parent
    
    credentials = os.environ.get("GIGA_CREDENTIALS")
    if not credentials:
        raise ValueError(
            "GIGA_CREDENTIALS not found in environment. "
            "Add 'GIGA_CREDENTIALS=your_base64_credentials' to .env file"
        )
    
    # Сертификаты в папке certs в корне проекта
    ca_bundle = pathlib.Path(__file__).resolve().parent.parent / "certs" / "ca-bundle.pem"
    
    # Если ca-bundle.pem не существует, создаём его из всех .cer файлов
    if not ca_bundle.exists():
        certs_dir = ca_bundle.parent
        if certs_dir.exists():
            cer_files = list(certs_dir.glob("*.cer"))
            if cer_files:
                with open(ca_bundle, 'w', encoding='ascii') as pem_file:
                    for cer_file in cer_files:
                        with open(cer_file, 'r', encoding='ascii') as cf:
                            pem_file.write(cf.read() + '\n')
    
    if ca_bundle.exists():
        os.environ["SSL_CERT_FILE"] = str(ca_bundle)
        os.environ["REQUESTS_CA_BUNDLE"] = str(ca_bundle)
    
    return credentials


def get_gigachat_token(env_path: str = None) -> str:
    """
    Get GigaChat access token using stored credentials.
    """
    credentials = prepare_gigachat_env(env_path)
    
    # Create GigaChat client and get token
    giga = GigaChat(credentials=credentials, verify_ssl_certs=True)
    token = giga.get_token()
    
    # Библиотека может вернуть объект/словарь — извлекаем строку токена
    if isinstance(token, dict):
        token = token.get("access_token") or token.get("token")
    elif hasattr(token, "access_token"):
        token = token.access_token
    
    if not isinstance(token, str):
        raise ValueError("GigaChat token must be a string, got unexpected type")
    
    return token


if __name__ == "__main__":
    try:
        token = get_gigachat_token()
        print(f"✅ Token received: {token[:20]}...")
    except ValueError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Connection error: {e}")