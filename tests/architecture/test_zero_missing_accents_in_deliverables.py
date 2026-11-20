"""Architectural Fitness Function: Zero Missing Diacritics in Spanish Deliverables.

Validates the RAE Orthographic Invariant across all 11 official deliverables.
"""

from __future__ import annotations

import re
from pathlib import Path

import docx
import pytest

from assessment_engine.infrastructure.runtime_paths import ROOT

SPANISH_ORTHOGRAPHIC_MAP = {
    "mas": "más",
    "tambien": "también",
    "ademas": "además",
    "segun": "según",
    "despues": "después",
    "aqui": "aquí",
    "alli": "allí",
    "estan": "están",
    "estara": "estará",
    "estaran": "estarán",
    "sera": "será",
    "seran": "serán",
    "habra": "habrá",
    "habran": "habrán",
    "atras": "atrás",
    "detras": "detrás",
    "tecnico": "técnico",
    "tecnicos": "técnicos",
    "tecnica": "técnica",
    "tecnicas": "técnicas",
    "analisis": "análisis",
    "catalogo": "catálogo",
    "catalogos": "catálogos",
    "area": "área",
    "areas": "áreas",
    "ambito": "ámbito",
    "ambitos": "ámbitos",
    "indice": "índice",
    "indices": "índices",
    "limite": "límite",
    "limites": "límites",
    "nucleo": "núcleo",
    "nucleos": "núcleos",
    "numero": "número",
    "numeros": "números",
    "pagina": "página",
    "paginas": "páginas",
    "periodo": "período",
    "periodos": "períodos",
    "modulo": "módulo",
    "modulos": "módulos",
    "metodo": "método",
    "metodos": "métodos",
    "ultimo": "último",
    "ultimos": "últimos",
    "ultima": "última",
    "ultimas": "últimas",
    "unico": "único",
    "unicos": "únicos",
    "unica": "única",
    "unicas": "únicas",
    "critico": "crítico",
    "criticos": "críticos",
    "critica": "crítica",
    "criticas": "críticas",
    "basico": "básico",
    "basicos": "básicos",
    "basica": "básica",
    "basicas": "básicas",
    "estandar": "estándar",
    "estandares": "estándares",
    "perdida": "pérdida",
    "perdidas": "pérdidas",
    "dias": "días",
    "dia": "día",
    "comite": "comité",
    "comites": "comités",
    "linea": "línea",
    "lineas": "líneas",
    "politica": "política",
    "politicas": "políticas",
    "publico": "público",
    "publicos": "públicos",
    "publica": "pública",
    "publicas": "públicas",
    "economico": "económico",
    "economicos": "económicos",
    "economica": "económica",
    "economicas": "económicas",
    "estrategico": "estratégico",
    "estrategicos": "estratégicos",
    "estrategica": "estratégica",
    "estrategicas": "estratégicas",
    "fisico": "físico",
    "fisicos": "físicos",
    "fisica": "física",
    "fisicas": "físicas",
    "logico": "lógico",
    "logicos": "lógicos",
    "logica": "lógica",
    "logicas": "lógicas",
    "automatico": "automático",
    "automaticos": "automáticos",
    "automatica": "automática",
    "automaticas": "automáticas",
    "especifico": "específico",
    "especificos": "específicos",
    "especifica": "específica",
    "especificas": "específicas",
    "historico": "histórico",
    "historicos": "históricos",
    "historica": "histórica",
    "historicas": "históricas",
    "practica": "práctica",
    "practicas": "prácticas",
    "maximo": "máximo",
    "maximos": "máximos",
    "maxima": "máxima",
    "maximas": "máximas",
    "minimo": "mínimo",
    "minimos": "mínimos",
    "minima": "mínima",
    "minimas": "mínimas",
    "optimo": "óptimo",
    "optimos": "óptimos",
    "optima": "óptima",
    "optimas": "óptimas",
    "dinamico": "dinámico",
    "dinamicos": "dinámicos",
    "dinamica": "dinámica",
    "dinamicas": "dinámicas",
    "estatico": "estático",
    "estaticos": "estáticos",
    "estatica": "estática",
    "estaticas": "estáticas",
    "autonomo": "autónomo",
    "autonomos": "autónomos",
    "autonoma": "autónoma",
    "autonomas": "autónomas",
    "sintesis": "síntesis",
    "hipotesis": "hipótesis",
    "diagnostico": "diagnóstico",
    "diagnosticos": "diagnósticos",
    "pronostico": "pronóstico",
    "pronosticos": "pronósticos",
    "deficit": "déficit",
    "superavit": "superávit",
    "boveda": "bóveda",
    "bovedas": "bóvedas",
    "tacito": "tácito",
    "tacitos": "tácitos",
    "tacita": "tácita",
    "tacitas": "tácitas",
    "exito": "éxito",
    "exitos": "éxitos",
    "valido": "válido",
    "validos": "válidos",
    "valida": "válida",
    "validas": "válidas",
    "rapido": "rápido",
    "rapidos": "rápidos",
    "rapida": "rápida",
    "rapidas": "rápidas",
    "facil": "fácil",
    "faciles": "fáciles",
    "dificil": "difícil",
    "dificiles": "difíciles",
    "util": "útil",
    "utiles": "útiles",
    "debil": "débil",
    "debiles": "débiles",
    "arbol": "árbol",
    "arboles": "árboles",
    "termino": "término",
    "terminos": "términos",
    "volumenes": "volúmenes",
    "origenes": "orígenes",
    "margenes": "márgenes",
    "ordenes": "órdenes",
    "regimen": "régimen",
    "regimenes": "regímenes",
    "gestion": "gestión",
    "operacion": "operación",
    "administracion": "administración",
    "direccion": "dirección",
    "configuracion": "configuración",
    "definicion": "definición",
    "integracion": "integración",
    "conmutacion": "conmutación",
    "recuperacion": "recuperación",
    "monitorizacion": "monitorización",
    "optimizacion": "optimización",
    "autenticacion": "autenticación",
    "autorizacion": "autorización",
    "evaluacion": "evaluación",
    "ejecucion": "ejecución",
    "resolucion": "resolución",
    "actualizacion": "actualización",
    "adquisicion": "adquisición",
    "asignacion": "asignación",
    "alineacion": "alineación",
    "consolidacion": "consolidación",
    "centralizacion": "centralización",
    "descentralizacion": "descentralización",
    "virtualizacion": "virtualización",
    "digitalizacion": "digitalización",
    "securizacion": "securización",
    "segmentacion": "segmentación",
    "orquestacion": "orquestación",
    "saturacion": "saturación",
    "proliferacion": "proliferación",
    "interconexion": "interconexión",
    "conexion": "conexión",
    "desconexion": "desconexión",
    "produccion": "producción",
    "reduccion": "reducción",
    "proteccion": "protección",
    "expansion": "expansión",
    "retencion": "retención",
    "contencion": "contención",
    "provision": "provisión",
    "transicion": "transición",
    "migracion": "migración",
    "clasificacion": "clasificación",
    "certificacion": "certificación",
    "identificacion": "identificación",
    "modificacion": "modificación",
    "notificacion": "notificación",
    "mitigacion": "mitigación",
    "remediacion": "remediación",
    "autorremediacion": "autorremediación",
    "infeccion": "infección",
    "deteccion": "detección",
    "excepcion": "excepción",
    "atencion": "atención",
    "comunicacion": "comunicación",
    "informacion": "información",
    "situacion": "situación",
    "aplicacion": "aplicación",
    "exposicion": "exposición",
    "inaccion": "inacción",
    "afectacion": "afectación",
    "justificacion": "justificación",
    "valoracion": "valoración",
    "estimacion": "estimación",
    "duracion": "duración",
}

