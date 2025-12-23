# Auditoría de Coherencia: Script vs Guidelines de PromptBase

## Resumen Ejecutivo

Este documento analiza si el funcionamiento actual del sistema PBT se ajusta a las guidelines oficiales de PromptBase y la documentación de reverse engineering actualizada.

**Fuentes de Referencia:**
- `docs/guidelines.md` - Guidelines oficiales de PromptBase
- `docs/ejemplos/*.md` - Ejemplos de prompts exitosos analizados
- `prompts.yaml` - Configuración actual del sistema
- `cli.py`, `src/api_handler.py` - Código fuente actual

---

## 1. Análisis de Variables

### Requisito de Guidelines

**📖 Referencia: `docs/guidelines.md` - Sección 2.2 "Prompt templates"**
```
"A prompt template contains areas within the prompt in [square brackets] 
that a buyer can edit to adapt your prompt for their own needs."

Ejemplo dado:
"Very tiny [KEYWORD] that looks like the iOS emoji..."
```

**📖 Referencia: `docs/guidelines.md` - Sección 3.4 "Too specific"**
```
"Usually this is an easy fix by adding editable variables to your prompt 
in [square brackets]."
```

**NOTA:** Las guidelines NO especifican un número mínimo o máximo de variables. Solo requieren que el prompt sea "templatable".

**📖 Referencia: `docs/ejemplos/` - Análisis de prompts exitosos**
| Prompt | Variables | Ventas |
|--------|-----------|--------|
| YouTube Complete Bundle | 3 (`[video title]`, `[niche]`, `[other video]`) | 1.5k |
| Top 1 Article Generator | 3 (`[title]`, `[niche]`, `[tone]`) | 1.5k |
| Complete Startup Plan | 1 (`[industry/sector]`) | 576 |
| YouTube Ideas Generator | 4 (`[niche]`, `[audience]`, `[format]`, `[goal]`) | 3 |

### Estado Actual del Script

**En `prompts.yaml` (reverse_engineer_image_prompt):**
```yaml
- **EXACTLY 4 VARIABLES - NO EXCEPTIONS**: The template MUST contain EXACTLY 4 variables.
- **REQUIRED VARIABLES**: 
  1. [SUBJECT]
  2. [MOOD]
  3. [COLOR_SCHEME]
  4. [SETTING]
```

**En `cli.py` (post_process_for_quick_copy):**
```python
if len(variables) < 4:
    click.echo(f"⚠️ Warning: Generated template has only {len(variables)} variables. 
               PromptBase requires minimum 4.", err=True)
```

### ❌ INCONSISTENCIA DETECTADA

| Aspecto | Guidelines | Script | Estado |
|---------|-----------|--------|--------|
| Mínimo variables | No especifica (solo "templatable") | Fuerza exactamente 4 | ⚠️ Muy restrictivo |
| Máximo variables | No especifica | Exactamente 4 | ⚠️ Inflexible |
| Evidencia ejemplos | 1-4 variables en top sellers | Fuerza 4 | ⚠️ No alineado |

**Problema:** Las guidelines de PromptBase NO requieren exactamente 4 variables. Los ejemplos exitosos muestran que prompts con 1-4 variables pueden ser muy exitosos (Complete Startup Plan tiene solo 1 variable y 576 ventas).

**Recomendación:** Cambiar de "EXACTLY 4" a "1-5 variables según necesidad" para mayor flexibilidad.

---

## 2. Análisis de Especificidad (Regla de 3 Ideas)

### Requisito de Guidelines

**📖 Referencia: `docs/guidelines.md` - Sección 3.4 "Too specific"**
```
"A general rule of thumb is a prompt is too niche for PromptBase if it is 
trying to combine more than 3 ideas, or has 3 ideas but one of those ideas 
is too niche.

In '3D doctor animals with moustaches' the prompt explores 4 ideas, with 
two of them being too niche (3d: broad, animals: broad, doctors: niche, 
moustaches: niche)

Changing the prompt to '3D doctor animals with a variable to add moustaches' 
would be an improvement, but still too niche (has 3 ideas: 3d: broad, 
animals: broad, doctors: niche).

However, an even better prompt would be '3D animals with jobs', allowing 
the use case of the prompt to be broadened even further (it has 3 ideas: 
3d: broad, animals: broad, jobs: broad)."
```

