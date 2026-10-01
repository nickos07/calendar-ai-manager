import os
import time
from datetime import datetime
from icalendar import Calendar
from auth_google import autenticar_google # Importamos la función que creaste antes

def procesar_evento_ics(componente):
    """Extrae la info del evento del archivo .ics y le da el formato que pide Google Calendar."""
    summary = componente.get('summary', 'Clase sin nombre')
    description = componente.get('description', '')
    location = componente.get('location', '')
    
    # Obtenemos las fechas del evento
    start = componente.get('dtstart').dt
    end = componente.get('dtend').dt
    
    # Formatear el diccionario para la API de Google
    evento_gcal = {
        'summary': str(summary),
        'location': str(location),
        'description': str(description),
        'start': {},
        'end': {}
    }
    
    # Diferenciar si es un evento de todo el día o un evento con horas específicas
    if isinstance(start, datetime):
        evento_gcal['start']['dateTime'] = start.isoformat()
        evento_gcal['end']['dateTime'] = end.isoformat()
        evento_gcal['start']['timeZone'] = 'Europe/Madrid'
        evento_gcal['end']['timeZone'] = 'Europe/Madrid'
    else:
        evento_gcal['start']['date'] = start.isoformat()
        evento_gcal['end']['date'] = end.isoformat()
        
    return evento_gcal

def importar_horario(ruta_ics):
    print("Autenticando con Google...")
    calendar_svc, _ = autenticar_google()
    
    if not calendar_svc:
        print("Error: No se pudo autenticar con Google.")
        return

    print(f"Leyendo el archivo '{ruta_ics}'...")
    try:
        with open(ruta_ics, 'rb') as f:
            cal = Calendar.from_ical(f.read())
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{ruta_ics}'. Revisa el nombre.")
        return

    print("Comenzando a subir eventos a Google Calendar...")
    contador = 0
    
    # Recorremos todos los elementos del archivo ICS
    for component in cal.walk():
        if component.name == "VEVENT": # VEVENT significa que es un evento
            evento_gcal = procesar_evento_ics(component)
            try:
                # Subimos el evento al calendario principal ('primary')
                calendar_svc.events().insert(calendarId='primary', body=evento_gcal).execute()
                print(f"✅ Añadido: {evento_gcal['summary']}")
                contador += 1
                time.sleep(1)
            except Exception as e:
                print(f"❌ Error al añadir '{evento_gcal['summary']}': {e}")
                
    print(f"\n¡Proceso completado! Se han importado {contador} clases/exámenes a tu calendario.")

if __name__ == '__main__':
    # Sustituye 'mi_horario.ics' por el nombre exacto de tu archivo de la universidad
    NOMBRE_ARCHIVO_ICS = 'mi_horario.ics' 
    importar_horario(NOMBRE_ARCHIVO_ICS)