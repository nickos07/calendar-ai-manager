from auth_google import autenticar_google

def limpiar_calendario():
    calendar_svc, _ = autenticar_google()
    if not calendar_svc:
        return

    print("Conectando con Google Calendar...")
    
    # Buscamos eventos desde el 1 de septiembre de 2026 (inicio de curso)
    fecha_inicio = "2026-09-01T00:00:00Z"
    
    resultados = calendar_svc.events().list(
        calendarId='primary', 
        timeMin=fecha_inicio, 
        maxResults=2500, 
        singleEvents=True, 
        orderBy='startTime'
    ).execute()
    
    eventos = resultados.get('items', [])
    
    # Agrupamos los eventos por su hora de inicio
    eventos_por_hora = {}
    for evento in eventos:
        # Solo agrupamos eventos que tengan hora exacta (ignoramos los de "todo el día")
        if 'dateTime' in evento['start']:
            inicio = evento['start']['dateTime']
            if inicio not in eventos_por_hora:
                eventos_por_hora[inicio] = []
            eventos_por_hora[inicio].append(evento)

    borrados = 0
    print("\nBuscando coincidencias de horario...\n")
    
    for inicio, lista_eventos in eventos_por_hora.items():
        if len(lista_eventos) > 1:
            print(f"⚠️ Atención: Tienes {len(lista_eventos)} eventos a la vez el {inicio}:")
            
            for i, evento in enumerate(lista_eventos):
                print(f"   [{i + 1}] {evento.get('summary', 'Sin título')}")
            print(f"   [0] No borrar ninguno (Saltar)")
            
            seleccion = input("👉 ¿Qué evento quieres BORRAR? (Introduce el número): ")
            
            try:
                opcion = int(seleccion)
                if 1 <= opcion <= len(lista_eventos):
                    evento_a_borrar = lista_eventos[opcion - 1]
                    calendar_svc.events().delete(
                        calendarId='primary', 
                        eventId=evento_a_borrar['id']
                    ).execute()
                    print(f"🗑️ Borrado: {evento_a_borrar.get('summary')}\n")
                    borrados += 1
                else:
                    print("⏭️ Saltando...\n")
            except ValueError:
                print("⏭️ Entrada no válida. Saltando...\n")

    print(f"¡Limpieza completada! Se han eliminado {borrados} duplicados.")

if __name__ == '__main__':
    limpiar_calendario()