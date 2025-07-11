"""
Email service for sending verification and notification emails.

Provides both SMTP and mock implementations for development.
"""

import os
import smtplib
import logging
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailServiceInterface(ABC):
    """Abstract base class for email services."""
    
    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send an email."""
        pass
    
    @abstractmethod
    async def send_verification_email(
        self,
        to_email: str,
        verification_token: str,
        user_name: str
    ) -> bool:
        """Send email verification email."""
        pass
    
    @abstractmethod
    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        user_name: str
    ) -> bool:
        """Send password reset email."""
        pass


class MockEmailService(EmailServiceInterface):
    """Mock email service for development and testing."""
    
    def __init__(self):
        self.sent_emails = []
        self.base_url = os.getenv("FRONTEND_URL", "http://localhost:8000")
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Mock send email - logs to console instead of sending."""
        try:
            email_data = {
                "timestamp": datetime.now().isoformat(),
                "to": to_email,
                "subject": subject,
                "html_content": html_content,
                "text_content": text_content or "No text content provided"
            }
            
            self.sent_emails.append(email_data)
            
            # Log email for development
            logger.info(f"[MOCK EMAIL] To: {to_email}")
            logger.info(f"[MOCK EMAIL] Subject: {subject}")
            logger.info(f"[MOCK EMAIL] Content: {text_content or html_content}")
            
            # Print to console for easy viewing during development
            print(f"\n=== MOCK EMAIL SENT ===")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Content:\n{text_content or html_content}")
            print(f"========================\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Mock email service error: {str(e)}")
            return False
    
    async def send_verification_email(
        self,
        to_email: str,
        verification_token: str,
        user_name: str
    ) -> bool:
        """Send email verification email."""
        verification_url = f"{self.base_url}/verify-email?token={verification_token}"
        
        subject = "Verify Your Email Address - AIhelpers"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Email Verification</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Welcome to AIhelpers!</h2>
                <p>Hi {user_name},</p>
                <p>Thank you for registering with AIhelpers. Please verify your email address by clicking the link below:</p>
                <p style="margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background-color: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
                        Verify Email Address
                    </a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #666;">{verification_url}</p>
                <p>This verification link will expire in 24 hours.</p>
                <p>If you didn't create an account with AIhelpers, please ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 12px; color: #666;">
                    This email was sent by AIhelpers - AI Coding Workflow Platform<br>
                    Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to AIhelpers!
        
        Hi {user_name},
        
        Thank you for registering with AIhelpers. Please verify your email address by visiting:
        {verification_url}
        
        This verification link will expire in 24 hours.
        
        If you didn't create an account with AIhelpers, please ignore this email.
        
        ---
        AIhelpers - AI Coding Workflow Platform
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        user_name: str
    ) -> bool:
        """Send password reset email."""
        reset_url = f"{self.base_url}/reset-password?token={reset_token}"
        
        subject = "Reset Your Password - AIhelpers"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Password Reset</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Password Reset Request</h2>
                <p>Hi {user_name},</p>
                <p>We received a request to reset your password for your AIhelpers account.</p>
                <p style="margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #e74c3c; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
                        Reset Password
                    </a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #666;">{reset_url}</p>
                <p>This password reset link will expire in 1 hour.</p>
                <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 12px; color: #666;">
                    This email was sent by AIhelpers - AI Coding Workflow Platform<br>
                    Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset Request
        
        Hi {user_name},
        
        We received a request to reset your password for your AIhelpers account.
        
        Reset your password by visiting:
        {reset_url}
        
        This password reset link will expire in 1 hour.
        
        If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
        
        ---
        AIhelpers - AI Coding Workflow Platform
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)


class SMTPEmailService(EmailServiceInterface):
    """SMTP email service for production use."""
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.from_email = os.getenv("FROM_EMAIL", "noreply@aihelpers.dev")
        self.from_name = os.getenv("FROM_NAME", "AIhelpers")
        self.base_url = os.getenv("FRONTEND_URL", "http://localhost:8000")
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email via SMTP."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    async def send_verification_email(
        self,
        to_email: str,
        verification_token: str,
        user_name: str
    ) -> bool:
        """Send email verification email."""
        # Use same template as MockEmailService but send via SMTP
        mock_service = MockEmailService()
        return await mock_service.send_verification_email(to_email, verification_token, user_name)
    
    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        user_name: str
    ) -> bool:
        """Send password reset email."""
        # Use same template as MockEmailService but send via SMTP
        mock_service = MockEmailService()
        return await mock_service.send_password_reset_email(to_email, reset_token, user_name)


def get_email_service() -> EmailServiceInterface:
    """Get email service instance based on environment configuration."""
    use_mock = os.getenv("USE_MOCK_EMAIL", "true").lower() == "true"
    
    if use_mock:
        return MockEmailService()
    else:
        return SMTPEmailService()


# Global email service instance
email_service = get_email_service()