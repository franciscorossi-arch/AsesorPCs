"""Asesor de PC · Ruta A (Streamlit Community Cloud).

El usuario cuenta para qué quiere el ordenador, su presupuesto y su país,
y Gemini le propone una torre por piezas o dos o tres portátiles, explicados
en lenguaje sencillo. Los enlaces de compra NO los inventa la IA: los genera
el código como búsquedas en tiendas reales del país elegido.
"""

import re
from urllib.parse import quote, quote_plus

import httpx
import streamlit as st
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field

# --------------------------------------------------------------------------
# Configuración
# --------------------------------------------------------------------------
# Modelos en orden de preferencia: (nombre, nivel de razonamiento o None).
# Medido con la clave gratuita el 04/11/2026 (torre para jugar, 1200 €):
#   gemini-3.5-flash (razonamiento bajo) ~6 s y aprovecha bien el presupuesto;
#   gemini-3.1-flash-lite ~5 s; gemini-3.5-flash-lite ~14 s;
#   gemini-3.8-flash daba 503 (saturado) y llegó a tardar 68 s en fallar.
MODELOS = [
    ("gemini-3.5-flash", "low"),
    ("gemini-3.1-flash-lite", None),
    ("gemini-3.5-flash-lite", None),
]
TIEMPO_MAXIMO_MS = 30_000  # si un modelo tarda más de 30 s, se pasa al siguiente
MAX_CARACTERES = 600

TITULO = "🖥️ Asesor de PC"
DESCRIPCION = (
    "Dime para qué quieres el ordenador y cuánto puedes gastar. "
    "Te propongo qué comprar, te explico por qué y te dejo enlaces para buscarlo en tiendas de tu país."
)

# Tiendas por país. {q} = búsqueda con '+', {slug} = búsqueda con guiones (MercadoLibre)
REGIONES = {
    "España": {
        "moneda": "EUR", "simbolo": "€", "simbolo_detras": True, "presupuesto": 900, "paso": 50,
        "tiendas": {
            "PcComponentes": "https://www.pccomponentes.com/search/?query={q}",
            "Amazon": "https://www.amazon.es/s?k={q}",
        },
    },
    "México": {
        "moneda": "MXN", "simbolo": "$", "simbolo_detras": False, "presupuesto": 18000, "paso": 1000,
        "tiendas": {
            "Mercado Libre": "https://listado.mercadolibre.com.mx/{slug}",
            "Amazon": "https://www.amazon.com.mx/s?k={q}",
        },
    },
    "Argentina": {
        "moneda": "ARS", "simbolo": "$", "simbolo_detras": False, "presupuesto": 1200000, "paso": 50000,
        "tiendas": {
            "Mercado Libre": "https://listado.mercadolibre.com.ar/{slug}",
            "Google Shopping": "https://www.google.com/search?tbm=shop&gl=ar&q={q}",
        },
    },
    "Colombia": {
        "moneda": "COP", "simbolo": "$", "simbolo_detras": False, "presupuesto": 4000000, "paso": 100000,
        "tiendas": {
            "Mercado Libre": "https://listado.mercadolibre.com.co/{slug}",
            "Google Shopping": "https://www.google.com/search?tbm=shop&gl=co&q={q}",
        },
    },
    "Chile": {
        "moneda": "CLP", "simbolo": "$", "simbolo_detras": False, "presupuesto": 900000, "paso": 50000,
        "tiendas": {
            "Mercado Libre": "https://listado.mercadolibre.cl/{slug}",
            "Google Shopping": "https://www.google.com/search?tbm=shop&gl=cl&q={q}",
        },
    },
    "Perú": {
        "moneda": "PEN", "simbolo": "S/", "simbolo_detras": False, "presupuesto": 3800, "paso": 100,
        "tiendas": {
            "Mercado Libre": "https://listado.mercadolibre.com.pe/{slug}",
            "Google Shopping": "https://www.google.com/search?tbm=shop&gl=pe&q={q}",
        },
    },
    "Estados Unidos": {
        "moneda": "USD", "simbolo": "$", "simbolo_detras": False, "presupuesto": 1000, "paso": 50,
        "tiendas": {
            "Amazon": "https://www.amazon.com/s?k={q}",
            "Newegg": "https://www.newegg.com/p/pl?d={q}",
        },
    },
}

