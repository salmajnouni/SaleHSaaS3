from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    name: str
    office_name: str
    project_type: str
    location: str
    scope: str
    phase: str
    delivery_date: Optional[date] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    office_name: Optional[str] = None
    project_type: Optional[str] = None
    location: Optional[str] = None
    scope: Optional[str] = None
    phase: Optional[str] = None
    delivery_date: Optional[date] = None


class ProjectOut(ProjectBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class Point3D(BaseModel):
    x: float
    y: float
    z: float


class RoutingRequest(BaseModel):
    start: Point3D
    end: Point3D
    duct_type: str = "HVAC"


class RoutingPathResponse(BaseModel):
    success: bool
    path: List[Point3D]
    distance: float
    notes: str


class ComplianceRequest(BaseModel):
    project_id: int
    corridor_height: float = Field(..., gt=0)
    duct_ceiling_distance: float = Field(..., gt=0)
    drainage_slope: float = Field(..., gt=0)
    electrical_water_distance: float = Field(..., gt=0)
    fire_mainline_accessible: bool
    detected_clashes: int = Field(..., ge=0)


class RuleResult(BaseModel):
    rule: str
    passed: bool
    message: str


class ComplianceResponse(BaseModel):
    compliant: bool
    score: float
    results: List[RuleResult]


class ApiStatus(BaseModel):
    status: str
    service: str
    version: str
