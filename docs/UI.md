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

## Alcance del Sprint 11.0

- conversación con sesiones del Juez;
- historial local en el navegador;
- creación de una nueva conversación;
- estados `answered`, `needs_clarification`, `strategy_required`, `insufficient_evidence` y `false_premise`;
- panel de cartas, reglas, rulings, supuestos y advertencias;
- origen, confianza, schema, versiones y salud de fuentes;
- indicador de disponibilidad de fuentes y Ollama;
- errores API estructurados;
- diseño responsive y navegación por teclado.

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

La sesión y el historial visible se guardan en `localStorage` del navegador. El servidor sigue manteniendo las conversaciones en memoria. Reiniciar el proceso FastAPI invalida las sesiones del servidor, aunque el navegador conserve el historial visual.

La primera beta no implementa cuentas, sincronización, base de datos de conversaciones ni acceso remoto seguro.

## Seguridad de presentación

El frontend construye nodos DOM mediante `textContent`; no inserta las respuestas del Juez mediante `innerHTML`. De esta forma, Oracle, rulings, preguntas y respuestas se muestran como texto y no como código ejecutable.

## Próximos bloques de UI

- gestión visual de sesiones persistentes;
- selección de candidatos en respuestas de desambiguación;
- búsqueda y copia de evidencia;
- preferencias de apariencia y densidad;
- exportación de conversaciones;
- soporte posterior para Deck Master y Deckbuilder sobre la misma shell modular.
