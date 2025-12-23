# Referencias Técnicas para Prompts de Texto

## Frameworks Utilizados en Prompts Exitosos

### 1. Frameworks de Análisis de Negocio

#### SWOT Analysis
```
Strengths (Fortalezas):
- Ventajas internas
- Recursos únicos
- Capacidades distintivas

Weaknesses (Debilidades):
- Limitaciones internas
- Áreas de mejora
- Recursos faltantes

Opportunities (Oportunidades):
- Tendencias favorables
- Mercados emergentes
- Cambios regulatorios positivos

Threats (Amenazas):
- Competencia
- Cambios de mercado
- Riesgos externos
```

#### PEST Analysis
```
Political: Regulaciones, políticas gubernamentales
Economic: Ciclos económicos, tasas, inflación
Social: Tendencias demográficas, comportamiento
Technological: Innovaciones, disrupciones tech
```

#### 7 P's del Marketing
```
Product: Características, beneficios, diferenciación
Price: Estrategia de precios, posicionamiento
Place: Canales de distribución, accesibilidad
Promotion: Comunicación, publicidad, PR
People: Equipo, servicio al cliente
Process: Operaciones, experiencia del cliente
Physical Evidence: Tangibles, pruebas de calidad
```

---

### 2. Frameworks de Copywriting

#### AIDA
```
Attention: Capturar atención inicial
Interest: Generar interés con beneficios
Desire: Crear deseo con pruebas/testimonios
Action: Llamada a la acción clara
```

#### PAS
```
Problem: Identificar el problema del lector
Agitate: Amplificar el dolor/frustración
Solution: Presentar la solución
```

#### Hook-Story-Offer
```
Hook: Captura inmediata de atención
Story: Narrativa que conecta emocionalmente
Offer: Propuesta de valor clara
```

---

### 3. Frameworks de Contenido

#### Estructura de Video (YouTube)
```
0:00-0:30 - Hook (pregunta, dato, promesa)
0:30-1:00 - Preview del contenido
1:00-X:00 - Contenido principal con "loops"
X:00-fin - CTA + cross-promotion
```

#### Estructura de Artículo SEO
```
H1: Título principal (keyword)
├── Intro (hook + preview)
├── H2: Sección 1
│   ├── H3: Subsección
│   └── H3: Subsección
├── H2: Sección 2
├── H2: Sección N
├── H2: Conclusión
└── H2: FAQs
```

---

## Elementos SEO Técnicos

### Keywords Research
```yaml
primary_keyword:
  - Término principal de búsqueda
  - Volumen alto, competencia media

secondary_keywords:
  - Variaciones del término principal
  - Long-tail keywords
  - Preguntas relacionadas

lsi_keywords:
  - Términos semánticamente relacionados
  - Sinónimos y variaciones
```

### Meta Tags
```html
<title>Keyword Principal | Brand - 60 chars max</title>
<meta name="description" content="155-160 chars con keyword y CTA">
<meta name="keywords" content="keyword1, keyword2, keyword3">
```

### URL Structure
```
/keyword-principal-secundario
- Lowercase
- Hyphens entre palabras
- Sin stop words innecesarias
- Máximo 60 caracteres
```

### Heading Hierarchy
```
H1: 1 por página (keyword principal)
H2: Secciones principales (keywords secundarias)
H3: Subsecciones (long-tail keywords)
H4+: Detalles adicionales
```

---

## Técnicas de Engagement

### Hooks Efectivos
```
Pregunta: "¿Sabías que...?"
Dato: "El 90% de las personas..."
Promesa: "En este video aprenderás..."
Controversia: "Todo lo que te dijeron está mal..."
Historia: "Hace 3 años, yo estaba..."
```

### Retention Loops
```
"Pero antes de eso, hay algo importante..."
"Quédate hasta el final para descubrir..."
"El punto #5 te va a sorprender..."
"Hay un secreto que revelaré más adelante..."
```

### CTAs Efectivos
```
Suscripción: "Suscríbete para más contenido como este"
Engagement: "Comenta cuál fue tu favorito"
Sharing: "Comparte con alguien que necesite esto"
Cross-promo: "Mira este otro video relacionado"
```

---

## Formatos de Output

### Listas Numeradas
```
1. Item con título - descripción breve
2. Item con título - descripción breve
3. Item con título - descripción breve
```

### Tablas de Comparación
```
| Característica | Opción A | Opción B |
|----------------|----------|----------|
| Precio         | $X       | $Y       |
| Calidad        | Alta     | Media    |
```

### Bullet Points con Emojis
```
✅ Beneficio 1
✅ Beneficio 2
❌ Lo que NO incluye
⚠️ Advertencia importante
```

---

## Modelos y Tokens

### Comparativa de Modelos
```
GPT-3.5-turbo:
- Costo: ~$0.002/1K tokens
- Velocidad: Rápida
- Calidad: Buena para tareas simples

GPT-4:
- Costo: ~$0.03/1K tokens
- Velocidad: Media
- Calidad: Excelente para tareas complejas

GPT-4o:
- Costo: ~$0.005/1K tokens
- Velocidad: Rápida
- Calidad: Muy buena, multimodal

o3:
- Costo: ~$0.06/1K tokens
- Velocidad: Lenta
- Calidad: Máxima para razonamiento
```

### Estimación de Tokens
```
Regla general: ~4 caracteres = 1 token
- 100 palabras ≈ 130-150 tokens
- 500 palabras ≈ 650-750 tokens
- 1000 palabras ≈ 1300-1500 tokens
```

---

## Validación de Calidad

### Checklist de Output
```
[ ] Estructura clara y consistente
[ ] Keywords integradas naturalmente
[ ] Sin errores gramaticales
[ ] Longitud apropiada
[ ] Valor actionable
[ ] Formato legible
```

### Métricas de Consistencia
```
Test 1: Mismo input → output similar
Test 2: Input variado → estructura consistente
Test 3: Edge cases → manejo graceful
```

---

## Recursos Adicionales

### Herramientas Útiles
- **Keyword Research:** Ahrefs, SEMrush, Ubersuggest
- **Readability:** Hemingway Editor, Grammarly
- **SEO Analysis:** Yoast, Surfer SEO
- **Token Counter:** OpenAI Tokenizer

### Fuentes de Tendencias
- Google Trends
- AnswerThePublic
- Reddit (subreddits de nicho)
- Twitter/X trending topics
- YouTube trending
