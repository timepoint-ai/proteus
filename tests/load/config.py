"""
Configuration for load testing.

Environment-specific settings for different test scenarios.
"""

# Default configuration
DEFAULT_CONFIG = {
    "host": "http://localhost:5000",
    "users": 50,
    "spawn_rate": 5,  # Users per second
    "run_time": "60s",
}

# Light load - smoke testing
SMOKE_CONFIG = {
    "host": "http://localhost:5000",
    "users": 10,
    "spawn_rate": 2,
    "run_time": "30s",
}

# Medium load - typical usage
MEDIUM_CONFIG = {
    "host": "http://localhost:5000",
    "users": 100,
    "spawn_rate": 10,
    "run_time": "120s",
}

# Heavy load - stress testing
STRESS_CONFIG = {
    "host": "http://localhost:5000",
    "users": 500,
    "spawn_rate": 25,
    "run_time": "300s",
}

# Spike test - sudden traffic surge
SPIKE_CONFIG = {
    "host": "http://localhost:5000",
    "users": 200,
    "spawn_rate": 50,  # Rapid ramp-up
    "run_time": "60s",
}

# Testnet configuration
TESTNET_CONFIG = {
    "host": "https://testnet.clockchain.app",  # Replace with actual
    "users": 20,
    "spawn_rate": 2,
    "run_time": "120s",
}


def get_locust_command(config: dict, tags: list = None) -> str:
    """Generate locust command from config.

    Args:
        config: Configuration dictionary
        tags: Optional list of tags to filter tests

    Returns:
        Command string to run locust
    """
    cmd = [
        "locust",
        "-f tests/load/locustfile.py",
        f"--host={config['host']}",
        "--headless",
        f"-u {config['users']}",
        f"-r {config['spawn_rate']}",
        f"-t {config['run_time']}",
    ]

    if tags:
        cmd.append(f"--tags {','.join(tags)}")

    return " ".join(cmd)


# Pre-built commands for convenience
COMMANDS = {
    "smoke": get_locust_command(SMOKE_CONFIG),
    "default": get_locust_command(DEFAULT_CONFIG),
    "medium": get_locust_command(MEDIUM_CONFIG),
    "stress": get_locust_command(STRESS_CONFIG),
    "spike": get_locust_command(SPIKE_CONFIG),
    "read_only": get_locust_command(DEFAULT_CONFIG, tags=["read"]),
    "auth_only": get_locust_command(DEFAULT_CONFIG, tags=["auth"]),
    "health_only": get_locust_command(SMOKE_CONFIG, tags=["health"]),
}


if __name__ == "__main__":
    print("Load Test Configurations")
    print("=" * 50)
    for name, cmd in COMMANDS.items():
        print(f"\n{name.upper()}:")
        print(f"  {cmd}")
