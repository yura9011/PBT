# PBT - Agentic PromptBase Generator

## Qué Es
Herramienta para crear prompt templates listos para vender en PromptBase.
Usa agentes de Gemini para generar, evaluar y refinar prompts.

## Estructura del Proyecto
```
PBT/
├── src/                 # Código principal
│   ├── api_handler.py   # 20 funciones de agentes IA
│   ├── ui.py            # Componentes Streamlit
│   ├── utils.py         # DB + utilidades
│   ├── quality_enhancers.py  # Post-procesamiento
│   └── run_agentic_workflow.py  # Orquestación
├── published/           # 71 prompts publicados (JSON)
├── docs/                # Documentación
├── .agent/              # Instrucciones para agentes (este archivo)
└── main.py              # Entry point
```

## Cómo Ejecutar

### UI Interactiva (Streamlit)
```bash
streamlit run main.py
```

### CLI (en desarrollo)
```bash
python cli.py reverse --image "imagen.png"
python cli.py create --topic "tema" --style "estilo"
```

## Funciones Principales

| Función | Ubicación | Propósito |
|---------|-----------|-----------|
| `agent_reverse_engineer_from_image` | `src/api_handler.py` | Imagen → Template |
| `agent_generate_initial_prompt` | `src/api_handler.py` | Tema → Template |
| `agent_analyze_trends` | `src/api_handler.py` | Análisis de mercado |
| `enhance_package` | `src/quality_enhancers.py` | Post-procesamiento |

## Workflows Comunes

### 1. Ingeniería Inversa de Imagen
1. Subir imagen en tab "🖼️ Image to Prompt"
2. Click "✨ Reverse Engineer from Image"
3. Revisar resultado en tab "📦 Results"
4. Guardar en Library si aprobado

### 2. Crear Prompt desde Idea
1. Tab "✨ Generation Mode"
2. Llenar: Topic, Content Type, Platform, Style
3. Click "🚀 Generate Full Prompt Package"
4. Revisar y exportar

### 3. Analizar Tendencias
1. Tab "📈 Trend Engine"
2. Pegar texto de análisis de mercado
3. Click "🔮 Analyze Trends"
4. Click "✨ Create This" en sugerencias

## Variables de Entorno
- `GEMINI_API_KEY`: Clave API de Google Gemini (se ingresa en UI)

## Archivos Importantes
- `prompts.yaml`: Meta-prompts para los agentes IA
- `config.yaml`: Configuración de modelos
- `prompt_library.db`: Base de datos SQLite con prompts guardados

## Para Agregar Features
1. Funciones de agentes van en `src/api_handler.py`
2. UI va en `src/ui.py`
3. Prompts/instrucciones van en `prompts.yaml`
4. Tests van en `tests/`

## Para Arreglar Bugs
1. Revisar logs en consola (usa `logging`)
2. `src/run_agentic_workflow.py` tiene el flujo principal
3. `src/utils.py` tiene operaciones de DB
