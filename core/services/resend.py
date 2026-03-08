import os
import resend

# Ensure API key is set from the environment variables.
resend.api_key = os.environ.get("RESEND_API_KEY", "")

def send_email(to_emails: list[str], subject: str, html_content: str, from_email: str = "Acme <onboarding@resend.dev>"):
    """
    Sends an email using the Resend API.
    
    Args:
        to_emails (list[str]): A list of email addresses to send the email to.
        subject (str): The subject line of the email.
        html_content (str): The HTML content of the email body.
        from_email (str, optional): The sender's email address. Defaults to "Acme <onboarding@resend.dev>".
        
    Returns:
        dict: The response from the Resend API containing the email ID or error details.
    """
    params: resend.Emails.SendParams = {
        "from": from_email,
        "to": to_emails,
        "subject": subject,
        "html": html_content,
    }

    email_response = resend.Emails.send(params)
    return email_response
