# src/assessment_engine/kanban_server.py
import json
import shutil
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Optional, Any
from pathlib import Path

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Schemas ---
class Task(BaseModel):
    id: str
    title: str
    description: str
    status: Optional[str] = None

class Columns(BaseModel):
    backlog: List[Task]
    inProgress: List[Task]
    done: List[Task]

class UpdateTasks(BaseModel):
    tasks: Columns

# --- MCP Server Logic (adapted) ---
ROOT = Path(__file__).resolve().parents[2]
CASES_DIR = ROOT / "cases"

# These would be imported from the assessment_engine schemas
class BlueprintPayload(BaseModel):
    document_meta: Dict[str, Any]

class AnnexPayload(BaseModel):
    document_meta: Dict[str, Any]

def _read_json_file(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))

def _summarize_validation_error(error: ValidationError) -> list[str]:
    summary: list[str] = []
    for item in error.errors():
        location = " -> ".join(str(part) for part in item["loc"])
        summary.append(f"{location}: {item['msg']}")
    return summary

def _inspect_payload_artifact(path: Path, schema, artifact_name: str) -> dict:
    # Simplified version for kanban
    if not path.exists():
        return {"status": "missing"}
    try:
        data = _read_json_file(path)
        schema.model_validate(data)
        return {"status": "valid"}
    except (json.JSONDecodeError, OSError, UnicodeDecodeError, ValidationError):
        return {"status": "invalid"}

def _canonical_overall_status(canonical_state: dict) -> str:
    payload_statuses = (
        canonical_state["blueprint_payload"]["status"],
        canonical_state["annex_payload"]["status"],
    )
    if all(status == "valid" for status in payload_statuses):
        return "done"
    if any(status in {"invalid"} for status in payload_statuses):
        return "backlog"  # Needs attention
    if any(status in {"valid", "present"} for status in payload_statuses):
        return "inProgress"
    return "backlog"

def get_cases_as_tasks() -> Columns:
    tasks = Columns(backlog=[], inProgress=[], done=[])
    if not CASES_DIR.exists():
        CASES_DIR.mkdir()

    for case_dir in sorted(CASES_DIR.iterdir()):
        if not case_dir.is_dir():
            continue

        blueprint_path = case_dir / "blueprint_payload.json"
        annex_path = case_dir / "approved_annex.template_payload.json"

        canonical_state = {
            "blueprint_payload": _inspect_payload_artifact(blueprint_path, BlueprintPayload, "Blueprint"),
            "annex_payload": _inspect_payload_artifact(annex_path, AnnexPayload, "Annex"),
        }
        status = _canonical_overall_status(canonical_state)

        task = Task(
            id=case_dir.name,
            title=case_dir.name.replace("_", " ").title(),
            description=f"Blueprint: {canonical_state['blueprint_payload']['status']}, Annex: {canonical_state['annex_payload']['status']}",
        )
        
        if status == "done":
            tasks.done.append(task)
        elif status == "inProgress":
            tasks.inProgress.append(task)
        else:
            tasks.backlog.append(task)
            
    return tasks

# --- API Endpoints ---
@app.get("/tasks", response_model=Columns)
async def get_tasks():
    return get_cases_as_tasks()

@app.post("/tasks", response_model=Columns)
async def create_task(task: Task):
    case_dir = CASES_DIR / task.id
    if case_dir.exists():
        raise HTTPException(status_code=400, detail="Case with this ID already exists")
    case_dir.mkdir()
    return get_cases_as_tasks()

@app.put("/tasks", response_model=Columns)
async def update_all_tasks(updated_tasks: UpdateTasks):
    # This endpoint could be used to trigger actions based on state changes
    # For now, it just returns the current state.
    return get_cases_as_tasks()


@app.put("/tasks/{task_id}", response_model=Columns)
async def update_task(task_id: str, updated_task: Task):
    # This would update files within a case directory, like a description file.
    case_dir = CASES_DIR / task_id
    if not case_dir.exists():
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Example: save description to a file
    desc_file = case_dir / "description.txt"
    desc_file.write_text(updated_task.description)
    
    return get_cases_as_tasks()

@app.delete("/tasks/{task_id}", response_model=Columns)
async def delete_task(task_id: str):
    case_dir = CASES_DIR / task_id
    if not case_dir.exists():
        raise HTTPException(status_code=404, detail="Case not found")
    shutil.rmtree(case_dir)
    return get_cases_as_tasks()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
