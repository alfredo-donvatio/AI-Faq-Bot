import fitz #pymupdf - biblioteca para manipular, analizar, convertir y extraer datos de documentos PDF 
import chromadb
from sentence_transformers import SentenceTransformer #crea los embeddings
from pathlib import Path

modelo = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
cliente_chroma = chromadb.PersistentClient(path="./chroma_db") #PersistentClient()almacena datos en una carpeta local/servidor

def leer_pdf (ruta:str) -> str:
    """Extrae texto de un PDF"""
    doc = fitz.open(ruta)
    texto = ""
    for pagina in doc:
        texto += pagina.get_text()
    return texto

def hacer_chunks(texto: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """Divide el texto en chunks con overlap""" #overlap es la superposicion de trozos de chunks unos en otros para conservar el contexto
    chunks = []
    inicio = 0

    while inicio < len(texto):
        fin = inicio + chunk_size
        chunk = texto [inicio:fin]
        if chunk.strip():
            chunks.append(chunk)
        inicio = fin - overlap

    return chunks

import re

def limpiar_nombre(nombre: str) -> str: #ChromaDB solo acepta letras, números, puntos, guiones y guiones bajos. limpiar el nombre por si acaso.
    """Limpia el nombre para que sea válido en ChromaDB"""
    nombre = nombre.replace(" ", "_")
    nombre = re.sub(r'[^a-zA-Z0-9._-]', '', nombre)
    return nombre[:50]  # máximo 50 caracteres

def indexar_documento(ruta_pdf: str):
    nombre_archivo = limpiar_nombre(Path(ruta_pdf).stem)

    # Verificar si ya está indexado
    colecciones_existentes = [c.name for c in cliente_chroma.list_collections()]
    if nombre_archivo in colecciones_existentes:
        print(f"⏭️ Ya indexado: {nombre_archivo}")
        return
    
    print(f" Indexando: {ruta_pdf}")

    #1. Leer PDF
    texto = leer_pdf(ruta_pdf)

    #2. Hacer chunks
    chunks = hacer_chunks(texto)
    print(f" {len(chunks)} chunks generados")

    #3. Generar embeddings
    embeddings = modelo.encode(chunks).tolist()

    #4. Guardar en ChromaDB
    nombre_archivo = limpiar_nombre(Path (ruta_pdf).stem)
    coleccion = cliente_chroma.get_or_create_collection(nombre_archivo)

    ids =[f"{nombre_archivo}_chunk {i}" for i in range(len(chunks))]

    coleccion.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids
    )

    print(f" {nombre_archivo} indexado correctamente")

def buscar_en_docs(pregunta: str, n_results: int = 3) -> list:
    """Busca en todos los documentros indexados"""
    embedding_pregunta = modelo.encode(pregunta).tolist()

    colecciones = cliente_chroma.list_collections()
    todos_resultados = []

    for col_info in colecciones:
        coleccion = cliente_chroma.get_collection(col_info.name)
        resultados = coleccion.query(
            query_embeddings=[embedding_pregunta],
            n_results=min(n_results, coleccion.count())
        )

        for doc, distancia in zip(resultados["documents"][0], resultados["distances"][0]):
            todos_resultados.append({
                "documento": col_info.name,
                "texto": doc,
                "distancia": distancia
            })

    # Ordenar por relevancia
    todos_resultados.sort(key=lambda x: x["distancia"])
    return todos_resultados[:n_results]


if __name__ == "__main__":
    # Test de búsqueda
    resultados = buscar_en_docs("¿cómo elegir una comercializadora?")
    for r in resultados:
        print(f"\n📄 {r['documento']} (distancia: {r['distancia']:.3f})")
        print(f"{r['texto'][:200]}...")


if __name__ == "__main__":
    docs_path = Path("./docs")
    for pdf in docs_path.glob("*.pdf"):
        indexar_documento(str(pdf))


# Verificar indexación
colecciones = cliente_chroma.list_collections()
print(f"\n📊 Colecciones en ChromaDB: {len(colecciones)}")
for col in colecciones:
    print(f"  - {col.name}")