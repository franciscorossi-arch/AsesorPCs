# AGENTS.md · AsesorPCs

> Este fichero lo leen los agentes de programación antes de tocar el código. Para Claude Code, `CLAUDE.md` contiene una sola línea: `Sigue las instrucciones de AGENTS.md`.

## Qué es este proyecto
Una app que ayuda a personas sin conocimientos técnicos a elegir un ordenador (una torre por piezas o un portátil) según el uso que le van a dar, su presupuesto y su país, con enlaces para buscar cada producto en tiendas de ese país.

## Cómo está hecho
- Python 3.12 o superior.
- Interfaz: Streamlit (ruta A, Streamlit Community Cloud).
- IA: API de Gemini con el SDK `google-genai`. Los modelos están en la lista `MODELOS` de `app.py`, en orden de preferencia; se pasa al siguiente ante un 429, 404 o 5xx, o si se supera `TIEMPO_MAXIMO_MS` (30 s). Ese orden sale de mediciones reales: no cambiarlo sin medir.
- Gemini devuelve JSON con la forma de las clases `Pieza` y `Recomendacion` (pydantic), usando `response_schema`.
- **Los enlaces de compra no los genera la IA**: se construyen en `enlaces_de_busqueda()` como búsquedas en las tiendas de `REGIONES`. La IA solo devuelve el texto de búsqueda (`busqueda`).
- Archivos: `app.py` (toda la app), `requirements.txt`, `README.md`, `especificacion.md` y este fichero.
- La especificación completa está en [especificacion.md](especificacion.md).

## Reglas
- La clave de la API va SIEMPRE en `st.secrets["GEMINI_API_KEY"]` (Settings → Secrets en Streamlit Cloud, `.streamlit/secrets.toml` en local, que está en `.gitignore`). Nunca en el código, en el README ni en el chat.
- Cada llamada a la API va dentro de `try/except` y muestra un mensaje claro y sin jerga (`mensaje_de_error()`). El detalle técnico va solo en un desplegable.
- Textos de la interfaz en español, sencillos, pensados para alguien sin conocimientos técnicos.
- Nunca pedir a la IA URLs ni mostrar enlaces inventados por ella.
- Los precios se presentan siempre como orientativos.
- Cambios pequeños: uno por petición. Al terminar, explica qué has cambiado y por qué.
- Si añades una librería, añádela también a `requirements.txt` y dilo.
- No uses datos personales reales. Para probar, inventa ejemplos.

## Cómo comprobar que funciona
- En local: `streamlit run app.py` con `.streamlit/secrets.toml` (copia de `.streamlit/secrets.toml.example`).
- Desplegado: haz push y revisa la app en Streamlit Cloud, en una ventana de incógnito.
- Casos de prueba (entrada → lo que esperamos):
  1. Torre, "jugar en 1080p y hacer streaming", 900 € en España → lista de piezas compatibles, total ≤ 945 €, botones de PcComponentes y Amazon.es.
  2. Portátil, "estudiante de diseño gráfico", 18.000 MXN en México → 2 o 3 portátiles con precio en MXN y botones de Mercado Libre y Amazon.com.mx.
  3. Torre, "jugar en 4K a todo", 300 € → aviso de que el presupuesto no llega, con el mínimo realista, y la mejor opción posible.
  4. "Dame una receta de paella" → la app dice amablemente que solo ayuda a elegir ordenadores, sin lista de piezas.
  5. Campo vacío o de menos de 10 caracteres → aviso, sin llamar a la IA.
  6. Cuota agotada (429) en todos los modelos → mensaje "se ha agotado el uso gratuito… espera un minuto".
  7. Ejemplo 🤖 IA local, torre de 1500 € → gráfica NVIDIA con 16 GB de VRAM o más, 32 GB de RAM y la frase de qué tamaño de modelo podrá ejecutar.

## Qué no hacer
- No borres ni reescribas el README sin preguntar.
- No cambies el modelo ni la arquitectura sin preguntar.
- No hagas push ni despliegues sin que yo lo haya revisado.
