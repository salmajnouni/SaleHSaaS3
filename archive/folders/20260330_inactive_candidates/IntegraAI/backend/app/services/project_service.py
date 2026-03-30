from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas import ProjectCreate, ProjectUpdate


def list_projects(db: Session):
    return db.query(Project).order_by(Project.id.desc()).all()


def create_project(db: Session, payload: ProjectCreate):
    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: int):
    return db.query(Project).filter(Project.id == project_id).first()


def update_project(db: Session, project_id: int, payload: ProjectUpdate):
    project = get_project(db, project_id)
    if not project:
        return None

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(project, k, v)

    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int):
    project = get_project(db, project_id)
    if not project:
        return False

    db.delete(project)
    db.commit()
    return True
