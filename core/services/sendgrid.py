import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email(to_emails: list[str] | str, subject: str, html_content: str):
    """
    Sends an email using the SendGrid API.
    
    Args:
        to_emails (list[str] | str): Email addresses to send the email to.
        subject (str): The subject line of the email.
        html_content (str): The HTML content of the email body.
        from_email (str, optional): The sender's email address. Defaults to "from_email@example.com".
        
    Returns:
        The response from the SendGrid API or None if an error occurred.
    """
    from_email = os.environ.get('DEFAULT_FROM_EMAIL')
    message = Mail(
        from_email=from_email,
        to_emails=to_emails,
        subject=subject,
        html_content=html_content
    )
    
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        return response
    except Exception as e:
        print(getattr(e, 'message', str(e)))
        return None
