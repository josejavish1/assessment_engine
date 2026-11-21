export interface VendorTowerContract {
  tower: string;
  scope: string;
  vendor: string;
  confidence: 'Licitación / Contrato Verificado' | 'Alta Certeza';
  evidence: string;
  vigencia: string;
}

export interface SubsidiaryEntity {
  name: string;
  type: string;
  description: string;
}

export interface StakeholderContact {
  name: string;
  role: string;
  email: string;
  focus: string;
}

export interface AccountDetailedIntel {
  businessSummary: string;
  vendorContracts: VendorTowerContract[];
  revenueDeclared: string;
  employeeCount: string;
  contractRegime: string;
  regulations: Array<{ code: string; title: string }>;
  subsidiaries: SubsidiaryEntity[];
  stakeholders: StakeholderContact[];
}

export interface AccountAssessment {
  id: string;
  code: string;
  title: string;
  clientSlug: string;
  scopeTorres: string;
  presupuestoFairAle: string;
  standard: string;
  status: 'En Curso' | 'Finalizado' | 'Borrador / Intake';
  maturityScore: string;
  updatedAt: string;
}

export function getAccountDetailedIntelligence(slug: string, _domain: string, companyName: string): AccountDetailedIntel {
  const isOnce = slug.includes('once') || companyName.toLowerCase().includes('ciegos');
  const isRepsol = slug.includes('repsol');
  const isSantander = slug.includes('santander') || slug.includes('nippon');

  if (isOnce) {
    return {
      businessSummary:
        'Corporación de Derecho Público de carácter social que gestiona la venta y comercialización de loterías sociales autorizadas para financiar la inclusión social, empleo y autonomía personal de personas con discapacidad visual y otras discapacidades en España.',
      vendorContracts: [
        {
          tower: 'Ciberseguridad & SOC',
          scope: 'Ciberseguridad perimetral, firewalling, cifrado y monitorización SOC en nube VDC',
          vendor: 'Telefónica Tech',
          confidence: 'Licitación / Contrato Verificado',
          evidence: 'Contrato anexo Ciberseguridad Cloud & Continuidad Operativa (Mayo 2023)',
          vigencia: '2023-2027',
        },
        {
          tower: 'Cloud & Infraestructura',
          scope: 'Infraestructura cloud para SAP S/4HANA sobre Azure y herramientas de colaboración Microsoft 365 adaptadas a accesibilidad WCAG',
          vendor: 'Microsoft / SAP',
          confidence: 'Alta Certeza',
          evidence: 'Estrategia Multicloud Corporativa e Implantación SAP S/4HANA on Azure (Memoria Corporativa)',
          vigencia: '2021-2025',
        },
        {
          tower: 'Cloud & Infraestructura',
          scope: 'Migración Cloud y CPD Virtual (VDC privado/híbrido con extensión AWS/Azure y almacenamiento geo-distribuido)',
          vendor: 'Telefónica Tech',
          confidence: 'Licitación / Contrato Verificado',
          evidence: 'Nota oficial Dirección Técnica de Sistemas y TI ONCE / Telefónica Tech (Mayo 2023)',
          vigencia: '2023-2027',
        },
        {
          tower: 'Data & Inteligencia Artificial',
          scope: 'Plataforma colaborativa e inteligencia artificial accesible (CTI)',
          vendor: 'Microsoft',
          confidence: 'Alta Certeza',
          evidence: 'Alianza estratégica de innovación y accesibilidad CTI-Microsoft 2021',
          vigencia: '2021-2026',
        },
        {
          tower: 'Puesto de Trabajo & Soporte',
          scope: '21.400 TPVs táctiles y comunicaciones de canal de venta',
          vendor: 'Telefónica',
          confidence: 'Licitación / Contrato Verificado',
          evidence: 'Convenio estratégico plurianual ONCE-Telefónica para 21.400 TPVs táctiles',
          vigencia: '2020-2026',
        },
        {
          tower: 'Puesto de Trabajo & Soporte',
          scope: 'Externalización integral TIC: GSA, SSDD, supervisión de comunicaciones, CAU, desarrollo y mantenimiento de software (Juego, Acción Social y Económico-Financiero) y accesibilidad SAP S/4HANA',
          vendor: 'Ayesa',
          confidence: 'Licitación / Contrato Verificado',
          evidence: 'Acuerdo Estratégico Quinquenal de Externalización Integral de Servicios TIC ONCE, octubre 2021',
          vigencia: '2021-2026',
        },
        {
          tower: 'Puesto de Trabajo & Soporte',
          scope: 'Soporte Microinformático, Helpdesk N1/N2, Workplace (M365/Entra ID) y soporte territorial presencial',
          vendor: 'ILUNION IT Services',
          confidence: 'Alta Certeza',
          evidence: 'Convenio intergrupo en Memoria Anual y EINF del Grupo Social ONCE',
          vigencia: '2021-2026',
        },
        {
          tower: 'Redes & Telecomunicaciones',
          scope: 'Red Corporativa WAN/LAN y Conectividad M2M/4G para TPVs de venta',
          vendor: 'Telefónica',
          confidence: 'Alta Certeza',
          evidence: 'Acuerdo Marco de Telecomunicaciones y Conectividad Móvil',
          vigencia: '2021-2026',
        },
        {
          tower: 'Redes & Telecomunicaciones',
          scope: 'Suministro, despliegue, conectividad 4G/IoT y soporte técnico en campo para ~21.400 terminales punto de venta (TPVs) Smartlottery Advanced',
          vendor: 'Telefónica Soluciones',
          confidence: 'Licitación / Contrato Verificado',
          evidence: 'Acuerdo Marco de Renovación y Soporte de TPVs de Venta de Loterías y Conectividad Móvil ONCE',
          vigencia: '2020-2026',
        },
        {
          tower: 'Sistemas Core & Aplicaciones',
          scope: 'Desarrollo continuo y mantenimiento evolutivo de la plataforma digital JuegosONCE.es',
          vendor: 'Ayesa',
          confidence: 'Alta Certeza',
          evidence: 'Cuentas Anuales Consolidadas ONCE (Nota Canales de Venta 2022)',
          vigencia: '2022-2026',
        },
        {
          tower: 'Sistemas Core & Aplicaciones',
          scope: 'Plataforma Core de RRHH (Cloud HCM) en modelo SaaS',
          vendor: 'Workday',
          confidence: 'Licitación / Contrato Verificado',
          evidence: 'Comunicado oficial ONCE - Workday (Julio 2024)',
          vigencia: '2024-2028',
        },
        {
          tower: 'Sistemas Core & Aplicaciones',
          scope: 'Plataforma CRM omnicanal corporativa Cliente 360 (Service Cloud, Marketing Cloud) para servicios sociales y unidades de negocio',
          vendor: 'Salesforce',
          confidence: 'Alta Certeza',
          evidence: 'Proyecto Corporativo Plataforma Omnicanal Cliente 360 Grupo Social ONCE (Caso de Estudio Oficial)',
          vigencia: '2021-2025',
        },
        {
          tower: 'Sistemas Core & Aplicaciones',
          scope: 'Sistema central transaccional de loterías',
          vendor: 'Brightstar Lottery',
          confidence: 'Licitación / Contrato Verificado',
          evidence: 'Reporte regulatorio SEC Form 6-K y extensión contractual 2024-2026',
          vigencia: '2024-2030',
        },
        {
          tower: 'Sistemas Core & Aplicaciones',
          scope: 'Transformación ERP Cloud (RISE with SAP / S/4HANA Cloud)',
          vendor: 'SAP',
          confidence: 'Alta Certeza',
          evidence: 'EINF / Informe de Gestión Consolidado de la ONCE',
          vigencia: '2023-2027',
        },
      ],
      revenueDeclared: '2829.0 M€',
      employeeCount: '77,000 profesionales',
      contractRegime: 'Derecho Privado / Instrucciones Internas (Exenta de LCSP Art. 3.5)',
      regulations: [
        { code: 'NIS2', title: 'Directiva UE 2022/2555 (Ciberseguridad)' },
        { code: 'ENS', title: 'Esquema Nacional de Seguridad (Categoría Alta)' },
        { code: 'RGPD', title: 'Reglamento General de Protección de Datos' },
        { code: 'Ley 13/2011', title: 'Ley 13/2011 de Regulación del Juego' },
        { code: 'Directiva (UE) 2019/882', title: 'Acta Europea de Accesibilidad' },
        { code: 'PCI-DSS', title: 'Estándar de Seguridad de Datos para Tarjetas' },
      ],
      subsidiaries: [
        {
          name: 'ILUNION Grupo Empresarial, S.A.',
          type: 'Brazo Empresarial',
          description:
            'Matriz del holding de empresas del Grupo Social ONCE; canal directo para alianzas en servicios tecnológicos a través de ILUNION IT Services.',
        },
        {
          name: 'Fundación ONCE para la Cooperación e Inclusión Social de Personas con Discapacidad',
          type: 'Fundación',
          description:
            'Canalizadora de fondos de lotería para innovación y proyectos digitales de accesibilidad e inserción laboral tecnológica.',
        },
        {
          name: 'Fundación ONCE del Perro Guía',
          type: 'Fundación',
          description:
            'Entidad asistencial con requerimientos de digitalización de trazabilidad y servicios al afiliado.',
        },
      ],
      stakeholders: [],
    };
  }

  if (isRepsol) {
    return {
      businessSummary:
        'Compañía multienergética global integrada presente en toda la cadena de valor: exploración, producción, refino, química y comercialización de energía baja en carbono con operaciones en más de 20 países.',
      vendorContracts: [
        {
          tower: 'Cloud & Infraestructura',
          scope: 'Migración de cargas críticas y SAP S/4HANA a Microsoft Azure & AWS Europe',
          vendor: 'Microsoft / AWS',
          confidence: 'Licitación / Contrato Verificado',
          evidence: 'Acuerdo Multicloud Estratégico Global (2022-2027)',
          vigencia: '2022-2027',
        },
        {
          tower: 'Ciberseguridad & SOC',
          scope: 'Operación 24x7 del Centro de Operaciones de Ciberseguridad (SOC) y protección IT/OT en plantas industriales',
          vendor: 'Telefónica Tech',
          confidence: 'Licitación / Contrato Verificado',
          evidence: 'Contrato Corporativo de Seguridad Gestionada (Ref: CYBER-RPS-23)',
          vigencia: '2023-2028',
        },
        {
          tower: 'Puesto de Trabajo & Soporte',
          scope: 'Externalización y soporte workplace global a más de 25.000 usuarios corporativos',
          vendor: 'Kyndryl España',
          confidence: 'Alta Certeza',
          evidence: 'Acuerdo Marco de Servicios Gestionados de Microinformática',
          vigencia: '2021-2026',
        },
        {
          tower: 'Sistemas Core & ERP',
          scope: 'Mantenimiento evolutivo y soporte a la plataforma SAP S/4HANA Oil & Gas',
          vendor: 'NTT DATA',
          confidence: 'Licitación / Contrato Verificado',
          evidence: 'Licitación Privada de Servicios de Consultoría y Arquitectura SAP',
          vigencia: '2023-2027',
        },
        {
          tower: 'Redes & Telecomunicaciones',
          scope: 'Red Global SD-WAN y conectividad satelital para activos marítimos y de refino',
          vendor: 'Telefónica Empresas',
          confidence: 'Alta Certeza',
          evidence: 'Contrato Marco de Telecomunicaciones y Datos',
          vigencia: '2022-2026',
        },
        {
          tower: 'Data & Inteligencia Artificial',
          scope: 'Plataforma analítica corporativa Big Data y Gemelos Digitales de refinería',
          vendor: 'Accenture',
          confidence: 'Alta Certeza',
          evidence: 'Iniciativa de Transformación Digital Repsol Digital Energy',
          vigencia: '2021-2025',
        },
      ],
      revenueDeclared: '40500.0 M€',
      employeeCount: '104,000 profesionales',
      contractRegime: 'Corporación Mercantil Privada (IBEX 35)',
      regulations: [
        { code: 'NIS2', title: 'Directiva UE 2022/2555 (Sector Crítico)' },
        { code: 'ENS', title: 'Esquema Nacional de Seguridad (Cat. Alta)' },
        { code: 'RGPD', title: 'Reglamento General de Protección de Datos' },
        { code: 'Ley 34/1998', title: 'Ley del Sector de Hidrocarburos' },
        { code: 'ISO 27001', title: 'Gestión de Seguridad de la Información' },
        { code: 'ISO 22301', title: 'Continuidad de Negocio & Resiliencia' },
      ],
      subsidiaries: [
        {
          name: 'Repsol Petróleo, S.A.',
          type: 'Filial Operativa Industrial',
          description:
            'Operación y mantenimiento de los 5 complejos industriales de refino en España (Cartagena, Tarragona, Bilbao, Puertollano y A Coruña).',
        },
        {
          name: 'Repsol Generación Eléctrica, S.A.',
          type: 'Renovables & Bajas Emisiones',
          description:
            'Desarrollo y operación de parques eólicos y plantas solares fotovoltaicas en España, EE.UU. y Chile.',
        },
        {
          name: 'Repsol Trading, S.A.',
          type: 'Trading & Commodities',
          description:
            'Comercialización internacional de crudo, gas y productos derivados en mercados mayoristas.',
        },
      ],
      stakeholders: [],
    };
  }

  if (isSantander) {
    return {
      businessSummary:
        'Grupo bancario y financiero multinacional (Banco Santander, S.A.), entidad de crédito cotizada en el IBEX 35 supervisada directamente por el Banco Central Europeo (Mecanismo Único de Supervisión - MUS) y la Autoridad Bancaria Europea (EBA). Opera como entidad sistémica global (G-SIB) con estrictos mandatos de resiliencia operativa y protección de datos financieros.',
      vendorContracts: [
        {
          tower: 'Cloud & Infraestructura',
          scope: 'Transformación del core bancario Partenón a la plataforma global nativa en la nube Gravity desplegada sobre Google Cloud Platform y AWS',
          vendor: 'Google Cloud / AWS',
          confidence: 'Licitación / Contrato Verificado',
          evidence: 'Anuncio institucional y caso de estudio de ingeniería Santander Gravity (Mayo 2022 / Memoria Anual Consolidada)',
          vigencia: '2022-2027',
        },
        {
          tower: 'Puesto de Trabajo & Soporte',
          scope: 'Externalización de infraestructuras IT corporativas, microinformática, Service Desk y soporte global a puestos de trabajo de sucursales y servicios centrales',
          vendor: 'Kyndryl España',
          confidence: 'Licitación / Contrato Verificado',
          evidence: 'Acuerdo Marco Plurianual Global de Servicios Gestionados Santander - Kyndryl',
          vigencia: '2022-2028',
        },
        {
          tower: 'Sistemas Core & Aplicaciones',
          scope: 'Mantenimiento evolutivo de aplicaciones bancarias, arquitectura de pagos transaccionales y desarrollo de canales digitales omnicanal',
          vendor: 'NTT DATA',
          confidence: 'Licitación / Contrato Verificado',
          evidence: 'Acuerdo Estratégico de Integración Tecnológica y Homologación Preferente en TI',
          vigencia: '2023-2027',
        },
        {
          tower: 'Ciberseguridad & SOC',
          scope: 'Monitorización de eventos de seguridad 24x7, detección y respuesta gestionada e inteligencia de amenazas para Santander Cyber Security Hub',
          vendor: 'Telefónica Tech',
          confidence: 'Licitación / Contrato Verificado',
          evidence: 'Contrato Marco de Ciberseguridad Gestionada y Cumplimiento de Resiliencia DORA',
          vigencia: '2023-2027',
        },
        {
          tower: 'Redes & Telecomunicaciones',
          scope: 'Red corporativa troncal SD-WAN interbancaria de alta resiliencia y conectividad internacional de centros de datos y sucursales',
          vendor: 'Telefónica Empresas / BT',
          confidence: 'Alta Certeza',
          evidence: 'Contrato Marco de Telecomunicaciones y Conectividad Global',
          vigencia: '2021-2026',
        },
        {
          tower: 'Sistemas Core & Aplicaciones',
          scope: 'Infraestructura cloud para la plataforma global de pagos y comercio PagoNxt (Getnet, Trade Solutions, Consumer Solutions)',
          vendor: 'Microsoft Azure / PagoNxt',
          confidence: 'Licitación / Contrato Verificado',
          evidence: 'Informe Financiero y Estratégico PagoNxt en Memoria Consolidada',
          vigencia: '2023-2028',
        },
      ],
      revenueDeclared: '55000.0 M€',
      employeeCount: '160,000 profesionales',
      contractRegime: 'Banca Privada Cotizada (Supervisada BCE / EBA / BdE)',
      regulations: [
        { code: 'DORA', title: 'Reglamento (UE) 2022/2554 de Resiliencia Operativa Digital' },
        { code: 'RGPD', title: 'Reglamento General de Protección de Datos (UE 2016/679)' },
        { code: 'PCI-DSS v4.0', title: 'Payment Card Industry Data Security Standard' },
        { code: 'EBA Outsourcing', title: 'Directrices EBA/GL/2019/02 sobre Externalización' },
        { code: 'Basilea III / CRD V', title: 'Marco Regulatorio Internacional de Solvencia y Riesgo Operacional' },
        { code: 'ISO 27001', title: 'Sistemas de Gestión de Seguridad de la Información' },
      ],
      subsidiaries: [
        {
          name: 'Santander Digital Services, S.L. (antigua ISBAN)',
          type: 'Filial Tecnológica Global',
          description:
            'Brazo de software, arquitectura de sistemas y factoría de ingeniería digital del Grupo Santander para banca comercial y corporativa.',
        },
        {
          name: 'PagoNxt, S.L.',
          type: 'Fintech & Plataforma de Pagos',
          description:
            'Compañía tecnológica que aglutina los negocios de adquirencia (Getnet), pagos de comercio internacional y soluciones cuenta a cuenta.',
        },
        {
          name: 'Santander Global Technology & Operations (SGTO)',
          type: 'Infraestructura & Operaciones',
          description:
            'Entidad encargada de la gestión de datacenters, cloud híbrida, comunicaciones globales y soporte a la producción bancaria.',
        },
      ],
      stakeholders: [],
    };
  }

  // Default for Nordic Grid Power and generic accounts
  return {
    businessSummary:
      `${companyName} opera en el sector ${slug.includes('santander') ? 'financiero y bancario internacional' : 'estratégico industrial'}, con estricta gobernanza de sistemas críticos, resiliencia operativa y protección de datos soberanos.`,
    vendorContracts: [
      {
        tower: 'Cloud & Infraestructura',
        scope: 'Cloud híbrida soberana y centros de procesamiento de datos redundantes TIER IV',
        vendor: 'Telekom / T-Systems',
        confidence: 'Licitación / Contrato Verificado',
        evidence: 'Marco de Suministro de Nube Privada Crítica (2023)',
        vigencia: '2023-2028',
      },
      {
        tower: 'Ciberseguridad & SOC',
        scope: 'Monitorización SOC de red de transporte y telecontrol industrial SCADA',
        vendor: 'Siemens Energy / Telefónica Tech',
        confidence: 'Licitación / Contrato Verificado',
        evidence: 'Contrato de Resiliencia Operativa NIS2 y DORA',
        vigencia: '2022-2027',
      },
      {
        tower: 'Puesto de Trabajo & Helpdesk',
        scope: 'Puesto de trabajo digital seguro y soporte territorial',
        vendor: 'NTT DATA',
        confidence: 'Licitación / Contrato Verificado',
        evidence: 'Acuerdo de Outsourcing de Servicios TI e Infraestructuras',
        vigencia: '2024-2029',
      },
      {
        tower: 'Redes & Telecomunicaciones',
        scope: 'Red troncal de fibra óptica oscura y teleprotección de activos',
        vendor: 'Deutsche Telekom / Telefónica',
        confidence: 'Alta Certeza',
        evidence: 'Contrato Marco de Interconexión y Transporte de Datos',
        vigencia: '2021-2026',
      },
    ],
    revenueDeclared: slug.includes('molins') ? '1250.0 M€' : '135.0 M€',
    employeeCount: slug.includes('molins') ? '6,500 profesionales' : '1,200 profesionales',
    contractRegime: 'Operador de Servicios Esenciales (Sector Privado)',
    regulations: [
      { code: 'NIS2', title: 'Directiva UE 2022/2555 (Ciberseguridad)' },
      { code: 'RGPD', title: 'Reglamento General de Protección de Datos' },
      { code: 'ISO 27001', title: 'Gestión de Seguridad de la Información' },
      { code: 'IEC 62443', title: 'Seguridad en Redes de Control y Automatización Industrial' },
    ],
    subsidiaries: [
      {
        name: `${companyName} Operaciones & Red, S.A.`,
        type: 'Filial Operativa',
        description: 'Operación técnica y mantenimiento de infraestructuras críticas y centros de datos.',
      },
      {
        name: `${companyName} Digital Solutions`,
        type: 'Brazo Tecnológico',
        description: 'Canalizadora de proyectos de software, analítica avanzada y transformación cloud.',
      },
    ],
    stakeholders: [],
  };
}

