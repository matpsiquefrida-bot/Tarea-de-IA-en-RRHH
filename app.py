import os
import streamlit as st
from openai import OpenAI
from fpdf import FPDF

# Configuración inicial de la página
st.set_page_config(
    page_title="Generador de Entrevistas por Competencias",
    page_icon="📋",
    layout="wide"
)

# Inicializar cliente de OpenAI apuntando al endpoint de Groq
try:
    client = OpenAI(
        api_key=st.secrets.get("GROQ_API_KEY"),
        base_url=st.secrets.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    )
except Exception as e:
    st.error("Error al configurar las credenciales de la API de Groq. Verifica tus Secrets.")

# --- INTERFAZ DE USUARIO (FRONT) ---
st.title("Generador de Entrevistas por Competencias")
st.markdown(
    """
    Herramienta diseñada para **reclutadores, analistas de gestión humana y líderes de TI**. 
    Genera preguntas de entrevista estructuradas bajo el **método STAR**, adaptadas al nivel de seniority 
    y garantizando el pleno cumplimiento de la normativa laboral y de protección de datos en España 
    (Constitución Española arts. 14 y 18, Estatuto de los Trabajadores y LOPDGDD).
    """
)

st.markdown("---")

# Menús desplegables y selección múltiple
col1, col2 = st.columns(2)

with col1:
    puesto = st.selectbox(
        "1. Selecciona el Puesto:",
        ["Gerente de Proyectos TI", "Analista Junior TI", "Desarrollador de software"]
    )
    
    seniority = st.selectbox(
        "2. Selecciona el Nivel de Seniority:",
        ["Junior", "Mid-Senior", "Senior"]
    )

with col2:
    competencias_disponibles = [
        "Liderazgo de equipos técnicos",
        "Gestión de riesgos e imprevistos en TI",
        "Metodologías Ágiles/Scrum",
        "Negociación con Stakeholders",
        "Gestión de tiempo y entregables",
        "Gestión de base de datos",
        "Programación",
        "Conocimientos y uso de lenguajes de programación",
        "Fundamentos TI",
        "Frameworks",
        "Arquitectura de datos",
        "Herramientas de desarrollo",
        "Conceptos de estructuras de datos",
        "Conocimientos en Ciberseguridad"
    ]
    
    competencias_seleccionadas = st.multiselect(
        "3. Selecciona las Competencias a Evaluar (mínimo una):",
        competencias_disponibles
    )

st.markdown("---")

# Función para generar PDF (Corregida para retornar 'bytes')
def generar_pdf(texto_resultado, puesto, seniority):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Encabezado
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Guia de Entrevista por Competencias", ln=True, align="C")
    pdf.set_font("helvetica", "I", 11)
    pdf.cell(0, 8, f"Puesto: {puesto} | Seniority: {seniority}", ln=True, align="C")
    pdf.ln(10)
    
    # Cuerpo del reporte
    pdf.set_font("helvetica", "", 10)
    # Limpieza básica para evitar problemas de codificación de fuentes estándar
    texto_limpio = texto_resultado.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, texto_limpio)
    
    # Conversión explícita a bytes
    return bytes(pdf.output())

# Botón de generación
if st.button("Generar Preguntas de Entrevista", type="primary"):
    # Validación 1: Verificar que se haya seleccionado al menos una competencia
    if not competencias_seleccionadas:
        st.warning("⚠️ Debes seleccionar al menos una competencia para continuar.")
    else:
        with st.spinner("Analizando requerimientos y generando preguntas con Groq (gpt-oss-20b)..."):
            
            # Construcción del prompt con restricciones normativas y técnicas
            prompt_sistema = (
                "Eres un experto en People Analytics, selección de talento TI y normativa laboral española. "
                "Genera preguntas de entrevista por competencias basadas en situaciones de la vida real. "
                "Cada pregunta debe cumplir strictly con el marco legal español: Constitución Española "
                "(artículo 14 sobre no discriminación y artículo 18 sobre intimidad), el Estatuto de los Trabajadores "
                "y la Ley Orgánica 3/2018 de Protección de Datos (LOPDGDD), evitando cualquier pregunta intrusiva o discriminatoria. "
                "Para cada competencia seleccionada, entrega la estructura exacta solicitada."
            )
            
            prompt_usuario = f"""
            Genera la guía de entrevista para:
            - Puesto: {puesto}
            - Seniority: {seniority}
            - Competencias a evaluar: {', '.join(competencias_seleccionadas)}

            Estructura requerida para CADA competencia:
            1. **Competencia evaluada**
            2. **Pregunta Principal (Método STAR - Situación real):** Situación hipotética o pasada orientada a la conducta.
            3. **Pregunta Secundaria:** Para profundizar y validar detalles técnicos o de comportamiento.
            4. **Indicadores de respuesta deseada:** Qué buscar en un candidato óptimo.
            5. **Indicadores de alerta (Red Flags):** Señales de riesgo o respuestas inadecuadas.
            """
            
            try:
                # Modelo gratuito y activo en la API de Groq
                response = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "system", "content": prompt_sistema},
                        {"role": "user", "content": prompt_usuario}
                    ],
                    temperature=0.7
                )
                
                resultado_ia = response.choices[0].message.content
                
                # Guardar en session_state para persistencia
                st.session_state["resultado_ia"] = resultado_ia
                st.session_state["puesto_gen"] = puesto
                st.session_state["seniority_gen"] = seniority
                
            except Exception as e:
                st.error(f"Ocurrió un error al conectar con Groq: {e}")

# Mostrar resultados si ya fueron generados
if "resultado_ia" in st.session_state:
    st.success("¡Preguntas generadas con éxito!")
    st.markdown("### Resultados de la Evaluación")
    st.markdown(st.session_state["resultado_ia"])
    
    st.markdown("---")
    
    # Botón destacado para la descarga del PDF
    pdf_bytes = generar_pdf(
        st.session_state["resultado_ia"], 
        st.session_state["puesto_gen"], 
        st.session_state["seniority_gen"]
    )
    
    st.download_button(
        label="📥 Descargar Guía en PDF",
        data=pdf_bytes,
        file_name=f"Guia_Entrevista_{st.session_state['puesto_gen'].replace(' ', '_')}.pdf",
        mime="application/pdf",
        type="primary"
    )