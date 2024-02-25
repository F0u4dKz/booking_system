from app.main import main_bp
from flask import render_template, request
from datetime import date
from app.util import prep_client_base, prep_booking_base, get_key_by_value, payment_performed, get_booking_data, checkin_performed, generate_qr_code, generate_pdf, encode_b64, send_booking_email
from flask_login import login_required, current_user

clients_ids, client_data, client_email = prep_client_base()
booking_ids, booking_list = prep_booking_base(client_data)


@main_bp.route('/')
@login_required
def index(): 
    return render_template('index.html')


@main_bp.route('/payment')
@login_required
def payment(): 
    clients_ids, client_data, client_email = prep_client_base()
    booking_ids, booking_list = prep_booking_base(client_data)
    data = {'clients':client_data, 'bookings':booking_list, 'current_date':date.today()}
    return render_template('payment.html', data = data )

@main_bp.route('/checkin/<string:booking_id>')
@login_required
def checkinok(booking_id : str): 

    values = get_booking_data(booking_id, clients_ids)

    if values['status'] == 'Paid' :
        checkin = checkin_performed(booking_id)
        values = get_booking_data(booking_id, clients_ids)
        data = {'client_name':values['client_name'], 'balance':values['balance'], 'active_from':values['active_from'], 'active_to':values['active_to']}
        return render_template('checkinok.html', data = data)
    
    elif values['status'] == 'Expired' : 

        data = {'client_name':values['client_name'], 'balance':values['balance'], 'active_from':values['active_from'], 'active_to':values['active_to']}
        return render_template('checkinko.html', data = data)


@main_bp.route('/send_payment', methods=['POST']) 
@login_required
def send_payment(): 
  
    
    data = request.form 
    
    client_id = get_key_by_value(client_data, data['client']) 
    raw_client_id = get_key_by_value(clients_ids, data['client']) 

    booking_id = data['num-res'].split(' -- ')[0]
    raw_booking_id = get_key_by_value(booking_ids, booking_id) 

    values = { 
        'payment_id' : f"{client_id}_{data['date']}" ,
        'client_id':[raw_client_id], 
        'date':data['date'], 
        'booking_id': [raw_booking_id], 
        'amount' : int(data['montant'])
    } 

    response = payment_performed(values)

    data = get_booking_data(raw_booking_id, clients_ids)

    generate_qr_code(raw_booking_id, 'http://192.168.1.188:5000')

    data['code_qr_file'] = str(encode_b64(f'./app/static/booking_pass/{raw_booking_id}.png').decode('utf-8'))

    if response == 1:
        
        html_code = render_template('booking_pass.html', data=data)
        path = generate_pdf(html_code, booking_id)
        send_booking_email(client_email[client_id], f"{data['client_name']}", path)
        return render_template('booking_pass.html', data=data)
    else :
        return 'ERRRROOOOOORRRR'
    