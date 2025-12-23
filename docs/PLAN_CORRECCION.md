# Plan de Corrección: Alineación con Guidelines PromptBase

## Referencias Base

Este plan se basa en las siguientes fuentes:
- **`docs/guidelines.md`** - Guidelines oficiales de PromptBase
- **`docs/ejemplos/*.md`** - Análisis de prompts exitosos
- **`docs/AUDITORIA_COHERENCIA.md`** - Auditoría del sistema actual

---

## Prioridad 1: Correcciones Críticas

### 1.1 Flexibilizar Requisito de Variables

**📖 Justificación:**

| Referencia | Contenido |
|------------|-----------|
| `docs/guidelines.md` §2.2 | "A prompt template contains areas within the prompt in [square brackets]" - No especifica cantidad |
| `docs/guidelines.md` §3.4 | "Usually this is an easy fix by adding editable variables" - Implica flexibilidad |
| `docs/ejemplos/CompleteStartupPlan.md` | Solo 1 variable `[industry/sector]`, 576 ventas |
| `docs/ejemplos/YouTubeCompleteBundle.md` | 3 variables, 1.5k ventas |
| `docs/ejemplos/Youtube Unique VideoIdeasGenerators.md` | 4 variables |

**Conclusión:** Los prompts exitosos tienen entre 1-4 variables. No hay requisito de "exactamente 4".

**Archivo:** `prompts.yaml`
**Sección:** `reverse_engineer_image_prompt`

**Cambio requerido:**
```yaml
# ANTES (muy restrictivo):
- **EXACTLY 4 VARIABLES - NO EXCEPTIONS**

# DESPUÉS (flexible, basado en evidencia):
- **VARIABLE COUNT**: Include 1-5 variables based on the image complexity.
- **MINIMUM**: At least 1 variable (usually [SUBJECT]) to make it templatable.
- **RECOMMENDED**: 2-4 variables for optimal balance of flexibility and usability.
- **SUGGESTED VARIABLES** (use as needed):
  1. [SUBJECT] - The main element (almost always needed)
  2. [STYLE_MODIFIER] - If style can vary meaningfully
  3. [MOOD/ATMOSPHERE] - If emotional tone is key
  4. [COLOR_SCHEME] - If colors are distinctive
  5. [SETTING/BACKGROUND] - If environment matters
```

**Archivo:** `cli.py`
**Función:** `post_process_for_quick_copy`

**Cambio requerido:**
```python
# ANTES:
if len(variables) < 4:
    click.echo(f"⚠️ Warning: Generated template has only {len(variables)} variables. 
               PromptBase requires minimum 4.", err=True)

# DESPUÉS (basado en guidelines §2.2):
if len(variables) < 1:
    click.echo(f"❌ Error: Template has no variables. PromptBase requires at least one [VARIABLE] for templating.", err=True)
elif len(variables) > 5:
    click.echo(f"⚠️ Warning: Template has {len(variables)} variables. Consider consolidating to 2-4 for better usability.", err=True)
```

---

### 1.2 Añadir Validación "Regla de 3 Ideas"

**📖 Justificación:**

| Referencia | Contenido |
|------------|-----------|
| `docs/guidelines.md` §3.4 | "A general rule of thumb is a prompt is too niche for PromptBase if it is trying to combine more than 3 ideas, or has 3 ideas but one of those ideas is too niche." |
| `docs/guidelines.md` §3.4 | Ejemplo: "3D doctor animals with moustaches" = 4 ideas, 2 niche → RECHAZADO |
| `docs/guidelines.md` §3.4 | Ejemplo mejorado: "3D animals with jobs" = 3 ideas, todas broad → APROBADO |
| `docs/guidelines.md` §3.4.1 | "We are trying to avoid the scenario where users continually submit the same prompts with small alterations" |

**Archivo:** `src/api_handler.py`
**Nueva función:**

