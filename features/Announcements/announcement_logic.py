"""
Business logic for SMS and Email notifications.
"""
import requests
import smtplib
import os
import mimetypes
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Tuple, Dict, Any
from features.Announcements.models import SMSNotification, EmailNotification, EmailAttachment, NotificationStatus, NotificationFilter
from features.Announcements.repo import NotificationRepository


class NotificationService:
    """Service class for handling SMS and Email notifications."""

    def __init__(self, repository: NotificationRepository):
        """Initialize with repository."""
        self.repository = repository
        self.sms_api_config = {
            'url': 'https://console.melipayamak.com/api/send/simple/02518acf41404001be90c2baafb85767',
            'from_number': '50002710094507'
        }
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',  # Configure based on your provider
            'smtp_port': 587,
            'username': '',  # Set from environment or config
            'password': ''  # Set from environment or config
        }

    # SMS Methods
    def send_sms(self, recipient_name: str, recipient_phone: str, message: str) -> SMSNotification:
        """Send SMS notification."""
        # Create SMS record
        sms = SMSNotification(
            recipient_name=recipient_name,
            recipient_phone=recipient_phone,
            message=message,
            status=NotificationStatus.PENDING
        )

        # Save to database
        sms = self.repository.save_sms(sms)

        try:
            # Send SMS via API
            response = self._send_sms_api(recipient_phone, message)

            # Update status based on response
            sms.status = NotificationStatus.SENT
            sms.sent_at = datetime.now()
            sms.provider_message_id = response.get('id', str(response.get('RecId', '')))

        except Exception as e:
            sms.status = NotificationStatus.FAILED
            sms.error_message = str(e)

        # Update record in database
        return self.repository.save_sms(sms)

    def _send_sms_api(self, recipient: str, text: str) -> Dict[str, Any]:
        """Send SMS using Melipayamak API."""
        data = {
            'from': self.sms_api_config['from_number'],
            'to': recipient,
            'text': text
        }

        response = requests.post(self.sms_api_config['url'], json=data, timeout=30)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"SMS API error: {response.status_code} - {response.text}")

    def get_sms_status_update(self, sms_id: int) -> Optional[SMSNotification]:
        """Get SMS status update from provider (if supported)."""
        sms = self.repository.get_sms_by_id(sms_id)
        if not sms or not sms.provider_message_id:
            return sms

        try:
            # This would be implemented based on Melipayamak's status API
            # For now, we'll just return the current SMS
            return sms
        except Exception as e:
            print(f"Error getting SMS status: {e}")
            return sms

    # Email Methods
    def send_email(self, recipient_name: str, recipient_email: str, subject: str,
                   message: str, attachments: List[str] = None) -> EmailNotification:
        """Send Email notification."""
        # Process attachments
        email_attachments = []
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path)
                    mime_type, _ = mimetypes.guess_type(file_path)

                    attachment = EmailAttachment(
                        filename=filename,
                        file_path=file_path,
                        file_size=file_size,
                        mime_type=mime_type or 'application/octet-stream'
                    )
                    email_attachments.append(attachment)

        # Create Email record
        email = EmailNotification(
            recipient_name=recipient_name,
            recipient_email=recipient_email,
            subject=subject,
            message=message,
            attachments=email_attachments,
            status=NotificationStatus.PENDING
        )

        # Save to database
        email = self.repository.save_email(email)

        try:
            # Send Email via SMTP
            message_id = self._send_email_smtp(recipient_email, subject, message, email_attachments)

            # Update status based on response
            email.status = NotificationStatus.SENT
            email.sent_at = datetime.now()
            email.provider_message_id = message_id

        except Exception as e:
            email.status = NotificationStatus.FAILED
            email.error_message = str(e)

        # Update record in database
        return self.repository.save_email(email)

    def _send_email_smtp(self, recipient_email: str, subject: str, message: str,
                         attachments: List[EmailAttachment] = None) -> str:
        """Send email using SMTP."""
        if not self.email_config['username'] or not self.email_config['password']:
            raise Exception("Email configuration not set")

        msg = MimeMultipart()
        msg['From'] = self.email_config['username']
        msg['To'] = recipient_email
        msg['Subject'] = subject

        # Add message body
        msg.attach(MimeText(message, 'plain', 'utf-8'))

        # Add attachments
        if attachments:
            for attachment in attachments:
                if os.path.exists(attachment.file_path):
                    with open(attachment.file_path, 'rb') as file:
                        part = MimeBase('application', 'octet-stream')
                        part.set_payload(file.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {attachment.filename}'
                        )
                        msg.attach(part)

        # Send email
        server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
        server.starttls()
        server.login(self.email_config['username'], self.email_config['password'])
        text = msg.as_string()
        server.sendmail(self.email_config['username'], recipient_email, text)
        server.quit()

        # Return a message ID (in real implementation, extract from server response)
        return f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Query Methods
    def get_sms_list(self, filter_criteria: NotificationFilter = None,
                     page: int = 1, page_size: int = 50) -> Tuple[List[SMSNotification], int]:
        """Get paginated SMS list with filters."""
        offset = (page - 1) * page_size
        sms_list = self.repository.get_sms_list(filter_criteria, page_size, offset)
        total_count = self.repository.get_sms_count(filter_criteria)
        return sms_list, total_count

    def get_email_list(self, filter_criteria: NotificationFilter = None,
                       page: int = 1, page_size: int = 50) -> Tuple[List[EmailNotification], int]:
        """Get paginated Email list with filters."""
        offset = (page - 1) * page_size
        email_list = self.repository.get_email_list(filter_criteria, page_size, offset)
        total_count = self.repository.get_email_count(filter_criteria)
        return email_list, total_count

    def get_sms_by_id(self, sms_id: int) -> Optional[SMSNotification]:
        """Get SMS by ID."""
        return self.repository.get_sms_by_id(sms_id)

    def get_email_by_id(self, email_id: int) -> Optional[EmailNotification]:
        """Get Email by ID."""
        return self.repository.get_email_by_id(email_id)

    def update_sms_status(self, sms_id: int, status: NotificationStatus,
                          error_message: str = None) -> Optional[SMSNotification]:
        """Update SMS status."""
        sms = self.repository.get_sms_by_id(sms_id)
        if sms:
            sms.status = status
            if error_message:
                sms.error_message = error_message
            if status == NotificationStatus.DELIVERED:
                sms.delivered_at = datetime.now()
            return self.repository.save_sms(sms)
        return None

    def update_email_status(self, email_id: int, status: NotificationStatus,
                            error_message: str = None) -> Optional[EmailNotification]:
        """Update Email status."""
        email = self.repository.get_email_by_id(email_id)
        if email:
            email.status = status
            if error_message:
                email.error_message = error_message
            if status == NotificationStatus.DELIVERED:
                email.delivered_at = datetime.now()
            return self.repository.save_email(email)
        return None

    def get_notification_stats(self) -> Dict[str, Dict[str, int]]:
        """Get notification statistics."""
        # Get SMS stats
        sms_stats = {
            'total': self.repository.get_sms_count(),
            'sent': self.repository.get_sms_count(NotificationFilter(status=NotificationStatus.SENT)),
            'failed': self.repository.get_sms_count(NotificationFilter(status=NotificationStatus.FAILED)),
            'pending': self.repository.get_sms_count(NotificationFilter(status=NotificationStatus.PENDING)),
            'delivered': self.repository.get_sms_count(NotificationFilter(status=NotificationStatus.DELIVERED))
        }

        # Get Email stats
        email_stats = {
            'total': self.repository.get_email_count(),
            'sent': self.repository.get_email_count(NotificationFilter(status=NotificationStatus.SENT)),
            'failed': self.repository.get_email_count(NotificationFilter(status=NotificationStatus.FAILED)),
            'pending': self.repository.get_email_count(NotificationFilter(status=NotificationStatus.PENDING)),
            'delivered': self.repository.get_email_count(NotificationFilter(status=NotificationStatus.DELIVERED))
        }

        return {
            'sms': sms_stats,
            'email': email_stats
        }

    def configure_email_settings(self, smtp_server: str, smtp_port: int,
                                 username: str, password: str):
        """Configure email settings."""
        self.email_config.update({
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'username': username,
            'password': password
        })

    def test_sms_connection(self) -> bool:
        """Test SMS API connection."""
        try:
            # Send a test request to check API availability
            test_data = {
                'from': self.sms_api_config['from_number'],
                'to': '09000000000',  # Test number
                'text': 'Test connection'
            }
            response = requests.post(self.sms_api_config['url'], json=test_data, timeout=10)
            return response.status_code in [200, 400]  # 400 might be invalid number but API is working
        except Exception:
            return False

    def test_email_connection(self) -> bool:
        """Test email SMTP connection."""
        try:
            if not self.email_config['username'] or not self.email_config['password']:
                return False

            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            server.quit()
            return True
        except Exception:
            return False
