from app.gigachat_token import get_gigachat_token

if __name__ == "__main__":
    try:
        token = get_gigachat_token()
        print(f"Token: {token}")
    except Exception as e:
        print(f"Error: {e}")