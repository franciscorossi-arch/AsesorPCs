# 🖥️ AsesorPCs

> *"Quiero un ordenador para editar vídeos y jugar algo, tengo 900 €. ¿Qué me compro?"*
> AsesorPCs contesta a esa pregunta en unos segundos, en tu idioma y con enlaces a tiendas de tu país.

| | |
|---|---|
| 🌐 **Pruébala** | https://my-app-app-franr-dhwqcrubnuucc48fqc6zk8.streamlit.app/ |
| 👤 **Autor** | Francisco Gabriel Rossi |
| 🎓 **Contexto** | Reto del módulo *Python para IA*, Máster en Inteligencia Artificial (OBS Business School) |
| 🧰 **Stack** | Python · Streamlit Community Cloud · API de Gemini (`google-genai`) · pydantic |

---

## En cinco frases

1. Quien no entiende de informática y necesita un ordenador depende del amigo "que sabe", de foros llenos de siglas o del dependiente de turno, y suele acabar pagando de más o quedándose corto.
2. AsesorPCs le pregunta para qué lo quiere, cuánto puede gastar y en qué país lo comprará, y le devuelve una torre pieza a pieza o dos o tres portátiles, con el motivo de cada elección y botones para buscarlos en tiendas locales.
3. La IA hace lo que ningún filtro de tienda puede hacer: convierte una frase como "quiero mover modelos de IA en local" en una configuración compatible y ajustada al presupuesto (en ese caso, priorizando una gráfica con 16 GB de VRAM), explicada sin jerga.
4. Al probarla desplegada, la primera consulta tardó más de un minuto porque el modelo previsto estaba saturado. Medí cinco modelos gratuitos, cambié a `gemini-3.5-flash` con un límite de 30 s por intento y una cadena de reserva, y ahora responde en 4-7 s aprovechando el 96 % del presupuesto, cuando antes se quedaba en el 70 %.
5. Lo siguiente sería conectar precios reales mediante las APIs de afiliados de las tiendas: en mis pruebas, la IA estimó el Ryzen 5 5600X en 140 € y PcComponentes lo vendía ese día a 177,48 €, un 27 % más.

---

## ¿Para quién es?

Pienso en tres personas: el estudiante de diseño que necesita un equipo para Blender y no sabe si "RTX" es importante, la familia que compra un portátil para la abuela, y quien quiere empezar a ejecutar LLM en su casa y no sabe que lo que manda es la VRAM. Hoy lo resuelven preguntando a alguien, viendo vídeos de una hora o fiándose de la etiqueta de "oferta". Es una compra cara que dura años, así que equivocarse sale caro.

**Qué resuelve la IA:** traducir una necesidad contada con palabras normales en piezas concretas, compatibles entre sí (socket, tipo de RAM, potencia de la fuente) y dentro del presupuesto, y explicarlo como lo haría un amigo paciente.

**Qué queda fuera, a propósito:** los precios en tiempo real y el stock (los precios son orientativos), la compra y el montaje. Los enlaces son búsquedas en tiendas reales, no fichas de producto.

## Cómo se usa

1. Elige **torre por piezas** o **portátil**, y el **país** (España, México, Argentina, Colombia, Chile, Perú o EE. UU.).
2. Cuenta **para qué lo quieres** o pulsa uno de los cinco ejemplos: 🎮 Jugar · 🎨 Diseño · 👵 Casa · 💻 Programar · 🤖 IA local.
3. Pon tu **presupuesto** en tu moneda y, si es una torre, marca si quieres monitor, teclado y ratón.
4. Pulsa **✨ Recomiéndame un equipo**. Recibes cada pieza con su precio y su porqué, el total frente a tu presupuesto, avisos (si no llega o si sobra) y consejos.
5. Cada producto tiene botones **🔎 Buscar en [tienda]**, y toda la propuesta se puede **descargar en .txt**.

## Decisiones de diseño (y por qué)

