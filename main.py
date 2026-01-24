from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from database import (
    init_db, 
    get_user_language, 
    set_user_language, 
    reset_user_session,
    is_bot_active, 
    set_bot_status,
    get_admin_phone
)

app = Flask(__name__)

# Inizializza database all'avvio
init_db()

# Testi multilingua
TEXTS = {
    'it': {
        'welcome': '👋 Benvenuto! Seleziona la lingua:\n\n1️⃣ Italiano\n2️⃣ English\n3️⃣ Čeština',
        'menu': '📋 *Menu Principale*\n\n1️⃣ Orari di apertura\n2️⃣ Menu del giorno\n3️⃣ Allergeni\n4️⃣ Prenotazioni\n5️⃣ Dove siamo\n\n0️⃣ Cambia lingua',
        'hours': '🕐 *Orari di apertura:*\n\nLun-Ven: 12:00-15:00, 18:00-23:00\nSab-Dom: 12:00-23:00\n\nChiuso il Martedì',
        'daily_menu': '🍝 *Menu del Giorno:*\n\nAntipasti:\n- Bruschette miste\n\nPrimi:\n- Pasta al ragù\n- Risotto ai funghi\n\nSecondi:\n- Tagliata di manzo\n\nContorni e dessert disponibili',
        'allergens': '⚠️ *Informazioni Allergeni:*\n\nTutti i nostri piatti possono contenere:\n- Glutine\n- Latticini\n- Uova\n\nPer allergie specifiche, contatta direttamente il ristorante.',
        'booking': '📅 *Prenotazioni:*\n\nPer prenotare un tavolo:\n- Scrivi giorno, ora e numero persone\n- Es: "Sabato alle 20:00 per 4 persone"\n\nOppure chiama: +420 XXX XXX XXX',
        'location': '📍 *Dove siamo:*\n\nVia Example 123, Praha 1\n\nMappa: [inserisci link Google Maps]',
        'bot_off': '🤖 Il bot è attualmente SPENTO.\n\nPer assistenza contatta direttamente il ristorante.',
        'invalid': 'Non ho capito. Scrivi un numero dal menu o "menu" per vedere le opzioni.',
    },
    'en': {
        'welcome': '👋 Welcome! Select your language:\n\n1️⃣ Italiano\n2️⃣ English\n3️⃣ Čeština',
        'menu': '📋 *Main Menu*\n\n1️⃣ Opening hours\n2️⃣ Daily menu\n3️⃣ Allergens\n4️⃣ Reservations\n5️⃣ Location\n\n0️⃣ Change language',
        'hours': '🕐 *Opening hours:*\n\nMon-Fri: 12:00-15:00, 18:00-23:00\nSat-Sun: 12:00-23:00\n\nClosed on Tuesday',
        'daily_menu': '🍝 *Daily Menu:*\n\nStarters:\n- Mixed bruschetta\n\nFirst courses:\n- Pasta with ragù\n- Mushroom risotto\n\nMain courses:\n- Beef tagliata\n\nSides and desserts available',
        'allergens': '⚠️ *Allergen Information:*\n\nAll our dishes may contain:\n- Gluten\n- Dairy\n- Eggs\n\nFor specific allergies, contact the restaurant directly.',
        'booking': '📅 *Reservations:*\n\nTo book a table:\n- Write day, time and number of people\n- Ex: "Saturday at 20:00 for 4 people"\n\nOr call: +420 XXX XXX XXX',
        'location': '📍 *Location:*\n\nVia Example 123, Praha 1\n\nMap: [insert Google Maps link]',
        'bot_off': '🤖 The bot is currently OFF.\n\nPlease contact the restaurant directly.',
        'invalid': 'I didn\'t understand. Write a number from the menu or "menu" to see options.',
    },
    'cs': {
        'welcome': '👋 Vítejte! Vyberte jazyk:\n\n1️⃣ Italiano\n2️⃣ English\n3️⃣ Čeština',
        'menu': '📋 *Hlavní Menu*\n\n1️⃣ Otevírací doba\n2️⃣ Denní menu\n3️⃣ Alergeny\n4️⃣ Rezervace\n5️⃣ Kde nás najdete\n\n0️⃣ Změnit jazyk',
        'hours': '🕐 *Otevírací doba:*\n\nPo-Pá: 12:00-15:00, 18:00-23:00\nSo-Ne: 12:00-23:00\n\nÚterý zavřeno',
        'daily_menu': '🍝 *Denní Menu:*\n\nPředkrmy:\n- Míchaná bruschetta\n\nPrvní chody:\n- Těstoviny s ragù\n- Houbové rizoto\n\nHlavní chody:\n- Hovězí tagliata\n\nPřílohy a dezerty k dispozici',
        'allergens': '⚠️ *Informace o alergenech:*\n\nVšechna naše jídla mohou obsahovat:\n- Lepek\n- Mléčné výrobky\n- Vejce\n\nPro specifické alergie kontaktujte restauraci přímo.',
        'booking': '📅 *Rezervace:*\n\nPro rezervaci stolu:\n- Napište den, čas a počet osob\n- Např: "Sobota ve 20:00 pro 4 osoby"\n\nNebo zavolejte: +420 XXX XXX XXX',
        'location': '📍 *Kde nás najdete:*\n\nVia Example 123, Praha 1\n\nMapa: [vložte odkaz Google Maps]',
        'bot_off': '🤖 Bot je momentálně VYPNUTÝ.\n\nPro pomoc kontaktujte restauraci přímo.',
        'invalid': 'Nerozuměl jsem. Napište číslo z menu nebo "menu" pro zobrazení možností.',
    }
}