**📖 Referencia: `docs/guidelines.md` - Sección 3.4.1 "Why are these prompts declined?"**
```
"We are trying to avoid the scenario where users continually submit the 
same prompts with small alterations... For example the prompts 'green haired 
wizards', 'blue haired wizards' and 'red haired wizards', would be much 
better as a single 'Wizards' prompt where the [hair] variable is changeable."
```

### Estado Actual del Script

**En `prompts.yaml` y `api_handler.py`:**
- ❌ No existe validación de la "regla de 3 ideas"
- ❌ No se detectan combinaciones demasiado específicas
- ❌ No hay sugerencias para generalizar prompts niche

### ❌ GAP CRÍTICO

| Aspecto | Guidelines | Script | Estado |
|---------|-----------|--------|--------|
| Regla de 3 ideas | Explícitamente documentada | No implementada | ❌ FALTA |
| Detección de niche | Requerida para aprobación | No existe | ❌ FALTA |
| Sugerencias de generalización | Documentadas con ejemplos | No implementadas | ❌ FALTA |

**Problema:** Este es un criterio de rechazo explícito en PromptBase que el sistema no valida.

---

## 3. Análisis de Consistencia de Estilo

### Requisito de Guidelines

**📖 Referencia: `docs/guidelines.md` - Sección 3.5 "Inconsistent style"**
```
"If your prompt was declined for having an inconsistent style, this means 
that either the style or the subject of the output changes too much for 
the prompt to be usable.

For example, if your prompt generated food imagery, but in one output the 
food was a 3d render, in one output it was a cartoon, and in the other a 
photograph, the style here is too inconsistent.

We are ideally looking for consistent styled outputs where the subject 
can be changed but remains in a consistent style."
```

**📖 Referencia: `docs/guidelines.md` - Sección 3.5.1**
```
"We decline these prompts because it often indicates that the prompt is 
unstable. As someone will be buying and using your prompt, they need to 
be confident that they can generate outputs in the same way as what they 
see in the examples before they hit purchase."
```

### Estado Actual del Script

**En `prompts.yaml` (agent_quality_evaluation):**
- ❌ No evalúa consistencia de estilo entre ejemplos
- ❌ No detecta variaciones de medio (3D vs cartoon vs foto)
- ❌ No valida estabilidad del prompt

### ❌ GAP CRÍTICO

| Aspecto | Guidelines | Script | Estado |
|---------|-----------|--------|--------|
| Consistencia de estilo | Criterio de rechazo | No evaluado | ❌ FALTA |
| Estabilidad del prompt | Requerida | No validada | ❌ FALTA |

---

## 4. Análisis de Diversidad de Ejemplos

### Requisito de Guidelines

**📖 Referencia: `docs/guidelines.md` - Sección 3.9 "Example outputs too similar"**
```
"We will decline prompts if the example outputs submitted alongside the 
prompt are too similar.

For example if your prompt is 'adorable watercolor animals', but alongside 
your prompt you submit 4 images of sheep, and 5 images of foxes, then we 
would decline this prompt."
```

**📖 Referencia: `docs/guidelines.md` - Sección 3.9.1**
```
"1. As a buyer of a prompt, you want to have a good sense of what the 
prompt can do. If all the example outputs on the prompt's store page are 
the same, you are less likely to purchase the prompt.

2. To assess the quality of your prompt, we need to be able to see that 
the prompt is generalisable to create outputs in the same style but with 
different subjects."
```

**📖 Referencia: `docs/ejemplos/` - Patrones de ejemplos exitosos**
- YouTube Complete Bundle: Ejemplos con diferentes animales/temas
- Top 1 Article Generator: 4 ejemplos con diferentes industrias
- Los prompts exitosos muestran 4-9 ejemplos variados

### Estado Actual del Script

**En `api_handler.py` (agent_generate_examples):**
```python
num_examples: int = 9
# Genera ejemplos pero no valida diversidad
```

### ⚠️ GAP PARCIAL

| Aspecto | Guidelines | Script | Estado |
|---------|-----------|--------|--------|
| Cantidad de ejemplos | 4-9 requeridos | 9 generados | ✅ OK |
| Diversidad de sujetos | Explícitamente requerida | No validada | ❌ FALTA |
| Validación de similitud | Criterio de rechazo | No implementada | ❌ FALTA |

