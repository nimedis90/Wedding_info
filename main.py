import streamlit as st
import gspread
from dotenv import load_dotenv
import json
import os
from google.oauth2 import service_account
import pandas as pd

# Load environment variables (e.g., from .env file, if needed for local execution)
load_dotenv()

# --- CONFIGURATION (Keep these settings as they were) ---
GOOGLE_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# !!! REPLACE '1sLMrawtIO0spDpGBrszfFFrye0z4xv8CaZt30eC_Fk8' with your actual Sheet ID
SHEET_ID = '1sLMrawtIO0spDpGBrszfFFrye0z4xv8CaZt30eC_Fk8'

# --- EVENT DETAILS CONFIGURATION (***MODIFIED***) ---
# This dictionary is now nested by language code (en, es, it)
EVENT_DETAILS = {
    'en': {
        'wedding': {
            'date': 'Friday, 3 July 2026',
            'location_name': 'Restaurante Palacio Mijares',
            'location_url': 'https://maps.app.goo.gl/XhkaRFnhLhhU2zEr5',
        },
        'pre_wedding': {
            'date': 'Thursday, 2 July 2026',
            'location_name': 'Restaurante Avril',
            'location_url': 'https://maps.app.goo.gl/CpGcNdvbZQnYmoD98',
        },
        'travel': {
            'bilbao_airport': "From **Bilbao Airport (BIO)**: It's about a 1.5 to 2-hour drive. We recommend renting a car or booking a pre-arranged taxi/private transfer, as public transport links can be slow and infrequent.",
            'santander_airport': "From **Santander Airport (SDR)**: It's a shorter drive, approximately 1 to 1.5 hours. A rental car is the most direct option, or check local shuttle services to the main city where taxi/bus connections may be available.",
        }
    },
    'es': {
        'wedding': {
            'date': 'Viernes, 3 de julio de 2026', # Translated
            'location_name': 'Restaurante Palacio Mijares', # Proper noun
            'location_url': 'https://maps.app.goo.gl/XhkaRFnhLhhU2zEr5',
        },
        'pre_wedding': {
            'date': 'Jueves, 2 de julio de 2026', # Translated
            'location_name': 'Restaurante Avril', # Proper noun
            'location_url': 'https://maps.app.goo.gl/CpGcNdvbZQnYmoD98',
        },
        'travel': {
            'bilbao_airport': "Desde el **Aeropuerto de Bilbao (BIO)**: Es un trayecto de 1,5 a 2 horas. Recomendamos alquilar un coche o reservar un taxi/transfer privado, ya que el transporte público puede ser lento y poco frecuente.", # Translated
            'santander_airport': "Desde el **Aeropuerto de Santander (SDR)**: Es un trayecto más corto, de 1 a 1,5 horas. Un coche de alquiler es la opción más directa, o consulta los servicios de shuttle locales a la ciudad.", # Translated
        }
    },
    'it': {
        'wedding': {
            'date': 'Venerdì 3 luglio 2026', # Translated
            'location_name': 'Restaurante Palacio Mijares', # Proper noun
            'location_url': 'https://maps.app.goo.gl/XhkaRFnhLhhU2zEr5',
        },
        'pre_wedding': {
            'date': 'Giovedì 2 luglio 2026', # Translated
            'location_name': 'Restaurante Avril', # Proper noun
            'location_url': 'https://maps.app.goo.gl/CpGcNdvbZQnYmoD98',
        },
        'travel': {
            'bilbao_airport': "Dall'**Aeroporto di Bilbao (BIO)**: Si tratta di un viaggio in auto da 1,5 a 2 ore. Consigliamo di noleggiare un'auto o prenotare un taxi/transfer privato, poiché i trasporti pubblici possono essere lenti e poco frequenti.", # Translated
            'santander_airport': "Dall'**Aeroporto di Santander (SDR)**: È un viaggio più breve, da 1 a 1,5 ore circa. Un'auto a noleggio è l'opzione più diretta, oppure controlla i servizi navetta locali per la città.", # Translated
        }
    }
}