```python
def validate_prompt_specificity(template: str, topic: str) -> dict:
    """
    Validates prompt against the "3 ideas rule" from PromptBase guidelines.
    
    Reference: docs/guidelines.md §3.4
    
    Rule: A prompt is too niche if it combines more than 3 ideas,
    or has 3 ideas but one is too niche.
    
    Examples from guidelines:
    - BAD: "3D doctor animals with moustaches" (4 ideas, 2 niche)
    - BETTER: "3D doctor animals" (3 ideas, 1 niche) - still too niche
    - GOOD: "3D animals with jobs" (3 ideas, all broad)
    """
    # Ver implementación completa en docs/AUDITORIA_COHERENCIA.md
```

---

### 1.3 Añadir Validación de Consistencia de Ejemplos

**📖 Justificación:**

| Referencia | Contenido |
|------------|-----------|
| `docs/guidelines.md` §3.5 | "If your prompt generated food imagery, but in one output the food was a 3d render, in one output it was a cartoon, and in the other a photograph, the style here is too inconsistent." |
| `docs/guidelines.md` §3.5 | "We are ideally looking for consistent styled outputs where the subject can be changed but remains in a consistent style." |
| `docs/guidelines.md` §3.5.1 | "We decline these prompts because it often indicates that the prompt is unstable." |

**Archivo:** `src/api_handler.py`
**Nueva función:** `validate_style_consistency()`

---

### 1.4 Añadir Validación de Diversidad de Ejemplos

**📖 Justificación:**

| Referencia | Contenido |
|------------|-----------|
| `docs/guidelines.md` §3.9 | "We will decline prompts if the example outputs submitted alongside the prompt are too similar." |
| `docs/guidelines.md` §3.9 | "For example if your prompt is 'adorable watercolor animals', but alongside your prompt you submit 4 images of sheep, and 5 images of foxes, then we would decline this prompt." |
| `docs/guidelines.md` §3.9.1 | "To assess the quality of your prompt, we need to be able to see that the prompt is generalisable to create outputs in the same style but with different subjects." |

**Archivo:** `src/api_handler.py`
**Nueva función:** `validate_example_diversity()`

---

## Prioridad 2: Mejoras de Calidad

### 2.1 Añadir Validación de Idioma

**📖 Justificación:**

| Referencia | Contenido |
|------------|-----------|
| `docs/guidelines.md` §3.12 | "We are currently only accepting prompts written in English." |
| `docs/guidelines.md` §3.12.1 | "Most models are optimized for use in English" |
| `docs/guidelines.md` §3.12.1 | "The PromptBase site is only in English (currently)" |

**Archivo:** `src/api_handler.py`
**Nueva función:** `validate_english_content()`

---

### 2.2 Añadir Validación de Simplicidad

**📖 Justificación:**

| Referencia | Contenido |
|------------|-----------|
| `docs/guidelines.md` §3.11 | "If we believe that a user would be able to quickly re-produce outputs in the same way just by looking at the title or example outputs of your prompt, then we will decline it." |
| `docs/guidelines.md` §3.11 | Ejemplo: prompt "Dog videos" con template "a video of a [dog]" = RECHAZADO |
| `docs/guidelines.md` §3.11 | "short prompts (word-count wise) do not always mean simple prompts" |

**Archivo:** `src/api_handler.py`
**Nueva función:** `validate_prompt_complexity()`

---

### 2.3 Mejorar Output para Prompts de Texto

**📖 Justificación:**

| Referencia | Contenido |
|------------|-----------|
| `docs/ejemplos/YouTubeCompleteBundle.md` | Output incluye: SEO tags (30), hashtags (10), timestamps, social posts, short-form script |
| `docs/ejemplos/Top1ArticleGenerator.md` | Output incluye: Outline, 10 keywords, internal/external links, FAQs, tips de optimización |
| `docs/ejemplos/SEO OptimizedBlogArticlesWriting.md` | Output incluye: Meta-title, meta-description, slug, excerpt, keywords, links, key phrases |

**Conclusión:** Los prompts de texto exitosos generan múltiples entregables con SEO integrado.

