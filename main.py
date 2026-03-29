"""Cravvy application entry point."""

import uvicorn

from src.shared import settings


def main() -> None:
    """Start the uvicorn server."""
    uvicorn.run(
        "src.api.app:create_app",
        factory=True,
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    main()
