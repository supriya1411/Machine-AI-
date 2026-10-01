# AURUM Service Intelligence — Frontend API Integration Mapping

This document provides the complete API contract between the **AURUM Service Intelligence Backend** and the **Antigravity Frontend** application.

All endpoints adhere to the unified envelope format:
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional human-readable feedback",
  "error_code": null,
  "meta": { ... }
}
```

Base URL: `http://localhost:8000/api/v1` (or relative path `/api/v1` when proxied).

---

## 1. Executive Dashboard (Composite Endpoint)

### `GET /api/v1/dashboard`
* **Powers Component**: Executive Command Center / Operations Overview Dashboard
* **Purpose**: Single optimized composite endpoint that returns all KPIs, distributions, maps, live status, and priority actions in one request.
* **Authentication**: Optional / Bearer JWT

#### Response Example
```json
{
  "success": true,
  "data": {
    "kpis": {
      "total_assets": 1248,
      "operational_assets": 1180,
      "high_risk_assets": 68,
      "critical_alerts_count": 4,
      "overall_health_index": 87.4,
      "pm_compliance_rate": 94.2,
      "active_contracts_value": 3480000.0,
      "contracts_expiring_30_days": 3
    },
    "health_distribution": {
      "optimal": 820,
      "good": 280,
      "fair": 110,
      "critical": 38
    },
    "assets_by_location": [
      {
        "site_id": "site-mdc",
        "site_name": "Metro Data Center",
        "latitude": 39.0438,
        "longitude": -77.4874,
        "total_assets": 320,
        "high_risk_assets": 14,
        "status": "ACTIVE"
      }
    ],
    "top_faults": [
      { "code": "OVERHEATING", "name": "Overheating & Thermal Excess", "count": 48, "severity": "CRITICAL" },
      { "code": "VIBRATION_ANOMALY", "name": "Excessive Mechanical Vibration", "count": 34, "severity": "HIGH" }
    ],
    "live_system_status": {
      "iot_gateway_status": "HEALTHY",
      "anomaly_detection_latency_ms": 18.4,
      "sensors_online": 2412,
      "sensors_offline": 84,
      "sensors_warning": 12,
      "background_worker_status": "ACTIVE",
      "last_sync_timestamp": "2026-09-12T23:00:00Z"
    },
    "action_center": [
      {
        "id": "act-alert-1",
        "priority": "CRITICAL",
        "type": "ENVIRONMENTAL",
        "entity_type": "ASSET",
        "entity_id": "asset-eq102",
        "asset_name": "Chiller Plant Unit #02",
        "issue": "High Temperature Anomaly",
        "risk_level": "CRITICAL",
        "reason": "Temperature exceeded 31.4°C for 18 minutes",
        "recommended_action": "Inspect cooling airflow dampers and evaporator coil",
        "cta": "DISPATCH_ENGINEER"
      }
    ],
    "high_risk_equipment": [
      {
        "id": "asset-eq102",
        "asset_id": "EQ-102",
        "name": "Chiller Plant Unit #02",
        "category": "Centrifugal Chiller",
        "site_name": "Metro Data Center",
        "health_score": 48.0,
        "risk_score": 78.0,
        "risk_level": "CRITICAL",
        "primary_risk_driver": "Recurring thermal threshold breaches & 2 recent compressor outages",
        "recommended_action": "Inspect auxiliary cooling fan and conduct thermal audit"
      }
    ],
    "iot_summary": {
      "total_sensors": 2496,
      "online_count": 2412,
      "anomalies_active": 4,
      "average_ambient_temp": 21.8,
      "average_ambient_humidity": 48.2
    },
    "pm_summary": {
      "scheduled_this_month": 42,
      "completed_this_month": 38,
      "overdue_count": 4,
      "cadence_compliance_rate": 94.2
    },
    "contract_renewal_pipeline": [
      {
        "contract_id": "AMC-2024-002",
        "name": "Data Center Power & Backup Generator Maintenance",
        "customer": "Vertex Data Systems",
        "type": "AMC",
        "end_date": "2026-09-24",
        "days_to_expiry": 12,
        "value": 88000.0,
        "compliance_score": 96.0,
        "renewal_risk": "CRITICAL",
        "recommended_strategy": "Urgent renewal action: contract expires in less than 15 days"
      }
    ],
    "ai_widget": {
      "daily_insight": "Chiller #2 (EQ-102) and AHU-04 show correlated thermal degradation linked to ambient heat spike.",
      "top_predicted_vulnerability": "Cooling tower basin vibration anomaly indicates imminent bearing friction within 14 days.",
      "action_item_highlight": "3 AMC contracts expiring before month-end require vendor performance reconciliation."
    }
  }
}
```

---

## 2. Action Center (Primary Operations Queue)

