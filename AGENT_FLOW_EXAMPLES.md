# Esempi di flusso agenti per tipo di domanda

Documentazione dettagliata del flusso di agenti per ogni categoria (A–L) del classificatore.

---

## Cat. A – Filtro ingrediente singolo

**Esempio:** *"Quali sono i piatti che includono i Sashimi di Magikarp?"*

```
1. Orchestrator
   └─ classify_question("...") → Cat. A (100%)

2. Orchestrator → Menu Search
   └─ "Cerca tutti i piatti con ingrediente 'Sashimi di Magikarp'"

3. Menu Search
   └─ search_dishes_by_ingredient("Sashimi di Magikarp")
      → "- Il Rapsodo Celestiale (restaurant: ..., planet: Ego)"

4. Orchestrator → Formatter
   └─ "Converti in ID: Il Rapsodo Celestiale"

5. Formatter
   └─ map_dishes_to_ids("Il Rapsodo Celestiale") → "IDS: 94"

6. Orchestrator → output finale: "94"
```

---

## Cat. B – Filtro tecnica singola

**Esempio:** *"Quali piatti sono preparati con la Sferificazione a Gravità Psionica Variabile?"*

```
1. Orchestrator
   └─ classify_question → Cat. B

2. Orchestrator → Menu Search
   └─ "Cerca piatti con tecnica 'Sferificazione a Gravità Psionica Variabile'"

3. Menu Search
   └─ search_dishes_by_technique("Sferificazione a Gravità Psionica Variabile")
      → lista di piatti

4. Orchestrator → Formatter
   └─ nomi piatti → ID

5. Output: "23,45,67,..."
```

---

## Cat. C – Combinazione AND

**Esempio:** *"Quali piatti sono preparati sia con Marinatura Temporale Sincronizzata che con Congelamento Bio-Luminiscente Sincronico?"*

```
1. Orchestrator
   └─ classify_question → Cat. C

2. Orchestrator → Menu Search
   └─ "Cerca piatti con ENTRAMBE le tecniche: Marinatura Temporale Sincronizzata E Congelamento Bio-Luminiscente Sincronico"

3. Menu Search
   └─ search_dishes_by_technique("Marinatura Temporale Sincronizzata")
      → lista A
   └─ search_dishes_by_technique("Congelamento Bio-Luminiscente Sincronico")
      → lista B
   └─ intersezione A ∩ B

4. Orchestrator → Formatter
   └─ nomi piatti intersezione → ID

5. Output: "12,34,..."
```

---

## Cat. D – Esclusione NOT

**Esempio:** *"Quali piatti usano Sferificazione Filamentare ma evitano Decostruzione Magnetica Risonante?"*

```
1. Orchestrator
   └─ classify_question → Cat. D

2. Orchestrator → Menu Search
   └─ "Cerca piatti con tecnica X, ESCLUDI quelli con tecnica Y"

3. Menu Search
   └─ search_dishes_by_technique("Sferificazione Filamentare a Molecole Vibrazionali")
      → lista A
   └─ search_dishes_by_technique("Decostruzione Magnetica Risonante")
      → lista B
   └─ A - B (escludi da A i piatti in B)

4. Orchestrator → Formatter → Output
```

---

## Cat. E – Almeno N da lista

**Esempio:** *"Quali piatti contengono almeno 2 tra Carne di Drago, Riso di Cassandra e Spezie Melange?"*

```
1. Orchestrator
   └─ classify_question → Cat. E

2. Orchestrator → Menu Search
   └─ "Cerca piatti con ALMENO N ingredienti dalla lista [A, B, C]. Per ogni piatto conta quanti ne ha."

3. Menu Search
   └─ search_dishes_by_ingredient("Carne di Drago") → set A
   └─ search_dishes_by_ingredient("Riso di Cassandra") → set B
   └─ search_dishes_by_ingredient("Spezie Melange") → set C
   └─ Per ogni piatto: conta in quanti set appare. Mantieni solo quelli con conteggio >= N

4. Orchestrator → Formatter
   └─ nomi piatti che soddisfano "almeno 2" → ID

5. Output: "5,12,89,..."
```

---

## Cat. F – Filtro ristorante/pianeta

**Esempio:** *"Quali piatti sono preparati nel ristorante di Asgard utilizzando Essenza di Speziaria?"*

```
1. Orchestrator
   └─ classify_question → Cat. F + A (composita)

2. Orchestrator → Menu Search
   └─ "Cerca piatti con ingrediente 'Essenza di Speziaria' E ristorante su Asgard"

3. Menu Search
   └─ search_dishes_by_ingredient("Essenza di Speziaria")
   └─ filter_dishes_by_planet("Asgard")
   └─ intersezione

4. Orchestrator → Formatter → Output
```

---

## Cat. G – Filtro licenza chef

**Esempio:** *"Quali piatti sono preparati da chef con licenza Psionica di grado almeno 5?"*

