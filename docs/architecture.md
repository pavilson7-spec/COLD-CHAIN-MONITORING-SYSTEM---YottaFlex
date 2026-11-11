# Cold Chain Monitoring System - Architecture Document

## System Overview

The Cold Chain Monitoring System is a mission-critical platform providing continuous end-to-end environmental surveillance, excursion detection, chain-of-custody tracking, and regulatory compliance for temperature-sensitive pharmaceuticals, biologics, and cellular therapies.

```mermaid
flowchart TD
    subgraph Edge["Virtual Sensor Simulation Layer"]
        Sensors["Dual-Channel Sensors (Temp + RH)"]
        Generator["Data Generator (seed: 20261022)"]
        Anomalies["Negative Scenario Injector"]
        Sensors --> Generator
        Anomalies --> Generator
    end

    subgraph Backend["FastAPI High-Performance Engine"]
        API["FastAPI REST Endpoints (/api/v1)"]
        Auth["JWT & Role-Based Access Control"]
        Engine["Deterministic Excursion Rule Engine"]
        Validator["Automated Data Integrity Validator"]
        Exporter["CSV/JSON/SQL Export Service"]
        
        API --> Auth
        API --> Engine
        API --> Validator
        API --> Exporter
    end

    subgraph Database["PostgreSQL Storage (cold_chain_monitoring_db)"]
        Pool["SQLAlchemy Connection Pool"]
        Tables["Core entities, assignment bridge, and append-only lifecycle histories"]
        Pool --> Tables
    end

    subgraph Frontend["React.js Modern Dashboard"]
        UI["Tailwind CSS + Lucide Icons"]
        Charts["Interactive Telemetry Curves (Recharts)"]
        Pages["Operational dashboard, entity views, reports, and settings"]
    end

    Generator -->|Batch Telemetry| Backend
    Backend -->|Persist & Query| Pool
    Frontend -->|Authenticated REST Requests| API
```

## Security & Role-Based Access Control (RBAC)

Five operational roles are enforced server-side:
1. **Plant Operator**: View active shipments, monitor live telemetries, acknowledge real-time alarms.
2. **Maintenance Engineer**: Record sensor calibration outcomes and maintenance notes.
3. **Quality Engineer**: Define threshold policies, review excursions, and manage corrective actions (CAPA).
4. **Production Planner**: Schedule shipments, assign containers and products, plan route waypoints.
5. **OT/IT Administrator**: Manage user accounts and system access.
