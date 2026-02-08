from flask import Flask, request, jsonify
import requests
import os
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

# ===== CONFIGURAZIONE META WHATSAPP API =====
VERIFY_TOKEN = "LD_webhook_verify_123"
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")  # Token generato da Meta
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")  # ID numero telefono (916761058197521)
GRAPH_API_VERSION = "v22.0"
WHATSAPP_API_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/messages"

# ===== TESTI MULTILINGUA =====
TEXTS = {
    'it': {
        'welcome': '👋 Benvenuto! Seleziona la lingua:\n\n1️⃣ Italiano\n2️⃣ English\n3️⃣ Čeština\n\n---\n\n👋 Welcome! Select your language:\n\n1️⃣ Italian\n2️⃣ English\n3️⃣ Czech\n\n---\n\n👋 Vítejte! Vyberte jazyk:\n\n1️⃣ Italsky\n2️⃣ Anglicky\n3️⃣ Česky',
        
        'menu': '📋 *Menu Principale*\n\n1️⃣ Orari di apertura\n2️⃣ Menu del giorno\n3️⃣ Specialità & Vini consigliati\n4️⃣ Prenotazioni\n5️⃣ Dove siamo\n6️⃣ Contattaci\n\n0️⃣ Cambia lingua',
        
        'hours': '🕐 *Orari di apertura:*\n\nLun-Ven: 12:00-15:00, 18:00-23:00\nSab-Dom: 12:00-23:00\n\nChiuso il Martedì\n\nScrivi "menu" per tornare al menu principale.',
        
        'daily_menu': '🍝 *Menu del Giorno:*\n\nAntipasti:\n- Bruschette miste\n- Carpaccio di manzo\n\nPrimi:\n- Pasta al ragù\n- Risotto ai funghi porcini\n\nSecondi:\n- Tagliata di manzo\n- Branzino al forno\n\nContorni e dessert disponibili\n\nScrivi "menu" per tornare al menu principale.',
        
        'specialties': '⭐ *Specialità della Casa & Vini:*\n\n🍷 *Vini Consigliati:*\n- Montepulciano d\'Abruzzo DOC\n- Trebbiano d\'Abruzzo DOC\n- Pecorino IGT\n\n🍝 *Le nostre Specialità:*\n- Arrosticini abruzzesi\n- Pasta alla chitarra\n- Porchetta artigianale\n\nTutti i nostri vini sono biologici e provengono direttamente dalla cantina Retrogusto Vini in Abruzzo.\n\nScrivi "menu" per tornare al menu principale.',
        
        'booking': '📅 *Prenotazioni:*\n\nPer prenotare un tavolo, inviami:\n\n1️⃣ Il tuo nome\n2️⃣ Numero di telefono\n3️⃣ Giorno (es: Sabato 25 Gennaio)\n4️⃣ Ora (es: 20:00)\n5️⃣ Numero di persone\n\nEsempio:\n"Mario Rossi\n+420 123 456 789\nSabato 25 Gennaio\n20:00\n4 persone"\n\n✉️ Riceverai conferma via WhatsApp!\n\nScrivi "menu" per tornare al menu principale.',
        
        'location': '📍 *Dove siamo:*\n\nVia Example 123\nPraha 1, 110 00\n\n🚇 Metro: Linea A - Staroměstská\n🚌 Tram: 17, 18\n\n🗺️ Mappa: [inserire link Google Maps]\n\nScrivi "menu" per tornare al menu principale.',
        
        'contact': '📞 *Contattaci:*\n\n☎️ Telefono: +420 XXX XXX XXX\n📧 Email: info@ristorante.cz\n\n📱 Social:\nInstagram: @ristorante\nFacebook: /ristorante\n\nSiamo aperti per domande, prenotazioni e informazioni!\n\nScrivi "menu" per tornare al menu principale.',
        
        'bot_off': '🤖 Il bot è attualmente SPENTO.\n\nPer assistenza contatta direttamente il ristorante al +420 XXX XXX XXX',
        
        'invalid': 'Non ho capito. Scrivi un numero dal menu (1-6) o "menu" per vedere le opzioni.',
        
        'booking_received': '✅ *Richiesta di prenotazione ricevuta!*\n\nRiceverai conferma a breve dal nostro staff.\n\nScrivi "menu" per tornare al menu principale.',
    },
    
    'en': {
        'welcome': '👋 Benvenuto! Seleziona la lingua:\n\n1️⃣ Italiano\n2️⃣ English\n3️⃣ Čeština\n\n---\n\n👋 Welcome! Select your language:\n\n1️⃣ Italian\n2️⃣ English\n3️⃣ Czech\n\n---\n\n👋 Vítejte! Vyberte jazyk:\n\n1️⃣ Italsky\n2️⃣ Anglicky\n3️⃣ Česky',
        
        'menu': '📋 *Main Menu*\n\n1️⃣ Opening hours\n2️⃣ Daily menu\n3️⃣ Specialties & Recommended wines\n4️⃣ Reservations\n5️⃣ Location\n6️⃣ Contact us\n\n0️⃣ Change language',
        
        'hours': '🕐 *Opening hours:*\n\nMon-Fri: 12:00-15:00, 18:00-23:00\nSat-Sun: 12:00-23:00\n\nClosed on Tuesday\n\nWrite "menu" to return to main menu.',
        
        'daily_menu': '🍝 *Daily Menu:*\n\nStarters:\n- Mixed bruschetta\n- Beef carpaccio\n\nFirst courses:\n- Pasta with ragù\n- Porcini mushroom risotto\n\nMain courses:\n- Beef tagliata\n- Baked sea bass\n\nSides and desserts available\n\nWrite "menu" to return to main menu.',
        
        'specialties': '⭐ *House Specialties & Wines:*\n\n🍷 *Recommended Wines:*\n- Montepulciano d\'Abruzzo DOC\n- Trebbiano d\'Abruzzo DOC\n- Pecorino IGT\n\n🍝 *Our Specialties:*\n- Abruzzese arrosticini\n- Pasta alla chitarra\n- Artisan porchetta\n\nAll our wines are organic and come directly from Retrogusto Vini winery in Abruzzo.\n\nWrite "menu" to return to main menu.',
        
        'booking': '📅 *Reservations:*\n\nTo book a table, send me:\n\n1️⃣ Your name\n2️⃣ Phone number\n3️⃣ Day (e.g., Saturday January 25)\n4️⃣ Time (e.g., 20:00)\n5️⃣ Number of people\n\nExample:\n"Mario Rossi\n+420 123 456 789\nSaturday January 25\n20:00\n4 people"\n\n✉️ You will receive confirmation via WhatsApp!\n\nWrite "menu" to return to main menu.',
        
        'location': '📍 *Location:*\n\nVia Example 123\nPraha 1, 110 00\n\n🚇 Metro: Line A - Staroměstská\n🚌 Tram: 17, 18\n\n🗺️ Map: [insert Google Maps link]\n\nWrite "menu" to return to main menu.',
        
        'contact': '📞 *Contact us:*\n\n☎️ Phone: +420 XXX XXX XXX\n📧 Email: info@ristorante.cz\n\n📱 Social:\nInstagram: @ristorante\nFacebook: /ristorante\n\nWe are open for questions, reservations and information!\n\nWrite "menu" to return to main menu.',
        
        'bot_off': '🤖 The bot is currently OFF.\n\nFor assistance, contact the restaurant directly at +420 XXX XXX XXX',
        
        'invalid': 'I didn\'t understand. Write a number from the menu (1-6) or "menu" to see options.',
        
        'booking_received': '✅ *Booking request received!*\n\nYou will receive confirmation from our staff shortly.\n\nWrite "menu" to return to main menu.',
    },
    
    'cs': {
        'welcome': '👋 Benvenuto! Seleziona la lingua:\n\n1️⃣ Italiano\n2️⃣ English\n3️⃣ Čeština\n\n---\n\n👋 Welcome! Select your language:\n\n1️⃣ Italian\n2️⃣ English\n3️⃣ Czech\n\n---\n\n👋 Vítejte! Vyberte jazyk:\n\n1️⃣ Italsky\n2️⃣ Anglicky\n3️⃣ Česky',
        
        'menu': '📋 *Hlavní Menu*\n\n1️⃣ Otevírací doba\n2️⃣ Denní menu\n3️⃣ Speciality & Doporučená vína\n4️⃣ Rezervace\n5️⃣ Kde nás najdete\n6️⃣ Kontaktujte nás\n\n0️⃣ Změnit jazyk',
        
        'hours': '🕐 *Otevírací doba:*\n\nPo-Pá: 12:00-15:00, 18:00-23:00\nSo-Ne: 12:00-23:00\n\nÚterý zavřeno\n\nNapište "menu" pro návrat do hlavního menu.',
        
        'daily_menu': '🍝 *Denní Menu:*\n\nPředkrmy:\n- Míchaná bruschetta\n- Hovězí carpaccio\n\nPrvní chody:\n- Těstoviny s ragù\n- Hřibové rizoto\n\nHlavní chody:\n- Hovězí tagliata\n- Pečený mořský vlk\n\nPřílohy a dezerty k dispozici\n\nNapište "menu" pro návrat do hlavního menu.',
        
        'specialties': '⭐ *Speciality domu & Vína:*\n\n🍷 *Doporučená vína:*\n- Montepulciano d\'Abruzzo DOC\n- Trebbiano d\'Abruzzo DOC\n- Pecorino IGT\n\n🍝 *Naše speciality:*\n- Abruzzské arrosticini\n- Pasta alla chitarra\n- Řemeslná porchetta\n\nVšechna naše vína jsou bio a pocházejí přímo z vinařství Retrogusto Vini v Abruzzu.\n\nNapište "menu" pro návrat do hlavního menu.',
        
        'booking': '📅 *Rezervace:*\n\nPro rezervaci stolu mi pošlete:\n\n1️⃣ Vaše jméno\n2️⃣ Telefonní číslo\n3️⃣ Den (např. Sobota 25. ledna)\n4️⃣ Čas (např. 20:00)\n5️⃣ Počet osob\n\nPříklad:\n"Mario Rossi\n+420 123 456 789\nSobota 25. ledna\n20:00\n4 osoby"\n\n✉️ Potvrzení obdržíte přes WhatsApp!\n\nNapište "menu" pro návrat do hlavního menu.',
        
        'location': '📍 *Kde nás najdete:*\n\nVia Example 123\nPraha 1, 110 00\n\n🚇 Metro: Linka A - Staroměstská\n🚌 Tramvaj: 17, 18\n\n🗺️ Mapa: [vložte odkaz Google Maps]\n\nNapište "menu" pro návrat do hlavního menu.',
        
        'contact': '📞 *Kontaktujte nás:*\n\n☎️ Telefon: +420 XXX XXX XXX\n📧 Email: info@ristorante.cz\n\n📱 Sociální sítě:\nInstagram: @ristorante\nFacebook: /ristorante\n\nJsme tu pro dotazy, rezervace a informace!\n\nNapište "menu" pro návrat do hlavního menu.',
        
        'bot_off': '🤖 Bot je momentálně VYPNUTÝ.\n\nPro pomoc kontaktujte restauraci přímo na +420 XXX XXX XXX',
        
        'invalid': 'Nerozuměl jsem. Napište číslo z menu (1-6) nebo "menu" pro zobrazení možností.',
        
        'booking_received': '✅ *Žádost o rezervaci přijata!*\n\nPotvrzení od našeho personálu obdržíte brzy.\n\nNapište "menu" pro návrat do hlavního menu.',
    }
}

