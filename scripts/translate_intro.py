import asyncio
from pathlib import Path

from google import genai

from assessment_engine.infrastructure.genai_client import ModelTier, get_model

client = genai.Client()
semaphore = asyncio.Semaphore(10)

async def translate_file(path: Path):
    text = path.read_text(encoding="utf-8-sig")
    
    prompt = f"""
Actúa como Traductor Técnico Senior especializado en Arquitectura de Sistemas y Consultoría Tecnológica (McKinsey/Gartner).
Traduce al ESPAÑOL TÉCNICO FORMAL (castellano neutro) el siguiente documento Markdown de introducción metodológica.

Reglas obligatorias:
1. Mantén intacta toda la estructura Markdown (#, ##, ###, viñetas -, negritas **, tablas).
2. Conserva intactos todos los nombres de marcas, tecnologías, acrónimos y nombres propios: (HPE SimpliVity, NetApp, Oracle 10g/11g, CentOS, SAP S/4HANA, Google Cloud, AWS, Azure, OCI, Equinix, VMware Broadcom, Sant Vicenç dels Horts, Secil, Open FAIR, ALE, P90, NIS2, ISO 27001, etc.).
3. Utiliza terminología técnica estándar del sector IT.
4. Devuelve ÚNICAMENTE el texto traducido en Markdown, sin introducciones ni comentarios adicionales.

TEXTO A TRADUCIR:
\"\"\"
{text}
\"\"\"
"""
    async with semaphore:
        for attempt in range(3):
            try:
                resp = await client.aio.models.generate_content(
                    model=get_model(ModelTier.FAST),
                    contents=prompt,
                )
                clean_res = resp.text.strip()
                if clean_res.startswith("```"):
                    lines = clean_res.splitlines()
                    if lines and lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    clean_res = "\n".join(lines)
                path.write_text(clean_res.strip() + "\n", encoding="utf-8")
                print(f"✓ {path.parent.name}/{path.name} traducido al español.")
                return
            except Exception as e:
                await asyncio.sleep(2)
                if attempt == 2:
                    print(f"❌ Error en {path}: {e}")

async def main():
    md_files = sorted(Path("working/molins").glob("T*/asis_modules/01_introduccion.md"))
    tasks = [translate_file(f) for f in md_files]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
    print("Traducción de 01_introduccion.md completada.")
