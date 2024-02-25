from pyairtable import Api
import datetime 
import os
import segno
from IPython.display import Image
import requests
import base64
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import Config

api = Api(Config.AIRTABLE_KEY)

def prep_client_base():
    '''
    Returns couple of client related data retrieved from client airtable.

            Parameters:
                    None

            Returns:
                    client_raw_ids (dict) : a mapping between raw airtable record id and client names
                    client_names (dict) : a mapping between client ids and their names
                    client_emails (dict) : a mapping between client ids and their emails
    '''
    table = api.table('appRERZ3d4pcnpEDF', 'client')
    client_data = table.all(fields=['client_id', 'name', 'email'])
    client_names = dict()
    client_raw_ids = dict()
    client_emails = dict()
    if client_data :
        for record in client_data:
            raw_record = record['fields']
            client_names[raw_record['client_id']] = raw_record['name']
            client_emails[raw_record['client_id']] = raw_record['email']
            client_raw_ids[record['id']] = raw_record['name']
        return client_raw_ids, client_names, client_emails
    else :
        return 'empty data input'
    


def prep_booking_base(client_data): 
    '''
    Returns couple of booking related data retrieved from booking airtable.

            Parameters:
                    client_data (dict) : 

            Returns:
                    booking_raw_ids (dict) : a mapping between raw airtable record id and booking ids
                    booking_list (list) : a list of all available bookings and client name (booking_id -- client_name)
    '''
    table_booking = api.table('appRERZ3d4pcnpEDF', 'booking')
    booking_data = table_booking.all(fields=['booking_id']) 
    booking_list = []
    if booking_data:
        booking_raw_ids = dict()
        for record in booking_data: 
            raw_record = record['fields']
            client_id = raw_record['booking_id'][:1]
            booking_id = raw_record['booking_id']
            booking_list.append(f'{booking_id} -- {client_data[int(client_id)]}')
            booking_raw_ids[record['id']] = raw_record['booking_id']
        return booking_raw_ids, booking_list
    else : 
        return 'no data available'
    

def get_key_by_value(dict, value):
    '''
    Returns couple of client related data retrieved from client airtable.

            Parameters:
                    None

            Returns:
                    client_raw_ids (dict) : a mapping between raw airtable record id and client names
                    client_names (dict) : a mapping between client ids and their names
                    client_emails (dict) : a mapping between client ids and their emails
    '''
    return list(dict.keys())[list(dict.values()).index(value)] 


def payment_performed(record):
    '''
    Updates a booking record once a payment is made (adding a record to payment table).

            Parameters:
                    record (dict): payment data

            Returns:
                    1: signaling the success of payment operation
    '''
    payment_table = api.table('appRERZ3d4pcnpEDF', 'payment')
    booking_table = api.table('appRERZ3d4pcnpEDF', 'booking')
    payment_table.create(record)
    start_date = datetime.datetime.strptime(record['date'], "%Y-%m-%d")
    end_date = start_date + datetime.timedelta(days=10)
    active_to = end_date.strftime( "%Y-%m-%d")
    update_data = {
        "status": 'Paid', 
        "active_from":record['date'], 
        'active_to':active_to,
        'balance':7
            }
    booking_table.update(record['booking_id'][0],update_data)
    return 1



def get_booking_data(record_id, client_names):
    '''
    Retriving a specific booking data with client name

            Parameters:
                    record_id (str): raw record id 
                    client_names (str): a mapping of client ids and their names 

            Returns:
                    values (dict): a single booking data with client name instead of id
    '''
    table = api.table('appRERZ3d4pcnpEDF', 'booking')
    data = table.get(record_id)['fields']
    values = {
    'client_name' : client_names[data['client_id'][0]],
    'active_from' : data['active_from'],
    'active_to' : data['active_to'],
    'balance'  : data['balance'],
    'status' : data['status']
    }

    return values


def checkin_performed(record_id):
    '''
    Perform a checkin for client valid booking by updating his booking balance

            Parameters:
                    record_id (str): raw record id 
                    client_names (str): a mapping of client ids and their names 

            Returns:
                    1: Signaling operation success
    '''
    booking_table = api.table('appRERZ3d4pcnpEDF', 'booking')
    data = booking_table.get(record_id)['fields']
    update_data = {
        'balance': int(data['balance']) - 1
            }
    booking_table.update(record_id,update_data)

    return 1


def generate_qr_code(booking_id, host):
    '''
    Generating a booking QR code after booking payment/confirmation

            Parameters:
                    booking_id (str): raw record id of booking
                    host (str): technical host link to use when checkin (www.ourspace.com)

            Returns:
                    done: Signaling operation success
    '''
    
    qrcode = segno.make_qr(f"{host}/checkin/{booking_id}")

    qrcode.save(
        f"app/static/booking_pass/{booking_id}.png",
        scale=5,
        dark="#00B77F",
    )
    return 'done'


def encode_b64(filename):
    '''
    Encode an image into a base64 object

            Parameters:
                    filename (str): the path of the image to encode

            Returns:
                    encoded_string (str): returns a bas64 image encoding
    '''
    with open(filename, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
        return encoded_string


def generate_pdf(html_input, booking_id):
    '''
    generate a pdf file using an html in input through rapidAPI

            Parameters:
                    html_input (str): html code of booking pass in string format
                    booking_id (str) : booking_id to pass it as pdf filename

            Returns:
                    path (str): returns the generated pdf path
    '''
    url = "https://yakpdf.p.rapidapi.com/pdf"

    payload = {
        "source": { "html": html_input },
        "pdf": {
            "format": "A4",
            "scale": 1,
            "printBackground": True
        },
        "wait": {
            "for": "navigation",
            "waitUntil": "load",
            "timeout": 30000
        }
    }
    headers = {
        "content-type": "application/json",
        
        "X-RapidAPI-Key": os.environ.get('API_KEY'),
        "X-RapidAPI-Host": "yakpdf.p.rapidapi.com"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
            path =f'app/static/booking_pass/{booking_id}.pdf'
            with open(path, 'wb') as f:
                f.write(response.content)
            print("File saved successfully.")
    return path 



def send_booking_email(to_email, filename, path):
    '''
    Send booking pass through mailtrap mailing service

            Parameters:
                    to_email (str): client email where to send the booking pass
                    filename (str) : specify the name of the attachement (usual client name)
                    path(str) : path of client's booking pass pdf file

            Returns:
                    None
    '''

    port = 587 
    smtp_server = "live.smtp.mailtrap.io"
    login = "api" # paste your login generated by Mailtrap
    password = os.environ.get('MAILTRAP_KEY') # paste your password generated by Mailtrap
   
    subject = "Booking confirmed"
    sender_email = "mailtrap@ngenagency.co"
    receiver_email = to_email

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    # Add body to email
    body = "Hello, please find your booking pass and qr code attached. Thanks"
    message.attach(MIMEText(body, "plain"))

    
    # Open PDF file in binary mode

    # We assume that the file is in the directory where you run your Python script from
    with open(path, "rb") as attachment:
        # The content type "application/octet-stream" means that a MIME attachment is a binary file
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode to base64
    encoders.encode_base64(part)

    # Add header 
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {filename}.pdf",
    )

    # Add attachment to your message and convert it to string
    message.attach(part)
    text = message.as_string()

    # send your email
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls() 
        server.login(login, password)
        server.sendmail(
            sender_email, receiver_email, text
        )
    print('Sent')