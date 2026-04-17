from dotenv import load_dotenv
from indexer import buscar_en_docs
import base64
import os


load_dotenv()

# Langfuse PRIMERO

from langfuse import Langfuse
from langfuse.openai import openai as langfuse_openai

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_BASE_URL")
)

# DESPUÉS OpenAI
from guardrails import es_pregunta_valida, detectar_alucinacion
# Usar el cliente de OpenAI de Langfuse en vez del normal
client = langfuse_openai.OpenAI()

SYSTEM_PROMPT = """Eres un asistente experto de Don Vatio, empresa especializada en energía.
Respondes preguntas sobre electricidad, comercializadoras y contratos energéticos.

INSTRUCCIONES
-Responde UNICAMENTE basándote en la información proporcionada.
-Si no tienes información suficiente, dilo claramente.
-Sé conciso y directo.
-Responde en el mismo idioma que el usuario.
"""

def responder(pregunta: str, historial: list) -> tuple[str, list]:

    #0. Guardrail input

    if not es_pregunta_valida(pregunta, client):
        respuesta = "Lo siento, solo puedo responder preguntas sobre Don Vatio y el mercado energético."
        historial.append({"role": "user", "content": pregunta})
        historial.append({"role": "assistant", "content": respuesta})
        return respuesta, historial

    #1. Buscar chunks relevantes
    chunks = buscar_en_docs(pregunta)

    if not chunks:
        return "No encontré información relevante en los documentos", historial
    
    #2. Construir contexto
    contexto = "\n\n".join([c["texto"] for c in chunks])

    # 3. Añadir pregunta al historial
    historial.append({
        "role": "user",
        "content": f"Contexto:\n{contexto}\n\nPregunta: {pregunta}"
    })
    
    # 4. Llamar al LLM
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + historial
    )
    
    respuesta = response.choices[0].message.content

    # 5. Detectar alucinación
    if detectar_alucinacion(pregunta, respuesta, contexto, client):
        respuesta= "No tengo información suficiente en los documenbtos para responder con seguridad." 

    historial.append({"role": "assistant", "content": respuesta})
    
    return respuesta, historial


print(f"LANGFUSE_PUBLIC_KEY: {os.getenv('LANGFUSE_PUBLIC_KEY')[:10]}...")
print(f"OTEL_ENDPOINT: {os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT')}")

if __name__ == "__main__":
    historial = []
    print("🤖 Don Vatio FAQ Bot. Escribe 'salir' para terminar.\n")
    
    try:
        while True:
            pregunta = input("Tú: ")
            if pregunta.lower() == "salir":
                break
            respuesta, historial = responder(pregunta, historial)
            print(f"\nBot: {respuesta}\n")
    finally:
        # Forzar envío de traces a Langfuse
        import time
        time.sleep(2)  # dar tiempo a que se envíen los datos