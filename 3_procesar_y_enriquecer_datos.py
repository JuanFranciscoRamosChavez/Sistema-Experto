import json
import re
import unicodedata
import spacy
from spacy.matcher import Matcher
from collections import defaultdict

"""
Procesamiento y enriquecimiento de datos de enfermedades:
- Extracción avanzada de síntomas estructurados.
- Análisis demográfico mejorado.
- Creación de un índice invertido desde categorías de síntomas hacia enfermedades.
- Unión de archivos JSON en uno solo.
"""

class ProcesadorEnfermedades:
    def __init__(self):
        """
        Inicializa el procesador con categorías de síntomas y configuraciones de NLP.
        Al no tener una gran referencia de síntomas, se opta por una categorización amplia y
        se mejora la extracción de síntomas y demografía para una cobertura total del texto.
        """
        self.categorias_sintomas = {
            "Dolor": ["acidez estomacal", "ardor al orinar", "disuria", "ardor de ojos", "dolor abdominal",
                     "dolor pelvico", "dolor al tener relaciones sexuales", "dispareunia",
                     "dolor articular", "dolor de cabeza", "cefalea", "migraña", "dolor de espalda",
                     "dolor de garganta", "odinofagia", "dolor de muelas", "dolor de oido", "otalgia",
                     "dolor en el costado", "dolor en el pecho", "opresion en el pecho",
                     "dolor muscular", "mialgia", "dolor oseo", "dolor ocular", "menstruacion dolorosa",
                     "dismenorrea", "rigidez de nuca"],
            "Fiebre": ["fiebre", "febricula"],
            "Mareo": ["alteraciones del equilibrio", "mareos", "vertigo", "lipotimia"],
            "Fatiga": ["apatia", "astenia", "cansancio", "fatiga", "somnolencia diurna excesiva",
                      "debilidad muscular", "debilidad", "lentitud de movimiento",
                      "bradicinesia", "malestar general"],
            "Nauseas": ["nauseas", "vomito", "reflujo gastroesofagico", "vomitos",
                       "vomitos con sangre", "hematemesis"],
            "Tos": ["expectoracion", "flema", "tos", "tos seca", "tos productiva"],
            "Diarrea": ["diarrea"],
            "Estrenimiento": ["estrenimiento"],
            "Erupcion": ["acne", "dermatitis", "erupciones cutaneas", "exantema", "urticaria", "petequias"],
            "Picazon": ["picazon", "prurito"],
            "Hinchazon": ["bultos", "masas", "distension abdominal", "hinchazon abdominal",
                         "edema", "ganglios linfaticos inflamados", "adenopatia", "hemorroides",
                         "hepatomegalia", "hinchazon en manos", "hinchazon en pies",
                         "inflamacion", "gingivitis", "encias inflamadas",
                         "inflamacion de las articulaciones", "rigidez articular"],
            "Sangrado": ["heces negras", "melena", "heces con sangre", "encias sangrantes",
                        "hemorragias nasales", "epistaxis", "menstruacion abundante",
                        "menorragia", "orina con sangre", "hematuria", "sangrado entre periodos",
                        "sangrado rectal"],
            "Hemorragia": ["hemorragia"],
            "Calambre": ["calambres musculares"],
            "Entumecimiento": ["adormecimiento", "entumecimiento", "hipoestesia"],
            "Hormigueo": ["hormigueo", "parestesia"],
            "Dificultad": ["dificultad para concentrarse", "dificultad para deglutir",
                          "disfagia", "dificultad para hablar", "afasia", "disartria",
                          "dificultad para respirar", "disnea", "incontinencia", "tenesmo vesical"],
            "Perdida": ["adelgazamiento del cabello", "afonia", "perdida de la voz",
                       "alteraciones de la memoria", "amnesia", "anhedonia",
                       "caida del cabello", "alopecia", "desmayos", "sincope",
                       "infertilidad", "perdida de apetito", "anorexia", "perdida de la libido",
                       "perdida de la coordinacion", "ataxia", "perdida del gusto",
                       "ageusia", "perdida del olfato", "anosmia", "perdida de peso inexplicable"],
            "Aumento": ["aumento de la sed", "polidipsia", "aumento del apetito",
                       "polifagia", "aumento de peso inexplicable", "aumento del vello corporal",
                       "hirsutismo", "orinar con frecuencia", "polaquiuria", "nicturia"],
            "Secrecion": ["exceso de gases", "flatulencia", "lagrimero excesivo", "epifora", "pus",
                         "salivacion excesiva", "sialorrea", "secrecion del pezon", "secrecion nasal",
                         "rinorrea", "secrecion ocular", "secrecion uretral", "secrecion vaginal"],
            "Ampollas": ["ampollas", "llagas", "ulceras", "vesiculas"],
            "Escalofrios": ["escalofrios", "piel fria", "piel humeda"],
            "Sudoracion": ["alteraciones en el sudor", "sudores nocturnos", "diaforesis"],
            "Ansiedad": ["agitacion", "ansiedad", "nerviosismo", "inquietud"],
            "Depresion": ["depresion", "animo bajo", "tristeza persistente"],
            "Insomnio": ["insomnio", "dificultad para dormir"],
            "Confusion": ["confusion", "desorientacion", "delirios", "despersonalizacion", "letargo"],
            "Palpitaciones": ["palpitaciones", "taquicardia", "bradicardia"],
            "Ojos y Vision": ["vision borrosa", "vision doble", "diplopia", "ojos rojos",
                             "sensibilidad a la luz", "fotofobia", "ceguera"],
            "Oido y Audicion": ["tinnitus", "acufenos", "perdida de la audicion", "hipoacusia"],
            "Boca y Garganta": ["boca seca", "xerostomia", "mal aliento", "halitosis", "llagas en la boca"],
            "Sistema Urinario": ["miccion frecuente", "dolor al orinar", "orina turbia"],
            "Piel y Anexos": ["palidez", "piel amarillenta", "ictericia", "piel azulada", "cianosis"],
            "Estado de Animo y Comportamiento": ["irritabilidad", "cambios de humor", "aislamiento social"]
        }
        self.sintomas_validos = [
            "acidez estomacal", "acné", "acufenos", "agitación", "aislamiento social", "amnesia", "ansiedad",
            "animo bajo", "anorexia", "articulaciones rígidas", "astenia", "aumento de peso", "boca seca",
            "bradicardia", "cambios de humor", "cianosis", "confusión", "congestión nasal", "debilidad",
            "depresión", "diarrea", "diplopia", "disartria", "disfagia (dificultad para tragar)",
            "disnea (falta de aliento)", "disuria", "dolor abdominal", "dolor al orinar", "dolor articular",
            "dolor de cabeza", "dolor de cuello", "dolor de espalda", "dolor de garganta", "dolor de oído",
            "dolor de rodilla", "dolor en el pecho", "dolor intermenstrual", "dolor oseo", "escalofríos",
            "estornudos", "estreñimiento", "fatiga", "febricula", "fiebre", "fotofobia", "halitosis",
            "hematemesis", "hemorragia vaginal", "hinchazón", "hipoacusia", "hirsutismo", "hormigueo",
            "ictericia", "indigestión", "inflamación de los ganglios linfáticos", "inquietud", "insomnio",
            "irritabilidad", "letargo", "lipotimia", "llagas en la boca", "mal aliento", "malestar general",
            "mareo", "melena", "migraña", "náusea", "nerviosismo", "nicturia", "ojos rojos", "palidez",
            "palpitaciones", "pérdida de la audicion", "pérdida de la memoria", "pérdida de peso",
            "pérdida del conocimiento", "pérdida del olfato", "petequias", "picazón", "picazón en los ojos",
            "piel amarillenta", "rigidez de nuca", "sangrado rectal", "secreción nasal", "sudores nocturnos",
            "taquicardia", "tenesmo vesical", "tinnitus", "tos", "tristeza persistente", "urticaria",
            "vision doble", "visión borrosa", "vómito", "xerostomia"
        ]
        self.mapa_sintomas = {
            "vomito": "vómito", "vomitos": "vómito", "vómitos": "vómito",
            "nausea": "náusea", "nauseas": "náusea",
            "mareos": "mareo", "agitacion": "agitación",
            "pedida de peso": "pérdida de peso", "ingestión": "indigestión",
            "disfagia": "disfagia (dificultad para tragar)", "disnea": "disnea (falta de aliento)",
            "acne": "acné", "acufenos": "tinnitus", "zumbido en los oidos": "tinnitus",
            "perdida de la audicion": "hipoacusia", "vision doble": "diplopia",
            "sensibilidad a la luz": "fotofobia", "dolor al tragar": "odinofagia",
            "mal aliento": "halitosis", "boca seca": "xerostomia", "piel amarilla": "ictericia",
            "piel azulada": "cianosis", "ganglios inflamados": "adenopatia",
            "perdida del apetito": "anorexia", "debilidad general": "astenia", "desmayo": "lipotimia"
        }
        self.nlp = spacy.load("es_core_news_sm")
        self.configurar_matcher_demografia()

    def configurar_matcher_demografia(self):
        #Configuración de patrones para extraer información demográfica como edad y género.
    
        self.matcher = Matcher(self.nlp.vocab)
        patrones = [
            [{"LOWER": {"IN": ["mayores", "después", "partir"]}}, {"LIKE_NUM": True}],
            [{"LOWER": {"IN": ["menores", "antes", "hasta"]}}, {"LIKE_NUM": True}],
            [{"LOWER": {"IN": ["entre", "de"]}}, {"LIKE_NUM": True}, {"LOWER": {"IN": ["y", "a"]}}, {"LIKE_NUM": True}],
            [{"LOWER": {"IN": ["edad", "edades"]}}, {"LIKE_NUM": True}, {"LOWER": {"IN": ["años", "año"]}}]
        ]
        for i, patron in enumerate(patrones):
            self.matcher.add(f"PATRON_{i}", [patron])

    def limpiar_texto(self, texto):
        # Normaliza y limpia el texto para facilitar la búsqueda de síntomas.

        if not isinstance(texto, str): return ""
        nfkd_form = unicodedata.normalize('NFKD', texto.lower())
        texto_limpio = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
        return re.sub(r'[^\w\s]', '', texto_limpio)

    def extraer_sintomas_estructurados(self, contenido_texto):
        # Extrae síntomas del texto y los organiza por categorías.
    
        contenido_limpio = self.limpiar_texto(contenido_texto)
        sintomas_encontrados = {}
        for categoria, lista_sintomas in self.categorias_sintomas.items():
            sintomas_categoria = [sintoma for sintoma in lista_sintomas if re.search(r'\b' + re.escape(sintoma) + r'\b', contenido_limpio)]
            if sintomas_categoria:
                sintomas_encontrados[categoria] = list(set(sintomas_categoria))
        return sintomas_encontrados

    def analizar_demografia(self, texto):
    
        # Analiza el texto para extraer información demográfica como edad y género.
        
        if not texto or not texto.strip():
            return {"min_edad": 18, "max_edad": 59, "rango_edad_comun": ["adulto"], "genero_mas_afectado": "Ambos"}
            
        doc = self.nlp(texto.lower())
        keywords_genero = {"Hombres": ["hombre", "masculino", "varón", "prostático"], "Mujeres": ["mujer", "femenino", "embarazo", "menopausia", "ovárico"]}
        keywords_edad = {"pediatrico": ["niño", "bebé", "infancia"], "joven": ["joven", "adolescente", "pubertad"], "adulto": ["adulto", "mediana edad"], "adulto_mayor": ["mayor", "anciano", "edad avanzada"]}
        genero = "Ambos"
        for gen, palabras in keywords_genero.items():
            if any(palabra in texto.lower() for palabra in palabras):
                if genero == "Ambos": genero = gen
                else: genero = "Ambos"; break
        rangos_edad = {rango for rango, palabras in keywords_edad.items() if any(palabra in texto.lower() for palabra in palabras)}
        if not rangos_edad: rangos_edad = {"adulto"}
        rangos_por_defecto = {"pediatrico": (0, 17), "joven": (12, 30), "adulto": (18, 59), "adulto_mayor": (60, 100)}
        min_edad = min(rangos_por_defecto[rango][0] for rango in rangos_edad)
        max_edad = max(rangos_por_defecto[rango][1] for rango in rangos_edad)
        return {"min_edad": min_edad, "max_edad": max_edad, "rango_edad_comun": list(rangos_edad), "genero_mas_afectado": genero}

    def procesar_enfermedad_completa(self, enfermedad):
        """
        Procesa una enfermedad, extrayendo síntomas y demografía de TODO el texto disponible
        para una cobertura máxima.
        """
        texto_analisis = []
        
        # Lista de todas las secciones que pueden contener texto relevante
        secciones_a_revisar = ['sintomas_causas', 'diagnostico_tratamiento']

        for nombre_seccion in secciones_a_revisar:
            if nombre_seccion in enfermedad and isinstance(enfermedad[nombre_seccion], list):
                for seccion in enfermedad[nombre_seccion]:
                    # Se procesa la sección sin importar el título para una cobertura total
                    if isinstance(seccion, dict) and seccion.get("contenido"):
                        for item in seccion["contenido"]:
                            if isinstance(item, dict):
                                if item.get("tipo") == "parrafo" and item.get("contenido"):
                                    texto_analisis.append(item.get("contenido", ""))
                                elif item.get("tipo") == "lista" and item.get("items"):
                                    # Asegurarse de que los items de la lista son strings
                                    items_str = [str(sub_item) for sub_item in item.get("items", []) if sub_item is not None]
                                    texto_analisis.extend(items_str)
        
        texto_completo = " ".join(filter(None, texto_analisis))
        
        sintomas_estructurados = self.extraer_sintomas_estructurados(texto_completo)
        demografia = self.analizar_demografia(texto_completo)
        
        enfermedad_actualizada = enfermedad.copy()
        enfermedad_actualizada["demografia"] = demografia
        enfermedad_actualizada["sintomas_compartidos"] = sintomas_estructurados
        
        return enfermedad_actualizada

    def crear_indice_sintomas(self, enfermedades_procesadas):
        # Crea un índice invertido desde las CATEGORÍAS de síntomas hacia las enfermedades.
        indice = defaultdict(list)
        for enfermedad in enfermedades_procesadas:
            info_enfermedad = {
                "id": enfermedad.get("id"),
                "nombre": enfermedad.get("nombre"),
                "url": enfermedad.get("url"),
                "demografia": enfermedad.get("demografia", {})
            }
            
            if "sintomas_compartidos" in enfermedad and enfermedad["sintomas_compartidos"]:
                for categoria in enfermedad["sintomas_compartidos"].keys():
                    if not any(e['id'] == info_enfermedad['id'] for e in indice[categoria]):
                        indice[categoria].append(info_enfermedad)
                        
        return dict(sorted(indice.items()))

    def unir_archivos_json(self, archivo_enfermedades, archivo_indice, archivo_salida_unificado):
        # Une los archivos de enfermedades procesadas y el índice de síntomas en uno solo.
        print("\n=== UNIENDO ARCHIVOS JSON ===")
        try:
            with open(archivo_enfermedades, 'r', encoding='utf-8') as f:
                datos_enfermedades = json.load(f)
            with open(archivo_indice, 'r', encoding='utf-8') as f:
                datos_indice = json.load(f)

            datos_unificados = {
                "enfermedades": datos_enfermedades.get("enfermedades", []),
                "indice_sintomas": datos_indice
            }
            
            with open(archivo_salida_unificado, 'w', encoding='utf-8') as f:
                json.dump(datos_unificados, f, ensure_ascii=False, indent=4)
            
            print(f" Archivos unificados guardados en: {archivo_salida_unificado}")
        except FileNotFoundError as e:
            print(f"Error: No se pudo encontrar el archivo {e.filename}")
        except json.JSONDecodeError:
            print("Error: Uno de los archivos JSON es inválido.")

    def ejecutar_pipeline_completo(self, archivo_entrada, archivo_salida_enfermedades, archivo_salida_indice, archivo_salida_unificado):
        # Ejecuta todo el pipeline de procesamiento y enriquecimiento de datos.
        print("=== INICIANDO PROCESAMIENTO COMPLETO DE ENFERMEDADES ===")
        try:
            with open(archivo_entrada, 'r', encoding='utf-8') as f:
                datos = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error al leer el archivo de entrada: {e}"); return
        
        enfermedades = datos.get("enfermedades", [])
        if not enfermedades:
            print("Advertencia: No se encontraron enfermedades en el archivo de entrada.")
            return

        print(f"Enfermedades a procesar: {len(enfermedades)}")
        
        enfermedades_procesadas = [self.procesar_enfermedad_completa(enf) for enf in enfermedades]
        print(f"Procesamiento de {len(enfermedades)} enfermedades completado.")
        
        datos_salida = {"enfermedades": enfermedades_procesadas}
        with open(archivo_salida_enfermedades, 'w', encoding='utf-8') as f:
            json.dump(datos_salida, f, ensure_ascii=False, indent=4)
        print(f" Enfermedades procesadas guardadas en: {archivo_salida_enfermedades}")
        
        indice_sintomas = self.crear_indice_sintomas(enfermedades_procesadas)
        with open(archivo_salida_indice, 'w', encoding='utf-8') as f:
            json.dump(indice_sintomas, f, ensure_ascii=False, indent=4)
        print(f" Índice de síntomas por categoría guardado en: {archivo_salida_indice}")
        
        self.unir_archivos_json(archivo_salida_enfermedades, archivo_salida_indice, archivo_salida_unificado)
        
        print(f"\n=== ESTADÍSTICAS FINALES ===")
        print(f"Enfermedades procesadas: {len(enfermedades_procesadas)}")
        print(f"Categorías de síntomas únicas en el índice: {len(indice_sintomas)}")
        if indice_sintomas:
            top_categorias = sorted(indice_sintomas.items(), key=lambda item: len(item[1]), reverse=True)
            print("Categorías con más enfermedades asociadas:")
            for categoria, lista in top_categorias[:10]:
                print(f"- {categoria}: {len(lista)} enfermedades")

if __name__ == "__main__":
    procesador = ProcesadorEnfermedades()
    archivo_entrada = "2_enfermedades_detallado_crudo.json"
    archivo_salida_enfermedades = "enfermedades_demograficas.json"
    archivo_salida_indice = "indice_sintomas.json"
    archivo_salida_unificado = "3_datos_completos_procesados.json"
    
    procesador.ejecutar_pipeline_completo(
        archivo_entrada, 
        archivo_salida_enfermedades, 
        archivo_salida_indice,
        archivo_salida_unificado
    )