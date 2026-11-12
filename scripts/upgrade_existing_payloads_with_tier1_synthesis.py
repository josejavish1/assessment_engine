import asyncio
import json
import logging
from pathlib import Path
from assessment_engine.infrastructure.genai_client import create_genai_client
from assessment_engine.application.services.universal_tower_synthesizer import UniversalTowerSynthesizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

async def main():
    REPO_ROOT = Path(__file__).resolve().parents[1]
    towers_dir = REPO_ROOT / "working" / "molins"
    client = create_genai_client()
    
    synthesizer = UniversalTowerSynthesizer(llm_client=client)
    
    firmographics = {
        "client_name": "Cementos Molins",
        "industry_vertical": "Heavy Manufacturing",
        "annual_revenue_eur": 1144000000.0,
        "operational_scale": "Global with 9 precast plants, 2 CPDs in Sant Vicenç, and SECIL Portugal acquisition."
    }

    for i in range(1, 11):
        tower_code = f"T{i}"
        fp = towers_dir / tower_code / f"blueprint_{tower_code.lower()}_payload.json"
        if not fp.exists():
            continue
            
        with open(fp) as f:
            data = json.load(f)
            
        logger.info(f"Synthesizing {tower_code} using new Tier-1 Map-Reduce architecture...")
        
        tower_payload = {
            "tower_id": tower_code,
            "tower_name": data.get("document_meta", {}).get("tower_name") or tower_code,
            "adjacent_evidence_summary": "", # Add global facts if available
            "pillars": data.get("pillars_analysis", [])
        }
        
        # Execute the map-reduce synthesis
        result = await synthesizer.synthesize_tower(tower_payload, firmographics)
        
        # Update payload
        data["executive_snapshot"] = result["executive_summary"]
        data["pillars_analysis"] = result["pillars"]
        
        with open(fp, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Successfully wrote {tower_code} payload.")

if __name__ == "__main__":
    asyncio.run(main())
