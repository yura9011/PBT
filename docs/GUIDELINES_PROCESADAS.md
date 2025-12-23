# Guidelines de PromptBase - Referencia Procesada

## Resumen Ejecutivo

Este documento procesa las guidelines oficiales de PromptBase para uso rápido en el desarrollo de prompts.

---

## ✅ Criterios de Aprobación

### 1. Prompt Templates (OBLIGATORIO)
```
REGLA: Todo prompt debe tener variables en [corchetes]
EXCEPCIÓN: "Random generator prompts" (estilo consistente, sujeto aleatorio)

EJEMPLO VÁLIDO:
"Very tiny [KEYWORD] that looks like iOS emoji..."

EJEMPLO INVÁLIDO:
"Very tiny koala that looks like iOS emoji..." (sin variable)
```

### 2. Alto Factor de Uso
```
PREGUNTA CLAVE: ¿Cuántas personas pueden usar este prompt?

BUENOS CASOS DE USO:
- Logo designs
- Imagery for blogs
- Product videos
- Album artwork
- Professional photography
- Icons/illustrations

EJEMPLOS TOP SELLERS:
- Great Tee Illustrations
- Professional Product Photography
- Food Advertising Photography
- Lineal Color Icons
```

### 3. Estilos Únicos (Categoría #1 en ventas)
```
CARACTERÍSTICAS:
- Efecto/estilo intangible
- Empuja límites del modelo
- Difícil de replicar sin el prompt

EJEMPLOS:
- Stylized Vintage Exotic Animal Illustrations
- Desaturation HD Photographs
- Amazing Transformations Weight Loss
- High Quality Cartoon Cat And Dog Animals
```

---

## ❌ Razones de Rechazo

### 3.3 No Use Case
```
PROBLEMA: Prompt sin valor comercial suficiente
SOLUCIÓN: No tiene arreglo - cambiar la idea completamente
PREVENCIÓN: Validar caso de uso ANTES de desarrollar
```

### 3.4 Too Specific
```
PROBLEMA: Alcance muy limitado
REGLA DE 3 IDEAS: Máximo 3 ideas, todas deben ser "broad"

EJEMPLO MALO:
"3D doctor animals with moustaches"
= 4 ideas (3D: broad, animals: broad, doctors: niche, moustaches: niche)

EJEMPLO MEJORADO:
"3D animals with jobs"
= 3 ideas (3D: broad, animals: broad, jobs: broad)

SOLUCIÓN: Añadir variables [corchetes] para generalizar
```

### 3.5 Inconsistent Style
```
PROBLEMA: Output varía demasiado entre generaciones
- Estilo cambia (3D vs cartoon vs foto)
- Sujeto cambia (catwalk vs speedboat vs magazine)

IDEAL: Estilo consistente + sujeto variable

SOLUCIÓN: Refinar prompt para mayor consistencia
```

### 3.6 Low Quality Output
```
PROBLEMA: 
- Errores ortográficos
- Texto sin sentido
- Descripciones poco útiles

SOLUCIÓN: Revisar y corregir antes de enviar
```

### 3.7 Bad Test Generations
```
PROBLEMA: Output no coincide con ejemplos mostrados
CAUSA COMÚN: Enviar prompt incorrecto por error

SOLUCIÓN: 
- Verificar prompt correcto
- Mejorar consistencia del prompt
```

### 3.8 Bad Test Prompt
```
PROBLEMA: Test prompt mal formateado

ERRORES COMUNES:
❌ "substitute [KEYWORD] -> Koala" (instrucciones en test)
❌ Múltiples prompts en uno

FORMATO CORRECTO:
Prompt: "Very tiny [KEYWORD] that looks like..."
Test: "Very tiny Koala that looks like..."
```

### 3.9 Example Outputs Too Similar
```
PROBLEMA: Todos los ejemplos son casi iguales

EJEMPLO MALO:
- Prompt "adorable watercolor animals"
- Ejemplos: 4 ovejas + 5 zorros (solo 2 animales)

SOLUCIÓN: Mostrar variedad de outputs con diferentes sujetos
```

### 3.10 Edits and Collages
```
PROHIBIDO:
- Cropping
- Filtros
- Texto añadido
- Collages (incluyendo 2x2 de Midjourney)

REQUERIDO: Raw output del modelo, upscaled si aplica
```

