package assessment.ontology

import future.keywords.if
import future.keywords.in

# 1. Definición del Universo de Competidores (Invariantes del Mercado 2026)
hyperscalers := {"AWS", "Azure", "GCP", "OCI"}
erps := {"SAP", "Oracle", "Microsoft Dynamics"}

# 2. Regla de Denegación: Colisión de Hyperscalers
# Bloquea si un dossier menciona múltiples competidores en el contexto estratégico principal
deny[msg] {
    some claim in input.claims
    count(detected_hyperscalers(claim.claim)) > 1
    msg := sprintf("Ontology Violation: Colisión de competidores detectada en claim '%v'. No se permite mezclar %v en el mismo contexto estratégico.", [claim.claim_id, detected_hyperscalers(claim.claim)])
}

deny[msg] {
    some driver in input.technology_context.technology_drivers
    count(detected_hyperscalers(driver.name)) > 1
    msg := sprintf("Ontology Violation: El driver '%v' contiene múltiples hyperscalers competidores.", [driver.name])
}

# 3. Función auxiliar para detectar hyperscalers en un texto
detected_hyperscalers(text) = {h |
    h := hyperscalers[_]
    contains_word(text, h)
}

# 4. Helper para evitar falsos positivos (coincidencia de palabra completa)
contains_word(text, word) {
    regex.match(sprintf("(?i)\\b%v\\b", [word]), text)
}

# 5. Regla de "Microsoft AWS" (El error específico detectado)
deny[msg] {
    some claim in input.claims
    contains(lower(claim.claim), "microsoft aws")
    msg := "Ontology Violation: La entidad 'Microsoft AWS' no existe físicamente. Es una alucinación por mezcla de competidores."
}