```
1. Orchestrator
   └─ classify_question → Cat. G

2. Orchestrator → License Checker
   └─ "Trova chef con licenza Psionica >= 5"

3. License Checker
   └─ get_chefs_with_license("P", 5)
      → "Chef X (ristorante A), Chef Y (ristorante B), ..."

4. Orchestrator → Menu Search
   └─ "Ecco i ristoranti con chef qualificati: A, B, C. Restituisci tutti i piatti di questi ristoranti"

5. Menu Search
   └─ filter_dishes_by_restaurant per ogni ristorante

6. Orchestrator → Formatter → Output
```

---

## Cat. H – Categorie Manuale (RAG)

**Esempio:** *"Quali piatti usano tecniche della categoria 'sferificazione' del Manuale?"*

```
1. Orchestrator
   └─ classify_question → Cat. H

2. Orchestrator → Manual Expert
   └─ query_manuale_cucina("Quali tecniche appartengono alla categoria sferificazione?")
      → RAG su collection manuale_cucina

3. Manual Expert
   └─ restituisce elenco tecniche (es. Sferificazione a Gravità Psionica, Sferificazione con Campi Magnetici, ...)

4. Orchestrator → Menu Search
   └─ "Cerca piatti con QUALSIASI di queste tecniche: [lista dal Manual Expert]"

5. Menu Search
   └─ search_dishes_by_technique per ogni tecnica, poi unione

6. Orchestrator → Formatter → Output
```

---

## Cat. I – Filtro distanza

**Esempio:** *"Quali piatti sono serviti su pianeti entro 50 anni luce da Tatooine?"*

```
1. Orchestrator
   └─ classify_question → Cat. I

2. Orchestrator → Distance Calculator
   └─ "Pianeti entro 50 anni luce da Tatooine"

3. Distance Calculator
   └─ get_planets_within_radius("Tatooine", 50)
      → "Asgard (30), Namecc (45), ..."

4. Orchestrator → Menu Search
   └─ "Ecco i pianeti validi: Asgard, Namecc, ... Cerca tutti i piatti su questi pianeti"

5. Menu Search
   └─ filter_dishes_by_planet per ogni pianeta, unione risultati

6. Orchestrator → Formatter → Output
```

---

## Cat. J – Filtro ordine professionale

**Esempio:** *"Quali piatti sono compatibili con l'Ordine dei Maestri della Griglia?"*

```
1. Orchestrator
   └─ classify_question → Cat. J

2. Orchestrator → Order Expert
   └─ query_codice_galattico + query_manuale_cucina
      → "Ordine Maestri della Griglia: regole, restrizioni, tecniche permesse..."

3. Order Expert (RAG)
   └─ restituisce vincoli (es. solo tecniche di grigliatura, no tecniche X)

4. Orchestrator → Menu Search
   └─ "Filtra piatti secondo questi vincoli: [da Order Expert]"

5. Menu Search → Formatter → Output
```

---

## Cat. K – Conformità limiti quantitativi

**Esempio:** *"Quali piatti recensiti nei blog rispettano i limiti del Codice per la Carne di Drago?"*

```
1. Orchestrator
   └─ classify_question → Cat. K

2. Orchestrator → Compliance Checker
   └─ get_ingredient_percentages (da blogpost_percentages.json)
   └─ query_codice_galattico("limiti Carne di Drago, coefficienti, soglie")
   └─ get_substance_limits

3. Compliance Checker
   └─ confronta % ingredienti con limiti legali
   └─ elenco piatti conformi

4. Orchestrator → Menu Search (se serve filtrare ulteriormente)
5. Orchestrator → Formatter → Output
```

---

## Cat. L – Conformità licenze per tecnica

**Esempio:** *"Quali piatti usano tecniche per cui lo chef ha le licenze richieste?"*

```
1. Orchestrator
   └─ classify_question → Cat. L

2. Orchestrator → License Checker
   └─ get_required_licenses_for_technique("Tecnica X")
   └─ get_chefs_with_license(...)

3. Orchestrator → Menu Search
   └─ piatti con tecnica X

4. Orchestrator → Compliance Checker
   └─ verifica che chef del ristorante abbia licenze adeguate

5. Orchestrator → Formatter → Output
```

---

## Riepilogo flussi

| Cat | Nome | Sequenza agenti |
|-----|------|-----------------|
| A | Filtro ingrediente | Menu Search → Formatter |
| B | Filtro tecnica | Menu Search → Formatter |
| C | Combinazione AND | Menu Search (query multipla) → Formatter |
| D | Esclusione NOT | Menu Search (filtri negativi) → Formatter |
| E | Almeno N da lista | Menu Search (conteggio) → Formatter |
| F | Filtro ristorante/pianeta | Menu Search (filter luogo) → Formatter |
| G | Filtro licenza chef | License → Menu Search → Formatter |
| H | Categorie Manuale | Manual Expert (RAG) → Menu Search → Formatter |
| I | Filtro distanza | Distance → Menu Search → Formatter |
| J | Filtro ordine | Order Expert (RAG) → Menu Search → Formatter |
| K | Conformità limiti | Compliance (+ Order) → Menu Search → Compliance → Formatter |
| L | Conformità licenze | License → Menu Search → Compliance → Formatter |
