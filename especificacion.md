# Especificación · AsesorPCs

## 1. Problema y usuario
- **Quién tiene el problema:** personas sin conocimientos de informática que necesitan comprar un ordenador para algo concreto (un estudiante de diseño, alguien que quiere jugar o hacer directos, una familia que compra un equipo para una persona mayor) y no saben qué es un procesador, una gráfica o cuánta RAM necesitan.
- **Cómo lo resuelve hoy:** pregunta al amigo "que sabe de ordenadores", lee foros y vídeos llenos de jerga, o se fía del dependiente de la tienda.
- **Qué le molesta de cómo lo hace hoy:** no entiende las recomendaciones, no sabe si las piezas son compatibles, acaba pagando de más por cosas que no usará o de menos y el equipo se le queda corto.
- **Qué parte resuelve la IA:** traduce una necesidad contada con sus palabras ("quiero editar vídeos y jugar algo") en una configuración concreta, compatible y ajustada al presupuesto, explicada sin jerga.
- **Qué queda fuera:** precios en tiempo real y stock (los precios son orientativos), la compra en sí y el montaje del equipo. Los enlaces son búsquedas en tiendas reales, no fichas de producto.

## 2. Qué hace el producto
1. Recoge el tipo de equipo (torre por piezas o portátil), el uso en lenguaje natural (con seis ejemplos de un clic: jugar, diseño, casa, oficina, programar e IA local), el presupuesto y el país.
2. Propone con Gemini una torre pieza a pieza o 2-3 portátiles, con precio orientativo, el motivo de cada elección, el total y consejos.
3. Da botones para buscar cada producto en tiendas del país elegido y permite descargar la propuesta en un .txt.

## 3. Entradas y salidas
| El usuario da… | La app devuelve… | Ejemplo |
|---|---|---|
| Tipo de equipo, uso en texto libre (10-600 caracteres), presupuesto, país y, si es torre, si incluir periféricos | Resumen, lista de piezas o portátiles con precio orientativo y motivo, total frente al presupuesto, avisos, consejos y botones de búsqueda por tienda | "Torre · jugar en 1080p y hacer streaming · 900 € · España" → Ryzen 5 + RTX de gama media, 16 GB DDR5, SSD 1 TB…, total ~890 €, botones de PcComponentes y Amazon.es |

Países y tiendas: España (PcComponentes, Amazon.es), México (Mercado Libre, Amazon.com.mx), Argentina, Colombia, Chile y Perú (Mercado Libre, Google Shopping), Estados Unidos (Amazon.com, Newegg).

## 4. La pieza de IA
- **Opción elegida:** API de un LLM, Gemini, con salida JSON estructurada (`response_schema`). Modelos en cadena: `gemini-3.5-flash` con razonamiento bajo como principal, y `gemini-3.1-flash-lite` y `gemini-3.5-flash-lite` de reserva. Cada intento tiene un límite de 30 s.
- **Por qué esos modelos:** se midieron con la clave gratuita el 04/11/2026. `gemini-3.8-flash` (el de la plantilla) devolvía 503 por saturación y llegó a tardar 68 s en fallar; `gemini-3.5-flash` respondía en unos 6 s y aprovechaba el presupuesto (1158-1200 € de 1200 €).
- **Por qué:** hace falta entender una necesidad escrita con las palabras del usuario y razonar sobre compatibilidad y presupuesto. Un modelo pequeño de clasificación no puede hacerlo, y un RAG no aporta nada porque no hay documentos propios. La salida estructurada permite pintar la propuesta como tarjetas y construir los enlaces en el código.
- **Instrucciones para el modelo (system prompt):** están en la constante `SYSTEM_PROMPT` de `app.py`. En resumen: asesor honesto que habla sin jerga, comprueba la compatibilidad (socket, tipo de RAM, potencia de la fuente, tamaño de la caja), se ajusta al presupuesto con un margen máximo del 5 %, avisa si el presupuesto no llega o sobra, usa modelos reales con precios orientativos en la moneda local, no inventa enlaces y rechaza amablemente lo que no trata de ordenadores. Para IA local, prioriza la VRAM de la gráfica (NVIDIA, 12 GB como mínimo, 16 GB o más para modelos de 14B), 32 GB de RAM o más y un SSD amplio, y dice qué tamaño de modelo podrá ejecutar.

## 5. Flujo del usuario
1. Entra y ve el formulario: torre o portátil, país, cuadro de uso con cuatro ejemplos, presupuesto.
2. Escribe para qué lo quiere (o pulsa un ejemplo), ajusta el presupuesto y pulsa "Recomiéndame un equipo".
3. Recibe la propuesta en tarjetas, el total frente a su presupuesto, consejos y botones para buscar cada producto, y puede descargarla.

## 6. Restricciones
- Coste cero: capa gratuita de la API de Gemini y Streamlit Community Cloud.
- La clave de la API va en secretos, nunca en el código.
- Sin datos personales: la app no pide nombre, correo ni ningún dato del usuario.
- Lenguaje sencillo, para alguien sin conocimientos técnicos.
- Los enlaces los genera el código, nunca la IA, para que no haya enlaces rotos o inventados.
- Respuestas guardadas en caché una hora para no gastar cuota con consultas repetidas.

## 7. Criterios de aceptación
| Entrada | Resultado esperado |
|---|---|
| Torre, "jugar en 1080p y hacer streaming", 900 €, España | Lista de piezas compatibles (CPU, placa, RAM, GPU, SSD, fuente, caja), total entre ~800 y 945 €, botones de PcComponentes y Amazon que abren una búsqueda con resultados |
| Portátil, "estudiante de diseño gráfico", 18.000 MXN, México | 2 o 3 portátiles en MXN ordenados por recomendación, botones de Mercado Libre y Amazon México |
| Torre, ejemplo 🤖 IA local, 1500 €, España | Gráfica NVIDIA con 16 GB de VRAM o más, 32 GB de RAM, SSD NVMe, y una frase sobre qué tamaño de modelo podrá mover (ej. 14B cuantizado a 4 bits) |
| Modelo principal saturado (503) o lento (más de 30 s) | Pasa solo al siguiente modelo; el usuario recibe la propuesta igualmente y el pie indica qué modelo respondió |
| Caso límite: torre, "jugar en 4K a todo", 300 € | Aviso de que el presupuesto no llega, con un mínimo realista, y la mejor opción posible para 300 € |
| Caso límite: "dame una receta de paella" | Mensaje amable de que solo ayuda a elegir ordenadores, sin lista de piezas |
| Caso límite: cuadro de uso vacío o de menos de 10 caracteres | Aviso de que cuente un poco más, sin llamar a la IA |
| Error: se acaba la cuota (429) | Prueba con los modelos de reserva y, si también fallan, muestra "se ha agotado el uso gratuito de la IA, espera un minuto" |
| Error: clave no válida (400/403) | Mensaje de que la clave no es válida, dirigido a quien gestiona la app |

## 8. Fuera de alcance (por ahora)
- Precios y stock en tiempo real (requeriría APIs de afiliados de las tiendas o búsqueda con Google).
- Cuentas de usuario para guardar propuestas (hoy se descargan en .txt).
- Ajustar la propuesta conversando ("cámbiame la gráfica por una más barata").
- Mejorar un ordenador que ya tienes.

## 9. Despliegue
- **Ruta:** A (Streamlit Community Cloud).