---

## 5. Análisis de Simplicidad/Adivinabilidad

### Requisito de Guidelines

**📖 Referencia: `docs/guidelines.md` - Sección 3.11 "Prompt too simple / guessable"**
```
"If we believe that a user would be able to quickly re-produce outputs 
in the same way just by looking at the title or example outputs of your 
prompt, then we will decline it.

For example if your prompt is 'Dog videos', and your prompt is 
'a video of a [dog]', then this would be deemed too simple.

It must be stressed that short prompts (word-count wise) do not always 
mean simple prompts. There are many complex, effective short prompts on 
PromptBase."
```

### Estado Actual del Script

**En `api_handler.py` (validate_prompt_title):**
```python
# Solo valida título, no complejidad del prompt
- Word count (3-6)
- Emotional descriptor
- Format specification
```

### ⚠️ GAP PARCIAL

| Aspecto | Guidelines | Script | Estado |
|---------|-----------|--------|--------|
| Título descriptivo | Requerido | ✅ Validado | ✅ OK |
| Prompt no adivinable | Criterio de rechazo | ❌ No validado | ❌ FALTA |
| Valor añadido | Implícito | ❌ No evaluado | ❌ FALTA |

---

## 6. Análisis de Idioma

### Requisito de Guidelines

**📖 Referencia: `docs/guidelines.md` - Sección 3.12 "Non-English prompt"**
```
"Whilst PromptBase is a global company, and our sellers come from many 
different countries, we are currently only accepting prompts written in 
English.

1. Most models are optimized for use in English, and as such the outputs 
from these models tend to be higher quality with English written prompts.

2. The PromptBase site is only in English (currently), and as such buyers 
on the website expect prompts to be written in English also."
```

### Estado Actual del Script

- ❌ No existe validación de idioma
- ❌ El sistema podría generar prompts en otros idiomas si el input es en otro idioma

### ❌ GAP

| Aspecto | Guidelines | Script | Estado |
|---------|-----------|--------|--------|
| Solo inglés | Obligatorio | No validado | ❌ FALTA |

---

## 7. Análisis de Contenido de Texto (Prompts de Texto)

### Requisito según Ejemplos Analizados

**📖 Referencia: `docs/ejemplos/YouTubeCompleteBundle.md`**
```
Output incluye:
- Hooking intro
- High retention middle  
- CTA outro
- SEO tags y hashtags (10 hashtags, 30 tags)
- SEO description + timestamps
- Clickbait variations
- Thumbnail ideas
- Short-form script
- Social media posts
```

**📖 Referencia: `docs/ejemplos/Top1ArticleGenerator.md`**
```
Output incluye:
- Title SEO optimizado
- Outline detallado
- Terms & Phrases
- 10 Keywords
- Internal Links (5)
- External Links (5)
- Artículo completo
- FAQs (5)
- Tips de optimización
```

**📖 Referencia: `docs/ejemplos/SEO OptimizedBlogArticlesWriting.md`**
```
Output incluye:
- Meta-Title, Sub-Title
- Meta-Description
- Slug
- Excerpt
- Outline
- Keywords (10)
- Internal/External Links
- Artículo detallado
- Key Phrases
- Tags
```

### Estado Actual del Script

**En `prompts.yaml` (text_meta_prompt):**
```yaml
# Output actual:
- template
- description
- variables_explanation
- example_prompts
- technical_tips
- instructions
```

### ⚠️ GAP SIGNIFICATIVO PARA TEXTO

| Elemento | Ejemplos Exitosos | Script Actual | Estado |
|----------|------------------|---------------|--------|
| Template | ✅ | ✅ | ✅ OK |
| Variables | ✅ | ✅ | ✅ OK |
| Examples | ✅ | ✅ | ✅ OK |
| Description | ✅ | ✅ | ✅ OK |
| Tips | ✅ | ✅ | ✅ OK |
| SEO Keywords | ✅ (10-30) | ❌ | ⚠️ FALTA |
| Hashtags | ✅ (10+) | ❌ | ⚠️ FALTA |
| FAQs | ✅ (3-5) | ❌ | ⚠️ FALTA |
| Links sugeridos | ✅ | ❌ | ⚠️ FALTA |
| Multi-deliverables | ✅ | ❌ | ⚠️ FALTA |