**Gemini con salida estructurada.** Necesitaba entender lenguaje natural y razonar sobre compatibilidad y presupuesto, que es terreno de un LLM. Un clasificador de Hugging Face no basta y un RAG no tiene sentido porque no hay documentos propios. Pido la respuesta como JSON validado con pydantic (`response_schema`), así la app pinta tarjetas en vez de un muro de texto.

**La IA no escribe enlaces.** Si se le piden URLs, se las inventa. Por eso Gemini solo devuelve el texto de búsqueda ("Ryzen 5 7600") y es el código el que construye la búsqueda en PcComponentes, Amazon, Mercado Libre, Newegg o Google Shopping, según el país.

**Elección de modelo con datos, no a ojo.** Medido con mi clave gratuita el 04/11/2026, con la misma consulta (torre para jugar, 1200 €):

| Modelo | Tiempo | ¿Aprovecha el presupuesto? | Notas |
|---|---|---|---|
| `gemini-3.8-flash` (el de las plantillas) | 1-68 s | — | Error 503 "alta demanda" en todos los intentos |
| `gemini-3.7-flash` | 5 s | — | Error 503 |
| **`gemini-3.5-flash`** (razonamiento bajo) | **~6 s** | **Sí: 1158-1200 €** | **Elegido como principal** |
| `gemini-3.1-flash-lite` | ~5 s | Sí: 1150 € | Primera reserva |
| `gemini-3.5-flash-lite` | ~14 s | Desigual: 837-1180 € | Segunda reserva |

**Si algo falla, la app sigue en pie.** Prueba los modelos en orden y salta al siguiente ante un 429 (cuota), un 5xx (saturación), un 404 (modelo retirado) o si pasan 30 s. Si fallan todos, muestra un mensaje en lenguaje normal ("se ha agotado el uso gratuito, espera un minuto") y deja el detalle técnico en un desplegable. Las respuestas se guardan una hora en caché para no gastar cuota con consultas repetidas.

**La clave nunca toca el repositorio.** Está en *Settings → Secrets* de Streamlit Cloud y en un `.streamlit/secrets.toml` local que está en `.gitignore`. Antes de cada push se comprueba automáticamente que la clave no aparece en ningún archivo del commit.

## Cómo la construí

La programé conversando con **Claude Code** (agente de programación) desde la app de escritorio, sin Colab. El agente lee [AGENTS.md](AGENTS.md) (a través de [CLAUDE.md](CLAUDE.md)), y la especificación completa está en [especificacion.md](especificacion.md).

**Los prompts que marcaron el rumbo** (copiados tal cual):

1. Elegir la idea:
   > *"Necesito que me des ideas de que hacer, en un programa en python con IA (con key de gemini para usar en streamlit mejor) […] una app que genere presupuestos de componentes para un ordenador de torre, o incluso portatiles […] y si es posible, con enlaces de compra disponibles en su region […] Otra idea es, una app para entrenamiento […] da tu criterio de cual seria mejor, para ejecutar y ACABAR en este ultimo dia"*
2. Construir sin Colab:
   > *"No quiero usar colab para crear el codigo, lo quiero hacer contigo, pero si quiero usar una key de gemini con un modelo gratuito en caso de, para no gastar contigo."*
3. Desplegar:
   > *"He pegado la clave en el archivo que has dicho y tambien en streamlit, que he vinculado la repo de la cuenta de github […] machaca todo lo que quieras dentro, y asi podre probar la app en streamlit"*
4. Mejorar tras la prueba:
   > *"Va bien aunque creo que tardo bastante en hacermela esta primera […] quizas habra que poner un modelo un poco mas rapido, pero sin que gaste mucho […] añadir […] un boton mas donde se evalue un presupuesto para gente que quiera un equipo para mover agentes LLM locales de IA"*

**Qué delegué y qué decidí o revisé yo:**

