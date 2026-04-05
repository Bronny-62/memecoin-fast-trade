from __future__ import annotations

import uvicorn

from monitoring_service.app import create_app
from monitoring_service.settings import load_settings

app = create_app()


def main() -> None:
    settings = load_settings()
    uvicorn.run(
        "monitoring_service.terminal_server:app",
        host="0.0.0.0",
        port=settings.listen_port,
        reload=True,
        log_level="warning",
        access_log=False,
    )


if __name__ == "__main__":
    main()

