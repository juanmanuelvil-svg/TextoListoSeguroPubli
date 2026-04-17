import streamlit as st
import google.generativeai as genai
import urllib.parse
from gtts import gTTS
import io
from PIL import Image

# ==========================================
# CONFIGURACIÓN INICIAL
# ==========================================
st.set_page_config(page_title="TextoListo", page_icon="📝", layout="centered")

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except KeyError:
    st.error("⚠️ Falta la llave de Google en los Secrets de Streamlit.")
    st.stop()

st.markdown("""
    <style>
    .stButton>button { height: 90px; font-size: 24px !important; font-weight: bold; border-radius: 18px; }
    .stTextArea textarea { font-size: 24px !important; line-height: 1.6; }
    p, div, label { font-size: 22px !important; }
    h3 { font-size: 28px !important; margin-top: 25px !important; }
    
    /* Estilos para el banner permanente */
    .patrocinador-caja { 
        background-color: #f1f5f9; 
        padding: 15px; 
        border-radius: 10px; 
        text-align: center; 
        margin-bottom: 20px;
        border: 2px dashed #cbd5e1;
    }
    .texto-oscuro { color: #0f172a !important; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# SISTEMA DE MEMORIA
# ==========================================
if "texto_acumulado" not in st.session_state:
    st.session_state.texto_acumulado = ""
if "historial" not in st.session_state:
    st.session_state.historial = []

def guardar_pasado():
    st.session_state.historial.append(st.session_state.texto_acumulado)

def agregar_texto(texto_nuevo):
    if not texto_nuevo or texto_nuevo.startswith("⚠️"):
        return
    guardar_pasado()
    if st.session_state.texto_acumulado == "":
        st.session_state.texto_acumulado = texto_nuevo
    else:
        st.session_state.texto_acumulado += f"\n\n{texto_nuevo}"

def guardar_edicion_manual():
    st.session_state.texto_acumulado = st.session_state.editor_texto

# ==========================================
# FUNCIONES DE INTELIGENCIA ARTIFICIAL (CON COMPRESIÓN)
# ==========================================
def procesar_imagenes_lote(lista_archivos_imagen):
    try:
        imagenes_listas = []
        for img_file in lista_archivos_imagen:
            img = Image.open(img_file)
            
            # Compresión de imágenes para mayor velocidad
            if img.mode in ("RGBA", "P"): 
                img = img.convert("RGB")
            max_size = 1280
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            imagenes_listas.append(img)

        prompt = """Extrae todo el texto de estas imágenes de forma clara y limpia. Corrige ortografía. 
        SI ENCUENTRAS TABLAS O CIFRAS: Conviértelas en una lista fácil de leer renglón por renglón.
        Devuelve SOLO el texto, sin saludos ni explicaciones."""
        
        contenido = [prompt] + imagenes_listas
        respuesta = model.generate_content(contenido)
        return respuesta.text
    except Exception as e:
        return "⚠️ Problema al leer las fotos. Revisa que sean claras o intenta subir menos a la vez."

def procesar_audio(audio_file):
    try:
        audio_data = {"mime_type": audio_file.type, "data": audio_file.getvalue()}
        prompt = "Transcribe este audio. Quita muletillas y corrige la ortografía. Devuelve SOLO el texto."
        respuesta = model.generate_content([prompt, audio_data])
        return respuesta.text
    except Exception as e:
        return "⚠️ Hubo un problema al escuchar el audio."

def procesar_pdf(pdf_file):
    try:
        pdf_data = {"mime_type": "application/pdf", "data": pdf_file.getvalue()}
        prompt = "Lee este PDF. Extrae el texto de forma clara. Convierte tablas en listas. SOLO el texto."
        respuesta = model.generate_content([prompt, pdf_data])
        return respuesta.text
    except Exception as e:
        return "⚠️ Hubo un error al leer el PDF."

def generar_voz(texto):
    try:
        tts = gTTS(text=texto, lang='es', tld='com.mx')
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        return audio_bytes.getvalue()
    except Exception as e:
        return None 

# ==========================================
# INTERFAZ PRINCIPAL Y BANNER FIJO
# ==========================================
st.title("📝 TextoListo")
st.write("Convierte fotos o voz en texto limpio.")

# --- BANNER PUBLICITARIO SIEMPRE VISIBLE ---
st.markdown("---")
st.markdown("""
<div class='patrocinador-caja'>
    <p class='texto-oscuro' style='font-size: 16px !important; margin-bottom: 2px;'>🎉 Herramienta gratuita gracias a:</p>
    <h4 class='texto-oscuro' style='margin-top: 0px !important;'>Clínica Visión Clara</h4>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 2], gap="small", vertical_alignment="center")
with col1:
    st.image("https://images.unsplash.com/photo-1505751172876-fa1923c5c528?q=80&w=300&auto=format&fit=crop", use_container_width=True)