# ===== FUNZIONI HELPER =====

def send_whatsapp_message(to_number, message_text):
    """Invia un messaggio WhatsApp tramite Meta Graph API"""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message_text
        }
    }
    
    try:
        response = requests.post(WHATSAPP_API_URL, headers=headers, json=data)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ Errore invio messaggio: {e}")
        return False

def handle_admin_command(incoming_msg, sender):
    """Gestisce comandi admin per ON/OFF e prenotazioni"""
    msg_lower = incoming_msg.lower()
    
    # Comandi bot ON/OFF
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

def is_booking_request(msg):
    """Controlla se il messaggio sembra una richiesta di prenotazione"""
    msg_lower = msg.lower()
    indicators = ['prenotazione', 'booking', 'reservation', 'rezervace', 
                  'tavolo', 'table', 'stůl', 'persone', 'people', 'osob']
    return any(indicator in msg_lower for indicator in indicators) and len(msg) > 30

def forward_booking_to_admin(booking_msg, customer_number):
    """Invia la prenotazione all'admin via WhatsApp"""
    admin_phone = get_admin_phone()
    if admin_phone:
        message = f"📅 *NUOVA PRENOTAZIONE*\n\nDa: {customer_number}\n\n{booking_msg}"
        send_whatsapp_message(admin_phone, message)
    return True

