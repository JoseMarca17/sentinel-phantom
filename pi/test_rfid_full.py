import asyncio
from modules.rfid.rfid_module import RFIDModule
from core.event_bus import bus

# Función para ver qué sale al "Dashboard" (Bus de eventos)
def monitor_bus(event):
    topic = event.get("topic")
    payload = event.get("payload")
    if topic == "card_detected":
        print(f"\n[BUS] Tarjeta: {payload['uid']} | Fuente: {payload['source']}")
        if payload['threats']:
            print(f"⚠️ AMENAZAS: {payload['threats']}")
        else:
            print("✅ Tarjeta limpia y autorizada.")

async def main():
    print("--- INICIANDO TEST DE PRODUCCIÓN RFID ---")
    bus.subscribe("*", monitor_bus)
    
    module = RFIDModule()
    await module._setup()
    
    # Añadimos un UID a la whitelist para la prueba
    # module.defense.add_to_whitelist("TU_UID_AQUI") 

    try:
        # Esto ejecutará el bucle del módulo
        await module._run()
    except KeyboardInterrupt:
        await module._teardown()

if __name__ == "__main__":
    asyncio.run(main())
