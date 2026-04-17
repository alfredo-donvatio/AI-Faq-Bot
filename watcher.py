from watchdog.observers import Observer  #Monitoriza eventos y en torno a eso crea tareas específicas
from watchdog.events import FileSystemEventHandler
from indexer import indexar_documento
import time

class PDFHandler(FileSystemEventHandler):
    """Detecta nuevos PDFs y los indexa automáticamente"""

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".pdf"):
            print(f" Nuevo PDF detectado: {event.src_path}")
            indexar_documento(event.src_path)


if __name__ == "__main__":
    ruta_docs = "./docs"
    handler = PDFHandler()
    observer = Observer()
    observer.schedule(handler, ruta_docs, recursive=False)
    observer.start()

    print("Monitoreando carpeta docs/... (Ctrl+C para detener)")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()