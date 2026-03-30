# ADVANCED SERVICES GUIDE

## Routing Engine

### Endpoints
- POST /api/v1/routing/find-path
- POST /api/v1/routing/alternative-paths
- POST /api/v1/routing/analyze-spacing

### Purpose
- Generate initial route candidates between two points.
- Provide alternatives for coordination decisions.
- Check spacing metrics for safety and constructability.

## Rule Validator

### Endpoints
- GET /api/v1/validation/rules
- POST /api/v1/validation/check-compliance

### Purpose
- Validate baseline SBC-related parameters.
- Produce pass/fail rule list with score.

## Advanced Services Health

- GET /api/v1/advanced-services/health
