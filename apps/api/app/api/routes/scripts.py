from fastapi import APIRouter, Depends, Request

from app.api.deps import get_current_user
from app.db.models import User
from app.schemas.scripts import ScriptFileResponse, ScriptFileUpdateRequest, ScriptInputRequest, ScriptLogResponse, ScriptRunResponse
from app.db.database import SessionLocal
from app.services.audit_service import create_audit_log
from app.services.script_runner import script_runner_service

router = APIRouter(prefix="/scripts", tags=["scripts"])


def serialize_script_file(item) -> ScriptFileResponse:
    return ScriptFileResponse(
        id=item.id,
        name=item.name,
        relative_path=item.relative_path,
        enabled=item.enabled,
        detected_at=item.detected_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def serialize_script_run(item) -> ScriptRunResponse:
    return ScriptRunResponse(
        id=item.id,
        script_file_id=item.script_file_id,
        status=item.status,
        pid=item.pid,
        started_at=item.started_at,
        stopped_at=item.stopped_at,
        exit_code=item.exit_code,
        error_message=item.error_message,
    )


def serialize_script_log(item) -> ScriptLogResponse:
    return ScriptLogResponse(
        id=item.id,
        script_run_id=item.script_run_id,
        stream=item.stream,
        line=item.line,
        created_at=item.created_at,
    )


@router.get("", response_model=list[ScriptFileResponse])
def list_scripts(_: User = Depends(get_current_user)) -> list[ScriptFileResponse]:
    return [serialize_script_file(item) for item in script_runner_service.list_scripts()]


@router.post("/refresh", response_model=list[ScriptFileResponse])
def refresh_scripts(_: User = Depends(get_current_user)) -> list[ScriptFileResponse]:
    return [serialize_script_file(item) for item in script_runner_service.scan_scripts()]


@router.patch("/{script_id}", response_model=ScriptFileResponse)
def update_script(script_id: int, payload: ScriptFileUpdateRequest, _: User = Depends(get_current_user)) -> ScriptFileResponse:
    return serialize_script_file(script_runner_service.update_script(script_id, payload.enabled))


@router.post("/{script_id}/start", response_model=ScriptRunResponse)
def start_script(script_id: int, request: Request, current_user: User = Depends(get_current_user)) -> ScriptRunResponse:
    run = script_runner_service.start_script(script_id)
    with SessionLocal() as db:
        create_audit_log(db, "script.start", "ScriptRun", str(run.id), actor_user=current_user, after={"status": run.status}, request=request)
    return serialize_script_run(run)


@router.get("/runs", response_model=list[ScriptRunResponse])
def list_runs(_: User = Depends(get_current_user)) -> list[ScriptRunResponse]:
    return [serialize_script_run(item) for item in script_runner_service.list_runs()]


@router.get("/runs/{run_id}", response_model=ScriptRunResponse)
def get_run(run_id: int, _: User = Depends(get_current_user)) -> ScriptRunResponse:
    return serialize_script_run(script_runner_service.get_run(run_id))


@router.post("/runs/{run_id}/stop", response_model=ScriptRunResponse)
def stop_run(run_id: int, request: Request, current_user: User = Depends(get_current_user)) -> ScriptRunResponse:
    run = script_runner_service.stop_run(run_id)
    with SessionLocal() as db:
        create_audit_log(db, "script.stop", "ScriptRun", str(run.id), actor_user=current_user, after={"status": run.status}, request=request)
    return serialize_script_run(run)


@router.post("/runs/{run_id}/restart", response_model=ScriptRunResponse)
def restart_run(run_id: int, request: Request, current_user: User = Depends(get_current_user)) -> ScriptRunResponse:
    run = script_runner_service.restart_run(run_id)
    with SessionLocal() as db:
        create_audit_log(db, "script.restart", "ScriptRun", str(run.id), actor_user=current_user, after={"status": run.status}, request=request)
    return serialize_script_run(run)


@router.post("/runs/{run_id}/stdin", response_model=ScriptRunResponse)
def script_stdin(run_id: int, payload: ScriptInputRequest, _: User = Depends(get_current_user)) -> ScriptRunResponse:
    return serialize_script_run(script_runner_service.send_stdin(run_id, payload.value))


@router.get("/runs/{run_id}/logs", response_model=list[ScriptLogResponse])
def run_logs(run_id: int, _: User = Depends(get_current_user)) -> list[ScriptLogResponse]:
    return [serialize_script_log(item) for item in script_runner_service.list_logs(run_id)]
