import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENVIRONMENTS_DIR = PROJECT_ROOT / "environments"

ENV_ALIASES = {
    "DEV": "dev",
    "QA": "qa",
    "UAT": "uat",
    "PRD": "prod",
}

ENV_KEY_VARS = {
    "DEV": "DEV_DEPLOYMENT_KEY",
    "QA": "QA_DEPLOYMENT_KEY",
    "UAT": "UAT_DEPLOYMENT_KEY",
    "PRD": "PRD_DEPLOYMENT_KEY",
}


def get_env_config(env_name: str):
    normalized = env_name.strip().upper()
    if normalized not in ENV_ALIASES:
        valid = ", ".join(sorted(ENV_ALIASES))
        raise ValueError(f"Unsupported environment '{env_name}'. Choose one of: {valid}")

    env_dir = ENVIRONMENTS_DIR / ENV_ALIASES[normalized]
    properties_path = env_dir / "env.properties"

    if not properties_path.exists():
        raise FileNotFoundError(f"Environment properties file not found: {properties_path}")

    org_id = None
    with properties_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("orgId="):
                org_id = line.split("=", 1)[1].strip()
                break

    if not org_id:
        raise ValueError(f"No orgId found in {properties_path}")

    key_var = ENV_KEY_VARS[normalized]
    env_dir = ENVIRONMENTS_DIR / ENV_ALIASES[normalized]
    return {
        "env": normalized,
        "folder": ENV_ALIASES[normalized],
        "org_id": org_id,
        "key_var": key_var,
        "env_dir": str(env_dir),
        "properties_path": str(properties_path),
        "model_json": str(env_dir / f"{ENV_ALIASES[normalized]}-model.json")
    }


def build_commands(env_name: str):
    config = get_env_config(env_name)
    key_var = config["key_var"]
    org_id = config["org_id"]
    model_json = config["model_json"]

    return [
        f'echo "${key_var}" | coveo auth:token',
        f"coveo org:resources:pull --organization {org_id} --model {model_json} --overwrite --wait 0",
    ]


def run_env_pull(env_name: str):
    config = get_env_config(env_name)
    key_var = config["key_var"]
    env_dir = config["env_dir"]

    if not os.getenv(key_var):
        raise RuntimeError(f"Missing required environment variable: {key_var}")

    commands = build_commands(env_name)

    for command in commands:
        print(f"$ {command}")
        result = subprocess.run(command, shell=True, check=False, cwd=env_dir)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, command)

    return config


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Pull Coveo resources for a named environment.")
    parser.add_argument("env", choices=["DEV", "QA", "UAT", "PRD"], help="Environment to pull")
    args = parser.parse_args()

    config = run_env_pull(args.env)
    print(f"Environment pull completed for {args.env}: {config['org_id']}")


if __name__ == "__main__":
    main()
