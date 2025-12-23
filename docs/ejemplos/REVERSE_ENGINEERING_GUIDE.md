# Guía de Reverse Engineering para Prompts de Texto

## Objetivo
Analizar prompts exitosos de PromptBase para extraer patrones, estructuras y técnicas que permitan crear prompts competitivos.

---

## Metodología de Análisis

### Paso 1: Recolección de Datos
Para cada prompt analizar:

```yaml
metadata:
  nombre: ""
  modelo: ""  # GPT-3.5, GPT-4, GPT-5.1, o3
  tokens: 0
  precio: 0.00
  ventas: 0
  rating: 0.0
  reviews: 0
  categoría: ""
```

### Paso 2: Análisis de Input
Identificar las variables del prompt:

```yaml
variables:
  - nombre: "[variable_name]"
    tipo: "text|select|number"
    descripción: ""
    ejemplo: ""
    obligatorio: true|false
```

### Paso 3: Análisis de Output
Mapear la estructura de salida:

```yaml
output_structure:
  secciones:
    - nombre: ""
      tipo: "texto|lista|tabla|código"
      longitud_aprox: ""
      valor_añadido: "alto|medio|bajo"
```

### Paso 4: Extracción de Patrones
Identificar técnicas utilizadas:

```yaml
técnicas:
  - estructuración: ""
  - personalización: ""
  - seo_integration: ""
  - valor_añadido: ""
```

---

## Plantilla de Análisis

### [Nombre del Prompt]

**Metadata:**
- Modelo: 
- Tokens: 
- Precio: $
- Ventas: 
- Rating: ★

**Variables de Input:**
1. `[var1]` - descripción
2. `[var2]` - descripción

**Estructura de Output:**
1. Sección 1
2. Sección 2
3. ...

**Técnicas Identificadas:**
- Técnica 1
- Técnica 2

**Fortalezas:**
- 

**Debilidades:**
- 

**Oportunidades de Mejora:**
- 

---

## Patrones de Prompts por Categoría

### Content Creation
```
ESTRUCTURA TÍPICA:
1. Hook/Intro
2. Contenido principal estructurado
3. CTA/Outro
4. SEO elements (tags, keywords, hashtags)
5. Extras (thumbnails, social posts, short-form)
```

### Article/Blog Writing
```
ESTRUCTURA TÍPICA:
1. Meta information (title, description, slug)
2. Outline detallado
3. Keywords y términos
4. Links (internal/external)
5. Artículo completo
6. FAQs
7. Tips adicionales
```

### Business/Planning
```
ESTRUCTURA TÍPICA:
1. Nombre/Branding
2. Narrativa (misión, visión, valores)
3. Análisis (SWOT, PEST, competencia)
4. Estrategia (marketing, pricing, distribución)
5. Financials (proyecciones, métricas)
6. Roadmap
7. Documentación legal
```

### Idea Generation
```
ESTRUCTURA TÍPICA:
1. Lista numerada de ideas (10-30)
2. Cada idea con:
   - Título/concepto
   - Ángulo único
   - Potencial viral/engagement
3. Variedad de formatos/enfoques
```

---

## Técnicas de Alto Impacto

### 1. Multi-Output Strategy
Generar múltiples entregables relacionados en una sola ejecución:
- Aumenta valor percibido
- Justifica precio más alto
- Reduce fricción del usuario

### 2. Framework Integration
Incorporar frameworks conocidos:
- SWOT, PEST, 7Ps (business)
- AIDA, PAS (copywriting)
- Hook-Story-Offer (content)

### 3. SEO-First Approach
Incluir elementos SEO nativamente:
- Keywords research integrado
- Meta tags generados
- Estructura heading optimizada

### 4. Actionable Extras
Añadir elementos inmediatamente usables:
- Social media posts listos
- Thumbnails descriptions
- Email templates
- Scripts cortos

### 5. Personalization Depth
Variables que permiten personalización profunda:
- Tono (formal/casual/técnico)
- Audiencia target
- Formato de salida
- Longitud deseada

---

## Métricas de Evaluación

### Calidad del Prompt
| Criterio | Peso | Evaluación |
|----------|------|------------|
| Consistencia de output | 25% | 1-5 |
| Valor de entregables | 25% | 1-5 |
| Facilidad de uso | 20% | 1-5 |
| Personalización | 15% | 1-5 |
| Unicidad | 15% | 1-5 |

### Potencial Comercial
| Criterio | Peso | Evaluación |
|----------|------|------------|
| Demanda de mercado | 30% | 1-5 |
| Diferenciación | 25% | 1-5 |
| Precio justificable | 20% | 1-5 |
| Escalabilidad | 15% | 1-5 |
| Competencia | 10% | 1-5 |

---

## Checklist de Reverse Engineering

### Análisis Inicial
- [ ] Capturar metadata completa
- [ ] Identificar todas las variables
- [ ] Documentar estructura de output
- [ ] Probar con diferentes inputs

### Análisis Profundo
- [ ] Identificar patrones de lenguaje
- [ ] Mapear técnicas de estructuración
- [ ] Evaluar consistencia de resultados
- [ ] Comparar con competidores

### Síntesis
- [ ] Extraer mejores prácticas
- [ ] Identificar gaps/oportunidades
- [ ] Documentar lecciones aprendidas
- [ ] Proponer mejoras/variaciones
