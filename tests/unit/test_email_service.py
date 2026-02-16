"""
Unit tests for EmailService.
Tests email sending with mocked SendGrid client.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os

# Skip tests if sendgrid is not installed
try:
    import sendgrid
    HAS_SENDGRID = True
except ImportError:
    HAS_SENDGRID = False

pytestmark = pytest.mark.skipif(not HAS_SENDGRID, reason="sendgrid not installed")


@pytest.fixture
def mock_sendgrid():
    """Create a mock SendGrid client."""
    mock = MagicMock()
    mock_response = Mock()
    mock_response.status_code = 202
    mock.send.return_value = mock_response
    return mock


class TestEmailServiceInit:
    """Tests for EmailService initialization."""

    @pytest.mark.unit
    def test_init_without_api_key(self):
        """EmailService initializes without API key."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('SENDGRID_API_KEY', None)
            from services.email_service import EmailService
            service = EmailService()
            assert service.client is None

    @pytest.mark.unit
    def test_init_with_api_key(self, mock_sendgrid):
        """EmailService initializes with API key."""
        with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test-key'}):
            with patch('services.email_service.SendGridAPIClient', return_value=mock_sendgrid):
                from services.email_service import EmailService
                service = EmailService()
                assert service.client is not None

    @pytest.mark.unit
    def test_default_from_email(self):
        """EmailService uses default from_email."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('FROM_EMAIL', None)
            from services.email_service import EmailService
            service = EmailService()
            assert service.from_email == 'noreply@proteus.markets'

    @pytest.mark.unit
    def test_custom_from_email(self):
        """EmailService uses custom from_email from env."""
        with patch.dict(os.environ, {'FROM_EMAIL': 'custom@example.com'}):
            from services.email_service import EmailService
            service = EmailService()
            assert service.from_email == 'custom@example.com'


class TestSendOtp:
    """Tests for EmailService.send_otp()"""

    @pytest.mark.unit
    def test_send_otp_without_client_returns_test_mode(self):
        """send_otp() returns test mode when client not configured."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('SENDGRID_API_KEY', None)
            from services.email_service import EmailService
            service = EmailService()

            result = service.send_otp('test@example.com', '123456')

            assert result['success'] is False
            assert result['test_mode'] is True
            assert result['otp'] == '123456'  # OTP returned for testing

    @pytest.mark.unit
    def test_send_otp_success(self, mock_sendgrid):
        """send_otp() returns success when email sent."""
        with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test-key'}):
            with patch('services.email_service.SendGridAPIClient', return_value=mock_sendgrid):
                from services.email_service import EmailService
                service = EmailService()

                result = service.send_otp('test@example.com', '123456')

                assert result['success'] is True
                assert result['status_code'] == 202
                mock_sendgrid.send.assert_called_once()

    @pytest.mark.unit
    def test_send_otp_creates_correct_subject(self, mock_sendgrid):
        """send_otp() creates email with correct subject."""
        with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test-key'}):
            with patch('services.email_service.SendGridAPIClient', return_value=mock_sendgrid):
                from services.email_service import EmailService
                service = EmailService()

                service.send_otp('test@example.com', '654321')

                # Get the Mail object passed to send()
                call_args = mock_sendgrid.send.call_args
                mail_obj = call_args[0][0]
                assert '654321' in mail_obj.subject.get()

    @pytest.mark.unit
    def test_send_otp_handles_sendgrid_error(self, mock_sendgrid):
        """send_otp() handles SendGrid errors gracefully."""
        mock_sendgrid.send.side_effect = Exception("SendGrid error")

        with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test-key'}):
            with patch('services.email_service.SendGridAPIClient', return_value=mock_sendgrid):
                from services.email_service import EmailService
                service = EmailService()

                result = service.send_otp('test@example.com', '123456')

                assert result['success'] is False
                assert 'error' in result
                assert result['test_mode'] is True
                assert result['otp'] == '123456'  # OTP returned as fallback


class TestSendTransactionAlert:
    """Tests for EmailService.send_transaction_alert()"""

    @pytest.mark.unit
    def test_send_transaction_alert_without_client(self):
        """send_transaction_alert() returns error when client not configured."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('SENDGRID_API_KEY', None)
            from services.email_service import EmailService
            service = EmailService()

            result = service.send_transaction_alert('test@example.com', {})

            assert result['success'] is False
            assert 'error' in result

    @pytest.mark.unit
    def test_send_transaction_alert_success(self, mock_sendgrid):
        """send_transaction_alert() returns success when email sent."""
        with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test-key'}):
            with patch('services.email_service.SendGridAPIClient', return_value=mock_sendgrid):
                from services.email_service import EmailService
                service = EmailService()

                tx_details = {
                    'amount_usd': 100.50,
                    'tx_hash': '0xabc123',
                    'market': 'Test Market'
                }

                result = service.send_transaction_alert('test@example.com', tx_details)

                assert result['success'] is True
                assert result['status_code'] == 202
                mock_sendgrid.send.assert_called_once()

    @pytest.mark.unit
    def test_send_transaction_alert_handles_error(self, mock_sendgrid):
        """send_transaction_alert() handles errors gracefully."""
        mock_sendgrid.send.side_effect = Exception("SendGrid error")

        with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test-key'}):
            with patch('services.email_service.SendGridAPIClient', return_value=mock_sendgrid):
                from services.email_service import EmailService
                service = EmailService()

                result = service.send_transaction_alert('test@example.com', {})

                assert result['success'] is False
                assert 'error' in result

    @pytest.mark.unit
    def test_send_transaction_alert_handles_missing_fields(self, mock_sendgrid):
        """send_transaction_alert() handles missing tx_details fields."""
        with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test-key'}):
            with patch('services.email_service.SendGridAPIClient', return_value=mock_sendgrid):
                from services.email_service import EmailService
                service = EmailService()

                # Empty tx_details
                result = service.send_transaction_alert('test@example.com', {})

                # Should still succeed with defaults
                assert result['success'] is True
