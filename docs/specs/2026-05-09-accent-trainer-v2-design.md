# Accent Trainer v2 - Design Specification

**Date:** 2026-05-09  
**Status:** Approved  
**Author:** George Orellana + Claude

## Overview

Rediseño del Accent Trainer para convertirlo en un sistema efectivo de mejora de pronunciación RP británica para hablantes de español latinoamericano. El sistema incluye diagnóstico inicial, journey map gamificado, y feedback visual en tiempo real.

## Goals

1. **Diagnóstico real** — Identificar el perfil fonético del usuario basado en su español nativo
2. **Plan personalizado** — Journey map adaptado a las dificultades específicas del usuario
3. **Feedback visual** — Waveform comparativo en cada intento para motivar mejora
4. **Evaluación estricta** — Scores honestos que reflejen nivel real de pronunciación RP
5. **Persistencia** — Progreso guardado entre sesiones
6. **Variedad** — Pool amplio de frases para no repetir

## User Flows

### Flow A: Onboarding Completo
```
Nuevo usuario → Configura perfil (voz M/F) → Diagnóstico (~90 seg) 
→ Ve heatmap + gap analysis → Journey map personalizado → Practica
```

### Flow B: Gradual
```
Nuevo usuario → Configura perfil (voz M/F) → Empieza a practicar 
→ Sistema aprende tu perfil en 5-10 frases → Journey map se revela
```

El usuario elige A o B al inicio. Ambos flujos deben estar implementados.

## Components

### 1. Perfil de Usuario

**Datos a persistir:**
- `id`: UUID
- `created_at`: timestamp
- `voice_preference`: "male" | "female" (Ryan o Sonia de Azure TTS)
- `onboarding_mode`: "full" | "gradual"
- `diagnostic_completed`: boolean
- `phoneme_scores`: JSON con scores por fonema
- `current_level`: int
- `total_practice_time`: int (segundos)

### 2. Diagnóstico Inicial

**Estructura del diagnóstico:**

**Parte 1: Pares mínimos (~30 segundos)**
```
Repite estas palabras:
- think / sink
- ship / sheep  
- cat / cut
- path / pat
- three / tree
- this / dis
- water (escuchar R no-rótica)
- rather (escuchar R no-rótica)
```

**Parte 2: Párrafo diagnóstico (~45 segundos)**
```
Párrafo diseñado que contenga todos los fonemas problemáticos:
/θ/, /ð/, /ɪ/, /iː/, /æ/, /ʌ/, /ɑː/, R no-rótica, /əʊ/, /ə/
```

**Output del diagnóstico:**
- Heatmap visual de fonemas (verde/amarillo/rojo)
- Lista de áreas problemáticas ordenadas por severidad
- Journey map personalizado basado en resultados

### 3. Journey Map (Sistema de Niveles)

| Nivel | Familia | Fonemas Target | Threshold |
|-------|---------|----------------|-----------|
| 1 | Sonidos que no existen | /θ/, /ð/ | 75% |
| 2 | Vocales confusas | /ɪ/ vs /iː/, /æ/, /ʌ/ | 75% |
| 3 | La R británica | no-rótica, linking R | 75% |
| 4 | Ritmo y reducción | schwa /ə/, weak forms | 75% |
| 5 | Diptongos RP | /əʊ/, /eɪ/, /aɪ/ | 75% |
| 6 | Vocabulario británico | expresiones + pronunciación | 75% |

**Reglas del sistema:**
- Cada nivel tiene pool de 30+ frases
- Nunca repite la misma frase en una sesión
- El nivel se completa cuando el promedio en fonemas target >= 75%
- El promedio se calcula sobre TODAS las frases históricas, no solo la sesión
- Puede seguir practicando niveles completados
- Frases incluyen vocabulario británico auténtico (rubbish, lift, rather, etc.)

### 4. Pantalla de Práctica

```
┌─────────────────────────────────────────────────────────────┐
│  Nivel 1: Sonidos que no existen          Frase 3 de 30+   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  "I think the weather is rather dreadful today."            │
│                                                              │
│  /aɪ θɪŋk ðə ˈweðə ɪz ˈrɑːðə ˈdredf(ə)l təˈdeɪ/            │
│                                                              │
│  Nota: /θ/ en "think", /ð/ en "the", "weather", "rather"   │
│                                                              │
│  [♪ Escuchar RP]  [● Grabar]                                │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  COMPARACIÓN VISUAL                                          │
│  ┌─────────────────────┐  ┌─────────────────────┐           │
│  │ TU PRONUNCIACIÓN    │  │ REFERENCIA RP       │           │
│  │ ~~~∿∿∿~~~∿∿~~~     │  │ ~~~∿∿∿~~~∿∿~~~     │           │
│  │ /aɪ tɪŋk ðə.../    │  │ /aɪ θɪŋk ðə.../    │           │
│  │                     │  │                     │           │
│  └─────────────────────┘  └─────────────────────┘           │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  Score: 6.8/10                                               │
│                                                              │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐           │
│  │ I   │ │think│ │ the │ │weath│ │ is  │ │rath │           │
│  │ ✓   │ │ ⚠️  │ │ ✓   │ │ ❌  │ │ ✓   │ │ ⚠️  │           │
│  │ 95  │ │ 68  │ │ 88  │ │ 45  │ │ 92  │ │ 71  │           │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘           │
│                                                              │
│  💡 Coaching:                                                │
│  "En 'weather', tu /ð/ suena como /d/. La lengua debe      │
│   ir entre los dientes, no tocar el paladar."              │
│                                                              │
│  [↺ Reintentar]  [Siguiente frase →]                        │
└─────────────────────────────────────────────────────────────┘
```

