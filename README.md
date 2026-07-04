# AI Farmer Assistant

A production-grade, collaborative multi-agent agricultural platform built on Google's **Agent Development Kit (ADK)**, **Gemini 2.5 Pro**, **Gemini Vision**, and **Streamlit**.

---

## Architecture Diagram

```mermaid
graph TD
    UI[Streamlit Web App] --> Orchestrator[Agricultural Orchestrator]
    Orchestrator --> MemAgent[Memory Manager Agent]
    Orchestrator --> RefAgent[Reflection Agent]
    
    subgraph "Specialized Sub-Agents"
        Orchestrator --> Crop[Crop Advisor]
        Orchestrator --> Weather[Weather Intel]
        Orchestrator --> Soil[Irrigation Advisor]
        Orchestrator --> Fert[Fertilizer Prescriber]
        Orchestrator --> Pest[Pest Advisor]
        Orchestrator --> Mkt[Market Intel]
        Orchestrator --> Gov[Scheme Finder]
        Orchestrator --> Fin[ROI Planner]
        Orchestrator --> Maps[Resource Locator]
        Orchestrator --> Rep[PDF compiler]
    end

    subgraph "External Integrations (MCP/DB)"
        Crop --> DB_Agron[(Local Caches & DB)]
        Weather --> Weather_API[MCP Weather Server]
        Soil --> Telemetry[MCP Soil Sensors]
        Mkt --> Mandi_API[MCP Market Server]
        Gov --> Web_Search[MCP Google Search]
        Maps --> Maps_API[MCP Places API]
    end
```

---

## Sequential Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    Farmer->>Streamlit UI: Input Query (e.g. crop pricing & weather alert)
    Streamlit UI->>Orchestrator: execute_plan(query, session_id)
    Orchestrator->>Memory Manager: get_personalized_context()
    Memory Manager-->>Orchestrator: Farmer profile & history logs
    Orchestrator->>Orchestrator: determine_plan() (Determine sub-agents)
    Par [Execute planned agents in parallel]
        Orchestrator->>Weather Agent: Run execution
        Orchestrator->>Market Agent: Run execution
    end
    Weather Agent-->>Orchestrator: Forecast recommendations
    Market Agent-->>Orchestrator: Pricing recommendations
    Orchestrator->>Reflection Agent: audit(aggregated recommendations)
    Reflection Agent-->>Orchestrator: Audited final advice (Warning & safety checked)
    Orchestrator->>SQLite DB: Log trace & cache advisory
    Orchestrator-->>Streamlit UI: Render advice + Explainability Log
    Streamlit UI-->>Farmer: Render Dashboard + Voice Audio Readout
```

---

## Project Structure

```text
├── assets/
│   └── style.css            # Custom CSS for premium glassmorphism dark theme
├── agents/
│   ├── base_agent.py        # Custom BaseFarmerAgent wrapping Google ADK Agent
│   ├── crop_agent.py        # Seed selection and crop rotation planner
│   ├── disease_agent.py     # Crop leaf disease diagnostic agent (Gemini Vision)
│   ├── weather_agent.py     # Meteorological alerts and risk assessment
│   ├── irrigation_agent.py  # Watering recommendations and moisture telemetry
│   ├── fertilizer_agent.py  # N-P-K nutrient prescription builder
│   ├── pest_agent.py        # Integrated Pest Management (IPM) advisor
│   ├── market_agent.py      # Mandi price trends and store recommendations
│   ├── gov_scheme_agent.py  # Subsidy search and policy support browser
│   ├── financial_agent.py   # Crop budgets, expense tracking, and ROI charts
│   ├── resource_agent.py    # GIS places finder for seed stores and cold storages
│   ├── report_agent.py      # ReportLab PDF compile agent
│   ├── reflection_agent.py  # Advisory quality audit and contradiction checker
│   └── memory_agent.py      # Personalization context injector
├── tools/
│   ├── mcp_clients.py       # API clients for weather, mandi price, maps with caching
│   └── pdf_generator.py     # PDF Report compiler layout
├── tests/
│   └── test_components.py   # Pytest unit and integration test suite
├── app.py                   # Primary Streamlit visual dashboard
├── config.py                # Pydantic configuration & secret variables loader
├── database.py              # SQLite models, repositories, and caches
├── exceptions.py            # Domain-specific custom Exception definitions
├── logger.py                # Structured console logging formatter
├── memory.py                # History management and Digital Farmer Profile service
├── requirements.txt         # Package dependencies
├── Dockerfile               # Production container compiler
├── docker-compose.yml       # Local container cluster builder
└── README.md                # Comprehensive documentation
```

---

## Setup Guide

### 1. Requirements
Ensure you have **Python 3.11+** installed.

### 2. Installation
Clone this repository and run:
```bash
pip install -r requirements.txt
```

### 3. Environment Config
Create a `.env` file in the root directory (based on `.env.example`) and fill in your Gemini API key:
```env
GEMINI_API_KEY=AIzaSy...
```
*(If no key is supplied, the application automatically runs in **high-fidelity Mock mode** so you can view all functionalities and layout demonstrations immediately)*.

### 4. Running the Application
To run the visual Streamlit dashboard:
```bash
streamlit run app.py
```

### 5. Running Tests
To run the automated test suite:
```bash
pytest tests/
```

---

## Troubleshooting Guide

- **Error: `Gemini API key is invalid`**
  - Check that your `.env` contains `GEMINI_API_KEY=your_key` with no quotes or spaces.
- **Error: `PDF generation fails`**
  - ReportLab requires write access to the `scratch/` folder. Ensure the local workspace has directory permissions.
- **Slow Dashboard Loading**
  - The application automatically caches weather for 1 hour and market prices for 4 hours inside the local `farming.db` SQLite database. Clear `farming.db` to purge local state.

---

## 📺 Visual Dashboard Demo & Gallery

Below are the screenshots and video logs demonstrating the visual layout and operations of the AI Farmer Assistant app:

### 1. Dashboard Interface
![Dashboard Screen](assets/dashboard_screenshot.png)

### 2. Multi-Agent Conversation & Visual Diagnostics Demo
![Dashboard Demo](assets/dashboard_demo.webp)

