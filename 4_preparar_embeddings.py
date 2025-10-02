import json
import pandas as pd
from sentence_transformers import SentenceTransformer
import torch # Usaremos PyTorch para guardar los embeddings

"""
Script para pre-calcular y guardar los embeddings de las enfermedades
usando un modelo de SentenceTransformer optimizado para español.
Estos embeddings se usarán luego para búsquedas semánticas rápidas.
Es importante ejecutar este script después de haber procesado y enriquecido
los datos con '3_procesar_y_enriquecer_datos.py' para asegurar que los datos
estén en el formato correcto.
"""

# --- CONSTANTES Y CONFIGURACIÓN ---
MODEL_NAME = 'hiiamsid/sentence_similarity_spanish_es'
INPUT_JSON = '3_datos_completos_procesados.json'
OUTPUT_DATA_FILE = 'processed_data.pkl' # Guardaremos los datos de las enfermedades
OUTPUT_EMBEDDINGS_FILE = 'disease_embeddings.pt' # Guardaremos los vectores en un archivo de PyTorch

def obtener_texto_sintomas(enfermedad):
    """
    Extrae y concatena el texto de la sección de síntomas de una enfermedad.
    Es importante que esta lógica sea consistente con la UI.
    """
    try:
        # Busca la sección de síntomas
        seccion_sintomas = next(
            s for s in enfermedad.get('sintomas_causas', []) 
            if s.get('titulo', '').lower() == 'síntomas'
        )
        
        # Concatena todo el contenido de la sección
        texto_completo = []
        for item in seccion_sintomas.get('contenido', []):
            if item.get('tipo') == 'parrafo':
                texto_completo.append(item.get('contenido', ''))
            elif item.get('tipo') == 'lista':
                texto_completo.extend([f"- {li}" for li in item.get('items', [])])
        return "\n".join(texto_completo)
    except (StopIteration, TypeError):
        # Si no hay sección de síntomas o hay algún error, devuelve un string vacío.
        return ""

def main():
    """
    Función principal para cargar los datos, generar los embeddings y guardarlos.
    """
    print("--- Iniciando pre-cálculo de embeddings ---")
    
    # 1. Cargar el modelo de SentenceTransformer
    print(f"Cargando el modelo '{MODEL_NAME}'... (Esto puede tardar unos minutos la primera vez)")
    model = SentenceTransformer(MODEL_NAME)
    print(" Modelo cargado.")

    # 2. Cargar y procesar los datos JSON
    print(f"Cargando datos desde '{INPUT_JSON}'...")
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    enfermedades = data.get('enfermedades', [])
    print(f" Se encontraron {len(enfermedades)} enfermedades.")
    
    # 3. Extraer el texto de los síntomas de cada enfermedad
    textos_sintomas = []
    enfermedades_validas = [] # Guardaremos solo las enfermedades que tengan texto de síntomas

    for enf in enfermedades:
        texto = obtener_texto_sintomas(enf)
        if texto: # Solo procesamos enfermedades con descripción de síntomas
            textos_sintomas.append(texto)
            enfermedades_validas.append(enf)
            
    print(f"Generando embeddings para {len(enfermedades_validas)} enfermedades con descripción de síntomas.")

    """
    4. Generar los embeddings para todos los textos
    Usamos convert_to_tensor=True para que el resultado sea un tensor de PyTorch,
    que es lo que la función de búsqueda semántica espera.
    """
    embeddings = model.encode(textos_sintomas, show_progress_bar=True, convert_to_tensor=True)

    """
    5. Guardar los resultados
    Guardamos los embeddings en el formato nativo de PyTorch, es muy eficiente.
    """
    torch.save(embeddings, OUTPUT_EMBEDDINGS_FILE)
    print(f"✓ Embeddings guardados en '{OUTPUT_EMBEDDINGS_FILE}'")

    # Guardamos los datos de las enfermedades (sin los embeddings) en un archivo pickle
    df = pd.DataFrame(enfermedades_validas)
    df.to_pickle(OUTPUT_DATA_FILE)
    print(f"✓ Datos de enfermedades guardados en '{OUTPUT_DATA_FILE}'")
    
    print("\n--- ¡Proceso completado con éxito! ---")

if __name__ == "__main__":
    main()