### 3.11 Prompt Too Simple / Guessable
```
PROBLEMA: Usuario puede adivinar el prompt

EJEMPLO MALO:
Título: "Dog videos"
Prompt: "a video of a [dog]"

NOTA: Corto ≠ simple, Largo ≠ complejo
```

### 3.12 Non-English Prompt
```
REGLA: Solo prompts en inglés
RAZÓN: Modelos optimizados para inglés + sitio en inglés
```

### 3.13 Matches Existing Prompt
```
PROBLEMA: Muy similar a prompt existente en marketplace
NOTA: Ideas similares OK si prompts son diferentes

PROHIBIDO:
- Copiar prompts de otros
- Re-subir mismo prompt
- Variaciones mínimas del mismo prompt
```

### 3.14 Unsafe
```
PROHIBIDO:
- Consejos médicos
- Actividades ilegales
- Contenido dañino
```

### 3.15 Violates Model Rules
```
PROHIBIDO:
- Contenido explícito donde modelo lo prohíbe
- Exploits del modelo
```

### 3.16 Plagiarism
```
PROHIBIDO:
- Prompts de Twitter/YouTube/comunidades
- Copiar sistemáticamente ideas de otros sellers
- Replicar estilos exitosos sin innovación

CONSECUENCIA: Ban de cuenta posible
```

### 3.17 NSFW
```
PROHIBIDO: Contenido adulto/explícito
RAZÓN: Políticas de procesadores de pago (Stripe)
```

### 3.18 AI Generated Prompts
```
PROHIBIDO: Prompts mass-generated por AI
RAZÓN: Baja calidad, falta de refinamiento humano
DISPUTA: Posible si fue incorrectamente flaggeado
```

### 3.19-3.22 Verification Link Issues
```
3.19 Mismatch: Link no coincide con prompt/output
3.20 Broken: Link no funciona
3.21 Inputs Mismatch: Diferentes inputs (ej: con/sin imagen ref)
3.22 Version Mismatch: Diferente versión del modelo

SOLUCIÓN: Verificar link en incógnito, usar DiffChecker
```

---

## 🖼️ Custom Thumbnails

### Rechazos de Thumbnails
```
4.1 Unrelated: No representa el prompt
4.2 Low Quality: Pixelado, borroso, mal compuesto
4.3 Prices/Discounts/Ratings: No incluir texto de precios
4.4 NSFW: Contenido inapropiado
4.5 Too Much Text: Thumbnail es visual, no textual
```

---

## 📋 Checklist Pre-Envío

### Estructura del Prompt
- [ ] Tiene variables en [corchetes]
- [ ] Variables son claras y útiles
- [ ] Alcance suficientemente amplio (regla de 3 ideas)
- [ ] No es demasiado simple/adivinable

### Calidad
- [ ] Sin errores ortográficos
- [ ] En inglés
- [ ] Output consistente en estilo
- [ ] Diferente a prompts existentes

### Ejemplos
- [ ] Variedad de sujetos/outputs
- [ ] Sin ediciones ni collages
- [ ] Raw output del modelo
- [ ] Upscaled si es Midjourney

### Test Prompt
- [ ] Un solo prompt
- [ ] Variables rellenadas (sin instrucciones)
- [ ] Produce output similar a ejemplos

### Verification (si aplica)
- [ ] Link funciona en incógnito
- [ ] Texto coincide exactamente
- [ ] Output coincide exactamente
- [ ] Misma versión del modelo
- [ ] Mismos inputs (con/sin imagen ref)

### Thumbnail
- [ ] Relacionado con el prompt
- [ ] Alta calidad
- [ ] Sin precios/ratings
- [ ] Mínimo texto
- [ ] SFW

---

## 🎯 Fórmula de Éxito

```
PROMPT EXITOSO = 
  Template con [variables]
  + Alto caso de uso (broad appeal)
  + Estilo único/difícil de replicar
  + Output consistente
  + Ejemplos variados
  + Calidad profesional
```

---

## ⚠️ Red Flags (Rechazo Probable)

1. **Sin variables** → Añadir [corchetes]
2. **Muy específico** → Generalizar alcance
3. **Estilo inconsistente** → Refinar prompt
4. **Ejemplos iguales** → Generar variedad
5. **Prompt adivinable** → Añadir complejidad/valor
6. **Similar a existente** → Diferenciar significativamente
7. **Contenido problemático** → No tiene solución
