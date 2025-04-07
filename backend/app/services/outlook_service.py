import logging
import imaplib
import email
from email.header import decode_header

logger = logging.getLogger(__name__)

def clean_subject(subject):
    if subject is None:
        return "No Subject"
    if isinstance(subject, bytes):
        return subject.decode()
    decoded, charset = decode_header(subject)[0]
    if isinstance(decoded, bytes):
        return decoded.decode(charset or "utf-8")
    return decoded

class OutlookService:
    def __init__(self):
        # No longer need Azure dependencies
        pass

    def check_personal_outlook_email(self, email_user, app_password):
        try:
            imap_server = 'imap-mail.outlook.com'
            mail = imaplib.IMAP4_SSL(imap_server)

            # Login to user's personal outlook
            mail.login(email_user, app_password)

            mail.select('inbox')
            status, messages = mail.search(None, 'ALL')

            if status != 'OK':
                return "❌ Failed to retrieve emails."

            mail_ids = messages[0].split()

            if not mail_ids:
                return "📭 No emails found."

            latest_emails = mail_ids[-5:]

            emails_info = []

            for mail_id in reversed(latest_emails):
                status, msg_data = mail.fetch(mail_id, '(RFC822)')
                if status != 'OK':
                    continue

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject = clean_subject(msg["subject"])
                        from_ = msg.get("From")
                        emails_info.append(f"✉️ From: {from_}\nSubject: {subject}")

            mail.logout()

            if not emails_info:
                return "📭 No recent emails found."

            return "\n\n".join(emails_info)

        except imaplib.IMAP4.error as e:
            return f"❌ Login failed: {str(e)}"

        except Exception as e:
            return f"❌ An unexpected error occurred: {str(e)}"