# --- TRANSLATIONS DICTIONARY (***MODIFIED***) ---
TRANSLATIONS = {
    'en': {
        'flag': '🇬🇧 English',
        'title': "Will you be there? 👰🏻‍♀️🤵🏻",
        'description': "We're thrilled to invite you to celebrate our special day! Please confirm your attendance for the wedding and pre-wedding events below.",
        'label_name': "Your First Name:",
        'label_surname': "Your Last Name:",
        'label_participation_wedding': "Will you be participating at the  Wedding Ceremony & Reception?",
        'label_participation_pre_wedding': "Will you be participating in the Pre-Wedding Event?",
        'label_participation_sleep_help': "Do you need assistance finding Accommodation?",
        'option_yes': 'Yes',
        'option_no': 'No',
        'sleep_option_no': "No, I have or will find a place",
        'sleep_option_yes_both': "Yes, I need help finding a place for Thursday and Friday",
        'sleep_option_yes_thursday': "Yes, I need help finding a place for Thursday only",
        'sleep_option_yes_friday': "Yes, I need help finding a place for Friday only",
        'button_submit': "Submit RSVP 🎉",
        'success_message': "Response Submitted Successfully! We can't wait to see you! ✅",
        'error_message': "Oops! Please enter both your First Name and Last Name before submitting.",
        'section_details': "Your Confirmed Details",
        'output_name': "Guest Name:",
        'output_participation': "Attendance Status",
        'output_attending': "You will be celebrating with us! See you soon!",
        'output_not_attending': "You will not be attending the wedding. We'll miss you!",
        'details_header': "Event Details & Travel Info 🗺️",
        'wedding_title': "Wedding 💍",
        'pre_wedding_title': "Pre-Wedding 🥂",
        'when': "When:",
        'where': "Where:",
        'travel_title': "Travel",
        # ***NEW*** Sidebar Expander Labels
        'expander_wedding': "Wedding Details",
        'expander_pre_wedding': "Pre-Wedding Details",
        'expander_travel': "Airport Directions",
    },
    'es': {
        'flag': '🇪🇸 Español',
        'title': "¿Vas a venir? 👰🏻‍♀️🤵🏻",
        'description': "¡Estamos encantados de invitarte a celebrar nuestro día especial! Por favor, confirma tu asistencia a la boda y a los eventos previos.",
        'label_name': "Introduce tu Nombre:",
        'label_surname': "Introduce tu Apellido:",
        'label_participation_wedding': "¿Asistirás a la Ceremonia y Recepción de la Boda?",
        'label_participation_pre_wedding': "¿Asistirás al Evento de Pre-Boda?",
        'label_participation_sleep_help': "¿Necesitas ayuda para encontrar Alojamiento?",
        'option_yes': 'Sí',
        'option_no': 'No',
        'sleep_option_no': "No, tengo o encontraré un lugar",
        'sleep_option_yes_both': "Sí, necesito ayuda para encontrar un lugar para el jueves y el viernes",
        'sleep_option_yes_thursday': "Sí, necesito ayuda para encontrar un lugar solo para el jueves",
        'sleep_option_yes_friday': "Sí, necesito ayuda para encontrar un lugar solo para el viernes",
        'button_submit': "Enviar RSVP 🎉",
        'success_message': "¡Respuesta enviada con éxito! ¡Estamos ansiosos por verte! ✅",
        'error_message': "¡Ups! Por favor, ingresa tu Nombre y Apellido antes de enviar.",
        'section_details': "Tus Detalles Confirmados",
        'output_name': "Nombre del Invitado:",
        'output_participation': "Estado de Asistencia",
        'output_attending': "¡Vas a celebrar con nosotros! ¡Nos vemos pronto!",
        'output_not_attending': "Tú no asistirás a la boda. ¡Te extrañaremos!",
        'details_header': "Detalles del Evento e Info de Viaje 🗺️",
        'wedding_title': "Boda 💍",
        'pre_wedding_title': "Pre-Boda 🥂",
        'when': "Cuándo:",
        'where': "Dónde:",
        'travel_title': "Viaje",
        # ***NEW*** Sidebar Expander Labels
        'expander_wedding': "Detalles de la Boda",
        'expander_pre_wedding': "Detalles de la Pre-Boda",
        'expander_travel': "Direcciones desde Aeropuertos",
    },
    'it': {
        'flag': '🇮🇹 Italiano',
        'title': "Ci sarai? 👰🏻‍♀️🤵🏻",
        'description': "Siamo entusiasti di invitarti a celebrare il nostro giorno speciale! Per favore, conferma la tua presenza al matrimonio e agli eventi pre-matrimonio qui sotto.",
        'label_name': "Inserisci il tuo Nome:",
        'label_surname': "Inserisci il tuo Cognome:",
        'label_participation_wedding': "Parteciperai alla Cerimonia e Ricevimento del Matrimonio?",
        'label_participation_pre_wedding': "Parteciperai all'Evento Pre-Matrimonio?",
        'label_participation_sleep_help': "Hai bisogno di aiuto per trovare un Alloggio?",
        'option_yes': 'Sì',
        'option_no': 'No',
        'sleep_option_no': "No, ho o troverò un posto",
        'sleep_option_yes_both': "Sì, ho bisogno di aiuto per trovare un posto per giovedì e venerdì",
        'sleep_option_yes_thursday': "Sì, ho bisogno di aiuto per trovare un posto solo per giovedì",
        'sleep_option_yes_friday': "Sì, ho bisogno di aiuto per trovare un posto solo per venerdì",
        'button_submit': "Invia RSVP 🎉",
        'success_message': "Risposta inviata con successo! Non vediamo l'ora di vederti! ✅",
        'error_message': "Ops! Per favore, inserisci sia il tuo Nome che il tuo Cognome prima di inviare.",
        'section_details': "I Tuoi Dettagli Confermati",
        'output_name': "Nome Ospite:",
        'output_participation': "Stato di Partecipazione",
        'output_attending': "Sarai presente per festeggiare con noi! A presto!",
        'output_not_attending': "Non sarai presente al matrimonio. Ci mancherai!",
        'details_header': "Dettagli Evento e Informazioni di Viaggio 🗺️",
        'wedding_title': "Matrimonio 💍",
        'pre_wedding_title': "Pre-Matrimonio 🥂",
        'when': "Quando:",
        'where': "Dove:",
        'travel_title': "Viaggio",
        # ***NEW*** Sidebar Expander Labels
        'expander_wedding': "Dettagli Matrimonio",
        'expander_pre_wedding': "Dettagli Pre-Matrimonio",
        'expander_travel': "Indicazioni Aeroporti",
    }
}