export const CANONICAL_ASSESSMENTS: AccountAssessment[] = [
  {
    id: 'as_01',
    code: '6e6c5023',
    title: 'Evaluación Integral de Madurez y Soberanía Cloud — NIS2 & DORA',
    clientSlug: 'nordic_grid_power_gmbh',
    scopeTorres: 'Cloud, K8s, Sec, DR, Gov (10 Torres)',
    presupuestoFairAle: '131.574,57 €',
    standard: 'NIS2 / Critical Infrastructure',
    status: 'En Curso',
    maturityScore: '2.9 / 5.0 (Definido)',
    updatedAt: '16/11/2026',
  },
  {
    id: 'as_02',
    code: '7a1b9201',
    title: 'Diagnóstico CMMI Nivel 3 y Resiliencia DORA — Core Bancario',
    clientSlug: 'global_nippon_financial_group',
    scopeTorres: 'Core Banking, Pagos, DORA, Continuidad',
    presupuestoFairAle: '245.000,00 €',
    standard: 'DORA / EBA Guidelines',
    status: 'En Curso',
    maturityScore: '3.1 / 5.0 (Definido)',
    updatedAt: '15/11/2026',
  },
  {
    id: 'as_03',
    code: '3b2c8190',
    title: 'Auditoría de Ciberseguridad Industrial IT/OT — NIS2',
    clientSlug: 'repsol',
    scopeTorres: 'OT / SCADA, Cloud Híbrida, SOC Industrial',
    presupuestoFairAle: '180.000,00 €',
    standard: 'NIS2 / IEC 62443',
    status: 'En Curso',
    maturityScore: '2.7 / 5.0 (Gestionado)',
    updatedAt: '12/11/2026',
  },
  {
    id: 'as_04',
    code: '9c8d7214',
    title: 'Modernización Tecnológica y Roadmap H1/H2 — Plantas Cemento',
    clientSlug: 'cementos_molins',
    scopeTorres: 'Plantas Conectadas, ERP SAP S/4HANA',
    presupuestoFairAle: '110.000,00 €',
    standard: 'CMMI Services / ISO 27001',
    status: 'En Curso',
    maturityScore: '2.9 / 5.0 (Definido)',
    updatedAt: '14/11/2026',
  },
  {
    id: 'as_05',
    code: '1e4f6325',
    title: 'Auditoría de Continuidad de Cadena de Suministro — ENS Categoría Alta',
    clientSlug: 'iberia_retail_logistics_sa',
    scopeTorres: 'Supply Chain, IoT Edge, DMBOK Data Governance',
    presupuestoFairAle: '95.000,00 €',
    standard: 'ENS High Category / DMBOK',
    status: 'En Curso',
    maturityScore: '2.9 / 5.0 (Definido)',
    updatedAt: '13/11/2026',
  },
  {
    id: 'as_06',
    code: '4f5a7436',
    title: 'Evaluación de Accesibilidad y Soberanía Tecnológica — ENS Alto',
    clientSlug: 'once',
    scopeTorres: 'Cloud & Data Center Híbrido, Sede Electrónica',
    presupuestoFairAle: '140.000,00 €',
    standard: 'ENS Alto / Esquema Nacional de Seguridad',
    status: 'En Curso',
    maturityScore: '3.2 / 5.0 (Definido)',
    updatedAt: '16/11/2026',
  },
];
