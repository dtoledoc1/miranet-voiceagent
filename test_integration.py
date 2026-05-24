import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path("D:/miranet-voiceagent")
sys.path.append(str(PROJECT_ROOT))

from backend.agents.responder import ResponderAgent
from backend.db.database import db

async def test():
    print("Connecting to DB...")
    await db.connect()
    
    agent = ResponderAgent()
    print("\n--- Test 1: Lento (Medium) ---")
    text1 = "El internet está super lento"
    res1, lat1 = await agent.generate_response(text=text1, history=[])
    print(f"User: {text1}")
    print(f"Response: {res1} (in {lat1}ms)")
    
    print("\n--- Test 2: Caída masiva (Critical) ---")
    text2 = "Se cayó toda la zona mis vecinos tampoco tienen"
    res2, lat2 = await agent.generate_response(text=text2, history=[])
    print(f"User: {text2}")
    print(f"Response: {res2} (in {lat2}ms)")
    
    print("\n--- Test 3: Consulta general (Low) ---")
    text3 = "Quería hacer una consulta sobre mi recibo"
    res3, lat3 = await agent.generate_response(text=text3, history=[])
    print(f"User: {text3}")
    print(f"Response: {res3} (in {lat3}ms)")

    await agent.close()
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(test())
