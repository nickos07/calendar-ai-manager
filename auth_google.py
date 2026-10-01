import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Definimos los permisos que necesita nuestro programa.
# Si cambias estos scopes, deberás borrar el archivo token.json y volver a ejecutar el código.
SCOPES = [
    'https://www.googleapis.com/auth/calendar',      # Permite leer y crear eventos en Calendar
    'https://www.googleapis.com/auth/gmail.readonly' # Permite leer los correos (sin poder borrarlos ni enviar)
]

def autenticar_google():
    """
    Gestiona la autenticación de OAuth2.
    Devuelve los objetos 'service' para interactuar con Gmail y Calendar.
    """
    creds = None
    
    # El archivo token.json almacena los tokens de acceso y actualización del usuario.
    # Se crea automáticamente la primera vez que completas la autorización.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    # Si no hay credenciales válidas disponibles, obligamos al usuario a iniciar sesión.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refrescando el token de acceso...")
            creds.refresh(Request())
        else:
            print("Iniciando flujo de autenticación en el navegador...")
            # Asegúrate de que el archivo descargado de Google Cloud se llame credentials.json
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            # Abre una ventana del navegador local en el puerto 0 (automático)
            creds = flow.run_local_server(port=0)
            
        # Guarda las credenciales para la próxima ejecución
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())
            print("Token guardado exitosamente en token.json")

    try:
        # Construimos los servicios de las APIs
        calendar_service = build('calendar', 'v3', credentials=creds)
        gmail_service = build('gmail', 'v1', credentials=creds)
        
        print("¡Autenticación completada! Servicios de Calendar y Gmail listos.")
        return calendar_service, gmail_service
        
    except Exception as e:
        print(f"Ocurrió un error al construir los servicios: {e}")
        return None, None

# Bloque de prueba para ejecutar este script directamente
if __name__ == '__main__':
    calendar_svc, gmail_svc = autenticar_google()
    
    # Pequeña prueba para confirmar que Calendar funciona
    if calendar_svc:
        print("\nObteniendo los próximos 3 eventos de tu calendario principal...")
        events_result = calendar_svc.events().list(calendarId='primary', maxResults=3, singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print("No se encontraron eventos.")
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(f"- {start}: {event['summary']}")