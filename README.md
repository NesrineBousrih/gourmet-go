# 🍽️ Gourmet-Go — Distributed Order System

> Full Stack + DevOps Project — Microservices Architecture with Saga Orchestration Pattern

---

## 📌 Project Overview

Gourmet-Go is a production-like distributed order management system built with:

- **Microservices** communicating via **gRPC**
- **Saga Orchestration Pattern** with compensation (rollback)
- **PostgreSQL** database per service
- **Angular** frontend UI
- **Docker** containerization
- **GitHub Actions** CI/CD pipeline
- **Docker Hub** image registry

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Angular Frontend                     │
│                    (http://localhost)                    │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP REST
┌──────────────────────────▼──────────────────────────────┐
│                    API Gateway (FastAPI)                  │
│                     port 8000                            │
└──────┬───────────────────┬───────────────────┬──────────┘
       │ gRPC              │ gRPC              │ gRPC
┌──────▼──────┐   ┌────────▼───────┐  ┌───────▼─────────┐
│Order Service│   │Kitchen Service │  │Accounting Service│
│  port 50051 │   │  port 50052    │  │   port 50053     │
└──────┬──────┘   └────────┬───────┘  └───────┬─────────┘
       │                   │                  │
┌──────▼──────┐   ┌────────▼───────┐  ┌───────▼─────────┐
│  order-db   │   │   kitchen-db   │  │  accounting-db   │
│ PostgreSQL  │   │  PostgreSQL    │  │   PostgreSQL     │
└─────────────┘   └────────────────┘  └─────────────────┘
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Angular 17 |
| API Bridge | FastAPI + Uvicorn |
| Services | Python 3.11 + gRPC |
| Databases | PostgreSQL 15 (one per service) |
| Containerization | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Image Registry | Docker Hub |

---

## 🔄 Saga Orchestration Flow

### Happy Path (amount < 100)
```
User → Create Order
         ↓
   APPROVAL_PENDING
         ↓
   Create Kitchen Ticket ✅
         ↓
   Authorize Payment ✅ (amount < 100)
         ↓
      APPROVED ✅
```

### Compensation Path (amount ≥ 100)
```
User → Create Order
         ↓
   APPROVAL_PENDING
         ↓
   Create Kitchen Ticket ✅
         ↓
   Authorize Payment ❌ (amount ≥ 100)
         ↓
   Reject Kitchen Ticket (compensation)
         ↓
      REJECTED ❌
```

---

## 🐳 Docker Hub Images

All images are publicly available at:

| Image | Link |
|-------|------|
| `nesrinebousrih/gourmet-go-order-service:latest` | Docker Hub |
| `nesrinebousrih/gourmet-go-kitchen-service:latest` | Docker Hub |
| `nesrinebousrih/gourmet-go-accounting-service:latest` | Docker Hub |
| `nesrinebousrih/gourmet-go-orchestrator:latest` | Docker Hub |
| `nesrinebousrih/gourmet-go-api-gateway:latest` | Docker Hub |
| `nesrinebousrih/gourmet-go-frontend:latest` | Docker Hub |

---

## 🚀 How to Run

### Prerequisites
- Docker Desktop installed and running
- No other services on ports 80, 8000, 5432, 50051-50053

### Start the full system

```bash
docker-compose up
```

All images are pulled automatically from Docker Hub. Wait ~30 seconds for all services to initialize.

### Access the UI

Open your browser at: **http://localhost**

### Stop the system

```bash
docker-compose down
```

---

## 📁 Project Structure

```
gourmet-go/
├── protos/
│   ├── order.proto
│   ├── kitchen.proto
│   └── accounting.proto
├── order-service/
│   ├── main.py          # gRPC server
│   ├── models.py        # SQLAlchemy Order model
│   ├── database.py      # PostgreSQL connection
│   ├── requirements.txt
│   └── Dockerfile
├── kitchen-service/
│   ├── main.py          # gRPC server
│   ├── models.py        # KitchenTicket model
│   ├── database.py
│   ├── requirements.txt
│   └── Dockerfile
├── accounting-service/
│   ├── main.py          # gRPC server (amount >= 100 = rejected)
│   ├── models.py        # Payment model
│   ├── database.py
│   ├── requirements.txt
│   └── Dockerfile
├── orchestrator/
│   ├── main.py          # Saga orchestration logic
│   ├── requirements.txt
│   └── Dockerfile
├── api-gateway/
│   ├── main.py          # FastAPI REST bridge
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/app/         # Angular components
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
└── .github/
    └── workflows/
        └── ci-cd.yml    # GitHub Actions pipeline
```

---

## 🔧 CI/CD Pipeline

Pipeline is triggered automatically on every push to `main` branch.

### Pipeline Stages

```
Push to main
     ↓
┌─────────────┐
│   BUILD     │  Install dependencies, generate gRPC stubs, syntax check
└──────┬──────┘
       ↓
┌─────────────┐
│   DOCKER    │  Build 6 Docker images + Push to Docker Hub
└─────────────┘
```

---

## 📸 Screenshots

### CI/CD Pipeline — All runs green ✅

> GitHub Actions — 3 successful pipeline runs

### Docker Hub — 6 images published ✅

> All 6 microservice images pushed to nesrinebousrih namespace

### Happy Path — Order APPROVED ✅

> Order ORD-JI9MH1 with amount €30 → Status: APPROVED

### Compensation Path — Order REJECTED ❌

> Order ORD-JI9MH1 with amount €150 → Status: REJECTED

### All containers running ✅

> docker ps showing all 9 containers Up for 27 minutes

### Saga Orchestrator logs ✅

```
🚀 Starting Saga for order [test-001] amount: 50.0
--- Step 1: Setting status to APPROVAL_PENDING ---
--- Step 2: Creating Kitchen Ticket ---
--- Step 3: Authorizing Payment ---
--- Step 4: HAPPY PATH — Setting status to APPROVED ---
✅ Order [test-001] successfully APPROVED!
```

---

## 🗄️ Database Schema

### Order Service DB (`order_db`)
| Column | Type | Description |
|--------|------|-------------|
| order_id | String (PK) | Unique order identifier |
| status | String | APPROVAL_PENDING / APPROVED / REJECTED |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

### Kitchen Service DB (`kitchen_db`)
| Column | Type | Description |
|--------|------|-------------|
| order_id | String (PK) | Linked order ID |
| status | String | CREATED / REJECTED |
| created_at | DateTime | Creation timestamp |

### Accounting Service DB (`accounting_db`)
| Column | Type | Description |
|--------|------|-------------|
| order_id | String (PK) | Linked order ID |
| amount | Float | Payment amount |
| authorized | Boolean | true if amount < 100 |
| created_at | DateTime | Creation timestamp |

---

## 👩‍💻 Author

**Nesrine Bousrih**
- GitHub: [@NesrineBousrih](https://github.com/NesrineBousrih)
- Docker Hub: [nesrinebousrih](https://hub.docker.com/u/nesrinebousrih)

---

## 📝 Notes

- Payment authorization rule: `amount < 100` → APPROVED, `amount ≥ 100` → REJECTED
- This rule is intentional and simulates the compensation (Saga rollback) path
- The orchestrator service exits after completing the saga — this is expected behavior
- All inter-service communication uses gRPC (no REST between microservices)