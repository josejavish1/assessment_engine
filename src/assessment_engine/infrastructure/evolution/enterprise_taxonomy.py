"""
Enterprise Taxonomy & Orthogonal Coordinate Space (SOTA 2026).
Defines a 3,000-dimensional discrete coordinate grid based on the UN ISIC / NAICS taxonomy:
- 100 Specific Industries across all economic sectors.
- 6 Universal Business & Monetization Models.
- 5 Regulatory & Compliance Regimes.

Guarantees 100% orthogonal entropy (Zero Mode Collapse) across the synthetic evaluation space.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DB_PATH = Path("storage/data/socratic_calibration.db")

# Global economic sector classification
INDUSTRIES_100 = (
    # Primary & Extractive Sector (1-10)
    "Acuicultura de Alta Mar y Piscifactorías Offshore",
    "Minería de Tierras Raras y Litio en Salmueras",
    "Silvicultura Sostenible y Trazabilidad Maderera",
    "Agricultura Regenerativa de Precisión con Drones",
    "Extracción y Refinado de Cobre Subterráneo",
    "Bioprospección de Microalgas y Biomasa Marina",
    "Ganadería Bovina Extensiva con Trazabilidad Genómica",
    "Apicultura Profesional y Trazabilidad de Miel Cruda",
    "Extracción de Gas Natural y Captura de Metano",
    "Viticultura de Clima Extremo y Bodegas Boutique",

    # Manufacturing & Heavy Industry (11-20)
    "Fundición y Forja de Aleaciones de Titanio Aeroespacial",
    "Fabricación de Baterías de Estado Sólido para Vehículos Eléctricos",
    "Impresión 3D Industrial con Polvo Metálico (SLM)",
    "Ensamblaje de Satélites CubeSat y Constelaciones LEO",
    "Robótica Humanoide para Cadenas de Montaje",
    "Construcción Naval y Astilleros de Yates de Lujo",
    "Fabricación de Maquinaria de Estampación y Prensas Hidráulicas",
    "Producción de Vidrio Fotovoltaico y Fachadas Solares",
    "Química Fina y Catalizadores Industriales",
    "Textiles Técnicos e Indumentaria de Protección Balística",

    # Energy, Utilities & Sustainability (21-30)
    "Parques Eólicos Marinos (Offshore Wind) de Aguas Profundas",
    "Plantas Geotérmicas de Alta Entalpía",
    "Almacenamiento de Energía en Baterías de Flujo Redox",
    "Desalación de Agua Marina por Ósmosis Inversa con Energía Solar",
    "Redes Inteligentes de Distribución Energética (Smart Grids)",
    "Producción de Hidrógeno Verde por Electrólisis PEM",
    "Reciclaje Químico de Plásticos Complejos",
    "Gestión y Tratamiento de Residuos Industriales Peligrosos",
    "Biogás y Biometano de Residuos Agropecuarios",
    "Desmantelamiento y Gestión Segura de Centrales Nucleares",

    # Healthcare, Biotechnology & Pharma (31-40)
    "Teledermatología Asíncrona con Diagnóstico Multimodal",
    "Terapia Génica y Edición CRISPR de Enfermedades Raras",
    "Fabricación de Implantes Quirúrgicos Ortopédicos a Medida",
    "Ensayos Clínicos Descentralizados y Reclutamiento de Pacientes",
    "Monitorización Cardíaca Remota Continua (Holter IoT)",
    "Plataformas de Telepsiquiatría y Salud Mental Basada en Datos",
    "Bancos de Células Madre y Criopreservación Tisular",
    "Farmacia Hospitalaria y Dispensación Robotizada",
    "Detección Precoz Oncológica por Biopsia Líquida",
    "Veterinaria de Animales Exóticos y Resonancia Magnética Animal",

    # Group 05 (41-50)
    "Transporte de Carga Marítima y Operativa de Terminales de Contenedores",
    "Reparto Urbano de Última Milla con Drones Autónomos",
    "Alquiler P2P de Barcos de Recreo y Yates de Chárter",
    "Gestión de Flotas de Camiones Eléctricos de Larga Distancia",
    "Alquiler de Furgonetas Camper y Vehículos Recreativos",
    "Ferrocarriles de Alta Velocidad y Mantenimiento Predictivo de Vías",
    "Logística de Cadena de Frío para Vacunas y Biológicos",
    "Servicios de Remolque y Asistencia en Carretera On-Demand",
    "Mudanzas Corporativas Internacionales y Aduanas de Menaje",
    "Taxis Aéreos Urbanos Eléctricos (eVTOL)",

    # Finance, Insurance & Investment (51-60)
    "Neobanca Multidivisa y Micro-inversiones Automatizadas",
    "Seguros Paramétricos Agrícolas contra Sequía e Inundación",
    "Casas de Subastas de Arte Contemporáneo y Alta Relojería",
    "Crowdfunding Inmobiliario y Tokenización de Edificios",
    "Factoring y Descuento de Pagarés B2B para Pymes",
    "Protocolos DeFi de Swap Descentralizado y Agregación de Liquidez",
    "Gestión de Patrimonios Familiares (Multi-Family Office)",
    "Plataformas de Compensación y Compraventa de Créditos de Carbono",
    "Auditoría Fiscal y Automatización de Factura Electrónica B2B",
    "Microcréditos para Emprendedoras en Países Emergentes",

    # Software, Telecommunications & DeepTech (61-70)
    "Computación Cuántica por Horas en QPUs de Superconductores",
    "Plataformas de Pentesting Continuo y Auditoría de CVEs",
    "Redes Privadas 5G/6G para Puertos y Factorías Autónomas",
    "SaaS de Análisis Legal y Auditoría de Contratos M&A con IA",
    "Estudios de Síntesis y Clonación de Voz Ultrarrealista",
    "Pizarras Colaborativas en Tiempo Real y Lienzos Infinitos",
    "Editores de Vídeo Automatizados con Línea de Tiempo e IA",
    "Plataformas de Automatización No-Code y Orquestación de Webhooks",
    "Scraping de Inteligencia de Precios y Monitorización de Stock",
    "Bases de Datos Vectoriales Distribuidas y Memoria para Agentes",

    # Real Estate, Architecture & Construction (71-80)
    "Portales Inmobiliarios de Villas de Ultralujo en Costas Exclusivas",
    "Gestión de Espacios de Coworking y Oficinas Flexibles Híbridas",
    "Arquitectura Modular Prefabricada Passivhaus de Hormigón",
    "Tasaciones Inmobiliarias Automatizadas por Algoritmo Híbrido",
    "Inspección de Edificios y Teclados con Termografía Aérea",
    "Gestión de Comunidades de Propietarios y Votaciones Telemáticas",
    "Alquiler de Trasteros y Almacenamiento Urbano con Acceso Digital",
    "Construcción Sostenible con Madera Contralaminada (CLT)",
    "Mantenimiento de Instalaciones Críticas y Centros de Datos",
    "Restauración de Monumentos Históricos y Patrimonio Cultural",

    # Hospitality, Gastronomy & Leisure (81-90)
    "Retiros de Desconexión Digital en Búnkeres y Cuevas de Lujo",
    "Tostadores Artesanales de Café de Especialidad con Suscripción",
    "Restaurantes de Alta Cocina con Menú Degustación y Maridaje",
    "Clubes Deportivos Indoor de Pádel de Alto Rendimiento",
    "Venta de Entradas y Festivales con Butacas y QR Dinámico",
    "Catering Corporativo para Rodajes y Producciones de Cine",
    "Hoteles Rurales con Experiencias Astronómicas Starlight",
    "Gimnasios Boutique con Clases de Boxeo y Biometría en Vivo",
    "Escuelas de Surf y Campamentos de Alto Rendimiento en Olas",
    "Centros Termales y Balnearios con Aguas Minero-Medicinales",

    # Education, Culture & Society (91-100)
    "Academias de Ingeniería de Software con Sandbox de Código",
    "Plataformas de Citas y Matchmaking con Intenciones Claras",
    "Sedes Electrónicas y Administración Pública Municipal",
    "Conservación de Archivos Históricos y Digitalización de Incunables",
    "Gestión de Galerías de Arte y Venta en Ferias Internacionales",
    "Agencias de Adopción de Mascotas y Rescate Animal",
    "Academias de Música Online con Corrección de Afinación en Vivo",
    "Preparación Telemática de Oposiciones de Alto Nivel Judicial",
    "Servicios Funerarios Ecológicos y Bosques de Memoria",
    "Plataformas de Voluntariado Internacional y Misiones Humanitarias",
)


INDUSTRIES_REAL_ECONOMY_100 = (
    "Agregador de Convocatorias y Empleo Público (BOE y Autonómico)",
    "Portal de Oposiciones Sanitarias y Bolsas de Enfermería",
    "Job Board de Docentes Interinos y Sustituciones Escolares",
    "Plataforma de Libres Designaciones y Movilidad de Funcionarios",
    "Bolsas de Trabajo de Personal Laboral de Ayuntamientos",
    "Portal de Empleo para Fuerzas y Cuerpos de Seguridad",
    "Agregador de Becas Públicas y Contratos de Investigación",
    "Portal de Plazas de Justicia y Letrados de la Administración",
    "Bolsas de Empleo en Empresas Públicas y Entes Estatales",
    "Plataforma de Alertas de Licitaciones Públicas para Pymes",
    "Empresa de Reformas Integrales y Coordinación de Obras",
    "Servicio Urgente de Fontanería y Desatascos 24 Horas",
    "Instaladora de Electricidad y Boletines Eléctricos",
    "Cerrajería Urgente de Apertura de Puertas y Bombines",
    "Empresa de Pintura Profesional y Tratamiento de Humedades",
    "Instalación y Mantenimiento de Aire Acondicionado y Climatización",
    "Carpintería de Madera a Medida y Armarios Empotrados",
    "Empresa de Mudanzas Locales y Guardamuebles Urbanos",
    "Instalación de Paneles Solares para Viviendas Unifamiliares",
    "Empresa de Limpiezas Técnicas y Desinfección de Oficinas",
    "Restaurante Gastrobar y Cocina de Temporada",
    "Pizzería Artesanal Napolitana con Pedidos para Recoger",
    "Dark Kitchen de Hamburguesas Gourmet y Delivery Propio",
    "Cafetería de Barrio y Panadería de Masa Madre",
    "Asador Tradicional de Carnes Maduradas y Brasas",
    "Empresa de Catering para Eventos Privados y Bodas",
    "Marisquería y Cervecería Gallega de Pescado Fresco",
    "Heladería Artesanal con Sabores Veganos y Sin Gluten",
    "Bar de Tapas Tradicional y Vermutería de Barrio",
    "Food Truck de Comida Callejera Mexicana para Fiestas",
    "Gabinete de Psicología Clínica y Terapia de Pareja Online",
    "Clínica de Fisioterapia y Readaptación Postural de Barrio",
    "Centro de Nutrición Clínica y Pérdida de Peso Saludable",
    "Clínica Podológica y Estudio Biomecánico de la Pisada",
    "Centro de Logopedia Infantil y Trastornos del Aprendizaje",
    "Centro de Depilación Láser Diodo y Medicina Estética Local",
    "Estudio de Tatuaje Artístico y Micropigmentación Facial",
    "Óptica de Barrio y Graduación Visual con Taller Propio",
    "Farmacia Comunitaria con Entrega Rápida de Parafarmacia",
    "Centro Auditivo y Adaptación de Audífonos Invisibles",
    "Gimnasio 24 Horas con Acceso Biométrico sin Permanencia",
    "Box de CrossFit Oficial y Halterofilia Guiada",
    "Club de Pádel Indoor con Alquiler de Pistas por Horas",
    "Estudio de Yoga y Pilates Reformer con Máquinas",
    "Escuela de Boxeo Tradicional y Defensa Personal",
    "Plataforma de Entrenadores Personales a Domicilio y Online",
    "Rocódromo Indoor y Escuela de Escalada Deportiva",
    "Centro de Natación y Matronatación Infantil",
    "Club de Ciclismo y Biomecánica Ciclista BikeFitting",
    "Escuela de Baile Social, Salsa, Bachata y Danza Urbana",
    "Taller Mecánico Multimarca de Mantenimiento y Frenos",
    "Taller de Chapa, Pintura y Bancada de Carrocería",
    "Centro Especializado en Neumáticos y Alineación Láser",
    "Concesionario de Coches de Ocasión y Segunda Mano Garantizados",
    "Estación de Pre-ITV y Servicio de Pase de Inspección",
    "Centro de Autolavado a Mano y Detailing Cerámico",
    "Taller Oficial de Reparación de Motos y Scooters Urbanos",
    "Alquiler de Furgonetas de Carga por Horas para Mudanzas",
    "Red de Parkings Urbanos con Reserva de Plaza por Horas",
    "Taller Especializado en Camperización y Homologación de Furgonetas",
    "Boutique de Ropa Urbana y Moda Sostenible Hecha en España",
    "Zapatería Tradicional de Calzado de Piel y Zapatillas",
    "Joyería Artesanal de Plata de Ley y Alianzas de Boda",
    "Tienda de Cosmética Natural, Jabones y Aceites Puros",
    "Papelería Técnica, Copistería Online y Material de Bellas Artes",
    "Floristería de Arte Floral y Ramos de Flores a Domicilio",
    "Juguetería Pedagógica y Juegos de Mesa de Madera",
    "Librería de Barrio y Catálogo de Libros con Envío Rápido",
    "Tienda de Nutrición Deportiva, Proteínas y Suplementación",
    "Tienda de Decoración del Hogar, Alfombras y Menaje",
    "Inmobiliaria de Barrio para Venta y Alquiler Seguro de Pisos",
    "Portal de Habitaciones en Pisos Compartidos para Estudiantes",
    "Centro de Alquiler de Trasteros Urbanos Self-Storage",
    "Marketplace de Plazas de Garaje en Alquiler entre Vecinos",
    "Portal de Fincas Rústicas, Parcelas de Campo y Huertos Urbanos",
    "Alquiler de Despachos y Puestos de Coworking por Días",
    "Bolsa de Locales Comerciales para Nuevos Emprendedores",
    "Complejo de Bungalows Rurales y Campings en la Naturaleza",
    "Comunidad de Coliving Urbano para Nómadas Digitales",
    "Fabricante de Casas Prefabricadas y Módulos de Hormigón",
    "Peluquería Canina y Spa de Estética para Perros",
    "Hotel y Residencia Canina con Parques de Recreo en el Campo",
    "Adiestramiento Canino y Modificación de Conducta Positiva",
    "Red de Paseadores Profesionales de Perros por Horas",
    "Tienda Especializada en Pienso Natural y Snacks Deshidratados",
    "Servicios Funerarios y Crematorio Ecológico de Mascotas",
    "Portal de Adopción Responsable de Animales y Protectoras",
    "Clínica Veterinaria de Proximidad y Medicina Preventiva",
    "Servicio de Urgencias Veterinarias 24 Horas y Hospitalización",
    "Centro de Fisioterapia e Hidroterapia de Rehabilitación Animal",
    "Agencia de Marketing Digital y Publicidad Local en Google Maps",
    "Estudio de Fotografía Social, Bodas y Retratos de Familia",
    "Diseñador Web Freelance y Mantenimiento Técnico de WordPress",
    "Imprenta Digital Rápida de Folletos, Vinilos y Rotulación",
    "Asesoría Laboral y Fiscal Especializada en Autónomos Digitales",
    "Empresa de Prevención de Riesgos Laborales (PRL) para Comercios",
    "Consultora de Protección de Datos (RGPD) y LSSI para Negocios",
    "Mantenimiento Informático de Oficinas y Soporte Remoto 24/7",
    "Agencia de Traducción Jurada Oficial y Traducciones Comerciales",
    "Gestoría Náutica y Trámites de Tráfico para Particulares",
)

INDUSTRIES_200 = INDUSTRIES_100 + INDUSTRIES_REAL_ECONOMY_100

BUSINESS_MODELS_6 = (
    ("marketplace_bilateral", "Marketplace Bilateral P2P (Oferta y Demanda con Fianza o Escrow)"),
    ("enterprise_b2b_saas", "SaaS B2B por Suscripción y Cuotas de Uso (Multi-Usuario con Roles)"),
    ("direct_booking_checkout", "Reserva Directa y Compra Transaccional Inmediata (Horas / Butacas)"),
    ("iot_hardware_scada", "Monitorización de Hardware, Telemetría en Vivo y Control Bi-direccional"),
    ("private_concierge_vetting", "Boutique Exclusiva de Alto Ticket con Formulario de Admisión / Vetting"),
    ("community_gamified_academy", "Comunidad Gamificada, Membresía y Acreditación de Hitos (Skool / Podio)"),
)

REGULATORY_REGIMES_5 = (
    ("health_rgpd_hipaa", "Sanitario y Datos Sensibles (Cumplimiento RGPD Art. 9 / HIPAA / Tracking Anónimo)"),
    ("financial_banking_aml", "Financiero y Custodia de Fondos (Validación Luhn / Escrow / Prevención Blanqueo)"),
    ("official_civic_gov", "Administración Pública y Legal (Firma Telemática Cl@ve / Código CSV / Sede Oficial)"),
    ("restricted_defense_safety", "Alta Seguridad / Industrial (Protocolos ITAR / Paros de Emergencia / Residuos)"),
    ("commercial_standard", "Comercio Global Estándar (RGPD Básico / Stripe / Factura Transaccional)"),
)


@dataclass(frozen=True)
class OrthogonalCoordinate:
    """Representa una coordenada de negocio 100% no solapada."""
    coordinate_id: int
    industry: str
    business_model_key: str
    business_model_desc: str
    regulatory_key: str
    regulatory_desc: str

    def generate_prompt_seed(self) -> str:
        """Generate synthetic prompt seeds for the given enterprise sector."""
        return (
            f"Plataforma de {self.industry} operando bajo el modelo de {self.business_model_desc}, "
            f"sujeta al marco regulatorio de {self.regulatory_desc}."
        )



def generate_all_6000_coordinates() -> list[OrthogonalCoordinate]:
    """Genera las 6.000 coordenadas ortogonales (200 x 6 x 5) deterministas."""
    coords: list[OrthogonalCoordinate] = []
    idx = 1
    for ind in INDUSTRIES_200:
        for bm_key, bm_desc in BUSINESS_MODELS_6:
            for reg_key, reg_desc in REGULATORY_REGIMES_5:
                coords.append(
                    OrthogonalCoordinate(
                        coordinate_id=idx,
                        industry=ind,
                        business_model_key=bm_key,
                        business_model_desc=bm_desc,
                        regulatory_key=reg_key,
                        regulatory_desc=reg_desc,
                    )
                )
                idx += 1
    return coords

def generate_all_3000_coordinates() -> list[OrthogonalCoordinate]:
    """Genera las 3.000 coordenadas ortogonales (100 x 6 x 5) deterministas."""
    coords: list[OrthogonalCoordinate] = []
    idx = 1
    for ind in INDUSTRIES_100:
        for bm_key, bm_desc in BUSINESS_MODELS_6:
            for reg_key, reg_desc in REGULATORY_REGIMES_5:
                coords.append(
                    OrthogonalCoordinate(
                        coordinate_id=idx,
                        industry=ind,
                        business_model_key=bm_key,
                        business_model_desc=bm_desc,
                        regulatory_key=reg_key,
                        regulatory_desc=reg_desc,
                    )
                )
                idx += 1
    return coords


def init_taxonomy_matrix_tables() -> None:
    """Initialize the SQLite schema for the enterprise taxonomy coordinates in WAL mode."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(DB_PATH), timeout=60.0) as conn:
        conn.execute("PRAGMA journal_mode = WAL;")
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS socratic_benchmark_progress (
                coordinate_id INTEGER PRIMARY KEY,
                industry TEXT NOT NULL,
                business_model TEXT NOT NULL,
                regulatory_regime TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                score REAL,
                domain_name TEXT,
                questions_count INTEGER,
                critique TEXT,
                axiom TEXT,
                completed_at TIMESTAMP
            );
        """)
        conn.commit()


def populate_coordinates_if_empty() -> int:
    """Populate all 6,000 orthogonal coordinates inserting pending items."""
    init_taxonomy_matrix_tables()
    with sqlite3.connect(str(DB_PATH), timeout=60.0) as conn:
        cur = conn.cursor()
        coords = generate_all_6000_coordinates()
        cur.executemany(
            """
            INSERT OR IGNORE INTO socratic_benchmark_progress (
                coordinate_id, industry, business_model, regulatory_regime, status
            ) VALUES (?, ?, ?, ?, 'pending');
            """,
            [(c.coordinate_id, c.industry, c.business_model_key, c.regulatory_key) for c in coords],
        )
        conn.commit()
        cur.execute("SELECT count(*) FROM socratic_benchmark_progress;")
        return cur.fetchone()[0]
