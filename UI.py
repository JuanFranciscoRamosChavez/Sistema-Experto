import streamlit as st
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch
from transformers import pipeline 

# --- 1. CONFIGURACIÓN Y CONSTANTES ---
DATA_FILE = 'processed_data.pkl'
EMBEDDINGS_FILE = 'disease_embeddings.pt'
MODEL_NAME = 'hiiamsid/sentence_similarity_spanish_es'
SUMMARIZER_MODEL = 'facebook/bart-large-cnn' # El especialista en español
NUM_RESULTADOS = 5

# --- 2. CARGA DE RECURSOS ---
@st.cache_resource
def load_model():
    return SentenceTransformer(MODEL_NAME)

@st.cache_data
def load_data():
    try:
        return pd.read_pickle(DATA_FILE)
    except FileNotFoundError:
        return None

@st.cache_resource
def load_embeddings():
    try:
        return torch.load(EMBEDDINGS_FILE)
    except FileNotFoundError:
        return None

@st.cache_resource
def load_summarizer():
    """Carga el pipeline de resumen una sola vez."""
    return pipeline("summarization", model=SUMMARIZER_MODEL)


# --- 3. LÓGICA DEL NEGOCIO ---
def find_similar_diseases_semantic(query, model, disease_embeddings, df):
    """Busca enfermedades similares usando búsqueda semántica."""
    if not query or disease_embeddings is None:
        return pd.DataFrame()
    query_embedding = model.encode(query, convert_to_tensor=True)
    hits = util.semantic_search(query_embedding, disease_embeddings, top_k=NUM_RESULTADOS)
    hits = hits[0] 
    result_indices = [hit['corpus_id'] for hit in hits]
    scores = [hit['score'] for hit in hits]
    results_df = df.iloc[result_indices].copy()
    results_df['similarity'] = scores
    return results_df

def get_section_text(disease_data, section_title):
    """Extrae el texto completo de una sección específica (ej. 'Descripción general')."""
    all_sections = disease_data.get('sintomas_causas', []) + disease_data.get('diagnostico_tratamiento', [])
    try:
        seccion = next(s for s in all_sections if s.get('titulo', '').lower() == section_title.lower())
        texto_completo = []
        for item in seccion.get('contenido', []):
            if item.get('tipo') == 'parrafo':
                texto_completo.append(item.get('contenido', ''))
            elif item.get('tipo') == 'lista':
                texto_completo.extend([f"- {li}" for li in item.get('items', [])])
        return "\n".join(texto_completo)
    except (StopIteration, TypeError):
        return None

def summarize_text(text, summarizer, max_length=150, min_length=40):
    """Genera un resumen del texto si es suficientemente largo."""
    if not text or len(text.split()) < min_length:
        return text # Devuelve el original si es muy corto
    summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return summary[0]['summary_text']


def setup_page():
    st.set_page_config(page_title="Asistente de Diagnóstico Semántico", layout="wide")
    st.title("Asistente de Diagnóstico Semántico ")

def display_results(results_df, summarizer):
    """Ahora esta función también necesita el 'summarizer' para funcionar.
     Muestra los resultados en la interfaz de Streamlit."""
    if results_df is None:
        st.info("El asistente está listo para analizar tus síntomas.")
        return
    if results_df.empty:
        st.warning("No se encontraron resultados para la búsqueda realizada.")
        return

    for _, row in results_df.iterrows():
        similarity_score = row['similarity'] * 100
        st.subheader(f"{row['nombre']} ({similarity_score:.2f}% de similitud)")
        with st.expander("Ver resúmenes y detalles"):
            # --- Integración del Resumen ---
            desc_text = get_section_text(row, "Descripción general")
            if desc_text:
                st.markdown("** Resumen General**")
                with st.spinner("Generando resumen..."):
                    summary = summarize_text(desc_text, summarizer)
                st.write(summary)
                st.markdown("---")

            # Información demográfica
            demografia = row.get('demografia', {})
            st.markdown(f"**Género más afectado:** {demografia.get('genero_mas_afectado', 'N/A')}")
            st.markdown(f"**Rango de edad:** {demografia.get('min_edad', 'N/A')} - {demografia.get('max_edad', 'N/A')} años")
            
            # Enlace
            url = row.get('url', '')
            if url:
                st.markdown(f"[Leer más en la fuente original]({url})")

def main():
    setup_page()
    
    # Cargar todos los recursos, incluido el nuevo resumidor
    model = load_model()
    df = load_data()
    disease_embeddings = load_embeddings()
    summarizer = load_summarizer() # Cargamos el modelo de resumen
    
    if df is None or disease_embeddings is None:
        st.error("Error: Faltan archivos de datos. Asegúrate de ejecutar `precompute_embeddings.py` primero.")
        return

    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'query_input' not in st.session_state:
        st.session_state.query_input = ""

    def trigger_search():
        st.session_state.results = find_similar_diseases_semantic(st.session_state.query_input, model, disease_embeddings, df)

    def clear_search():
        st.session_state.query_input = ""
        st.session_state.results = None

    st.subheader("1. Describe tus síntomas")
    st.text_area(
        "Escribe aquí de la forma más detallada posible.",
        key="query_input",
        height=100,
        label_visibility="collapsed"
    )
    
    col1, col2, _ = st.columns([1, 1, 4])
    with col1:
        st.button("Buscar Enfermedades Similares", on_click=trigger_search, type="primary")
    with col2:
        st.button("Nueva Consulta", on_click=clear_search)
    
    st.markdown("---")
    st.subheader("2. Resultados del Análisis")
    
    # Pasamos el 'summarizer' a la función que muestra los resultados
    display_results(st.session_state.results, summarizer)

    st.markdown("---")

if __name__ == "__main__":
    main()