with col2:
    wpp_patrocinador = urllib.parse.quote("Hola, vi su anuncio en la aplicación TextoListo y me gustaría pedir informes.")
    enlace_contacto_patrocinador = f"https://api.whatsapp.com/send?text={wpp_patrocinador}"
    st.link_button("📞 Agendar cita de valoración", enlace_contacto_patrocinador, use_container_width=True)
st.markdown("---")

# --- FLUJO DE LA APLICACIÓN ---
st.info("🔒 **Consejo:** No tomes fotos de tarjetas o contraseñas.")

st.markdown("### 🛑 Paso 1: Permiso de Seguridad")
acepto_privacidad = st.checkbox("✅ Acepto que la computadora me ayude procesando mis fotos o voz.")

# --- TEXTO LEGAL BLINDADO ---
with st.expander("👀 Ver detalles legales y de privacidad"):
    st.markdown("""
    **1. Privacidad de Datos (LFPDPPP):** Sus imágenes y audios se procesan temporalmente de forma cifrada mediante Inteligencia Artificial y NO se guardan en ninguna base de datos. Todo se elimina automáticamente al cerrar la página.
    
    **2. Publicidad y Responsabilidad:** *TextoListo* es una herramienta independiente que se mantiene gratuita gracias a nuestros patrocinadores. *TextoListo* opera únicamente como espacio de difusión publicitaria y no se hace responsable por la calidad, permisos, tarifas o cumplimiento de los servicios médicos, legales o comerciales que los anunciantes ofrecen de manera externa.
    """)

st.divider()

st.subheader("🎙️ Paso 2: Dictar un mensaje")
audio_grabado = st.audio_input("Toca el micrófono para hablar")
if audio_grabado:
    if not acepto_privacidad:
        st.error("🚨 Por favor, acepta el permiso en el Paso 1.")
    else:
        # TRANSPARENCIA EN EL SPINNER
        with st.spinner("⏳ Escuchando... Patrocinado por Clínica Visión Clara."):
            texto = procesar_audio(audio_grabado)
            agregar_texto(texto)
            st.success("¡Agregado!")

st.divider()

st.subheader("📷 Paso 3: Tomar Foto o Subir Documento")
archivos_subidos = st.file_uploader(
    "Toca aquí:", 
    type=['png', 'jpg', 'jpeg', 'pdf', 'mp3', 'wav', 'm4a', 'ogg', 'opus'],
    accept_multiple_files=True 
)

if archivos_subidos and st.button("✅ PROCESAR", type="secondary", use_container_width=True):
    if not acepto_privacidad:
        st.error("🚨 Acepta el permiso en el Paso 1.")
    else:
        # TRANSPARENCIA EN EL SPINNER
        with st.spinner("⏳ Leyendo documentos... Servicio gratuito gracias a Clínica Visión Clara."):
            textos_nuevos = []
            imagenes_a_procesar = []

            for archivo in archivos_subidos:
                if archivo.type.startswith("image/"): 
                    imagenes_a_procesar.append(archivo)
                elif archivo.type.startswith("audio/"): 
                    textos_nuevos.append(procesar_audio(archivo))
                elif archivo.type == "application/pdf": 
                    textos_nuevos.append(procesar_pdf(archivo))
            
            if imagenes_a_procesar:
                textos_nuevos.append(procesar_imagenes_lote(imagenes_a_procesar))
            
            if textos_nuevos:
                agregar_texto("\n\n".join([t for t in textos_nuevos if not t.startswith("⚠️")]))
                st.success("¡Texto extraído con éxito!")

# ==========================================
# REVISIÓN Y ENVÍO
# ==========================================
if st.session_state.texto_acumulado.strip():
    st.subheader("👀 Paso 4: Revisa tu mensaje")
    
    if st.session_state.historial:
        if st.button("↩️ Borrar lo último"):
            st.session_state.texto_acumulado = st.session_state.historial.pop()
            st.rerun()

    texto_final = st.text_area("Mensaje:", value=st.session_state.texto_acumulado.strip(), height=300, key="editor_texto", on_change=guardar_edicion_manual)
    
    if st.button("🔊 Preparar Audio para Escuchar"):
        with st.spinner("⏳ Preparando audio..."):
            audio_generado = generar_voz(texto_final)
            if audio_generado:
                # FIX PARA IPHONE
                st.info("👇 Toca el botón de 'Play' abajo para escuchar:")
                st.audio(audio_generado, format='audio/mpeg')
            else:
                st.error("⚠️ Error de conexión al generar voz.")

    st.divider()
    mensaje_wpp = urllib.parse.quote(f"Hola, por favor ayúdame a imprimir esto:\n\n{texto_final}")
    st.link_button("✅ ENVIAR POR WHATSAPP", f"https://api.whatsapp.com/send?text={mensaje_wpp}", type="primary", use_container_width=True)

    if st.button("🗑️ Borrar TODO"):
        st.session_state.texto_acumulado = ""
        st.session_state.historial = []
        st.rerun()
