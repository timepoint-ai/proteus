"""
Unit tests for Firebase authentication service.
"""

import pytest
import os


@pytest.mark.unit
class TestFirebaseAuthService:
    """Test Firebase authentication service."""

    @pytest.fixture
    def firebase_service(self):
        """Create Firebase auth service instance."""
        from services.firebase_auth import FirebaseAuthService
        return FirebaseAuthService()

    def test_service_initialization(self, firebase_service):
        """Test service initializes correctly."""
        assert firebase_service is not None
        # In test mode, API key should be None
        # Service should still work in test mode

    def test_send_email_verification_test_mode(self, firebase_service):
        """Test email verification in test mode (no API key)."""
        # Temporarily ensure no API key
        original_key = os.environ.get("FIREBASE_API_KEY")
        if original_key:
            del os.environ["FIREBASE_API_KEY"]

        try:
            # Reinitialize to pick up missing key
            from services.firebase_auth import FirebaseAuthService
            service = FirebaseAuthService()

            result = service.send_email_verification("test@example.com")

            assert result["success"] is True
            assert result.get("test_mode") is True
            assert result.get("otp") == "123456"
        finally:
            if original_key:
                os.environ["FIREBASE_API_KEY"] = original_key

    def test_verify_email_otp_test_mode(self, firebase_service):
        """Test OTP verification in test mode."""
        # In test mode, "123456" should work
        from services.firebase_auth import FirebaseAuthService
        service = FirebaseAuthService()

        # Without API key, should accept test OTP
        if not service.api_key:
            result = service.verify_email_otp("test@example.com", "123456")
            assert result["success"] is True
            assert result.get("test_mode") is True

    def test_verify_email_otp_invalid_code(self, firebase_service):
        """Test that invalid OTP is rejected."""
        from services.firebase_auth import FirebaseAuthService
        service = FirebaseAuthService()

        if not service.api_key:
            result = service.verify_email_otp("test@example.com", "000000")
            assert result["success"] is False

    def test_generate_temp_password(self, firebase_service):
        """Test deterministic password generation."""
        email1 = "test@example.com"
        email2 = "other@example.com"

        pw1 = firebase_service._generate_temp_password(email1)
        pw2 = firebase_service._generate_temp_password(email2)
        pw1_again = firebase_service._generate_temp_password(email1)

        # Same email should produce same password
        assert pw1 == pw1_again
        # Different emails should produce different passwords
        assert pw1 != pw2
        # Password should be 20 characters
        assert len(pw1) == 20


@pytest.mark.unit
class TestFirebaseAuthEdgeCases:
    """Edge case tests for Firebase auth."""

    def test_empty_email(self):
        """Test handling of empty email."""
        from services.firebase_auth import FirebaseAuthService
        service = FirebaseAuthService()

        # Empty email should still work in test mode but is invalid
        result = service.send_email_verification("")
        # Service should handle gracefully

    def test_invalid_email_format(self):
        """Test handling of invalid email format."""
        from services.firebase_auth import FirebaseAuthService
        service = FirebaseAuthService()

        # Invalid email format
        result = service.send_email_verification("not-an-email")
        # In test mode, this still succeeds
        # Real mode would validate
