import smtplib
from email.message import EmailMessage
import ssl
from pathlib import Path

emails_path = Path("dba_exam2.tsv")
emails = emails_path.read_text(encoding='utf-8').split("\n")
n = 0

for email_record in emails[1:]:
    arr = email_record.split("\t")
    name = arr[3]
    to = arr[4]
    attachment = arr[5]

    # Create the email
    msg = EmailMessage()
    msg['Subject'] = "Administración de Bases de Datos > Exam 2's answers..."
    msg['From'] = 'acald013@ucr.edu'
    msg['To'] = to
    content = f"""Hola {name},
    
    Las respuestas del segundo examen de DBA están en el archivo adjunto.
    
    Cheers!
    """
    print(f"{content}{attachment}")
    msg.set_content(content)

    # Attach the image
    with open(attachment, 'rb') as img_file:
        img_data = img_file.read()
        msg.add_attachment(img_data, maintype = 'image', subtype = 'jpeg', filename = attachment)

    # Send the email using SMTP
    smtp_server = 'smtp.gmail.com'
    smtp_port = 465

    # Use your actual email and app password
    your_email = 'acald013@ucr.edu'
    your_password = 'rmvm zfog dqsp dyao'  # App password if using Gmail

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
        server.login(your_email, your_password)
        server.send_message(msg)

    print(f"Email sent to {to}\n")
    n = n + 1

print(f"Total number of email sent: {n}")
