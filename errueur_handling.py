import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback



def send_error_email(error_message):
    sender_email = "kasmiy33@gmail.com"         # Your email
    sender_password = "jvyhmfourfruiyqs"  # remove any spaces, must be exactly 16 chars
   # App password if using Gmail
    receiver_email = "youssefkasmi05@gmail.com" # Person to notify

    subject = "Flask App Notification"

    # Create message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    body = f"Message from server:\n\n{error_message}"
    msg.attach(MIMEText(body, 'plain'))

    # Connect and send email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Change if not Gmail
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("Error email sent successfully!")
    except Exception as e:
        print(f"Failed to send error email: {e}")