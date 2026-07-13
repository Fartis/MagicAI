# MagicAI Judge UI beta

La primera UI de MagicAI es una aplicación web local servida por el mismo proceso FastAPI que expone `JudgeResult`.

## Abrir la interfaz

```bash
python -m uvicorn magicai.api:app --reload
```

Después abre:

```text
http://127.0.0.1:8000/ui
```

No necesita Node, npm, un servidor web adicional ni recursos externos.

## Alcance implementado

### Sprint 11.0 — base funcional

- conversación con sesiones del Juez;
- historial local en el navegador;
- creación de una nueva conversación;
- estados `answered`, `needs_clarification`, `strategy_required`, `insufficient_evidence` y `false_premise`;
- panel de cartas, reglas, rulings, supuestos y advertencias;
- origen, confianza, schema, versiones y salud de fuentes;
- indicador de disponibilidad de fuentes y Ollama;
- errores API estructurados;
- diseño responsive y navegación por teclado.

### Sprint 11.1a — resiliencia y accesibilidad

- cancelación explícita de consultas mediante `AbortController`;
- timeout de seguridad de tres minutos para `/ask`;
- descarte de respuestas obsoletas mediante identificador de petición;
- bloqueo de sondeos `/health` solapados y timeout auxiliar;
- validación del estado recuperado de `localStorage`;
- aviso único cuando el navegador impide persistir el historial;
- helpers seguros para leer, escribir y eliminar almacenamiento local;
- allowlist HTTPS para enlaces de Scryfall;
- `aria-busy`, región de estado y control de cancelación accesible.

La cancelación detiene la espera del navegador. El backend o el proceso de Ollama pueden necesitar terminar internamente el trabajo ya iniciado, dependiendo de su soporte de cancelación.

### Sprint 11.1b — usabilidad y presentación

- botones interactivos para seleccionar cartas cuando `JudgeResult.status=needs_clarification`;
- persistencia local de los candidatos de desambiguación;
- copia de la respuesta en texto plano;
- copia de respuesta y evidencia en un resumen legible;
- exportación del último `JudgeResult` como JSON;
- apertura automática de las secciones que contienen evidencia;
- jerarquía visual diferenciada para Oracle, reglas, rulings, supuestos y advertencias;
- presentación de las consultas de recuperación dentro de los detalles técnicos;
- controles responsive sin introducir frameworks frontend.

## Arquitectura

```text
Browser
  │
  ├── GET /ui
  ├── GET /ui/assets/*
  ├── GET /meta
  ├── GET /health
  └── POST /ask
          │
          ▼
       JudgeResult 1.0
```

La UI no interpreta reglas ni modifica la respuesta del Juez. Únicamente presenta el contrato estructurado de la API.

## Persistencia

La UI conserva una copia de recuperación rápida en `localStorage`, pero la autoridad de persistencia es ahora una base SQLite local gestionada por FastAPI. Las conversaciones pueden reabrirse después de reiniciar el servidor y el panel de historial permite renombrarlas o eliminarlas. Si el navegador bloquea `localStorage`, el historial del servidor sigue disponible.

La base se guarda por defecto en `~/.local/share/magicai/conversations.sqlite3` en Linux/WSL. Puede cambiarse con `MAGICAI_CONVERSATION_DB`.

La primera beta no implementa cuentas, sincronización, base de datos de conversaciones ni acceso remoto seguro.

## Seguridad de presentación

El frontend construye nodos DOM mediante `textContent`; no inserta las respuestas del Juez mediante `innerHTML`. De esta forma, Oracle, rulings, preguntas y respuestas se muestran como texto y no como código ejecutable.

## Próximos bloques de UI

- pulido visual guiado por uso real y captura para el README;
- pruebas manuales ampliadas de accesibilidad;
- filtros, búsqueda y orden avanzado del historial persistente;
- búsqueda y copia de evidencia;
- preferencias de apariencia y densidad;
- exportación de conversaciones;
- soporte posterior para Deck Master y Deckbuilder sobre la misma shell modular.
