from typing import List

from fastapi import APIRouter, Depends, HTTPException

from artreactor.api.dependencies import get_project_manager
from artreactor.core.managers.project_manager import ProjectManager
from artreactor.models.api import CreateProjectRequest
from artreactor.models.domain import Project

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=List[Project])
async def list_projects(pm: ProjectManager = Depends(get_project_manager)):
    return pm.list_projects()


@router.post("/", response_model=Project)
async def create_project(
    request: CreateProjectRequest, pm: ProjectManager = Depends(get_project_manager)
):
    try:
        return pm.create_project(request.name, request.path, request.description)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project}/workflows")
async def list_workflows(
    project: str, pm: ProjectManager = Depends(get_project_manager)
):
    workflows = pm.get_workflows(project)
    return workflows
