import asyncio
from assessment_engine.scripts.tools.run_product_owner_orchestrator import (
    generate_plan,
    load_orchestrator_policy,
)


async def main():
    p = load_orchestrator_policy()
    res = await generate_plan(
        "Crea un nuevo worker asíncrono para procesar facturas.", p
    )
    import json

    print(json.dumps(res, indent=2))


asyncio.run(main())
