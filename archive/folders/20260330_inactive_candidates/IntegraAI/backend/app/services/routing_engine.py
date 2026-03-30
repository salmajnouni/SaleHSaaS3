from math import dist
from typing import List

from app.schemas import Point3D, RoutingPathResponse, RoutingRequest


class RoutingEngine:
    """MVP routing engine with deterministic waypoint generation."""

    def find_path(self, payload: RoutingRequest) -> RoutingPathResponse:
        start = payload.start
        end = payload.end

        waypoint = Point3D(
            x=(start.x + end.x) / 2,
            y=(start.y + end.y) / 2,
            z=max(start.z, end.z) + 0.5,
        )

        path = [start, waypoint, end]
        distance = self._polyline_distance(path)
        return RoutingPathResponse(
            success=True,
            path=path,
            distance=round(distance, 3),
            notes=f"Route generated for {payload.duct_type}",
        )

    def alternative_paths(self, payload: RoutingRequest) -> List[RoutingPathResponse]:
        start = payload.start
        end = payload.end

        alt1 = [start, Point3D(x=start.x, y=end.y, z=start.z + 0.4), end]
        alt2 = [start, Point3D(x=end.x, y=start.y, z=end.z + 0.6), end]

        return [
            RoutingPathResponse(
                success=True,
                path=alt1,
                distance=round(self._polyline_distance(alt1), 3),
                notes="Alternative path A",
            ),
            RoutingPathResponse(
                success=True,
                path=alt2,
                distance=round(self._polyline_distance(alt2), 3),
                notes="Alternative path B",
            ),
        ]

    def analyze_spacing(self, payload: RoutingRequest):
        horizontal = dist((payload.start.x, payload.start.y), (payload.end.x, payload.end.y))
        vertical = abs(payload.end.z - payload.start.z)
        return {
            "safe_spacing": horizontal >= 1.2,
            "horizontal_distance": round(horizontal, 3),
            "vertical_clearance": round(vertical, 3),
            "recommendation": "Increase corridor clearance" if horizontal < 1.2 else "Spacing is acceptable",
        }

    @staticmethod
    def _polyline_distance(points: List[Point3D]) -> float:
        total = 0.0
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            total += dist((p1.x, p1.y, p1.z), (p2.x, p2.y, p2.z))
        return total