| Delegado al agente | Revisado o decidido por mí |
|---|---|
| Comparar las dos ideas (presupuestos de PC frente a rutinas de ejercicio) | Elegí la de PC: la de ejercicio necesitaba login y base de datos y manejaba datos de salud, y no se acababa en un día |
| Escribir `app.py`, el esquema JSON y el manejo de errores | Probé la app desplegada como usuario: caso normal, fuera de tema, enlaces y descarga |
| Generar los enlaces por código en lugar de pedírselos a la IA | Comprobé que las búsquedas de PcComponentes y Amazon.es abren el producto correcto (capturas 4) |
| Pruebas automáticas con Gemini simulado (429, campo vacío, falta de clave) | Detecté la lentitud de la primera consulta y pedí un modelo más rápido sin gastar |
| Medir los modelos y montar la cadena de reserva con límite de tiempo | Pedí el ejemplo 🤖 IA local y revisé que la propuesta prioriza la VRAM |
| Borradores de especificación, AGENTS.md y README | Cambié el nombre del repositorio y ajusté el texto final |

Un tropiezo real del proceso: la app desplegada se quedaba cargando en Brave, Edge y LibreWolf. El servidor estaba bien (comprobado por el agente) y la causa era mi DNS, Quad9, que bloqueaba parte de la conexión con Streamlit. Al cambiar de DNS cargó a la primera.

## Prueba y mejora

| Quién | Qué probó | Qué pasó | Qué cambió |
|---|---|---|---|
| Yo, con el agente, en local | Torre para jugar y hacer directos, 900 €, España | Piezas compatibles, pero solo 665 €: le sobraban 235 € que podían ir a la gráfica | Nueva regla en el prompt: aprovechar el 85-100 % del presupuesto cuando mejora el uso. Corregí también el formato de los precios en México (18,000) |
| Yo, con el agente, en local | 4K a tope por 300 € y "receta de paella" | Avisa de que hacen falta unos 2.000 € y propone lo mejor posible; la paella la rechaza con amabilidad | Nada, cumple la especificación |
| Yo, en la app desplegada | Torre para jugar, 1200 €, España; enlaces; descarga; "receta de tarta de queso" | La primera respuesta tardó mucho y la dio el modelo de reserva (837 €, sobraban 363 €). Enlaces y descarga correctos; tarta rechazada | Medí 5 modelos y cambié el principal a `gemini-3.5-flash` con límite de 30 s y dos reservas: 4-7 s y 1158 € de 1200 €. Añadí el ejemplo 🤖 IA local |
| Yo, con el agente | 🤖 IA local: torre de 1500 € (España) y portátil de 30.000 MXN | Torre con RTX 4070 Ti SUPER de 16 GB, 32 GB de DDR5 y la nota "modelos de 7B y 14B cuantizados a 4 bits"; portátil con RTX 4070 | — |
| [PENDIENTE: un compañero] | | | |

## Capturas

| | |
|---|---|
| ![Propuesta con total frente al presupuesto](docs/capturas/01_propuesta.png) **1.** La app funcionando: propuesta y total frente al presupuesto | ![Lista de piezas con botones de tienda](docs/capturas/02_piezas.png) **2.** Cada pieza con su porqué y sus botones de búsqueda |
| ![Consejos y modelo usado](docs/capturas/03_consejos.png) **3.** Consejos y modelo que respondió (aquí, el de reserva) | ![Búsqueda en PcComponentes](docs/capturas/04_busqueda_pccomponentes.webp) **4.** El botón abre la búsqueda real en PcComponentes |
| ![Propuesta descargada en txt](docs/capturas/05_descarga_txt.webp) **5.** La propuesta descargada en .txt, con los enlaces | ![Caso límite fuera de tema](docs/capturas/06_fuera_de_tema.png) **6.** Caso límite: una receta de tarta de queso, rechazada con amabilidad |

## Ejecutarla en tu ordenador

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # y pon tu GEMINI_API_KEY
streamlit run app.py
```

La clave se crea gratis en [AI Studio](https://aistudio.google.com/apikey). No hace falta tarjeta.
