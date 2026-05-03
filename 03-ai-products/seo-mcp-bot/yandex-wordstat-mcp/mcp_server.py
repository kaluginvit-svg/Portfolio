from fastapi_mcp import FastApiMCP
from app import app

mcp = FastApiMCP(
    app,
    name="yandex-wordstat-mcp",
    description="Yandex Wordstat API wrapper (topRequests, dynamics)",
    base_url="http://localhost:8002",
)

if __name__ == "__main__":
    mcp.run()