# Map flag display names back to language codes
LANG_OPTIONS = {data['flag']: code for code, data in TRANSLATIONS.items()}
DEFAULT_LANG_CODE = 'en'


# --- GOOGLE SHEETS CONNECTION FUNCTIONS (Unchanged) ---

def get_gspread_client():
    """
    Initializes and caches the Google Sheets client.
    """
    try:
        # Assumes service account JSON is loaded into environment variable
        service_account_info = json.loads(os.getenv('coach-survey-serv-account'))
        creds = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=GOOGLE_SCOPES
        )
        return gspread.authorize(creds)
    except Exception as e:
        # Use st.warning for non-critical errors in the UI
        st.warning(f"Google Sheets connection failed. Please ensure the 'coach-survey-serv-account' environment variable is correctly set: {e}")
        return None

def save_log_to_gsheet(row_to_append):
    """Appends a single row to the designated Google Sheet."""
    client = get_gspread_client()
    if client:
        try:
            worksheet = client.open_by_key(SHEET_ID).sheet1
            worksheet.append_row(row_to_append)
            return True
        except Exception as e:
            st.error(f"Error saving to Google Sheet: {e}")
            return False
    return False

# --- NEW FUNCTION: EVENT DETAILS DISPLAY (***MODIFIED***) ---
def display_event_details_sidebar(T):
    """
    Displays the wedding and pre-wedding details, and travel info, with specific styling for the sidebar.
    Now pulls text from the correct language.
    """
    
    # ***NEW***: Get the current language code from session state
    lang = st.session_state.lang
    
    # ***NEW***: Select the correct dictionary from EVENT_DETAILS
    details = EVENT_DETAILS[lang]
    
    # Custom CSS for the details box in the sidebar (Unchanged)
    st.markdown(
        """
        <style>
        .details-box {
            background-color: #f7f7f7; /* Light gray background */
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #C70039; /* Red accent bar */
            margin-top: 15px;
            font-size: 0.9em;
        }
        .details-box h4 {
            color: #C70039;
            margin-top: 0;
            margin-bottom: 5px;
            font-size: 1.1em;
        }
        .details-box p {
            margin: 2px 0;
        }
        .travel-info {
            margin-top: 10px;
            font-style: italic;
            font-size: 0.85em;
        }
        </style>
        """, unsafe_allow_html=True
    )
    
    st.markdown(f"**{T['details_header']}**")
    
    # WEDDING DETAILS (***MODIFIED***)
    st.markdown(f"<h4>{T['wedding_title']}</h4>", unsafe_allow_html=True)
    # ***MODIFIED***: Use translated expander label
    with st.expander(T['expander_wedding']):
        # ***MODIFIED***: Use 'details' dictionary
        st.markdown(f"<p><strong>{T['when']}</strong> {details['wedding']['date']}</p>", unsafe_allow_html=True)
        # ***MODIFIED***: Use 'details' dictionary
        st.markdown(f"<p><strong>{T['where']}</strong> <a href='{details['wedding']['location_url']}' target='_blank'>{details['wedding']['location_name']}</a></p>", unsafe_allow_html=True)
        # ***FIXED***: Removed stray </div> tag
    
    # PRE-WEDDING DETAILS (***MODIFIED***)
    st.markdown("---")
    st.markdown(f"<h4>{T['pre_wedding_title']}</h4>", unsafe_allow_html=True)
    # ***MODIFIED***: Use translated expander label
    with st.expander(T['expander_pre_wedding']):
        # ***MODIFIED***: Use 'details' dictionary
        st.markdown(f"<p><strong>{T['when']}</strong> {details['pre_wedding']['date']}</p>", unsafe_allow_html=True)
        # ***MODIFIED***: Use 'details' dictionary
        st.markdown(f"<p><strong>{T['where']}</strong> <a href='{details['pre_wedding']['location_url']}' target='_blank'>{details['pre_wedding']['location_name']}</a></p>", unsafe_allow_html=True)
        # ***FIXED***: Removed stray </div> tag

    # TRAVEL DETAILS (***MODIFIED***)
    st.markdown("---")
    st.markdown(f"**{T['travel_title']}**")
    # ***MODIFIED***: Use translated expander label
    with st.expander(T['expander_travel']):
        # ***MODIFIED***: Use 'details' dictionary
        st.markdown(details['travel']['bilbao_airport'])
        st.markdown(details['travel']['santander_airport'])