def handle_admin_command(incoming_msg):
    """Gestisce comandi admin per ON/OFF"""
    msg_lower = incoming_msg.lower()
    if 'bot on' in msg_lower or 'accendi bot' in msg_lower:
        set_bot_status(True)
        return '✅ Bot ACCESO. Ora risponderà ai clienti.'
    elif 'bot off' in msg_lower or 'spegni bot' in msg_lower:
        set_bot_status(False)
        return '🔴 Bot SPENTO. Non risponderà ai clienti (tranne a te).'
    elif 'status' in msg_lower:
        status = 'ACCESO ✅' if is_bot_active() else 'SPENTO 🔴'
        return f'📊 Stato bot: {status}\n\nComandi disponibili:\n- "bot on" / "accendi bot"\n- "bot off" / "spegni bot"\n- "status"'
    return None

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')

    resp = MessagingResponse()
    msg = resp.message()

    admin_phone = get_admin_phone()

    # Se è l'admin, gestisci comandi speciali
    if sender == admin_phone:
        admin_response = handle_admin_command(incoming_msg)
        if admin_response:
            msg.body(admin_response)
            return str(resp)

    # Se il bot è spento (e non è l'admin)
    if not is_bot_active():
        msg.body(TEXTS['it']['bot_off'])
        return str(resp)

    # Ottieni lingua corrente dal database
    current_lang = get_user_language(sender)

    # Se non ha ancora scelto la lingua
    if not current_lang:
        if incoming_msg in ['1', 'italiano', 'it']:
            set_user_language(sender, 'it')
            msg.body(TEXTS['it']['menu'])
        elif incoming_msg in ['2', 'english', 'en']:
            set_user_language(sender, 'en')
            msg.body(TEXTS['en']['menu'])
        elif incoming_msg in ['3', 'čeština', 'cs', 'czech']:
            set_user_language(sender, 'cs')
            msg.body(TEXTS['cs']['menu'])
        else:
            msg.body(TEXTS['it']['welcome'])
        return str(resp)

    # Ha già scelto la lingua - gestisci il menu
    texts = TEXTS[current_lang]

    # Cambio lingua
    if incoming_msg == '0':
        reset_user_session(sender)
        msg.body(TEXTS['it']['welcome'])
        return str(resp)

    # Menu principale
    if incoming_msg.lower() in ['menu', 'start', 'ciao', 'hello', 'ahoj']:
        msg.body(texts['menu'])
    elif incoming_msg == '1':
        msg.body(texts['hours'])
    elif incoming_msg == '2':
        msg.body(texts['daily_menu'])
    elif incoming_msg == '3':
        msg.body(texts['allergens'])
    elif incoming_msg == '4':
        msg.body(texts['booking'])
    elif incoming_msg == '5':
        msg.body(texts['location'])
    else:
        msg.body(texts['invalid'])

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