EJEMPLOS = {
    "🎮 Jugar": "Jugar a juegos actuales en 1080p con buena fluidez y hacer algún directo en Twitch de vez en cuando.",
    "🎨 Diseño": "Soy estudiante de diseño gráfico: uso Photoshop, Illustrator y estoy empezando con Blender.",
    "👵 Casa": "Para una persona mayor: navegar, ver vídeos, videollamadas con la familia y algo de ofimática. Que sea silencioso y fácil.",
    "💼 Oficina": (
        "Para trabajar: Word, Excel y PowerPoint, correo, videollamadas por Teams o Zoom y el navegador "
        "con muchas pestañas. Que sea fiable, silencioso y que dure años."
    ),
    "💻 Programar": "Programar, tener muchas pestañas abiertas, Docker y alguna máquina virtual. Lo llevaré a clase.",
    "🤖 IA local": (
        "Quiero ejecutar modelos de IA (LLM) en mi propio ordenador con Ollama o LM Studio, "
        "como Llama, Qwen o Mistral de 7 a 14B, y montar agentes que me ayuden a programar sin depender de la nube."
    ),
}

SYSTEM_PROMPT = """
Eres un asesor de informática honesto que ayuda a personas SIN conocimientos técnicos
a elegir un ordenador. Respondes siempre en español, con frases cortas y sin jerga;
si usas un término técnico (GPU, RAM, SSD...) lo explicas en pocas palabras.

Recibirás: tipo de equipo (torre por piezas o portátil), para qué lo quiere, presupuesto,
moneda y país. Devuelve SOLO el JSON del esquema indicado.

Reglas:
1. Si la petición no tiene nada que ver con comprar un ordenador, pon fuera_de_tema=true,
   explica amablemente en "aviso" qué puedes hacer, y deja "piezas" vacía y los importes a 0.
2. Torre por piezas: devuelve una pieza por categoría: Procesador, Placa base, Memoria RAM,
   Tarjeta gráfica (omítela si el procesador tiene gráficos integrados suficientes para el uso),
   Almacenamiento, Fuente de alimentación, Caja, y Disipador si el procesador no lo incluye.
   Añade Monitor, Teclado y ratón solo si te lo piden. Comprueba la compatibilidad:
   socket del procesador con la placa, tipo de RAM (DDR4/DDR5) con la placa,
   potencia de la fuente suficiente con margen, y que la gráfica quepa en la caja.
3. Portátil: devuelve 2 o 3 portátiles concretos en "piezas", ordenados de más recomendado
   a menos. En "categoria" pon "Opción recomendada", "Alternativa más barata" o
   "Alternativa superior"; en "motivo" incluye procesador, RAM, almacenamiento, pantalla
   y gráfica. "total_estimado" es el precio de la opción recomendada.
4. Usa modelos concretos, reales y fáciles de encontrar en tiendas de ese país.
   "busqueda" es el texto que alguien escribiría en el buscador de una tienda para
   encontrar ese producto: marca y modelo, corto, sin precio (ej. "Ryzen 5 7600").
5. Precios ORIENTATIVOS en la moneda indicada, redondeados. No inventes enlaces.
6. Ajústate al presupuesto (puedes pasarte como mucho un 5 %). Si con ese presupuesto
   no se puede conseguir algo razonable para ese uso, pon presupuesto_suficiente=false,
   explícalo en "aviso" diciendo qué presupuesto mínimo sería realista, y propón igualmente
   la mejor opción posible para el dinero disponible. Si gastar más del presupuesto
   disponible mejora de forma notable la experiencia para ese uso (por ejemplo, una
   gráfica mejor para jugar o editar), aprovéchalo: apunta a usar entre el 85 % y el
   100 %. Solo si el uso es sencillo (ofimática, navegar) y el presupuesto sobra mucho,
   dilo en "aviso" y no gastes por gastar.
7. "resumen": 2 o 3 frases explicando la idea general de la propuesta para ese uso.
   "consejos": de 2 a 4 consejos prácticos y breves (ej. qué mejorar en el futuro,
   si hace falta comprar Windows, qué revisar antes de comprar).
8. Ofimática o trabajo: no hace falta tarjeta gráfica dedicada (usa procesadores con gráficos
   integrados), pero sí 16 GB de RAM, SSD de 512 GB o más y, en portátil, buena batería,
   buen teclado, pantalla IPS y cámara/micrófono decentes para videollamadas. Prioriza
   fiabilidad y silencio; si el presupuesto sobra, dilo y no gastes por gastar.
9. IA local (ejecutar LLM o agentes en el propio ordenador con Ollama, LM Studio, llama.cpp...):
   lo que más importa es la memoria de la tarjeta gráfica (VRAM), porque el modelo tiene que
   caber en ella. Prioriza una gráfica NVIDIA (CUDA es lo más compatible) con la mayor VRAM que
   permita el presupuesto: 12 GB como mínimo razonable, 16 GB o más para modelos de 14B o más.
   Gasta en la gráfica antes que en el procesador. Pon al menos 32 GB de RAM (64 GB si sobra
   presupuesto), un SSD NVMe de 1-2 TB (los modelos ocupan mucho) y una fuente con margen.
   En "resumen" o "consejos" di, de forma sencilla, qué tamaño de modelo podrá mover
   (ej. "modelos de hasta 14B cuantizados a 4 bits"). En portátil, busca la gráfica con más VRAM;
   si el presupuesto lo permite, menciona que un Mac con chip M y mucha memoria unificada
   también es una opción.
"""


