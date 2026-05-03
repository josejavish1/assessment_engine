import json
from pathlib import Path

out = """/home/jsanchhi/assessment_engine/.venv/lib/python3.11/site-packages/google/adk/features/_feature_decorator.py:72: UserWarning: [EXPERIMENTAL] feature FeatureName.PLUGGABLE_AUTH is enabled.
  check_feature_enabled()
{"timestamp": "2026-05-02 14:06:32,432", "severity": "INFO", "logger": "google_genai._api_client", "message": "The project/location from the environment variables will take precedence over the API key from the environment variables."}
{"timestamp": "2026-05-02 14:06:32,530", "severity": "INFO", "logger": "google_adk.google.adk.models.google_llm", "message": "Sending out request, model: gemini-2.5-pro, backend: GoogleLLMVariant.VERTEX_AI, stream: False"}
{"timestamp": "2026-05-02 14:06:32,530", "severity": "INFO", "logger": "google_genai.models", "message": "AFC is enabled with max remote calls: 10."}
{"timestamp": "2026-05-02 14:06:44,784", "severity": "INFO", "logger": "google_adk.google.adk.models.google_llm", "message": "Response received from the model."}
{"timestamp": "2026-05-02 14:06:44,792", "severity": "INFO", "logger": "assessment_engine.scripts.lib.ai_client", "message": "AI Agent Telemetry", "telemetry": {"agent_name": "N/A", "model": "N/A", "user_id": "ad-hoc-user", "duration_seconds": 13.15, "retries": 0, "output_schema": "ProductOwnerPlan"}}
{"timestamp": "2026-05-02 14:06:44,798", "severity": "INFO", "logger": "__main__", "message": "Plan generado en /home/jsanchhi/assessment_engine/working/product_owner_requests/20260502_140631_prueba"}
"""
for line in out.splitlines():
    try:
        log_data = json.loads(line)
        msg = log_data.get("message", "")
        if "Plan generado en " in msg:
            request_dir = msg.split("Plan generado en ")[1].strip()
            plan_path = Path(request_dir) / "plan.json"
            if plan_path.exists():
                plan_data = plan_path.read_text(encoding="utf-8")
                print("FOUND IT!")
                exit(0)
    except Exception as e:
        print(f"Exception: {e} for line {line}")
        continue
print("NOT FOUND")
