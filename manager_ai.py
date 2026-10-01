import os
import json
import base64
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError
from auth_google import autenticar_google
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# 1. DICCIONARIOS DE IDENTIFICACIÓN
ASIGNATURAS_MAP = {
    "C2.218.20605": "Estructuras de datos",
    "C2.218.13875": "Fundamentos de gestión empresarial",
    "C2.218.13877": "Teoría de Autómatas",
    "C2.218.13874": "Estructura de computadores",
    "C2.506.20197": "Heurística y Optimización"
}

# AÑADE AQUÍ LOS CORREOS DE TUS PROFESORES
PROFESORES_MAP = {
    "jiglesia@inf.uc3m.es": "Teoría de Autómatas",
    "asainz@emp.uc3m.es": "Fundamentos de gestión empresarial",
    "valcazar@inf.uc3m.es": "Heurística y Optimización"
}

def obtener_texto_mensaje(payload):
    cuerpo = ""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                cuerpo += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            elif part['mimeType'] == 'text/html' and not cuerpo:
                cuerpo += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            elif 'parts' in part: 
                cuerpo += obtener_texto_mensaje(part)
    elif 'body' in payload and 'data' in payload['body']:
        cuerpo = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    return cuerpo

def extraer_info_con_ia(remitente, asunto, cuerpo):
    prompt = f"""
    Eres un asistente de calendario universitario. Lee el siguiente correo.
    Remitente: {remitente}
    Asunto: {asunto}
    Cuerpo: {cuerpo}
    
    Tu única tarea es determinar si este correo notifica un cambio de horario, cancelación, o examen.
    
    INFORMACIÓN IMPORTANTE PARA IDENTIFICAR LA ASIGNATURA:
    1. Si el profesor no menciona la asignatura, usa este diccionario de remitentes para saber cuál es:
    {json.dumps(PROFESORES_MAP, ensure_ascii=False)}
    2. Si menciona un código en vez del nombre, usa este diccionario:
    {json.dumps(ASIGNATURAS_MAP, ensure_ascii=False)}
    
    Devuelve ÚNICAMENTE un objeto JSON válido. Si el correo no tiene cambios de horario, devuelve la palabra null sin comillas.
    
    Estructura:
    {{
        "tipo": "cambio_clase" | "cancelacion" | "examen",
        "asignatura": "Nombre real de la asignatura (traducido del remitente o código)",
        "fecha_original": "YYYY-MM-DDTHH:MM:SS+02:00" (o null),
        "nueva_fecha": "YYYY-MM-DDTHH:MM:SS+02:00" (o null),
        "comentarios": "Breve resumen"
    }}
    Asegúrate de que la fecha incluya la zona horaria de España.
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        texto_respuesta = response.text.strip()
        
        if texto_respuesta.startswith("```json"):
            texto_respuesta = texto_respuesta[7:-3].strip()
        if texto_respuesta.lower() == "null":
            return None
            
        return json.loads(texto_respuesta)
    except Exception as e:
        print(f"Error con la IA: {e}")
        return None

def evento_ya_existe(calendar_svc, titulo, fecha_inicio_iso):
    try:
        inicio = datetime.fromisoformat(fecha_inicio_iso)
        min_time = (inicio - timedelta(minutes=1)).isoformat()
        max_time = (inicio + timedelta(minutes=1)).isoformat()
        
        resultados = calendar_svc.events().list(
            calendarId='primary', 
            timeMin=min_time, 
            timeMax=max_time, 
            q=titulo 
        ).execute()
        
        return len(resultados.get('items', [])) > 0
    except Exception as e:
        print(f"Error al verificar duplicados: {e}")
        return False

def actualizar_calendario(calendar_svc, info):
    print(f"   -> Procesando evento para: {info['asignatura']}")
    
    if info['tipo'] == 'examen' and info['nueva_fecha']:
        titulo = f"🔴 [EXAMEN] {info['asignatura']}"
        if evento_ya_existe(calendar_svc, info['asignatura'], info['nueva_fecha']):
            print("   ⏩ El examen ya está en tu calendario. Omitiendo.")
            return

        inicio = datetime.fromisoformat(info['nueva_fecha'])
        fin = inicio + timedelta(hours=2)
        evento = {
            'summary': titulo,
            'description': info.get('comentarios', ''),
            'colorId': '11',
            'start': {'dateTime': inicio.isoformat(), 'timeZone': 'Europe/Madrid'},
            'end': {'dateTime': fin.isoformat(), 'timeZone': 'Europe/Madrid'},
        }
        calendar_svc.events().insert(calendarId='primary', body=evento).execute()
        print(f"   ✅ Examen programado en tu calendario.")

    elif info['tipo'] == 'cambio_clase' and info['nueva_fecha']:
        titulo = f"🔄 [CAMBIO] {info['asignatura']}"
        if evento_ya_existe(calendar_svc, info['asignatura'], info['nueva_fecha']):
            print("   ⏩ Este cambio de clase ya está en tu calendario. Omitiendo.")
            return

        inicio = datetime.fromisoformat(info['nueva_fecha'])
        fin = inicio + timedelta(hours=1, minutes=30)
        evento = {
            'summary': titulo,
            'description': info.get('comentarios', ''),
            'colorId': '5',
            'start': {'dateTime': inicio.isoformat(), 'timeZone': 'Europe/Madrid'},
            'end': {'dateTime': fin.isoformat(), 'timeZone': 'Europe/Madrid'},
        }
        calendar_svc.events().insert(calendarId='primary', body=evento).execute()
        print(f"   ✅ Cambio de clase añadido a tu calendario.")
        
    elif info['tipo'] == 'cancelacion':
        print(f"   ⚠️ Clase cancelada. Revisa tu calendario para confirmar la fecha original: {info.get('fecha_original')}")

def buscar_y_procesar_correos():
    calendar_svc, gmail_svc = autenticar_google()
    if not gmail_svc or not calendar_svc: return

    print("\nBuscando correos recientes...")
    try:
        resultados = gmail_svc.users().messages().list(userId='me', maxResults=5).execute()
        mensajes = resultados.get('messages', [])
        
        for msg in mensajes:
            msg_id = msg['id']
            mensaje_completo = gmail_svc.users().messages().get(userId='me', id=msg_id, format='full').execute()
            
            headers = mensaje_completo['payload']['headers']
            asunto = next((h['value'] for h in headers if h['name'].lower() == 'subject'), "Sin asunto")
            # Extraemos el remitente para pasárselo a la IA
            remitente = next((h['value'] for h in headers if h['name'].lower() == 'from'), "Desconocido")
            
            cuerpo = obtener_texto_mensaje(mensaje_completo['payload'])
            
            print(f"\nAnalizando correo de: {remitente}")
            info_horario = extraer_info_con_ia(remitente, asunto, cuerpo)
            
            if info_horario:
                actualizar_calendario(calendar_svc, info_horario)
            else:
                print("   - Ignorado (sin cambios de horario).")

    except HttpError as error:
        print(f"Error con la API: {error}")

if __name__ == '__main__':
    buscar_y_procesar_correos()