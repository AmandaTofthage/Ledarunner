# LedaFlow CO₂ Offloading Simulator 
*A fully automated workflow for running LedaFlow transient simulations using QS templates + Streamlit GUI*

## Overview
This repository provides a complete workflow for running **LedaFlow Cae simulations** using a flexible templating system and an interactive web interface. The project allows user to: 

- Run single transient simulations
- Run multi-case parameter studies
- Define constant or time-series boundary conditions
- Automatically generate .qs case files
- Execute simulations via SoftSH and the LedaFlow API
- Load, parse, and visualize trend and profile logger data
- Compare results across multiple cases

The entire system removes the need to manually edit QS files or interact with the LedaFlow GUI. Once set up, simulations run entirely from the browser-based interface.


## Repository Structure
```
Ledarunner/
├── README.md                       # This file - project documentation
├── LedaFlow.py                     # Original LedaFlow API (included with installation)
├── gui_app.py                      # Streamlit GUI for running simulations and visualizing results
├── requirements.txt                # Python dependencies (to be created)
│           
├── cases/                          # Simulation case files
│   ├── CO2_pipe.qs                 # Original export from LedaFlow GUI
│   └── template.qs                 # Base template for generating new cases with placeholders
│                 
├── automation/                     # Core automation modules
│   ├── template_engine.py          # QS template parser and variable substitution engine
│   ├── simulation_pipeline.py      # Orchestrates end-to-end simulation workflow
│   ├── run_softsh.py               # SoftSH launcher for headless LedaFlow execution
│   ├── extended_ledaflow.py        # Enhanced LedaFlow API with additional utilities
│   ├── generate_template.py        # Creates templates from existing QS files
│   └── qs_to_template.py           # Converts QS files to template format
│               
├── results/                        # Simulation outputs
│   └── run_xx_xx /                 # Timestamped run directories
```

## System Architecture
Below is a simplified flow of how the system works: 
```
            ┌──────────────────┐
            │  Streamlit GUI   │ 
            └─────────┬────────┘
                      │
            collects user inputs
                      ▼
     ┌────────────────────────────────┐
     │     simulation_pipeline.py     │
     │      (Workflow Orchestrator)   │
     └───────────┬───────────────┬────┘
                 │               │
                 ▼               ▼
   ┌────────────────────┐   ┌──────────────────────┐
   │ template_engine.py │   │ extended_ledaflow.py │
   │ Build final QS     │   │ Run simulation       │
   └──────────┬─────────┘   └──────────┬───────────┘
              │                        │
              ▼                        ▼
        model.qs              LedaFlow simulation output
                                     trends/*.csv
                                     profiles/*.csv
                                        │
                                        ▼
                ┌───────────────────────────────────┐
                │  simulation_pipeline.py (parsers) │
                └───────────────┬───────────────────┘
                                ▼
                       Parsed DataFrames
                                ▼
                    ┌────────────────────┐
                    │ Streamlit Visuals  │
                    │ Trends / Profiles  │
                    └────────────────────┘

```

## Key Features

### QS Template Engine
The `template_engine.py` module converts `.qs` files into **dynamic templates** by inserting placeholders for the variables that can be user-specified -> Boundry conditions (Inlet and Outlet) and devices (valve).

**Key capabilities:**
- Automatically expands constants to arrays (`50` → `[50, 50, 50]`)
- Validates time-series lengths match their time vectors
- Ensures all arrays follow LedaFlow syntax: `[1, 2, 3]`
- Raises errors for missing or mismatched placeholders

**Template creation:**
Run `generate_template.py` that use `qs_to_template.py` to automatically create a template from an existing `.qs` file (e.g., `CO2_pipe.qs`). These scripts identify numerical values and convert them into configurable placeholders, making it easy to parameterize any case without manual editing.

### Automated Simulation Workflow
The `simulation_pipeline.py` orchestrates and standarized all workflow steps: 

#### 1) Create result folder: 
**Single Case Mode:**
- Creates timestamped result folder containing: 
    - Generated `model.qs` file with specific parameter values
    - `trends/` and `profiles/` subdirectories with simulation outputs
    - `case_uuid.txt` for unique identification
    - `inputs.json` capturing all user-specified parameters and settings for reproducibility
    - `run_case.js` automation script for LedaFlow execution

**Parameter Study Mode:**
- Generates all parameter combinations from user-defined value lists
- Creates individual case folders within timestamped run directory 
- Each case folder contains:
    - Generated `model.qs` file with specific parameter values
    - `trends/` and `profiles/` subdirectories with simulation outputs
    - `case_uuid.txt` for unique identification
    - `inputs.json` capturing all user-specified parameters and settings for reproducibility
    - `run_case.js` automation script for LedaFlow execution


#### 2) Build final QS file
From the template.qs a model.qs file is created based on user input

### 3) Run simulation
**Single Case Mode:**
- Executes simulation via SoftSH and LedaFlow API
- Automatically parses trend and profile logger outputs

**Parameter Study Mode:**
- Runs all cases sequentially (as a single case)
- Aggregates results across cases for multi-case comparison



### Streamlit GUI
The GUI supports:

**Input Definition**
- Constant or time-series boundary conditions
- Inlet mass flow & temperature
- Valve opening
- Wellhead pressure & temperature

**Single Simulation Mode**
- One-click scoring of the entire workflow
- Instant visualization of results

**Parameter Study Mode**
- Multi-parameter sweeping
- Automatic generation of all case combinations
- Comparison across cases

**Visualization**
- Trend plots (time-based)
- Profile plots (position-based)

For parameter study: 
- Multi-variable comparison
- Multi-case comparison
- Case metric tables

#### **Visualizations**
- Trend plots (time-based)
- Profile plots (position-based)
- Multi-logger comparison
- Multi-case comparison
- Statistics tables

## Contents
- Test data files
- Analysis scripts
- Configuration files
- Results and outputs

## Getting Started
1. Clone the repository
2. Install required dependencies
3. Requires LedaFlow Engineering installed locally
4. Generate template (optional step)
- If you modify the original CO2_pipe.qs, you need to regenerate the template.qs file by running `generate_template_py`
5. Launch the GUI: `python -m streamlit run gui_app.py` 
6. Run simulations inside the streamlit UI

## Limitations (Student License)
This project works around several restrictions of the LedaFlow Student License:

### 1. No .lpf case export
The full "LedaFlow Project File" cannot be exported. Only .qs scripts are available.

**Solution:** A full QS templating engine is used to build new cases programmatically.

### 2. No built-in parameter study functionality
Only the commercial license supports multi-case sweeps.

**Solution:** Parameter study mode implemented in Python.

### 3. Limited API capabilities
The student license cannot:
- Add or modify loggers via the API
- Modify geometry or PVT programmatically
- Change numerical discretization

**Solution:** All modifications are injected into the QS template.

### 4. GUI slow for iteration
QS reloads in the GUI are heavy.

**Solution:** Keep loggers minimal in template; automate all workflows outside GUI.


## License
This project is intended for academic use and interacts with licensed LedaFlow software provided by Kongsberg.
Follow your institution’s LedaFlow license terms.