# --------------------------------------------------------------------------
# Esquema de la respuesta (Gemini devuelve JSON con esta forma)
# --------------------------------------------------------------------------
class Pieza(BaseModel):
    categoria: str = Field(description="Ej. 'Procesador' o 'Opción recomendada'")
    nombre: str = Field(description="Marca y modelo concretos")
    busqueda: str = Field(description="Texto corto para buscarlo en una tienda")
    precio_estimado: float = Field(description="Precio orientativo en la moneda indicada")
    motivo: str = Field(description="Por qué esta pieza, en una o dos frases sencillas")


class Recomendacion(BaseModel):
    fuera_de_tema: bool
    presupuesto_suficiente: bool
    aviso: str = Field(description="Aviso importante para el usuario, o cadena vacía")
    resumen: str
    piezas: list[Pieza]
    total_estimado: float
    consejos: list[str]


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------
def formatear_precio(valor: float, region: str) -> str:
    datos = REGIONES[region]
    numero = f"{valor:,.0f}"  # 18,000 (México y EE. UU. usan coma de miles)
    if datos["moneda"] not in ("MXN", "USD"):
        numero = numero.replace(",", ".")  # 1.200.000 (España y resto de LATAM)
    return f"{numero} {datos['simbolo']}" if datos["simbolo_detras"] else f"{datos['simbolo']}{numero}"


def enlaces_de_busqueda(region: str, busqueda: str) -> dict[str, str]:
    """Crea enlaces de búsqueda en las tiendas del país. Nunca los inventa la IA."""
    texto = busqueda.strip()
    slug = re.sub(r"[^0-9a-zA-ZáéíóúñÁÉÍÓÚÑ]+", "-", texto).strip("-").lower()
    return {
        tienda: plantilla.format(q=quote_plus(texto), slug=quote(slug))
        for tienda, plantilla in REGIONES[region]["tiendas"].items()
    }


def construir_peticion(tipo: str, uso: str, presupuesto: float, region: str, perifericos: bool) -> str:
    datos = REGIONES[region]
    lineas = [
        f"Tipo de equipo: {tipo}",
        f"Para qué lo quiere: {uso.strip()}",
        f"Presupuesto máximo: {presupuesto:.0f} {datos['moneda']}",
        f"País donde lo comprará: {region} (precios en {datos['moneda']})",
    ]
    if tipo == "Torre por piezas":
        lineas.append(
            "Incluir monitor, teclado y ratón: " + ("sí, dentro del presupuesto" if perifericos else "no, ya los tiene")
        )
    return "\n".join(lineas)


def mensaje_de_error(error: Exception) -> str:
    """Traduce los errores técnicos a un mensaje que entienda cualquiera."""
    codigo = getattr(error, "code", None)
    if codigo == 429:
        return ("Ahora mismo hay demasiadas consultas y se ha agotado el uso gratuito de la IA. "
                "Espera un minuto y vuelve a pulsar el botón. Si sigue pasando, prueba más tarde.")
    if codigo in (400, 401, 403):
        return ("La app no puede conectarse con la IA porque la clave no es válida. "
                "Si eres quien gestiona la app, revisa GEMINI_API_KEY en los secretos.")
    if codigo == 404:
        return "El modelo de IA configurado ya no está disponible. Hay que actualizar el nombre del modelo en la app."
    if codigo in (500, 502, 503, 504) or isinstance(error, httpx.TimeoutException):
        return "El servicio de IA está saturado o caído en este momento. Inténtalo de nuevo en unos minutos."
    if isinstance(error, ValueError):
        return "La IA ha devuelto una respuesta que no he podido leer. Vuelve a pulsar el botón, suele arreglarse."
    return "No he podido conectar con la IA (¿problema de conexión?). Inténtalo de nuevo en un momento."


