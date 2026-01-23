from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')

    resp = MessagingResponse()
    msg = resp.message()

    if incoming_msg.lower() == 'ciao':
        msg.body('Ciao! Sono Local Defender, il tuo assistente automatico per ristoranti. Come posso aiutarti?')
    elif 'prenotazione' in incoming_msg.lower():
        msg.body('Per prenotare, dimmi: giorno, ora e numero di persone. Es: "Domani alle 20:00 per 4 persone"')
    elif 'menu' in incoming_msg.lower():
        msg.body('Ecco il nostro menu del giorno: [qui inseriresti il menu vero]')
    else:
        msg.body(f'Hai scritto: {incoming_msg}\n\nProva a scrivere "menu" o "prenotazione"')

    return str(resp)

@app.route('/webhook/status', methods=['POST'])
def status_callback():
    message_sid = request.values.get('MessageSid')
    message_status = request.values.get('MessageStatus')
    print(f"Messaggio {message_sid}: {message_status}")
    return '', 200

@app.route('/', methods=['GET'])
def home():
    return 'Local Defender WA Bot is running!', 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)

