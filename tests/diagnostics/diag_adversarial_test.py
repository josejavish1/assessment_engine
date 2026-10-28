#!/usr/bin/env python3
import os
from google import genai

def main():
    # Inicializamos el cliente nativo de Vertex AI / Gemini
    client = genai.Client()
    model_name = "gemini-3.1-pro-preview"
    
    # Riesgo real extraído de la Torre T2 (tras nuestra calibración P99)
    risk_finding = """
    Torre: T2 (Computación Híbrida)
    Capacidad: Fiabilidad de Servicio y Gestión de Rendimiento (SRE)
    Vulnerabilidad: Ausencia de un marco de ingeniería de fiabilidad estandarizado (SRE). La gestión del rendimiento no se basa en Objetivos de Nivel de Servicio (SLOs) y 'error budgets'.
    Exposición Promedio (ALE): 82.208 €
    Exposición Máxima Plausible (P99): 1.426.329 €
    """
    
    print("=====================================================================")
    print(" 🥊 SIMULACIÓN DE CONSENSO ADVERSARIAL (ITERACIÓN 1)")
    print("=====================================================================")
    print(f"Riesgo Base:\n{risk_finding}")
    print("=====================================================================\n")
    
    print("👔 [AGENTE CFO ESCÉPTICO] Pensando su ataque...")
    cfo_prompt = f"""
    Actúa como el CFO hiper-escéptico, financiero y pragmático de un Operador de Infraestructura Crítica.
    Analiza este riesgo técnico calculado por una consultora tecnológica. 
    Tu objetivo es destruir la credibilidad de la cifra extrema (P99 de 1,4 Millones €), argumentando por qué la falta de metodologías de moda como "SRE o SLOs" no va a costar esa fortuna a una empresa que ya tiene procesos ITIL tradicionales maduros y externalizados. Sé duro, directo, financiero y defiende tu caja. No uses saludos, ve directo al grano.
    
    Riesgo:
    {risk_finding}
    """
    
    cfo_response = client.models.generate_content(
        model=model_name,
        contents=cfo_prompt
    ).text
    print(f"\n{cfo_response}\n")
    
    print("=====================================================================")
    print("🧮 [AGENTE ACTUARIO TIER-1] Procesando defensa y recalibración...")
    actuary_prompt = f"""
    Actúa como un Analista de Riesgos Cuantitativos (Quant) Tier-1 experto en modelos estocásticos (Monte Carlo) y riesgo operacional bancario.
    Acabas de recibir una objeción durísima del CFO sobre tu cálculo de riesgo (P99 de 1,4M € por no tener SRE).
    
    CRÍTICA DEL CFO:
    {cfo_response}
    
    Tu objetivo: Responder al CFO en 3 párrafos de forma ejecutiva, fría y matemáticamente impecable.
    1. Concesión Estratégica: Dale la razón en que la ineficiencia operativa de no tener SRE (el 'business as usual') está cubierta por ITIL y su impacto es solo el ALE (82K € de horas hombre).
    2. Defensa Estocástica: Defiende de dónde sale el P99 de 1,4M €. Explica que ITIL es humano y lineal, y que el P99 representa el "fat tail" (el día que un clúster cae en cascada y los humanos de ITIL no dan abasto para levantar los servicios en el RTO exigido por el regulador).
    3. Consenso Final: Propón un ajuste. (ej. "Acepto limitar el impacto primario a OPEX, pero mantengo el riesgo secundario de multa si la caída supera las 4 horas").
    No uses saludos. Usa lenguaje técnico/financiero.
    """
    
    actuary_response = client.models.generate_content(
        model=model_name,
        contents=actuary_prompt
    ).text
    print(f"\n{actuary_response}\n")

if __name__ == "__main__":
    main()