# --------------------------------------------------------------------------
# Llamada a Gemini
# --------------------------------------------------------------------------
@st.cache_resource
def obtener_cliente(api_key: str) -> genai.Client:
    """Crea el cliente de Gemini una sola vez y lo reutiliza."""
    return genai.Client(api_key=api_key)


def _leer_respuesta(respuesta) -> dict:
    if isinstance(respuesta.parsed, Recomendacion):
        return respuesta.parsed.model_dump()
    if not respuesta.text:
        raise ValueError("respuesta vacía")
    return Recomendacion.model_validate_json(respuesta.text).model_dump()


@st.cache_data(ttl=3600, show_spinner=False)
def pedir_recomendacion(api_key: str, peticion: str) -> tuple[dict, str]:
    """Pide la recomendación a Gemini probando los modelos de MODELOS en orden.
    Si uno falla por cuota (429), saturación (5xx), modelo retirado (404) o tarda
    más de TIEMPO_MAXIMO_MS, pasa al siguiente. Las respuestas se guardan una hora
    para no gastar cuota si alguien repite la misma consulta."""
    cliente = obtener_cliente(api_key)
    ultimo_error: Exception | None = None
    for modelo, razonamiento in MODELOS:
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=Recomendacion,
            temperature=0.4,
            http_options=types.HttpOptions(timeout=TIEMPO_MAXIMO_MS),
            thinking_config=types.ThinkingConfig(thinking_level=razonamiento) if razonamiento else None,
        )
        try:
            respuesta = cliente.models.generate_content(model=modelo, contents=peticion, config=config)
            return _leer_respuesta(respuesta), modelo
        except errors.APIError as error:
            if error.code in (429, 404, 500, 502, 503, 504):
                ultimo_error = error
                continue  # probamos con el siguiente modelo
            raise
        except httpx.TimeoutException as error:
            ultimo_error = error
            continue
    raise ultimo_error


# --------------------------------------------------------------------------
# Interfaz
# --------------------------------------------------------------------------
st.set_page_config(page_title="Asesor de PC", page_icon="🖥️", layout="centered")
st.title(TITULO)
st.caption(DESCRIPCION)

# La clave NUNCA va en el código: está en Settings → Secrets de Streamlit Cloud
try:
    clave = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("Falta el secreto GEMINI_API_KEY. Añádelo en Settings → Secrets de la app (o en .streamlit/secrets.toml en local).")
    st.stop()


def usar_ejemplo(texto: str) -> None:
    st.session_state.uso = texto


col_tipo, col_region = st.columns(2)
with col_tipo:
    tipo = st.radio("¿Qué buscas?", ["Torre por piezas", "Portátil"], horizontal=True)
with col_region:
    region = st.selectbox("¿Dónde lo vas a comprar?", list(REGIONES.keys()))

datos_region = REGIONES[region]
st.write("**¿Para qué lo vas a usar?** Cuéntalo con tus palabras, o pulsa un ejemplo:")
BOTONES_POR_FILA = 3
lista_ejemplos = list(EJEMPLOS.items())
for inicio in range(0, len(lista_ejemplos), BOTONES_POR_FILA):
    fila = lista_ejemplos[inicio:inicio + BOTONES_POR_FILA]
    for columna, (etiqueta, texto) in zip(st.columns(BOTONES_POR_FILA), fila):
        columna.button(etiqueta, on_click=usar_ejemplo, args=(texto,), width="stretch")

uso = st.text_area(
    "Uso del ordenador",
    key="uso",
    max_chars=MAX_CARACTERES,
    placeholder="Ej.: quiero editar vídeos para YouTube y jugar de vez en cuando…",
    label_visibility="collapsed",
)

col_presupuesto, col_extra = st.columns(2)
with col_presupuesto:
    presupuesto = st.number_input(
        f"Presupuesto máximo ({datos_region['moneda']})",
        min_value=0,
        value=datos_region["presupuesto"],
        step=datos_region["paso"],
        key=f"presupuesto_{region}",
    )
with col_extra:
    perifericos = False
    if tipo == "Torre por piezas":
        st.write("")
        perifericos = st.checkbox("Incluir monitor, teclado y ratón")

