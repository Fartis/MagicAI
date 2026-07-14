# Tactician / Estratega

`Tactician` es el nombre interno del primer perfil estratégico de MagicAI. En la
interfaz se muestra como **Estratega**. Sustituye el nombre provisional
`Deck Master`, porque su responsabilidad no se limita a construir o valorar mazos:
también revisa líneas de juego, riesgos, sinergias y posibles combos.

## Jerarquía de autoridad

```text
Oracle + Comprehensive Rules + rulings
                  │
                  ▼
                Juez
        autoridad factual única
                  │
         paquete factual validado
                  ▼
        Tactician / Estratega
       interpretación estratégica
```

El Estratega:

- no consulta Scryfall directamente;
- no consulta Comprehensive Rules directamente;
- no puede corregir Oracle ni una regla;
- puede impugnar una conclusión provisional si contradice la evidencia que ya
  recuperó el Juez;
- devuelve la decisión factual al Juez para la respuesta final;
- utiliza el paquete factual del Juez para detectar roles, sinergias, riesgos y
  líneas de juego.

## Protocolo de revisión

Las respuestas generadas por LLM pasan por dos revisiones independientes:

1. El validador factual tradicional.
2. El revisor del Estratega, que comprueba relaciones causales estructuradas.

Ejemplo:

```text
sacrificar un permanente
→ estaba en el campo de batalla
→ va al cementerio
→ si era criatura, muere
→ comprobar Undying y otras habilidades de muerte
```

Si una respuesta contradice esa cadena, el Estratega devuelve un challenge
estructurado. El Juez puede reconstruir una respuesta desde las fuentes, pero la
autoridad final sigue siendo `judge`.

## Primera cobertura estratégica

Tactician v0.1 reconoce de forma determinista roles básicos derivados del Oracle que
le entrega el Juez:

- aceleración de maná;
- motores de sacrificio;
- valor al morir;
- recursión;
- ventaja de cartas;
- removal;
- generación de fichas;
- protección.

También distingue una sinergia de sacrificio de un combo infinito. Por ejemplo,
Young Wolf y Carrion Feeder generan valor, pero no forman un bucle infinito por sí
solos porque Undying devuelve Young Wolf con un contador +1/+1.

## API

### Juez

```http
POST /ask
```

### Estratega

```http
POST /tactician/ask
```

El cuerpo es el mismo:

```json
{
  "question": "¿Young Wolf y Carrion Feeder forman un combo?",
  "session_id": null
}
```

La respuesta estratégica conserva `cards`, `rules`, `rulings` y las versiones de
fuentes del Juez, y añade:

```json
{
  "authority": "tactician",
  "origin": "tactician_strategy",
  "synergies": [],
  "risks": [],
  "authority_trace": [
    "judge:factual_evidence",
    "tactician:strategic_interpretation"
  ],
  "judge_result": {}
}
```

## Límites de v0.1

- No analiza todavía una lista completa de 100 cartas.
- No calcula probabilidades de robo ni consistencia.
- No consulta metajuego ni estadísticas externas.
- No genera líneas complejas mediante LLM.
- Los patrones estratégicos iniciales son deterministas y auditables.

Las siguientes versiones añadirán estado de partida, secuencias de acciones,
mulligans, paquetes de sinergia y demostración formal de ciclos infinitos.
