from dotenv import load_dotenv


load_dotenv()


def es_pregunta_valida(pregunta: str, client) -> bool:
    """Verifica si la pregunta está relacionada con el mercado energético"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=10,
        messages=[
            {"role": "system","content": "Eres un clasificador. Responde sólo SI o NO."},
            {"role": "user","content": f"¿Esta pregunta está relacionada con energía eléctrica, comercializadoras de luz, tarifas eléctricas, Don Vatio, facturas de electricidad o el sector energético español? Pregunta: '{pregunta}'"}
            ]
    )

    resultado = response.choices[0].message.content.strip().upper()
    return resultado == "SI"

def detectar_alucinacion(pregunta: str, respuesta: str, datos_reales: str, client) -> bool:
    """Detecta si la respuesta contiene información no respaldada por los datos"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=10,
        messages=[
            {"role": "system","content":"Eres un verificador de respuestas. Responde solo SÍ o NO."},
            {"role": "user","content": f"""¿Esta respuesta contiene información NO respaldada por los datos?
            
Data: {datos_reales}
Response: {respuesta}

Responde SÍ si la respuesta contiene hechos inventados que no están en los datos. Responde NO si la respuesta solo utiliza los datos proporcionados."""
        }]
    )
    
    resultado = response.choices[0].message.content.strip().upper()
    return resultado == "SI"