if st.button("✨ Recomiéndame un equipo", type="primary", width="stretch"):
    if len(uso.strip()) < 10:
        st.warning("Cuéntame un poco más para qué lo quieres (al menos una frase), así acierto mejor.")
    elif presupuesto <= 0:
        st.warning("Indica un presupuesto mayor que cero.")
    else:
        peticion = construir_peticion(tipo, uso, presupuesto, region, perifericos)
        with st.spinner("Buscando la mejor combinación para ti…"):
            try:
                resultado, modelo_usado = pedir_recomendacion(clave, peticion)
                st.session_state.resultado = {
                    "datos": resultado, "region": region, "tipo": tipo,
                    "presupuesto": presupuesto, "modelo": modelo_usado,
                }
            except Exception as error:  # cuota, clave, red, respuesta rara...
                st.session_state.pop("resultado", None)
                st.error("⚠️ " + mensaje_de_error(error))
                with st.expander("Detalle técnico (para quien gestiona la app)"):
                    st.code(f"{type(error).__name__}: {error}")


# --------------------------------------------------------------------------
# Resultado
# --------------------------------------------------------------------------
def texto_para_descargar(res: dict) -> str:
    d, reg = res["datos"], res["region"]
    lineas = [f"Asesor de PC · {res['tipo']} · {reg}", "", d["resumen"], ""]
    if d["aviso"]:
        lineas += [f"Aviso: {d['aviso']}", ""]
    for p in d["piezas"]:
        lineas.append(f"- {p['categoria']}: {p['nombre']} · {formatear_precio(p['precio_estimado'], reg)}")
        lineas.append(f"  {p['motivo']}")
        for tienda, url in enlaces_de_busqueda(reg, p["busqueda"]).items():
            lineas.append(f"  {tienda}: {url}")
    lineas += ["", f"Total estimado: {formatear_precio(d['total_estimado'], reg)}", "", "Consejos:"]
    lineas += [f"- {c}" for c in d["consejos"]]
    lineas += ["", "Precios orientativos generados con IA. Comprueba precio y compatibilidad antes de comprar."]
    return "\n".join(lineas)


if "resultado" in st.session_state:
    res = st.session_state.resultado
    d, reg = res["datos"], res["region"]
    st.divider()

    if d["fuera_de_tema"]:
        st.info("🤔 " + (d["aviso"] or "Solo puedo ayudarte a elegir un ordenador. Cuéntame para qué lo quieres."))
    else:
        if not d["presupuesto_suficiente"]:
            st.warning("💸 " + d["aviso"])
        elif d["aviso"]:
            st.info("ℹ️ " + d["aviso"])

        st.subheader("Mi propuesta")
        st.write(d["resumen"])

        etiqueta_total = "Precio de la opción recomendada" if res["tipo"] == "Portátil" else "Total estimado"
        diferencia = res["presupuesto"] - d["total_estimado"]
        st.metric(
            etiqueta_total,
            formatear_precio(d["total_estimado"], reg),
            delta=(f"te sobran {formatear_precio(diferencia, reg)}" if diferencia >= 0
                   else f"te pasas {formatear_precio(-diferencia, reg)}"),
            delta_color="normal" if diferencia >= 0 else "inverse",
        )

        for pieza in d["piezas"]:
            with st.container(border=True):
                izquierda, derecha = st.columns([4, 1])
                izquierda.markdown(f"**{pieza['categoria']}** · {pieza['nombre']}")
                izquierda.caption(pieza["motivo"])
                derecha.markdown(f"**{formatear_precio(pieza['precio_estimado'], reg)}**")
                enlaces = enlaces_de_busqueda(reg, pieza["busqueda"])
                for columna, (tienda, url) in zip(st.columns(len(enlaces)), enlaces.items()):
                    columna.link_button(f"🔎 Buscar en {tienda}", url, width="stretch")

        if d["consejos"]:
            st.subheader("Consejos")
            for consejo in d["consejos"]:
                st.markdown(f"- {consejo}")

        st.download_button(
            "📄 Descargar la propuesta",
            data=texto_para_descargar(res),
            file_name="propuesta_ordenador.txt",
            mime="text/plain",
            width="stretch",
        )
        st.caption(
            "⚠️ Precios orientativos generados con IA: pueden variar según la tienda y el día. "
            "Los botones abren una búsqueda en la tienda; comprueba el precio y que todo sea compatible antes de comprar. "
            f"Modelo usado: {res['modelo']}."
        )