def process_message(sender, message_text):
    """Processa il messaggio e restituisce la risposta"""
    
    admin_phone = get_admin_phone()
    
    # Se è l'admin, gestisci comandi speciali
    if sender == admin_phone:
        admin_response = handle_admin_command(message_text, sender)
        if admin_response:
            return admin_response
    
    # Se il bot è spento (e non è l'admin)
    if not is_bot_active():
        return TEXTS['it']['bot_off']
    
    # Ottieni lingua corrente dal database
    current_lang = get_user_language(sender)
    
    # Se non ha ancora scelto la lingua
    if not current_lang:
        if message_text in ['1', 'italiano', 'it', 'italian', 'italsky']:
            set_user_language(sender, 'it')
            return TEXTS['it']['menu']
        elif message_text in ['2', 'english', 'en', 'inglese', 'anglicky']:
            set_user_language(sender, 'en')
            return TEXTS['en']['menu']
        elif message_text in ['3', 'čeština', 'cs', 'czech', 'ceco', 'česky']:
            set_user_language(sender, 'cs')
            return TEXTS['cs']['menu']
        else:
            return TEXTS['it']['welcome']
    
    # Ha già scelto la lingua - gestisci il menu
    texts = TEXTS[current_lang]
    
    # Cambio lingua
    if message_text == '0':
        reset_user_session(sender)
        return TEXTS['it']['welcome']
    
    # Menu principale
    msg_lower = message_text.lower()
    
    if msg_lower in ['menu', 'start', 'ciao', 'hello', 'ahoj']:
        return texts['menu']
    elif message_text == '1':
        return texts['hours']
    elif message_text == '2':
        return texts['daily_menu']
    elif message_text == '3':
        return texts['specialties']
    elif message_text == '4':
        return texts['booking']
    elif message_text == '5':
        return texts['location']
    elif message_text == '6':
        return texts['contact']
    # Se sembra una prenotazione
    elif is_booking_request(message_text):
        forward_booking_to_admin(message_text, sender)
        return texts['booking_received']
    else:
        return texts['invalid']

