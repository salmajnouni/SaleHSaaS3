from app.schemas import ComplianceRequest, ComplianceResponse, RuleResult


class RuleValidator:
    """SBC-oriented validator for baseline MEP checks."""

    def list_rules(self):
        return [
            {"code": "SBC-MECH-01", "description": "Minimum corridor height >= 2.4m"},
            {"code": "SBC-MECH-02", "description": "Duct to ceiling distance >= 0.3m"},
            {"code": "SBC-PLUMB-01", "description": "Drainage slope >= 1%"},
            {"code": "SBC-ELEC-01", "description": "Electrical-water distance >= 1.0m"},
            {"code": "SBC-FIRE-01", "description": "Fire mainline must be accessible"},
            {"code": "SBC-COORD-01", "description": "Detected clashes should be 0"},
        ]

    def check_compliance(self, payload: ComplianceRequest) -> ComplianceResponse:
        results = [
            RuleResult(
                rule="SBC-MECH-01",
                passed=payload.corridor_height >= 2.4,
                message=f"Corridor height={payload.corridor_height}m",
            ),
            RuleResult(
                rule="SBC-MECH-02",
                passed=payload.duct_ceiling_distance >= 0.3,
                message=f"Duct-ceiling distance={payload.duct_ceiling_distance}m",
            ),
            RuleResult(
                rule="SBC-PLUMB-01",
                passed=payload.drainage_slope >= 0.01,
                message=f"Drainage slope={payload.drainage_slope}",
            ),
            RuleResult(
                rule="SBC-ELEC-01",
                passed=payload.electrical_water_distance >= 1.0,
                message=f"Electrical-water distance={payload.electrical_water_distance}m",
            ),
            RuleResult(
                rule="SBC-FIRE-01",
                passed=payload.fire_mainline_accessible,
                message=f"Fire mainline accessible={payload.fire_mainline_accessible}",
            ),
            RuleResult(
                rule="SBC-COORD-01",
                passed=payload.detected_clashes == 0,
                message=f"Detected clashes={payload.detected_clashes}",
            ),
        ]

        passed = sum(1 for r in results if r.passed)
        score = (passed / len(results)) * 100

        return ComplianceResponse(
            compliant=passed == len(results),
            score=round(score, 2),
            results=results,
        )
