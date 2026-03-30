from fastapi import APIRouter

from app.schemas import ComplianceRequest, RoutingRequest
from app.services.routing_engine import RoutingEngine
from app.services.rule_validator import RuleValidator


router = APIRouter()
routing_engine = RoutingEngine()
rule_validator = RuleValidator()


@router.post("/routing/find-path")
def find_path(payload: RoutingRequest):
    return routing_engine.find_path(payload)


@router.post("/routing/alternative-paths")
def alternative_paths(payload: RoutingRequest):
    return routing_engine.alternative_paths(payload)


@router.post("/routing/analyze-spacing")
def analyze_spacing(payload: RoutingRequest):
    return routing_engine.analyze_spacing(payload)


@router.get("/validation/rules")
def list_rules():
    return {"rules": rule_validator.list_rules()}


@router.post("/validation/check-compliance")
def check_compliance(payload: ComplianceRequest):
    return rule_validator.check_compliance(payload)


@router.get("/advanced-services/health")
def advanced_services_health():
    return {"status": "healthy", "routing": "ok", "validation": "ok"}