# --- NEW FUNCTION: THANK YOU PAGE (Unchanged) ---
def display_thank_you_page(T):
    """
    Displays the thank you page using data stored in session state.
    """
    # Use data stored in session state from the successful submission
    name = st.session_state.rsvp_name
    surname = st.session_state.rsvp_surname
    participation_wedding_key = st.session_state.rsvp_wedding_key
    participation_wedding_display = st.session_state.rsvp_wedding_display
    participation_pre_wedding_display = st.session_state.rsvp_pre_wedding_display
    sleep_help_display = st.session_state.rsvp_sleep_help_display

    st.balloons()
    
    # Use a large, celebratory title
    st.markdown(f"# {T['success_message']}")
    
    # Format the output message
    full_name = f"{name} {surname}"
    
    # Determine overall participation status message (based on wedding attendance)
    if participation_wedding_key == 'Yes':
        attendance_status = T['output_attending']
        status_emoji = "💖"
    else:
        attendance_status = T['output_not_attending']
        status_emoji = "😢"
        
    response_message = f"""
    <div style="padding: 20px; border-radius: 15px; border: 3px solid #FFC300; background-color: #FFF8E1; text-align: center;">
    
    ## {T['section_details']} 🎉
    
    <p style="font-size: 1.2em; margin-bottom: 20px;">
    {T['output_name']} {full_name}
    </p>

    <div style="text-align: left; background-color: white; padding: 15px; border-radius: 10px;">
        <p><strong>{T['label_participation_wedding']}</strong>: {participation_wedding_display}</p>
        <p><strong>{T['label_participation_pre_wedding']}</strong>: {participation_pre_wedding_display}</p>
        <p><strong>{T['label_participation_sleep_help']}</strong>: {sleep_help_display}</p>
    </div>

    <hr style="margin-top: 20px; margin-bottom: 20px;">

    <h3 style="color: #C70039;">{T['output_participation']}</h3> 
    <p style="font-size: 1.5em; font-weight: bold;">{attendance_status} {status_emoji}</p>
    </div>
    """
    
    # Display the result using st.markdown with HTML for custom styling
    st.markdown(response_message, unsafe_allow_html=True)
    
    # Add a simple button to reset if needed (for testing/multi-submission)
    if st.button("Submit another RSVP (Admin use)", type='secondary'):
        st.session_state.submitted = False
        st.rerun() # Reload the app to show the form again


