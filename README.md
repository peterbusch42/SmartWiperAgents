# SmartWiperAgents

**Orchestration of Safety Use Cases in digital.auto SDV**

A proof-of-concept that demonstrates how multi-agent AI orchestration can enforce vehicle safety policies in a Software-Defined Vehicle (SDV) environment. A [Velocitas](https://eclipse-velocitas.github.io/velocitas-docs/) Vehicle App reacts to VSS signal changes from a [KUKSA](https://eclipse.dev/kuksa/) data broker and delegates safety decisions to a [LangGraph](https://github.com/langchain-ai/langgraph) agent pipeline powered by a local LLM via [Ollama](https://ollama.com/).

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Python Environment](#2-python-environment)
  - [3. Install Dependencies](#3-install-dependencies)
  - [4. Ollama & LLM Model](#4-ollama--llm-model)
- [Running the App](#running-the-app)
  - [Mode A — Local Mock (no Docker required)](#mode-a--local-mock-no-docker-required)
  - [Mode B — Full Velocitas Dev Container](#mode-b--full-velocitas-dev-container)
- [How It Works](#how-it-works)
  - [The Velocitas Vehicle App](#the-velocitas-vehicle-app)
  - [KUKSA Data Broker & MQTT](#kuksa-data-broker--mqtt)
  - [The LangGraph Agent Pipeline](#the-langgraph-agent-pipeline)
  - [Agent Roles & Activities](#agent-roles--activities)
  - [VSS Signals Used](#vss-signals-used)
- [Project Structure](#project-structure)
- [The Big Picture: Safety Orchestration in digital.auto SDV](#the-big-picture-safety-orchestration-in-digitalauto-sdv)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Vehicle Runtime                         │
│                                                             │
│  ┌──────────────┐    MQTT/KUKSA    ┌────────────────────┐   │
│  │  VSS Signals │◄────────────────►│Velocitas VehicleApp│   │
│  │  (KUKSA DB)  │                  │   SmartWiperApp    │   │
│  └──────────────┘                  └────────┬───────────┘   │
│                                             │ ainvoke()     │
└─────────────────────────────────────────────┼───────────────┘
                                              │
                          ┌───────────────────▼──────────────────┐
                          │        LangGraph Agent Pipeline      │
                          │                                      │
                          │  ┌──────────┐   ┌─────────────────┐  │
                          │  │Supervisor│──►│  Safety Agent   │  │
                          │  │  (rules) │◄──│  (LLM / Ollama) │  │
                          │  └────┬─────┘   └─────────────────┘  │
                          │       │                              │
                          │  ┌────▼──────────┐                   │
                          │  │Actuator Agent │                   │
                          │  │(Velocitas SDK)│                   │
                          │  └───────────────┘                   │
                          └──────────────────────────────────────┘
```

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | ≥ 3.12 (tested on 3.14.2) | Runtime |
| [Ollama](https://ollama.com/) | latest | Local LLM inference |
| Docker Desktop | latest | Velocitas dev container (Mode B only) |
| MQTT broker (Mosquitto) | 2.x | Velocitas middleware (Mode B only) |
| KUKSA Data Broker | 0.4.x | VSS signal store (Mode B only) |

> **Mode A (local mock)** requires only Python and Ollama — no Docker, no MQTT, no KUKSA.

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/<your-org>/SmartWiperAgents.git
cd SmartWiperAgents
```

### 2. Python Environment

Requires **Python 3.12 or newer**. On macOS with Homebrew:

```bash
python3 --version          # confirm ≥ 3.12
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

`grpcio` (required by `kuksa_client`) does not publish source-build wheels for Python 3.13+. Use `--only-binary=:all:` to force pre-built wheels:

```bash
pip install --upgrade pip
pip install --only-binary=:all: grpcio grpcio-tools
pip install -r requirements.txt
```

> **Why `--only-binary`?** `grpcio==1.64.x` ships no pre-built wheels for Python 3.13/3.14. The `--only-binary` flag resolves to the latest version that _does_ have wheels (≥ 1.80.0).

### 4. Ollama & LLM Model

Install Ollama from [ollama.com](https://ollama.com/download), then pull the model used by the Safety Agent:

```bash
ollama pull llama3.1:8b
ollama serve          # starts the API on http://localhost:11434
```

Verify:

```bash
curl http://localhost:11434/api/tags
```

---

## Running the App

### Mode A — Local Mock (no Docker required)

Uses `vehicle.py` — an in-memory mock of the VSS signal tree. No MQTT broker, no KUKSA data broker needed.

```bash
source .venv/bin/activate
MOCK_VEHICLE=1 python -m app.SmartWiper
```

**Expected output:**

```
[Velocitas] Scheibenwischer auf MEDIUM schalten
[Mock Vehicle] Vehicle.Body.Windshield.Front.Wiping.Mode = MEDIUM
[Mock Vehicle] Subscribed to Vehicle.Body.Hood.IsOpen
[Velocitas] Listener registriert
[Velocitas] Motorhaube öffnen
[Mock Vehicle] Vehicle.Body.Hood.IsOpen = True
[DEBUG] hood_open=True  mode='MEDIUM'  speed=0.0
[Velocitas → Agents] Invoking LangGraph...

=== AGENT REASONING TRACE ===
  [Supervisor] → safety_agent
  [Safety] HIGH: Wipers are moving while the hood is open, which can cause mechanical collision and damage to the wiper motor.
  [Supervisor] → actuator_agent
  [Actuator] Executed: Wiper.Mode = OFF via Velocitas SDK
  [Supervisor] → END
  Final action: STOP_WIPER
=============================

[Velocitas] Demo abgeschlossen — App beendet.
```

### Mode B — Full Velocitas Dev Container

The [Eclipse Velocitas](https://eclipse-velocitas.github.io/velocitas-docs/) dev container provides a complete SDV runtime: MQTT broker (Mosquitto), KUKSA Data Broker, and the Vehicle App runtime.

#### Start the dev container

Open the project in VS Code and use **Dev Containers: Reopen in Container**. The container image is:

```
ghcr.io/eclipse-velocitas/devcontainer-base-images/python:v0.4
```

#### Inside the container

```bash
# Install dependencies (same as Mode A, but in the container's Python env)
pip install --only-binary=:all: grpcio grpcio-tools
pip install -r app/requirements.txt

# Run via Velocitas runtime (connects to MQTT + KUKSA automatically)
cd /workspaces/SmartWiperApp
python -m app.src.SmartWiper
```

The Velocitas SDK connects to:
- **MQTT broker** at `localhost:1883` — used for pub/sub event transport
- **KUKSA Data Broker** at `localhost:55555` (gRPC) — used for VSS signal reads/writes

The Safety Agent LLM endpoint must be reachable from inside the container:

```python
# agents/safety_agent.py (dev container version)
base_url="http://host.docker.internal:11434"
```

---

## How It Works

### The Velocitas Vehicle App

`app/SmartWiper.py` extends `VehicleApp` from the [Eclipse Velocitas Python SDK](https://github.com/eclipse-velocitas/vehicle-app-python-sdk).

**Startup sequence (`on_start`):**

1. Sets `Vehicle.Body.Windshield.Front.Wiping.Mode` to `"MEDIUM"` via the Velocitas SDK.
2. Registers a subscription listener on `Vehicle.Body.Hood.IsOpen`.
3. Sets `Vehicle.Body.Hood.IsOpen` to `True` (simulating a hood-open event).
4. Waits on an `asyncio.Event` (`self._done`) until the agent pipeline completes.

**On every hood change event (`on_hood_changed`):**

1. Reads `hood_is_open` from the subscription reply.
2. Reads `current_wiper_mode` and `vehicle_speed` via SDK `.get()` calls.
3. Builds the `WiperState` dict and calls `graph.ainvoke(initial_state)` — the LangGraph pipeline.
4. Prints the full agent reasoning trace.
5. Sets `self._done` to unblock the waiting loop.

### KUKSA Data Broker & MQTT

In Mode B (dev container), the Velocitas SDK uses two transport layers:

| Layer | Protocol | Role |
|-------|----------|------|
| **MQTT** (paho-mqtt) | TCP port 1883 | Event bus — carries subscription notifications between the Vehicle App and the Velocitas middleware |
| **KUKSA Data Broker** | gRPC port 55555 | VSS signal store — persists signal values and delivers typed reads/writes via the Vehicle Signal Specification |

When `VehicleApp.run()` is called (Mode B), the SDK:
- Connects to the MQTT broker and subscribes to configured topics.
- Connects to KUKSA via gRPC to resolve signal paths like `Vehicle.Body.Hood.IsOpen`.
- Calls `on_start()` once the middleware handshake completes.

In **Mode A** (mock), `MOCK_VEHICLE=1` bypasses `app.run()` entirely and calls `on_start()` directly. The `vehicle.py` mock replaces all SDK I/O with in-memory state and synchronous async callbacks.

### The LangGraph Agent Pipeline

The pipeline is a `StateGraph[WiperState]` with a **feedback loop** — every specialist agent returns to the supervisor before the graph terminates.

```
ENTRY
  │
  ▼
Supervisor ──► safety_agent ──┐
  ▲                           │
  └───────────────────────────┘
  │
  ▼
Supervisor ──► actuator_agent ──┐
  ▲                              │
  └──────────────────────────────┘
  │
  ▼
  END
```

State flows forward through `WiperState` — a `TypedDict` with:

| Field | Type | Description |
|-------|------|-------------|
| `hood_is_open` | `bool` | Whether the hood is currently open |
| `current_wiper_mode` | `str` | Active wiper mode from VSS (`OFF`, `SLOW`, `MEDIUM`, `HIGH`) |
| `vehicle_speed` | `float` | Vehicle speed in km/h |
| `safety_assessment` | `str` | One-sentence risk reasoning from Safety Agent |
| `safety_risk_level` | `LOW/MEDIUM/HIGH` | Risk classification |
| `decided_action` | `STOP_WIPER/KEEP_WIPER/REDUCE_WIPER` | Recommended action |
| `reasoning_log` | `list[str]` | Full trace of all agent decisions |
| `next_agent` | `str` | Routing decision set by the Supervisor |

### Agent Roles & Activities

#### Supervisor (`agents/supervisor.py`)

- **Type:** Rule-based (no LLM — zero hallucination risk on control paths)
- **Role:** Orchestrates the pipeline by inspecting `WiperState` and routing to the correct specialist.
- **Logic:**
  - `safety_assessment is None` → route to `safety_agent`
  - `decided_action is None` → route to `actuator_agent`
  - Both populated → route to `END`
- Appends `[Supervisor] → <next>` to `reasoning_log`

#### Safety Agent (`agents/safety_agent.py`)

- **Type:** LLM-based (llama3.1:8b via Ollama, `temperature=0.0` for determinism)
- **Role:** Assesses physical risk from the combination of VSS signal values.
- **Input:** `hood_is_open`, `current_wiper_mode`, `vehicle_speed`
- **Activity:**
  1. Sends a structured prompt to the LLM with a strict JSON response schema.
  2. Extracts the JSON block from the LLM response via regex.
  3. Populates `safety_risk_level`, `safety_assessment`, `decided_action`.
- **System prompt context:** The LLM is told that wipers moving while the hood is open create a HIGH-risk mechanical collision between the wiper arm and the open hood panel.
- **Output example:**
  ```json
  {
    "risk_level": "HIGH",
    "assessment": "Wipers are moving while the hood is open, which can cause mechanical collision.",
    "recommended_action": "STOP_WIPER"
  }
  ```

#### Actuator Agent (`agents/actuator_agent.py`)

- **Type:** Deterministic (no LLM)
- **Role:** Executes the decided action by writing back to the vehicle via the Velocitas SDK.
- **Activity:**
  - `STOP_WIPER` → sets `Vehicle.Body.Windshield.Front.Wiping.Mode` to `"OFF"`
  - `REDUCE_WIPER` → sets it to `"SLOW"`
  - `KEEP_WIPER` → no change
- Appends `[Actuator] Executed: ...` to `reasoning_log`

### VSS Signals Used

| VSS Path | Type | Used For |
|----------|------|----------|
| `Vehicle.Body.Hood.IsOpen` | `DataPointBoolean` | Trigger signal — subscribed for hood open/close events |
| `Vehicle.Body.Windshield.Front.Wiping.Mode` | `DataPointString` | Read current wiper mode; written by Actuator Agent |
| `Vehicle.Speed` | `DataPointFloat` | Read vehicle speed for safety context |

---

## Project Structure

```
SmartWiperAgents/
├── app/
│   └── SmartWiper.py        # Velocitas VehicleApp — event handler + LangGraph bridge
├── agents/
│   ├── __init__.py
│   ├── supervisor.py        # Rule-based routing agent
│   ├── safety_agent.py      # LLM-based risk assessor (Ollama / llama3.1:8b)
│   └── actuator_agent.py    # Deterministic actuator (Velocitas SDK write-back)
├── graph/
│   ├── __init__.py
│   ├── state.py             # WiperState TypedDict definition
│   └── wiper_graph.py       # LangGraph StateGraph construction
├── vehicle.py               # In-memory mock vehicle (Mode A — no Docker needed)
├── requirements.txt         # Pinned Python dependencies
└── requirements-working.txt # Exact pip freeze of verified working environment
```

---

## The Big Picture: Safety Orchestration in digital.auto SDV

This project demonstrates a pattern for **AI-augmented vehicle safety enforcement** in a Software-Defined Vehicle stack.

### The Problem

Modern vehicles expose hundreds of VSS signals. Certain **combinations** of signal states represent dangerous situations that are difficult to express purely as hard-coded rules — e.g., "wipers active while hood is open" is not inherently dangerous in isolation, but becomes a high-risk scenario when considered together with wiper speed, vehicle state, and the type of hood mechanism.

Classical AUTOSAR-style safety logic handles this with static lookup tables and Boolean expressions. This approach does not scale to the long tail of edge cases in SDV environments where signals evolve dynamically and vehicle configurations vary widely.

### The Solution

SmartWiperAgents introduces an **agentic safety layer** between the raw signal bus and the vehicle actuators:

1. **Velocitas + KUKSA + MQTT** provide the production-grade SDV plumbing — typed VSS signal access, event-driven subscriptions, and a standardized vehicle API that works identically across hardware and simulators.

2. **The Supervisor** acts as a stateless orchestrator. It never calls an LLM, which means it has zero latency overhead for routing and zero risk of non-deterministic behavior on control paths.

3. **The Safety Agent** uses a local LLM (llama3.1:8b running on Ollama) to reason over signal combinations in natural language. This allows the safety policy to be expressed as a **prompt** — human-readable, auditable, and updatable without recompilation. The LLM is constrained to return structured JSON, so its output is always machine-parseable.

4. **The Actuator Agent** is fully deterministic — it maps the LLM's recommendation to a concrete Velocitas SDK call, maintaining a strict boundary between AI reasoning and safety-critical actuation.

### Why This Matters for digital.auto

The [digital.auto](https://digital.auto) ecosystem targets exactly this challenge: enabling software teams to define, iterate, and validate vehicle behavior without full hardware access. SmartWiperAgents shows that:

- **Safety logic can be authored in natural language** and validated in simulation before hardware deployment.
- **LangGraph's feedback loop architecture** mirrors the sense–plan–act cycle of automotive control systems.
- **The Velocitas SDK abstracts the hardware boundary** — the same Python code runs against an in-memory mock, a KUKSA data broker in Docker, or a real ECU gateway, with only the vehicle client swapped.
- **Multi-agent AI is a viable architecture** for the soft safety layer — the non-LLM agents (Supervisor, Actuator) preserve determinism on control paths while the LLM agent provides flexible reasoning over signal semantics.

This architecture is extensible: additional specialist agents (e.g., a Regulatory Agent for ISO 26262 compliance checks, a Telemetry Agent for cloud reporting) can be added to the LangGraph graph without changing the Velocitas application or the VSS signal subscription logic.