**Problema:** Los prompts de texto exitosos generan múltiples entregables con SEO integrado. El sistema actual genera output básico sin estos elementos de alto valor.

---

## 8. Resumen de Hallazgos

### ✅ Aspectos Coherentes
1. Estructura básica de prompt package
2. Generación de ejemplos múltiples (9)
3. Validación de título (parcial)
4. Soporte multi-plataforma para output
5. Sistema de evaluación básico
6. Workflow de reverse engineering

### ❌ Aspectos que Requieren Ajuste

| Prioridad | Aspecto | Problema | Referencia Guidelines | Impacto |
|-----------|---------|----------|----------------------|---------|
| 🔴 Alta | Variables fijas en 4 | Demasiado restrictivo | §2.2, §3.4 - No especifica número fijo | Rechazos innecesarios |
| 🔴 Alta | Sin validación "3 ideas" | No detecta prompts too specific | §3.4 - Regla explícita con ejemplos | Rechazos |
| 🔴 Alta | Sin validación consistencia | No detecta estilos inconsistentes | §3.5 - Criterio de rechazo | Rechazos |
| 🔴 Alta | Sin validación diversidad | No verifica ejemplos variados | §3.9 - Criterio de rechazo | Rechazos |
| 🟡 Media | Sin validación idioma | Podría generar no-inglés | §3.12 - Solo inglés permitido | Rechazos |
| 🟡 Media | Sin SEO para texto | Falta keywords/FAQs | Ejemplos: YouTubeBundle, Top1Article | Menor valor |
| 🟡 Media | Sin validación simplicidad | No detecta prompts adivinables | §3.11 - Criterio de rechazo | Rechazos |
| 🟢 Baja | Sin check originalidad | Difícil de automatizar | §3.13, §3.16 - Plagio/duplicados | Riesgo bajo |

---

## 9. Matriz de Referencias

### Criterios de Rechazo vs Validaciones Implementadas

| Sección Guidelines | Criterio | Implementado | Archivo Afectado |
|-------------------|----------|--------------|------------------|
| §3.3 No use case | Caso de uso comercial | ⚠️ Parcial (evaluación) | `prompts.yaml` |
| §3.4 Too specific | Regla de 3 ideas | ❌ No | Nuevo en `api_handler.py` |
| §3.5 Inconsistent style | Consistencia de estilo | ❌ No | Nuevo en `api_handler.py` |
| §3.6 Low quality | Calidad de output | ⚠️ Parcial | `prompts.yaml` |
| §3.7 Bad test generations | Test reproducible | ❌ No | N/A (manual) |
| §3.8 Bad test prompt | Formato test prompt | ❌ No | `cli.py` |
| §3.9 Examples too similar | Diversidad ejemplos | ❌ No | Nuevo en `api_handler.py` |
| §3.10 Edits and collages | Raw output | N/A | N/A (imágenes) |
| §3.11 Too simple | No adivinable | ❌ No | Nuevo en `api_handler.py` |
| §3.12 Non-English | Solo inglés | ❌ No | Nuevo en `api_handler.py` |
| §3.13 Matches existing | Originalidad | ❌ No | Difícil automatizar |

---

## 10. Conclusión

El sistema PBT tiene una base sólida pero presenta **gaps significativos** con las guidelines actuales de PromptBase, especialmente en:

1. **Rigidez de variables** - El script fuerza 4 variables exactas cuando las guidelines y ejemplos exitosos muestran que 1-5 es aceptable (§2.2, ejemplos analizados)

2. **Validaciones faltantes** - No implementa validación de criterios de rechazo explícitos:
   - Regla de 3 ideas (§3.4)
   - Consistencia de estilo (§3.5)
   - Diversidad de ejemplos (§3.9)
   - Simplicidad/adivinabilidad (§3.11)
   - Idioma inglés (§3.12)

3. **Output incompleto para texto** - Los ejemplos exitosos (YouTubeCompleteBundle, Top1ArticleGenerator) incluyen SEO, FAQs, y múltiples entregables que el sistema no genera

**Riesgo actual:** Prompts generados podrían ser rechazados por PromptBase debido a criterios no validados por el sistema.

**Recomendación:** Implementar las correcciones de Fase 1 antes de continuar con desarrollo de nuevas features.