# ===== WEBHOOK ENDPOINTS =====

@app.route('/webhook/whatsapp', methods=['GET'])
def verify_webhook():
    """Verifica webhook per Meta (richiesta GET iniziale)"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print("✅ Webhook verificato!")
        return challenge, 200
    else:
        print("❌ Verifica webhook fallita")
        return 'Forbidden', 403

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """Riceve messaggi da Meta WhatsApp"""
    try:
        data = request.get_json()
        
        # Estrai i dati dal webhook Meta
        if data.get('object') == 'whatsapp_business_account':
            entries = data.get('entry', [])
            
            for entry in entries:
                changes = entry.get('changes', [])
                
                for change in changes:
                    value = change.get('value', {})
                    
                    # Verifica che ci siano messaggi
                    messages = value.get('messages', [])
                    
                    if messages:
                        for message in messages:
                            sender = message.get('from')
                            message_type = message.get('type')
                            
                            # Gestisci solo messaggi di testo
                            if message_type == 'text':
                                message_text = message.get('text', {}).get('body', '')
                                
                                # Processa il messaggio
                                response_text = process_message(sender, message_text)
                                
                                # Invia la risposta
                                send_whatsapp_message(sender, response_text)
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"❌ Errore webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    """Homepage per verificare che il bot sia online"""
    return 'Local Defender WA Bot (Meta API) is running! 🚀', 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    bot_status = 'ON ✅' if is_bot_active() else 'OFF 🔴'
    return jsonify({
        "status": "healthy",
        "bot_active": is_bot_active(),
        "message": f"Bot status: {bot_status}"
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