# --- STREAMLIT MAIN APP (Unchanged) ---

def main():
    """
    The main function for the Streamlit application.
    """
    # 1. INITIALIZE SESSION STATE
    if 'lang' not in st.session_state:
        st.session_state.lang = DEFAULT_LANG_CODE
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False # New state variable to control the view
        
    # 2. RENDER LANGUAGE SELECTOR AND UPDATE STATE
    with st.sidebar:
        st.header("🌐 Language | Idioma | Lingua")
        
        # Get the index of the language currently in state
        current_lang_index = list(LANG_OPTIONS.values()).index(st.session_state.lang)
        
        # Render the radio. Its value will be what the user just clicked (or default).
        lang_display = st.radio(
            "Choose your preference:",
            list(LANG_OPTIONS.keys()),
            index=current_lang_index,
            horizontal=True,
            key='lang_selector', # Give it a key
            label_visibility='collapsed' 
        )
        
        # **CRITICAL FIX**: Update the session state *immediately*
        # based on the radio's current return value.
        st.session_state.lang = LANG_OPTIONS[lang_display]
        
    # 3. GET TRANSLATIONS
    # Now that st.session_state.lang is updated for *this* run,
    # we fetch the correct translation dictionary.
    T = TRANSLATIONS[st.session_state.lang]

    # 4. RENDER THE REST OF THE SIDEBAR
    # We can "re-open" the sidebar to add more content.
    with st.sidebar:
        st.markdown("---")
        st.image("A&N.jpg", caption="Your Wedding Photo") # Caption will be default
        
        st.markdown("---")
        # This function now receives the *correct* T
        display_event_details_sidebar(T) 
        
    # --- UI LOGIC: SHOW FORM OR THANK YOU PAGE ---
    
    if st.session_state.submitted:
        # If submitted is True, only show the thank you page (using correct T)
        display_thank_you_page(T)
        return # Stop execution of main to prevent form rendering

    # --- UI RENDERING (Form) ---
    
    # Use a customized title for better styling (using correct T)
    st.markdown(f"# {T['title']}")
    st.info(T['description']) 

    st.markdown("---")

    # Use a Streamlit form for better organization and handling of input values
    with st.form(key='rsvp_form'):
        
        # Name and Surname
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(T['label_name'])
        with col2:
            surname = st.text_input(T['label_surname'])

        st.markdown("---")
        st.subheader("📝 Your Attendance")

        # Map options
        participation_options = {
            T['option_yes']: 'Yes',
            T['option_no']: 'No'
        }
        
        # Wedding Participation
        participation_wedding_display = st.radio(
            T['label_participation_wedding'],
            list(participation_options.keys()),
            key='radio_wedding',
            horizontal=True 
        )
        participation_wedding_key = participation_options[participation_wedding_display]

        # Pre-Wedding Participation (in an expander)
        with st.expander("Optional Events"): # This is separate from the event details in the sidebar
            participation_pre_wedding_display = st.radio(
                T['label_participation_pre_wedding'],
                list(participation_options.keys()),
                key='radio_pre_wedding',
                horizontal=True
            )
            participation_pre_wedding_key = participation_options[participation_pre_wedding_display] # Get key for sheet save

        st.markdown("---")
        st.subheader("🛌 Accommodation")

        # Sleep Help Question
        sleep_options_map = {
            T['sleep_option_no']: 'No',
            T['sleep_option_yes_both']: 'Yes - Thu & Fri',
            T['sleep_option_yes_thursday']: 'Yes - Thu only',
            T['sleep_option_yes_friday']: 'Yes - Fri only',
        }
        
        sleep_help_display = st.radio(
            T['label_participation_sleep_help'],
            list(sleep_options_map.keys()),
            key='radio_sleep_help'
        )
        sleep_help_key = sleep_options_map[sleep_help_display] # Get key for sheet save


        # Submission Button inside the form
        st.markdown("---")
        submitted = st.form_submit_button(T['button_submit'], use_container_width=True, type='primary')


