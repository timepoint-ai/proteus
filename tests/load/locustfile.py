"""
Load testing for Proteus Markets Prediction Market API.

Uses Locust to simulate concurrent users hitting various endpoints.
Run with: locust -f tests/load/locustfile.py --host=http://localhost:5000

For headless mode:
locust -f tests/load/locustfile.py --host=http://localhost:5000 --headless -u 100 -r 10 -t 60s
"""

from locust import HttpUser, task, between, tag
import random
import string


class APIUser(HttpUser):
    """Simulates a typical API user browsing markets and checking stats."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Called when a simulated user starts."""
        self.test_address = self._generate_address()

    def _generate_address(self) -> str:
        """Generate a random Ethereum address for testing."""
        return "0x" + "".join(random.choices("0123456789abcdef", k=40))

    @task(10)
    @tag("health")
    def health_check(self):
        """Check API health endpoint - highest frequency."""
        self.client.get("/api/base/health", name="/api/base/health")

    @task(8)
    @tag("markets", "read")
    def get_markets(self):
        """Fetch all markets from blockchain."""
        self.client.get("/api/chain/markets", name="/api/chain/markets")

    @task(5)
    @tag("markets", "read")
    def get_markets_filtered(self):
        """Fetch markets with status filter."""
        status = random.choice(["active", "resolved", "pending"])
        self.client.get(
            f"/api/chain/markets?status={status}",
            name="/api/chain/markets?status=[status]"
        )

    @task(6)
    @tag("actors", "read")
    def get_actors(self):
        """Fetch all actors from blockchain."""
        self.client.get("/api/chain/actors", name="/api/chain/actors")

    @task(4)
    @tag("stats", "read")
    def get_stats(self):
        """Fetch platform statistics."""
        self.client.get("/api/chain/stats", name="/api/chain/stats")

    @task(3)
    @tag("genesis", "read")
    def get_genesis_holders(self):
        """Fetch Genesis NFT holders."""
        self.client.get("/api/chain/genesis/holders", name="/api/chain/genesis/holders")

    @task(5)
    @tag("auth", "read")
    def get_nonce(self):
        """Request authentication nonce for an address."""
        self.client.get(
            f"/auth/nonce/{self.test_address}",
            name="/auth/nonce/[address]"
        )

    @task(4)
    @tag("auth", "read")
    def check_jwt_status(self):
        """Check JWT authentication status."""
        self.client.get("/auth/jwt-status", name="/auth/jwt-status")

    @task(3)
    @tag("embedded", "read")
    def check_embedded_auth_status(self):
        """Check embedded wallet auth status."""
        self.client.get(
            "/api/embedded/auth/status",
            name="/api/embedded/auth/status"
        )


class AuthenticatedUser(HttpUser):
    """Simulates authenticated user actions requiring valid auth."""

    wait_time = between(2, 5)
    weight = 1  # Lower weight - fewer authenticated users

    def on_start(self):
        """Called when a simulated user starts."""
        self.test_address = "0x" + "".join(random.choices("0123456789abcdef", k=40))
        self.test_email = f"test_{random.randint(1000, 9999)}@example.com"

    @task(3)
    @tag("auth", "write")
    def attempt_verify_invalid(self):
        """Attempt verification with invalid signature (tests error handling)."""
        with self.client.post(
            "/auth/verify",
            json={
                "address": self.test_address,
                "signature": "0x" + "a" * 130,
                "message": "Sign in to Proteus Markets"
            },
            name="/auth/verify",
            catch_response=True
        ) as response:
            # Expect 400 or 401 for invalid signature
            if response.status_code in [400, 401]:
                response.success()

    @task(2)
    @tag("embedded", "write")
    def attempt_send_otp_invalid(self):
        """Attempt to send OTP (tests rate limiting and validation)."""
        with self.client.post(
            "/api/embedded/auth/send-otp",
            json={"email": self.test_email},
            name="/api/embedded/auth/send-otp",
            catch_response=True
        ) as response:
            # Accept various responses (success, rate limited, etc.)
            if response.status_code in [200, 429, 400]:
                response.success()

    @task(1)
    @tag("auth", "write")
    def attempt_refresh_without_token(self):
        """Attempt token refresh without valid token (tests error handling)."""
        with self.client.post(
            "/auth/refresh",
            name="/auth/refresh",
            catch_response=True
        ) as response:
            # Expect 401 Unauthorized
            if response.status_code == 401:
                response.success()


class HeavyUser(HttpUser):
    """Simulates power user making many rapid requests."""

    wait_time = between(0.5, 1.5)
    weight = 1  # Lower weight

    @task(5)
    @tag("health")
    def rapid_health_check(self):
        """Rapid health checks to test rate limiting."""
        self.client.get("/api/base/health", name="/api/base/health [rapid]")

    @task(4)
    @tag("markets", "read")
    def rapid_markets(self):
        """Rapid market fetches."""
        self.client.get("/api/chain/markets", name="/api/chain/markets [rapid]")

    @task(3)
    @tag("stats", "read")
    def rapid_stats(self):
        """Rapid stats fetches."""
        self.client.get("/api/chain/stats", name="/api/chain/stats [rapid]")


class BrowsingUser(HttpUser):
    """Simulates user browsing the web interface."""

    wait_time = between(3, 8)
    weight = 2  # Medium weight

    @task(5)
    @tag("pages")
    def view_homepage(self):
        """View homepage."""
        self.client.get("/", name="/ (homepage)")

    @task(4)
    @tag("pages")
    def view_dashboard(self):
        """View dashboard."""
        with self.client.get(
            "/dashboard",
            name="/dashboard",
            catch_response=True
        ) as response:
            # May redirect if not authenticated
            if response.status_code in [200, 302]:
                response.success()

    @task(3)
    @tag("pages")
    def view_markets_page(self):
        """View markets page."""
        self.client.get("/proteus/", name="/proteus/ (markets)")

    @task(2)
    @tag("pages")
    def view_actors_page(self):
        """View actors page."""
        self.client.get("/actors/", name="/actors/")