**Archivo:** `prompts.yaml`
**Sección:** `text_meta_prompt`

**Añadir al output:**
```yaml
# Basado en análisis de docs/ejemplos/

OUTPUT REQUIREMENTS (UPDATED):
  # NUEVOS - Basados en ejemplos exitosos
  - "seo_package": {
      "keywords": List of 10 relevant SEO keywords,
      "hashtags": List of 10 hashtags for social sharing,
      "meta_description": 155-160 char description for SEO
    }
  - "suggested_faqs": List of 3-5 FAQ questions
  - "output_structure": List of sections the generated text should include
```

---

## Prioridad 3: Actualizar Sistema de Evaluación

**📖 Justificación:**

El sistema de evaluación actual (`agent_quality_evaluation` en `prompts.yaml`) no cubre los criterios de rechazo documentados en las guidelines.

| Criterio Guidelines | Sección | Actualmente Evaluado |
|--------------------|---------|---------------------|
| Too specific | §3.4 | ❌ No |
| Inconsistent style | §3.5 | ❌ No |
| Example outputs too similar | §3.9 | ❌ No |
| Prompt too simple | §3.11 | ❌ No |
| Non-English | §3.12 | ❌ No |

**Archivo:** `prompts.yaml`
**Sección:** `agent_quality_evaluation`

**Añadir criterios:**
```yaml
  6. SPECIFICITY CHECK [10 points]
     Reference: docs/guidelines.md §3.4
     
  7. EXAMPLE DIVERSITY [10 points]
     Reference: docs/guidelines.md §3.9
     
  8. STYLE CONSISTENCY [10 points]
     Reference: docs/guidelines.md §3.5
     
  9. COMPLEXITY CHECK [5 points]
     Reference: docs/guidelines.md §3.11
  
  10. LANGUAGE CHECK [5 points]
      Reference: docs/guidelines.md §3.12
```

---

## Resumen de Referencias

| Corrección | Referencia Principal | Sección Guidelines |
|------------|---------------------|-------------------|
| 1.1 Flexibilizar variables | `docs/guidelines.md` | §2.2, §3.4 |
| 1.2 Validación 3 ideas | `docs/guidelines.md` | §3.4, §3.4.1 |
| 1.3 Validación consistencia | `docs/guidelines.md` | §3.5, §3.5.1 |
| 1.4 Validación diversidad | `docs/guidelines.md` | §3.9, §3.9.1 |
| 2.1 Validación idioma | `docs/guidelines.md` | §3.12, §3.12.1 |
| 2.2 Validación simplicidad | `docs/guidelines.md` | §3.11 |
| 2.3 SEO para texto | `docs/ejemplos/*.md` | Análisis de ejemplos |
| 3.1 Actualizar evaluación | `docs/guidelines.md` | §3.4-§3.12 |

---

## Orden de Implementación

```
Semana 1 (Crítico):
├── 1.1 Flexibilizar variables
│   └── Ref: §2.2, §3.4, ejemplos analizados
├── 1.2 Validación 3 ideas
│   └── Ref: §3.4
├── 1.3 Validación consistencia
│   └── Ref: §3.5
└── 1.4 Validación diversidad
    └── Ref: §3.9

Semana 2 (Mejoras):
├── 2.1 Validación idioma
│   └── Ref: §3.12
├── 2.2 Validación simplicidad
│   └── Ref: §3.11
└── 2.3 SEO para texto
    └── Ref: ejemplos analizados

Semana 3 (Integración):
├── 3.1 Actualizar evaluación
│   └── Ref: §3.4-§3.12
└── Testing y ajustes
```

---

## Métricas de Éxito

| Métrica | Situación Actual | Objetivo Post-Corrección |
|---------|-----------------|-------------------------|
| Validaciones de guidelines cubiertas | ~30% | >90% |
| Criterios de rechazo detectados | 2/10 | 8/10 |
| Prompts rechazados por "too specific" | No detectado | Detectado pre-envío |
| Prompts rechazados por "inconsistent" | No detectado | Detectado pre-envío |