# --- Submission Processing (Outside the Form) (Unchanged) ---
    if submitted:
        # Check if both name and surname have been entered
        if name and surname:
            
            # Data to save to Google Sheets (always send the key, not the display string)
            data_to_save = [
                name, 
                surname, 
                participation_wedding_key, 
                participation_pre_wedding_key, 
                sleep_help_key
            ]
            
            # Save data to Google Sheets
            if save_log_to_gsheet(data_to_save):
                
                # --- Success: Store data in session state and flip the view flag ---
                st.session_state.rsvp_name = name
                st.session_state.rsvp_surname = surname
                st.session_state.rsvp_wedding_key = participation_wedding_key
                st.session_state.rsvp_wedding_display = participation_wedding_display
                st.session_state.rsvp_pre_wedding_display = participation_pre_wedding_display
                st.session_state.rsvp_sleep_help_display = sleep_help_display
                
                st.session_state.submitted = True
                
                # Rerun the script to display the thank you page
                st.rerun() 
                
            else:
                # Error message if sheets save failed
                st.error("Submission failed due to a problem saving the data. Please check the sheet connection or try again.")
        else:
            # Error message if fields are empty
            st.error(T['error_message'])

if __name__ == '__main__':
    # Set a custom page config for an elegant, centered look
    st.set_page_config(
        page_title="Wedding RSVP", 
        page_icon="💍", 
        layout="centered",
        initial_sidebar_state="expanded"
    )
    # Optional: Apply a simple custom theme for a softer look
    st.markdown(
        """
        <style>
        /* General Streamlit container padding */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        /* Style for the main title */
        h1 {
            color: #C70039; /* A romantic color */
            text-align: center;
        }
        /* Primary button color (can be configured in .streamlit/config.toml too) */
        .stButton>button {
            color: white;
            background-color: #FFC300; /* A gold/festive color */
        }
        </style>
        """, 
        unsafe_allow_html=True
    )
    main()