ANNEX_DIR = ROOT / "working" / "out" / "Molins_Entrega_Oficial_Piramide_Tier1"
CANONICAL_TOMO1 = (
    ANNEX_DIR
    / "01_TRIADA_ESTRATEGICA_TRANSVERSAL_CTO"
    / "Molins_202610_Tomo_1_Diagnostico_ASIS.docx"
    if (
        ANNEX_DIR
        / "01_TRIADA_ESTRATEGICA_TRANSVERSAL_CTO"
        / "Molins_202610_Tomo_1_Diagnostico_ASIS.docx"
    ).exists()
    else ROOT
    / "evaluations"
    / "molins_evaluation_dossier"
    / "02_GENERATED_DELIVERABLES"
    / "Molins_202610_Tomo_1_Diagnostico_ASIS.docx"
)
OFFICIAL_DOCX_FILES = [CANONICAL_TOMO1] + sorted(
    (ANNEX_DIR / "02_ANEXOS_TECNICOS_ESPECIALISTAS").glob("*_ASIS.docx")
)


@pytest.mark.parametrize("docx_path", OFFICIAL_DOCX_FILES, ids=lambda p: p.name)
def test_zero_unaccented_spanish_words_in_document(docx_path: Path) -> None:
    """Verifies that generated DOCX deliverable contains zero unaccented Spanish words from authoritative lexicon."""
    assert docx_path.exists(), f"Deliverable file does not exist: {docx_path}"

    doc = docx.Document(docx_path)
    violations: list[str] = []

    # Check paragraphs
    for p_idx, p in enumerate(doc.paragraphs):
        words = re.findall(r"\b[A-Za-záéíóúñÁÉÍÓÚÑ]+\b", p.text)
        for w in words:
            w_lower = w.lower()
            if w_lower in SPANISH_ORTHOGRAPHIC_MAP:
                expected = SPANISH_ORTHOGRAPHIC_MAP[w_lower]
                if w == w_lower and expected != w_lower:
                    violations.append(
                        f"P{p_idx}: '{w}' (expected '{expected}') -> context: {p.text[:60]}"
                    )
                elif w.capitalize() == w and expected.capitalize() != w:
                    violations.append(
                        f"P{p_idx}: '{w}' (expected '{expected.capitalize()}') -> context: {p.text[:60]}"
                    )

    # Check tables
    for t_idx, t in enumerate(doc.tables):
        for r_idx, r in enumerate(t.rows):
            for c_idx, c in enumerate(r.cells):
                words = re.findall(r"\b[A-Za-záéíóúñÁÉÍÓÚÑ]+\b", c.text)
                for w in words:
                    w_lower = w.lower()
                    if w_lower in SPANISH_ORTHOGRAPHIC_MAP:
                        expected = SPANISH_ORTHOGRAPHIC_MAP[w_lower]
                        if w == w_lower and expected != w_lower:
                            violations.append(
                                f"T{t_idx}[R{r_idx}C{c_idx}]: '{w}' (expected '{expected}') -> context: {c.text[:60]}"
                            )
                        elif w.capitalize() == w and expected.capitalize() != w:
                            violations.append(
                                f"T{t_idx}[R{r_idx}C{c_idx}]: '{w}' (expected '{expected.capitalize()}') -> context: {c.text[:60]}"
                            )

    assert not violations, (
        f"Orthographic invariant violated in {docx_path.name}: {len(violations)} words missing graphic accents:\n"
        + "\n".join(violations[:15])
    )
