# 🖥️ Asesor de PC

**Enlace a la app:** https://my-app-app-franr-dhwqcrubnuucc48fqc6zk8.streamlit.app/
**Autor/a:** [PENDIENTE: tu nombre]

## Pitch
1. Quien no sabe de informática y tiene que comprar un ordenador depende del amigo "que sabe", de foros llenos de jerga o del dependiente, y a menudo paga de más o se queda corto.
2. Asesor de PC le pregunta para qué lo quiere, cuánto puede gastar y dónde vive, y le propone una torre pieza a pieza o dos o tres portátiles, con el motivo de cada elección y botones para buscarlos en tiendas de su país.
3. La IA convierte una frase como "quiero editar vídeos y jugar algo" en una configuración compatible y ajustada al presupuesto, explicada sin jerga, algo que ningún filtro de tienda puede hacer.
4. [PENDIENTE tras la prueba: qué aprendí y qué cambié.]
5. [PENDIENTE: qué haría después, con un dato. Ej.: conectar precios reales mediante las APIs de afiliados de las tiendas, porque los precios de los componentes cambian a menudo de una semana a otra.]

## El problema
Comprar un ordenador sin saber de informática es confuso: las fichas están llenas de siglas (GPU, DDR5, NVMe) y no se sabe si las piezas son compatibles entre sí ni cuánto hace falta gastar para un uso concreto. Hoy se resuelve preguntando a alguien de confianza, leyendo foros o fiándose de la tienda. Merece la pena porque un ordenador es una compra cara que se usa durante años.

## Qué hace la app
1. Eliges **torre por piezas** o **portátil** y el **país** donde lo comprarás.
2. Escribes **para qué lo quieres** con tus palabras (o pulsas un ejemplo: jugar, diseño, casa, programar) y tu **presupuesto**.
3. Pulsas **Recomiéndame un equipo** y recibes la propuesta: cada pieza o portátil con su precio orientativo y por qué se ha elegido, el total frente a tu presupuesto, avisos si el presupuesto no llega o sobra, y consejos.
4. Cada producto tiene botones **🔎 Buscar en [tienda]** que abren la búsqueda en una tienda de tu país.
5. Puedes **descargar la propuesta** en un archivo de texto.

## La pieza de IA
- **Qué usa:** API de Gemini (`gemini-3.8-flash`, con `gemini-3.5-flash-lite` de reserva) con salida JSON estructurada.
- **Por qué esa opción:** hay que entender una necesidad escrita en lenguaje natural y razonar sobre compatibilidad y presupuesto, algo propio de un LLM. La salida estructurada permite mostrar la propuesta en tarjetas y que **los enlaces los genere el código** (búsquedas en tiendas reales), no la IA, para evitar enlaces inventados.
- **Qué pasa si falla:** si se agota la cuota (429) o el modelo está saturado, la app prueba automáticamente con el modelo de reserva. Si también falla, muestra un mensaje claro ("se ha agotado el uso gratuito, espera un minuto"). Los errores de clave, de modelo retirado, de red o de una respuesta que no se puede leer también tienen su propio mensaje. Las respuestas se guardan en caché una hora para no gastar cuota.
- **Dónde está la clave:** en los secretos de Streamlit Cloud (`GEMINI_API_KEY`), nunca en el código.

## Cómo la he construido
- **Herramientas:** Claude Code (agente de programación en el escritorio), Streamlit, SDK `google-genai`.
- **Fichero de contexto del agente:** [AGENTS.md](AGENTS.md) (y [CLAUDE.md](CLAUDE.md), que apunta a él). Especificación en [especificacion.md](especificacion.md).
- **Prompts clave:**
  1. *"Necesito que me des ideas de qué hacer en un programa en Python con IA (con key de Gemini, mejor en Streamlit) para un reto… una app que genere presupuestos de componentes para un ordenador de torre o portátiles, donde el usuario diga para qué lo quiere y la IA le dé los componentes ideales, con enlaces de compra en su región… Opina y dime cuál es mejor para acabarla en un día."*
  2. *"No quiero usar Colab para crear el código, lo quiero hacer contigo, pero sí quiero usar una key de Gemini con un modelo gratuito. Cuando quieras, empieza."*
  3. [PENDIENTE: añade aquí los prompts que uses para ajustar la app, copiados tal cual.]
- **Qué delegué al agente y qué revisé a mano:**
  - Delegué la estructura del proyecto, el código de `app.py`, el esquema JSON, el manejo de errores y los borradores de la documentación.
  - Decisión revisada: el agente propuso **no pedir enlaces a la IA**, porque los inventa, y generarlos como búsquedas en las tiendas. Comprobé en el navegador que las búsquedas de PcComponentes, Amazon y Mercado Libre abren resultados.
  - El agente hizo pruebas automáticas con Gemini simulado (caso normal, 429 en los dos modelos, campo vacío, falta de clave) antes de probar con la clave real.
  - [PENDIENTE: lo que revises tú a mano, ej. que las piezas propuestas son compatibles y los precios razonables.]

## Prueba y mejora
| Quién la probó | Qué probó | Qué pasó | Qué cambié |
|---|---|---|---|
| Yo, como usuario (con el agente) | Torre para jugar en 1080p y hacer directos, 900 € en España | Propuesta compatible, pero de solo 665 €: le sobraban 235 € que podían ir a una gráfica mejor | Cambié la regla 6 del prompt para que aproveche el 85-100 % del presupuesto cuando mejora el uso; la propuesta subió a 710 €. También corregí el formato de los precios en México (18,000 en vez de 18.000) |
| Yo, como usuario | Presupuesto imposible (4K por 300 €) y una pregunta fuera de tema (receta de paella) | Avisó de que hacen falta unos 2.000 € y dio la mejor opción posible; la paella la rechazó amablemente | Nada, funciona como dice la especificación |
| [PENDIENTE: un compañero] | | | |

## Ejecutar en local (opcional)
```bash
pip install -r requirements.txt
# Copia .streamlit/secrets.toml.example a .streamlit/secrets.toml y pon tu clave
streamlit run app.py
```

## Capturas
[PENDIENTE: la app funcionando, la app ante un caso límite, un momento del trabajo con la IA y la prueba. Sin ninguna clave a la vista.]