### `GET /api/v1/action-center`
* **Powers Component**: Action Center Drawer & Action Queue Cards
* **Query Parameters**:
  * `filter_type` (`ALL`, `CRITICAL`, `HIGH`, `PM`, `CONTRACT`)
* **Features**: Urgency-sorted synthesis of Active Alerts, Overdue PMs, Expiring Contracts, and High-Risk Assets with clear `CTA` buttons.

#### Response Example
```json
{
  "success": true,
  "data": [
    {
      "id": "act-alert-1",
      "priority": "CRITICAL",
      "type": "ENVIRONMENTAL",
      "entity_type": "ASSET",
      "entity_id": "asset-eq102",
      "asset_name": "Chiller Plant Unit #02",
      "issue": "High Temperature Anomaly on Chiller Plant Unit #02",
      "risk_level": "CRITICAL",
      "reason": "Temperature exceeded operational ceiling continuously",
      "recommended_action": "Inspect cooling airflow dampers and evaporator coil",
      "cta": "DISPATCH_ENGINEER",
      "created_at": "2026-09-12T22:45:00Z",
      "metadata": {
        "alert_id": "alert-001",
        "current_value": "31.4 °C",
        "threshold": "28.0 °C",
        "duration": "18 minutes"
      }
    }
  ]
}
```

---

## 3. Assets & Health / Risk Engine

### `GET /api/v1/assets`
* **Powers Component**: Asset Fleet Inventory Grid / Filter Table
* **Query Parameters**:
  * `query`: string (search by name, EQ-ID, serial)
  * `category`: string
  * `site_id`: string
  * `risk_level`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
  * `status`: `OPERATIONAL`, `DEGRADED`, `DOWN`, `MAINTENANCE`
  * `sort_by`: `risk_score`, `health_score`, `name`
  * `sort_desc`: boolean
  * `page`: integer (default 1)
  * `page_size`: integer (default 20)

### `GET /api/v1/assets/{id}`
* **Powers Component**: Asset 360° Detail View (Tabs: Overview, Health & Risk, Fault History, Telemetry, Maintenance, Contracts, Documents)

### `GET /api/v1/assets/{id}/risk-explanation`
* **Powers Component**: "Why is this asset risky?" Explainable Risk Modal
* **Response Contract (Section 5)**:
```json
{
  "success": true,
  "data": {
    "asset_id": "EQ-204",
    "asset_name": "Primary Rooftop AHU-204",
    "health_score": 55.0,
    "risk_score": 72.0,
    "risk_level": "HIGH",
    "factors": [
      {
        "factor": "Recent failures",
        "value": "3 failures in 30 days",
        "impact": "HIGH"
      },
      {
        "factor": "IoT Anomaly",
        "value": "Vibration threshold exceeded 3.8 mm/s",
        "impact": "HIGH"
      },
      {
        "factor": "Maintenance Cadence",
        "value": "Cadence violation (130-day gap between PMs)",
        "impact": "MEDIUM"
      }
    ],
    "recommended_actions": [
      "Inspect cooling system and blower fan balance",
      "Schedule preventive maintenance"
    ],
    "prediction_available": true,
    "prediction_reason": "Based on 3 historical failure intervals and active sensor anomalies."
  }
}
```

---

## 4. IoT & Telemetry Stream Engine

### `GET /api/v1/iot/sensors`
* **Powers Component**: IoT Sensor Telemetry Monitor
* **Query Parameters**: `sensor_type`, `status` (`ONLINE`, `OFFLINE`, `DELAYED`, `STALE`, `NO_SENSOR`), `asset_id`

### `GET /api/v1/iot/sensors/{id}`
* **Powers Component**: Real-Time Sensor Gauge & Configured Threshold Bands

### `GET /api/v1/iot/readings?sensor_id={id}&limit=50`
* **Powers Component**: High-frequency Telemetry Timeseries Chart (D3 / Recharts)

### `POST /api/v1/iot/readings`
* **Powers Component**: Simulated IoT Stream Ingestion / Gateway webhook
* **Request**:
```json
{
  "sensor_id": "sensor-uuid",
  "value": 32.4,
  "unit": "°C"
}
```
* **Engine Execution**: Triggers Threshold Evaluation -> Anomaly Detection -> Deduplicated Alert -> Asset Risk Update.

---

## 5. Fault Analytics & MTBF

### `GET /api/v1/fault-analytics`
* **Powers Component**: Fault Analytics Command Center, Pareto Charts, Correlations
* **Response**: Top faults, recurrence rates, MTBF, average resolution times, and weather/sensor correlations.

### `GET /api/v1/fault-analytics/mtbf`
* **Powers Component**: Mean Time Between Failures (MTBF) Calculator Widget
* **Query Parameters**: `asset_id` or `category`
* **Response (Section 8)**:
```json
{
  "success": true,
  "data": {
    "entity_type": "ASSET",
    "entity_id": "EQ-102",
    "entity_name": "Chiller Plant Unit #02",
    "has_sufficient_data": true,
    "mtbf_hours": 360.0,
    "total_failures": 3,
    "failure_intervals_hours": [240.0, 480.0],
    "average_failure_interval_hours": 360.0,
    "trend": "DEGRADING",
    "reason": "Calculated across 2 valid operating intervals."
  }
}
```

