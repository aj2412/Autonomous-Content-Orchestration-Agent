import smtplib
import os
from email.message import EmailMessage
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def send_daily_brief(brief_content):
    """
    Sends the generated content brief via Email.
    """
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    receiver_email = os.getenv("RECEIVER_EMAIL")

    if not all([smtp_username, smtp_password, receiver_email]) or smtp_username == "your-email@gmail.com":
        logger.warning("Email not configured. Printing brief to console instead:")
        print("="*50)
        print(brief_content)
        print("="*50)
        return False

    msg = EmailMessage()
    msg.set_content(brief_content)
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    msg['Subject'] = f"🌅 Your Morning LinkedIn Content Brief | {date_str}"
    msg['From'] = smtp_username
    msg['To'] = receiver_email

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        logger.info(f"Successfully sent email brief to {receiver_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
