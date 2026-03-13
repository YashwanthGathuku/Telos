"""TELOS Orchestrator — uvicorn entry point."""

import uvicorn

from services.orchestrator.config import get_settings


def main() -> None:
    s = get_settings()
    uvicorn.run(
        "services.orchestrator.app:app",
        host=s.orchestrator_host,
        port=s.orchestrator_port,
        reload=False,
        log_level=s.telos_log_level,
    )


if __name__ == "__main__":
    main()