### `POST /api/v1/service-calls`
* **Powers Component**: Log Service Call Modal (Auto-normalizes field technician text while preserving verbatim input).

---

## 6. Maintenance & Strict Cadence Evaluation

### `GET /api/v1/maintenance`
* **Powers Component**: Preventive Maintenance Calendar & Task List
* **Query Parameters**: `status` (`SCHEDULED`, `COMPLETED`, `OVERDUE`, `MISSED`)

### `GET /api/v1/maintenance/compliance`
* **Powers Component**: PM Cadence Audit Report (Section 11)
* **Response (Section 11 Cadence Verification)**:
```json
{
  "success": true,
  "data": [
    {
      "asset_id": "EQ-204",
      "asset_name": "Primary Rooftop AHU-204",
      "pm_frequency_days": 90,
      "total_pm_scheduled": 4,
      "total_pm_completed": 4,
      "cadence_compliance": false,
      "violation": true,
      "reason": "Required maintenance interval was not maintained (Maximum interval 130 days exceeds 90-day requirement).",
      "actual_intervals_days": [30, 10, 130],
      "max_gap_days": 130,
      "evaluation_detail": "Evaluated interval consistency across 4 completed maintenance events."
    }
  ]
}
```

---

## 7. AMC / CMC Contracts & Renewal Pipeline

### `GET /api/v1/contracts`
* **Powers Component**: Contract Management Directory

### `GET /api/v1/contracts/renewal-pipeline`
* **Powers Component**: Contract Renewal Pipeline & Renewal Risk Matrix (Section 14)
* **Response**:
```json
{
  "success": true,
  "data": [
    {
      "contract_id": "AMC-2024-002",
      "name": "Data Center Power & Backup Generator Maintenance",
      "customer": "Vertex Data Systems",
      "type": "AMC",
      "end_date": "2026-09-24",
      "days_to_expiry": 12,
      "value": 88000.0,
      "compliance_score": 96.0,
      "renewal_risk": "CRITICAL",
      "risk_factors": [
        "Contract expires in 12 days (critical renewal window)"
      ],
      "recommended_strategy": "Urgent renewal action: contract expires in less than 15 days"
    }
  ]
}
```

### `GET /api/v1/contracts/compliance`
* **Powers Component**: Overall Contract Compliance Audit (SLA, Schedule, Documentation, Monthly Trends)

---

## 8. Grounded AI Assistant

### `POST /api/v1/ai/query`
* **Powers Component**: Grounded AI Assistant Drawer / Copilot Chat
* **Supported Queries (Section 20)**:
  * "Which equipment is high risk?"
  * "Why is EQ-204 high risk?"
  * "Which PMs are overdue?"
  * "Which contracts expire this month?"
  * "What are the top recurring faults?"
  * "Which sites have environmental problems?"
  * "Summarize today's critical alerts."

#### Request
```json
{
  "question": "Which equipment is high risk?"
}
```

#### Response (Section 20 Contract)
```json
{
  "success": true,
  "data": {
    "answer": "Currently, 2 equipment assets are classified as HIGH or CRITICAL risk...",
    "evidence": [
      {
        "source": "Asset Record EQ-102",
        "type": "ASSET_RECORD",
        "timestamp": "2026-09-12T23:00:00Z",
        "detail": "Health: 48.0, Risk: 78.0 (CRITICAL), Criticality: CRITICAL"
      }
    ],
    "recommended_actions": [
      "Review active thermal and vibration anomalies in Action Center",
      "Dispatch Field Service Engineers for priority inspection"
    ],
    "confidence_score": 0.98,
    "grounded_in_db": true,
    "model_used": "aurum-grounded-intelligence"
  }
}
```

---

## 9. Reports & CSV Exports

### `GET /api/v1/reports/summary?report_type=ASSET_HEALTH`
* **Powers Component**: Reports View - Structured JSON summaries.

### `GET /api/v1/reports/export/csv?report_type=ASSET_HEALTH`
* **Powers Component**: Direct CSV Export Button (triggers browser download).

---

## 10. Authentication & Security (RBAC)

* `POST /api/v1/auth/login`: `{ "email": "admin@aurum.ai", "password": "admin123" }`
* `POST /api/v1/auth/refresh`: `{ "refresh_token": "..." }`
* `GET /api/v1/auth/me`: Profile of authenticated user with role permissions.
* Built-in RBAC roles supported:
  * Operations Manager
  * Field Service Engineer
  * Facilities Director
  * IoT/Data Analyst
  * Compliance Officer
  * Administrator
