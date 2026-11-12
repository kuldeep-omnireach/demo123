import os

from fastapi.testclient import TestClient

from src.main import app
from src.scripts.pull_environment import build_commands, get_env_config


def test_read_main():
    client = TestClient(app)
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}


def test_dev_env_config_uses_env_specific_key_and_org(monkeypatch):
    monkeypatch.setenv("DEV_DEPLOYMENT_KEY", "dev-secret")

    config = get_env_config("DEV")

    assert config["key_var"] == "DEV_DEPLOYMENT_KEY"
    assert config["org_id"] == "resmednonproduction1fl4b3vdz"
    assert build_commands("DEV")[0] == 'echo "$DEV_DEPLOYMENT_KEY" | coveo auth:token'
