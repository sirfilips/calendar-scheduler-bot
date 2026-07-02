import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import Update, BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Configurazione del logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TIMEZONE = ZoneInfo("Europe/Rome")

# Stati per le conversazioni
TITOLO, DATA_ORA = range(2)  # Per la creazione
SCELTA_ELIMINA = 2           # Per l'eliminazione

# Database temporaneo
eventi_in_programma = []

# --- FUNZIONI DI SUPPORTO ---

async def is_admin_in_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_chat.type == 'private':
        return False
    member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    return member.status in ['administrator', 'creator']

async def imposta_menu_comandi(application: Application) -> None:
    comandi = [
        BotCommand("start", "Mostra il messaggio di benvenuto o avvia registrazione"),
        BotCommand("calendario", "Visualizza le prossime sedute del Senato"),
        BotCommand("nuovaseduta", "(Admin) Calendarizza una nuova seduta"),
        BotCommand("eliminaseduta", "(Creatore) Elimina una tua seduta in programma"), # AGGIORNATO
        BotCommand("annulla", "Interrompi un'operazione in corso")
    ]
    await application.bot.set_my_commands(comandi)
    logger.info("Menu dei comandi aggiornato con successo!")

# --- JOB QUEUE (Avvisi automatici) ---

async def invia_promemoria_evento(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    titolo_evento = job.data['titolo']
    
    messaggio = (
        f"🏛 **SENATO DELLA REPUBBLICA: INIZIO DISCUSSIONE** 🏛\n\n"
        f"Discussione dell'evento in calendario:\n"
        f"📌 *{titolo_evento}*\n\n"
        f"La seduta è aperta."
    )
    await context.bot.send_message(chat_id=chat_id, text=messaggio, parse_mode='Markdown')

# --- HANDLER: CREAZIONE EVENTI ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_chat.type == 'private' and context.args:
        payload = context.args[0]
        
        if payload.startswith("seduta_"):
            try:
                target_chat_id = int(payload.replace("seduta_", ""))
                context.user_data['target_chat_id'] = target_chat_id
            except ValueError:
                await update.message.reply_text("❌ Link di programmazione non valido.")
                return ConversationHandler.END

            try:
                member = await context.bot.get_chat_member(target_chat_id, update.effective_user.id)
                if member.status not in ['administrator', 'creator']:
                    await update.message.reply_text("⛔ Non hai i permessi di amministratore in quel gruppo.")
                    return ConversationHandler.END
            except Exception:
                await update.message.reply_text("❌ Impossibile verificare i permessi. Assicurati che il bot sia nel gruppo.")
                return ConversationHandler.END

            await update.message.reply_text(
                "🏛 **Programmazione Nuova Seduta**\n\n"
                "Inserisci il **Titolo o Argomento** della seduta da calendarizzare:\n"
                "(Usa /annulla per interrompere l'operazione)", parse_mode='Markdown'
            )
            return TITOLO

    await update.message.reply_text(
        "Salve. Sono il bot per la calendarizzazione del Senato. "
        "Usa /nuovaseduta o /eliminaseduta, "
        "oppure /calendario per vedere gli eventi futuri."
    )
    return ConversationHandler.END

async def inizia_programmazione(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type == 'private':
        await update.message.reply_text("Questo comando serve nei gruppi. Per programmare, usa il link generato nel gruppo!")
        return
    
    if not await is_admin_in_group(update, context):
        await update.message.reply_text("⛔ Solo i membri del senato/admin possono calendarizzare eventi.")
        return

    bot_username = context.bot.username
    chat_id = update.effective_chat.id
    link_privato = f"https://t.me/{bot_username}?start=seduta_{chat_id}"
    
    keyboard = [[InlineKeyboardButton("Programma in Privato 📝", url=link_privato)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Per mantenere pulita la chat, andiamo in privato a configurare i dettagli della seduta:",
        reply_markup=reply_markup
    )

async def ricevi_titolo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['titolo_temp'] = update.message.text
    await update.message.reply_text(
        f"Titolo registrato: *{update.message.text}*\n\n"
        "Ora inserisci la **Data e l'Ora** nel formato: `GG/MM/AAAA HH:MM`", parse_mode='Markdown'
    )
    return DATA_ORA

async def ricevi_data_ora(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    testo_data = update.message.text
    titolo = context.user_data.get('titolo_temp')
    chat_id = context.user_data.get('target_chat_id')
    user_id = update.effective_user.id  # <-- NUOVO: Salviamo l'ID di chi crea
    
    try:
        data_ora_evento = datetime.strptime(testo_data, "%d/%m/%Y %H:%M")
        data_ora_evento = data_ora_evento.replace(tzinfo=TIMEZONE)
        
        if data_ora_evento < datetime.now(TIMEZONE):
            await update.message.reply_text("La data inserita è nel passato! Riprova con una data futura:")
            return DATA_ORA

        # Salva in background con un NOME UNIVOCO
        context.job_queue.run_once(
            invia_promemoria_evento, 
            when=data_ora_evento, 
            chat_id=chat_id, 
            data={'titolo': titolo},
            name=f"evento_{chat_id}_{data_ora_evento.timestamp()}" # NOME CHIAVE PER L'ELIMINAZIONE
        )

        # <-- NUOVO: Aggiunto creatore_id al dizionario
        eventi_in_programma.append({
            'chat_id': chat_id,
            'titolo': titolo,
            'data': data_ora_evento,
            'creatore_id': user_id 
        })

        context.user_data.clear()
        await update.message.reply_text(
            f"✅ **Seduta Calendarizzata con Successo!**\n\n"
            f"📌 Argomento: {titolo}\n"
            f"📅 Data e Ora: {data_ora_evento.strftime('%d/%m/%Y alle %H:%M')}\n"
            f"*(Solo tu potrai eliminare questa seduta)*", parse_mode='Markdown'
        )
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("⚠️ Formato non valido. Usa `GG/MM/AAAA HH:MM` (es. `25/10/2026 21:30`). Riprova:")
        return DATA_ORA

# --- HANDLER: ELIMINAZIONE EVENTI ---

async def inizia_eliminazione(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id # <-- NUOVO: Prendiamo l'ID di chi lancia il comando
    
    # Filtro gruppo
    if chat_type in ['group', 'supergroup']:
        chat_filter_id = update.effective_chat.id
    else:
        chat_filter_id = None # Se usato in privata, mostra tutto nei propri gruppi

    ora_attuale = datetime.now(TIMEZONE)
    
    # <-- NUOVO: Trova gli eventi futuri creati ESCLUSIVAMENTE da questo utente
    if chat_filter_id:
        eventi_eliminabili = [
            e for e in eventi_in_programma 
            if e['data'] > ora_attuale and e['chat_id'] == chat_filter_id and e.get('creatore_id') == user_id
        ]
    else:
        eventi_eliminabili = [
            e for e in eventi_in_programma 
            if e['data'] > ora_attuale and e.get('creatore_id') == user_id
        ]

    if not eventi_eliminabili:
        await update.message.reply_text("Non ci sono sedute create da te in programma da eliminare.")
        return ConversationHandler.END

    eventi_eliminabili.sort(key=lambda x: x['data'])
    context.user_data['eventi_eliminabili'] = eventi_eliminabili

    messaggio = "🗑 **ELIMINAZIONE SEDUTA** 🗑\n\nQuale delle tue sedute vuoi annullare? **Rispondi con il numero** corrispondente:\n\n"
    for i, evento in enumerate(eventi_eliminabili, 1):
        data_str = evento['data'].strftime('%d/%m %H:%M')
        messaggio += f"{i}. *{evento['titolo']}* ({data_str})\n"
    
    messaggio += "\n*(Scrivi /annulla per annullare l'operazione)*"

    await update.message.reply_text(messaggio, parse_mode='Markdown')
    return SCELTA_ELIMINA

async def esegui_eliminazione(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    scelta = update.message.text
    eventi_eliminabili = context.user_data.get('eventi_eliminabili', [])

    # Controlla se ha inserito un numero valido
    if not scelta.isdigit() or not (1 <= int(scelta) <= len(eventi_eliminabili)):
        await update.message.reply_text("⚠️ Numero non valido. Inserisci un numero presente nell'elenco oppure scrivi /annulla:")
        return SCELTA_ELIMINA

    indice = int(scelta) - 1
    evento_selezionato = eventi_eliminabili[indice]

    # 1. Ferma e cancella il timer programmato usando il nome univoco
    job_name = f"evento_{evento_selezionato['chat_id']}_{evento_selezionato['data'].timestamp()}"
    jobs = context.job_queue.get_jobs_by_name(job_name)
    for job in jobs:
        job.schedule_removal()

    # 2. Cancella dalla memoria globale
    if evento_selezionato in eventi_in_programma:
        eventi_in_programma.remove(evento_selezionato)

    context.user_data.clear()

    await update.message.reply_text(
        f"✅ **Seduta eliminata con successo!**\n\nL'evento *{evento_selezionato['titolo']}* è stato rimosso e non verranno inviati avvisi.", 
        parse_mode='Markdown'
    )
    return ConversationHandler.END

# --- HANDLER COMUNI ---

async def annulla(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Operazione annullata.")
    return ConversationHandler.END

# --- FUNZIONE LISTA EVENTI AGGIORNATA (CON CONTROLLO PRIVACY) ---

async def mostra_calendario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    # 1. Pulisce eventi passati dalla lista
    ora_attuale = datetime.now(TIMEZONE)
    eventi_futuri = [e for e in eventi_in_programma if e['data'] > ora_attuale]

    if not eventi_futuri:
        await update.message.reply_text("Non ci sono sedute in programma al momento.")
        return

    eventi_da_mostrare = []

    # 2. Logica se il comando è inviato nel GRUPPO
    if chat_type in ['group', 'supergroup']:
        if not await is_admin_in_group(update, context):
            await update.message.reply_text("Solo gli admin possono mostrare il calendario pubblicamente nel gruppo. Scrivimi in privato per vederlo!")
            return
        
        # Mostra solo gli eventi di questo specifico gruppo
        chat_filter_id = update.effective_chat.id
        eventi_da_mostrare = [e for e in eventi_futuri if e['chat_id'] == chat_filter_id]

    # 3. Logica se il comando è inviato in PRIVATO
    else:
        # Troviamo tutti i gruppi unici che hanno almeno un evento in programma
        gruppi_con_eventi = set(e['chat_id'] for e in eventi_futuri)
        gruppi_autorizzati = set()

        for chat_id in gruppi_con_eventi:
            try:
                # Chiediamo alle API di Telegram lo status dell'utente in quel gruppo
                member = await context.bot.get_chat_member(chat_id, user_id)
                
                # Se l'utente è dentro al gruppo (membro normale, admin, creatore o con restrizioni ma presente)
                if member.status in ['member', 'administrator', 'creator', 'restricted']:
                    gruppi_autorizzati.add(chat_id)
            except Exception:
                # Se il bot è stato cacciato dal gruppo o l'API dà errore, saltiamo la verifica
                continue
        
        # Filtriamo gli eventi: teniamo solo quelli dei gruppi in cui l'utente è effettivamente presente
        eventi_da_mostrare = [e for e in eventi_futuri if e['chat_id'] in gruppi_autorizzati]

        if not eventi_da_mostrare:
            await update.message.reply_text(
                "⛔ **Accesso negato**\nNon risulti membro di alcun gruppo del Senato, oppure non ci sono eventi in programma per i tuoi gruppi.",
                parse_mode='Markdown'
            )
            return

    # Selettore vuoto di sicurezza
    if not eventi_da_mostrare:
        await update.message.reply_text("Non ci sono sedute in programma per questo Senato al momento.")
        return

    # 4. Formattazione del messaggio finale
    messaggio = "🗓 **CALENDARIO SEDUTE SENATO DELLA REPUBBLICA** 🗓\n\n"
    
    # Ordina cronologicamente
    eventi_da_mostrare.sort(key=lambda x: x['data'])
    
    for i, evento in enumerate(eventi_da_mostrare, 1):
        data_str = evento['data'].strftime('%d/%m/%Y')
        ora_str = evento['data'].strftime('%H:%M')
        messaggio += f"{i}. *{evento['titolo']}*\n   ⏱ {data_str} alle {ora_str}\n\n"

    await update.message.reply_text(messaggio, parse_mode='Markdown')

# --- AVVIO DEL BOT ---

def main() -> None:
    TOKEN = "BOT_TOKEN"  # Sostituisci con il tuo token

    # Aumentati i timeout per prevenire errori ConnectTimeout
    application = (
        Application.builder()
        .token(TOKEN)
        .post_init(imposta_menu_comandi)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )

    # Comandi diretti
    application.add_handler(CommandHandler("nuovaseduta", inizia_programmazione))
    application.add_handler(CommandHandler("calendario", mostra_calendario))

    # Conversazione per la Creazione
    conv_creazione = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TITOLO: [MessageHandler(filters.TEXT & ~filters.COMMAND, ricevi_titolo)],
            DATA_ORA: [MessageHandler(filters.TEXT & ~filters.COMMAND, ricevi_data_ora)],
        },
        fallbacks=[CommandHandler('annulla', annulla)],
        per_chat=True,
        per_user=True,
    )
    
    # Conversazione per l'Eliminazione
    conv_eliminazione = ConversationHandler(
        entry_points=[CommandHandler('eliminaseduta', inizia_eliminazione)],
        states={
            SCELTA_ELIMINA: [MessageHandler(filters.TEXT & ~filters.COMMAND, esegui_eliminazione)],
        },
        fallbacks=[CommandHandler('annulla', annulla)],
        per_chat=True,
        per_user=True,
    )

    application.add_handler(conv_creazione)
    application.add_handler(conv_eliminazione)

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()