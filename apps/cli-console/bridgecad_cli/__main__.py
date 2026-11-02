"""Allow ``python -m bridgecad_cli`` (used by apps/cli-console/Dockerfile ENTRYPOINT)."""

from bridgecad_cli.main import app

if __name__ == "__main__":
    app()