### 5. Visualización Waveform

Cada intento muestra:
- **Waveform del usuario** — forma de onda de la grabación
- **Waveform de referencia** — forma de onda del TTS RP (Azure)
- **IPA de ambos** — transcripción fonética para comparar
- **Objetivo visual** — que el usuario intente igualar la forma de la onda

Implementación: Web Audio API + Canvas

### 6. Sistema de Scoring (Estricto)

| Score | Significado |
|-------|-------------|
| 9-10 | Pasarías por nativo británico |
| 7-8 | Acento extranjero muy bueno, totalmente comprensible |
| 5-6 | Se entiende, pero claramente no es RP |
| 3-4 | Problemas notables, algunos fonemas incorrectos |
| 1-2 | Difícil de entender para un británico |

**Calibración:**
- Threshold de aprobación por fonema: 75% (no 60%)
- Penalización extra en fonemas clave RP (/θ/, /ð/, R no-rótica)
- Comparación contra modelo RP, no "inglés general"

## Technical Architecture

### Stack

| Componente | Tecnología |
|------------|------------|
| Frontend | HTML/JS (migrable a React en v3) |
| Backend | FastAPI (Python) |
| Base de datos | SQLite (persistencia local) |
| Evaluación pronunciación | Azure Pronunciation Assessment |
| TTS referencia | Azure TTS Neural (en-GB-SoniaNeural, en-GB-RyanNeural) |
| Coaching IA | Cerebras (Llama 3.1 8B) |
| Visualización waveform | Web Audio API + Canvas |

### Database Schema (SQLite)

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    voice_preference TEXT DEFAULT 'female',
    onboarding_mode TEXT DEFAULT 'full',
    diagnostic_completed BOOLEAN DEFAULT FALSE
);

CREATE TABLE phoneme_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT REFERENCES users(id),
    phoneme TEXT NOT NULL,
    score REAL NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE practice_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT REFERENCES users(id),
    phrase_id INTEGER NOT NULL,
    level INTEGER NOT NULL,
    score REAL NOT NULL,
    word_scores JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE level_progress (
    user_id TEXT REFERENCES users(id),
    level INTEGER NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    avg_score REAL DEFAULT 0,
    phrases_practiced INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, level)
);
```

### API Endpoints

```
GET  /api/user                    → Obtener/crear perfil de usuario
PUT  /api/user                    → Actualizar preferencias
POST /api/diagnostic              → Enviar audio de diagnóstico
GET  /api/diagnostic/results      → Obtener resultados del diagnóstico
GET  /api/levels                  → Obtener journey map con progreso
GET  /api/level/{id}/phrases      → Obtener frases de un nivel (no repetir)
POST /api/assess                  → Evaluar pronunciación (ya existe)
GET  /api/tts/{phrase_id}         → Obtener audio TTS de referencia (Azure)
GET  /api/history                 → Historial de práctica
```

### File Structure

```
accent-trainer/
├── server.py                 → FastAPI app principal
├── database.py               → SQLite setup y queries
├── models.py                 → Pydantic models
├── routers/
│   ├── user.py              → Endpoints de usuario
│   ├── diagnostic.py        → Endpoints de diagnóstico
│   ├── practice.py          → Endpoints de práctica
│   └── tts.py               → Endpoints de TTS Azure
├── services/
│   ├── azure_speech.py      → Azure Pronunciation Assessment
│   ├── azure_tts.py         → Azure TTS Neural
│   ├── cerebras.py          → Coaching con Cerebras
│   └── scoring.py           → Lógica de scoring estricto
├── static/
│   ├── index.html           → App principal
│   ├── diagnostic.html      → Pantalla de diagnóstico
│   ├── profile.html         → Configuración de perfil
│   └── js/
│       ├── waveform.js      → Visualización de waveforms
│       ├── recorder.js      → Grabación de audio
│       └── app.js           → Lógica principal
├── data/
│   ├── phrases.json         → Pool de frases por nivel
│   ├── diagnostic.json      → Frases de diagnóstico
│   └── accent-trainer.db    → SQLite database
├── docs/
│   └── specs/
│       └── 2026-05-09-accent-trainer-v2-design.md
└── requirements.txt
```

## Content Requirements

### Frases por Nivel (mínimo 30 cada uno)

Las frases deben:
- Contener los fonemas target del nivel
- Usar vocabulario británico auténtico
- Ser situaciones comunicativas reales
- Variar en dificultad (easy/medium/hard)
- Incluir IPA y notas de pronunciación

### Vocabulario Británico a Incorporar

| Americano | Británico |
|-----------|-----------|
| trash | rubbish |
| elevator | lift |
| apartment | flat |
| subway | underground/tube |
| sidewalk | pavement |
| schedule (skedule) | schedule (shedule) |
| aluminum | aluminium |

### Expresiones RP

- "How do you do?"
- "I beg your pardon"
- "Frightfully sorry"
- "Rather good"
- "Quite right"
- "I suppose"
- "Lovely to meet you"

## Future Considerations (v3+)

- Migración frontend a React
- Sistema de XP y streaks
- Badges y achievements
- Leaderboards (opcional)
- Animaciones con Framer Motion
- Más visualizaciones con D3.js
- Deploy a producción (Vercel/Railway)

## Success Criteria

1. Usuario puede completar diagnóstico en < 2 minutos
2. Heatmap de fonemas claramente muestra áreas problemáticas
3. Waveform comparativo visible en cada intento
4. Progreso persiste entre sesiones
5. Nunca se repite la misma frase en una sesión
6. Scores reflejan nivel real de pronunciación RP (estrictos)
7. TTS siempre usa la voz seleccionada (consistente)
