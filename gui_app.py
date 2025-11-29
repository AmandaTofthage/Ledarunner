"""
gui_app.py
-----------
Streamlit-based GUI for running LedaFlow simulations interactively or as parameter studies.
Includes:
 - Single case & parameter study modes
 - Accepts both single values & time-series inputs
 - Logger and variable selection with dynamic plotting
"""

import streamlit as st
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

from automation.simulation_pipeline import (
    create_result_folder,
    validate_timeseries,
    save_inputs,
    build_qs_case,
    run_single_case_simulation, 
    run_parameter_study_simulation,
    load_csv_with_units,
)

from automation.extended_ledaflow import ExtendedLedaFlow

# --- USER CONFIG -------------------------------------------------------------
LEDAFLOW_VERSION = "2.11.271.018"
TEMPLATE_QS_PATH = Path(r"C:/Users/amand/Documents/Prosjektoppgave/Ledarunner/cases/template.qs")
RESULTS_DIR = Path(r"C:/Users/amand/Documents/Prosjektoppgave/Ledarunner/runs")
DYNAMIC_TIME = 3600
# -----------------------------------------------------------------------------


# --- SESSION STATE INITIALIZATION ----
if "lf" not in st.session_state:
    st.session_state.lf = ExtendedLedaFlow(LEDAFLOW_VERSION)

if "simulation_done" not in st.session_state:
    st.session_state.simulation_done = False

if "result_folder" not in st.session_state:
    st.session_state.result_folder = None

if "qs_out" not in st.session_state:
    st.session_state.qs_out = None

if "visualization_ready" not in st.session_state:
    st.session_state.visualization_ready = False



# --- PAGE SETUP / GUI LAYOUT ---
st.set_page_config(page_title="LedaFlow CO₂ Simulator", layout="wide")
st.title("LedaRunner - Automated execution and analysis of LedaFlow simulations")
st.markdown("Run, monitor and analyze LedaFlow simulations in one place!")

    
# --- Initialize session state flags ---
if "inputs" not in st.session_state:
    st.session_state["inputs"] = {}
if "mode" not in st.session_state: 
    st.session_state.mode = "Single Case"
    


# ------------------------------------------------
# MODE SELECTION & INPUT SECTIONS
# ------------------------------------------------

st.markdown("""
    <style>
    [data-testid="stSidebar"][aria-expanded="true"] {width: 340px !important;}
    [data-testid="stSidebar"][aria-expanded="false"] {width: 0px !important;}
    [data-testid="stSidebar"] section[aria-label="main"] {
        padding-left: 1rem; padding-right: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

st.sidebar.markdown("<h1 style='margin-top:-40px;'>Simulation Setup</h1>", unsafe_allow_html=True)

# --- Mode selector (stable) ---
new_mode = st.sidebar.radio(
    "Select Study Mode",
    options=["Single Case", "Parameter Study"],
    index=["Single Case", "Parameter Study"].index(st.session_state.get("mode", "Single Case")),
    horizontal=True,
    help="Choose between running a single simulation or a full parameter study.",
)


if new_mode != st.session_state.get("mode"):
    st.session_state.mode = new_mode
mode = st.session_state.mode
inputs = {}

if mode == "Single Case":
    st.sidebar.caption("Define the simulation inputs below, as constant values or time-series data")
    # --- INLET BOUNDARIES ---
    with st.sidebar.expander("Source (Inlet Boundary)", expanded=False):
        st.caption("Defines the incoming flow rate and temperature of CO₂ entering the pipeline")
        mode_inlet = st.radio(
            "Input mode:",
            ["Constant value", "Time-series"],
            index=0,
            key="inlet_mode",
            horizontal=True,
        )

        if mode_inlet == "Constant value":
            # Single constant values
            inlet_mfr = st.number_input("Mass Flow Rate [kg/s]", min_value=0.0, max_value=200.0, value=110.0, step=1.0, key="inlet_mass_flow_const")
            inlet_temp = st.number_input("Temperature [°C]", min_value=0.0, max_value=100.0, value=40.0, step=1.0, key="inlet_temp_const")
            inputs["Source_mfr"] = inlet_mfr
            inputs["Source_temp"] = inlet_temp

        else:
            # Shared time base
            st.markdown("**Define time series** (comma-separated)")
            time_points_str = st.text_input("Time intervals [s]", "0,600,1200", key="inlet_time_points")
            time_points = [float(t.strip()) for t in time_points_str.split(",") if t.strip()]

            mfr_values_str = st.text_input("Mass Flow Rate [kg/s]", "80,100,120", key="inlet_mf_values")
            in_temp_values_str = st.text_input("Temperature [°C]", "40,45,50", key="inlet_temp_values")

            mfr_values = [float(v.strip()) for v in mfr_values_str.split(",") if v.strip()]
            in_temp_values = [float(v.strip()) for v in in_temp_values_str.split(",") if v.strip()]

            # NEW: validated alignment
            mfr_values = validate_timeseries("Source Mass Flow Rate", time_points, mfr_values)
            in_temp_values = validate_timeseries("Source Temperature", time_points, in_temp_values)


            inputs["Source_mfr"] = list(zip(time_points, mfr_values))
            inputs["Source_temp"] = list(zip(time_points, in_temp_values))



    # --- VALVE ---
    with st.sidebar.expander("Valve (Control Device)", expanded=False):
        st.caption("Controls the CO₂ flow through the system by adjusting the valve opening")
        mode_valve = st.radio(
            "Input mode:",
            ["Constant value", "Time-series"],
            index=0,
            key="valve_mode",
            horizontal=True,
        )

        if mode_valve == "Constant value":
            valve_open = st.number_input("Valve Opening [-]", min_value=0.0, max_value=1.0, value=0.22, step=0.01, key="valve_open_const")
            inputs["Valve_opening"] = valve_open

        else:
            # Use same time base logic
            st.markdown("**Define time series** (comma-separated)")
            time_points_str = st.text_input("Time intervals [s]", "0,600,1200", key="valve_time_points")
            time_points = [float(t.strip()) for t in time_points_str.split(",") if t.strip()]

            valve_values_str = st.text_input("Valve Opening [-]", "0.2,0.4,0.6", key="valve_values")
            valve_values = [float(v.strip()) for v in valve_values_str.split(",") if v.strip()]
            
            valve_values = validate_timeseries("Valve Opening", time_points, valve_values)
            inputs["Valve_opening"] = list(zip(time_points, valve_values))



    # --- OUTLET BOUNDARIES ---
    with st.sidebar.expander("Wellhead (Outlet Boundary)", expanded=False):
        st.caption("Sets the pressure and temperature conditions where CO₂ exits the system")
        mode_outlet = st.radio(
            "Input mode:",
            ["Constant value", "Time-series"],
            index=0,
            key="outlet_mode",
            horizontal=True,
        )

        if mode_outlet == "Constant value":
            st.caption("⚠️ All pressure values must be ≥ 1 bara")
            outlet_press = st.number_input("Pressure [bara]", min_value=1.0, max_value=200.0, value=80.0, step=1.0, key="outlet_press_const", help="Absolute pressure in bar (bara). Minimum 1 bara.")
            outlet_temp = st.number_input("Temperature [°C]", min_value=0.0, max_value=100.0, value=4.0, step=1.0, key="outlet_temp_const")
            inputs["Wellhead_pressure"] = outlet_press
            inputs["Wellhead_temp"] = outlet_temp

        else:
            st.markdown("**Define time series** (comma-separated)")
            st.caption("⚠️ All pressure values must be ≥ 1 bara")
            time_points_str = st.text_input("Time intervals [s]", "0,600,1200", key="outlet_time_points")
            time_points = [float(t.strip()) for t in time_points_str.split(",") if t.strip()]

            pout_values_str = st.text_input("Pressure [bara]", "80,100,120", key="outlet_press_values")
            out_temp_values_str = st.text_input("Temperature [°C]", "4,4,4", key="outlet_temp_values")

            pout_values = [float(v.strip()) for v in pout_values_str.split(",") if v.strip()]
            out_temp_values = [float(v.strip()) for v in out_temp_values_str.split(",") if v.strip()]

            # Validate minimum pressure
            if any(p < 1.0 for p in pout_values):
                st.error("❌ Wellhead pressure values must be ≥ 1 bara. Values below 1 bar cause simulation failure.")
                st.stop()

            pout_values = validate_timeseries("Wellhead Pressure", time_points, pout_values)
            out_temp_values = validate_timeseries("Wellhead Temperature", time_points, out_temp_values)

            inputs["Wellhead_pressure"] = list(zip(time_points, pout_values))
            inputs["Wellhead_temp"] = list(zip(time_points, out_temp_values))
            

elif mode == "Parameter Study":
    st.sidebar.caption("Define the base inputs for the simulation, select which parameter and what values to study")
    
    inputs = {}
    
    # BASE-CASE INPUTS (no time-series)
    st.sidebar.subheader("Base-Case:")
    with st.sidebar.expander("Source (Inlet Boundary)", expanded=False):
        st.caption("Defines the incoming flow rate and temperature of CO₂ entering the pipeline")
        inlet_mfr = st.number_input("Mass Flow Rate [kg/s]", min_value=0.0, max_value=200.0,
                                            value=110.0, step=1.0, key="ps_inlet_mfr")
        inlet_temp = st.number_input("Temperature [°C]", min_value=0.0, max_value=100.0,
                                            value=40.0, step=1.0, key="ps_inlet_temp")

        inputs["Source_mfr"] = inlet_mfr
        inputs["Source_temp"] = inlet_temp


    with st.sidebar.expander("Valve (Control Device)", expanded=False):
        st.caption("Controls the CO₂ flow through the system by adjusting the valve opening")
        valve_open = st.number_input("Valve Opening [-]", min_value=0.0, max_value=1.0,
                                            value=0.22, step=0.01, key="ps_valve_open")
        inputs["Valve_opening"] = valve_open


    with st.sidebar.expander("Wellhead (Outlet Boundary)", expanded=False):
        st.caption("Sets the pressure and temperature conditions where CO₂ exits the system")
        outlet_press = st.number_input("Pressure [bar]", min_value=0.0, max_value=300.0,
                                            value=80.0, step=1.0, key="ps_outlet_press")
        outlet_temp = st.number_input("Temperature [°C]", min_value=0.0, max_value=100.0,
                                            value=4.0, step=1.0, key="ps_outlet_temp")

        inputs["Wellhead_pressure"] = outlet_press
        inputs["Wellhead_temp"] = outlet_temp


    # SELECT VARIABLES TO VARY
    st.sidebar.subheader("Parameters to vary")
    
    param_labels = {
        "Source Mass Flow Rate": "SOURCE_MFR",
        "Source Temperature (°C)": "SOURCE_TEMP",
        "Valve Opening": "VALVE_OPENING",
        "Wellhead Pressure (bar)": "WH_PRESS",
        "Wellhead Temperature (°C)": "WH_TEMP",
    }

    
    selected_params = st.sidebar.multiselect(
        "Select parameters to include in study:",
        list(param_labels.keys()),
    )
    
    # dictionary that stores lists of values to sweep
    study_values = {}
    
    for label in selected_params:
        key = param_labels[label]

        # Adjust placeholder based on parameter type
        if key == "VALVE_OPENING":
            placeholder = "e.g., 20, 40, 60 (percentage: 0-100)"
        else:
            placeholder = "e.g., 60, 80, 100"

        values_str = st.sidebar.text_input(
            f"Values for {label} (comma-separated):",
            key=f"ps_values_{key}",
            placeholder=placeholder
        )

        try:
            values = [float(v.strip()) for v in values_str.split(",") if v.strip()]
            if values:
                # Convert valve opening from percentage (0-100) to fraction (0-1)
                if key == "VALVE_OPENING":
                    values = [v / 100.0 for v in values]
                    # Validate range
                    if any(v < 0 or v > 1 for v in values):
                        st.sidebar.error(f"Valve opening values must be between 0 and 100%")
                        continue
                study_values[key] = values
            else:
                st.sidebar.warning(f"Enter at least one value for {label}.")
        except:
            st.sidebar.error(f"Invalid values entered for {label}.")


    st.session_state["study_values"] = study_values
    
# Store inputs in session
st.session_state.inputs = inputs

# Simulation Duration 
st.session_state.DYNAMIC_TIME = st.sidebar.text_input( 
    "Simulation duration [s]", str(DYNAMIC_TIME), 
    help="Defines how long the transient simulation will run" )

if mode == "Single Case":
    # Preview of inputs
    st.sidebar.markdown("<h3 style='text-align: center;'>Preview of Inputs </h3>", unsafe_allow_html=True) 

    # --- Show input summary ---
    if not inputs:
        st.sidebar.info("No inputs defined yet.")
    else:
        # Helper to format inputs consistently
        def format_value(v):
            if isinstance(v, (int, float)):
                return f"{v:.2f}"
            elif isinstance(v, list):
                # Show short preview of time-series
                preview = ", ".join(f"({t:.0f}s, {val:.2f})" for t, val in v[:3])
                if len(v) > 3:
                    preview += ", ..."
                return preview
            else:
                return str(v)

        # Combine into table dat
        preview_rows = [{"Variable": k, "Value": format_value(v)} for k, v in inputs.items()]

        df_preview = pd.DataFrame(preview_rows)

        # Render nicely
        st.sidebar.dataframe(
            df_preview,
            hide_index=True,
            width='stretch',
            height=min(280, 100 + 25 * len(df_preview)),  # adaptive height
        )

run_clicked = st.sidebar.button("Run Simulation", width='stretch', type="primary")


# ------------------------------------------------
# RUN SIMULATION
# ------------------------------------------------

if run_clicked:
    with st.spinner("Running simulation... Please wait."):
        
        lf = st.session_state.lf 
        
        
        # --- SINGLE CASE MODE --------------------
        if mode == "Single Case":
            result_folder = create_result_folder(RESULTS_DIR) # simulation_pipeline function
            
            # --- SOURCE ---
            source_in = inputs["Source_mfr"]
            if isinstance(source_in, list):      # time-series
                source_time = [t for t, _ in source_in]
                source_mfr_vals = [v for _, v in source_in]
            else:                                # constant
                source_time = [0]
                source_mfr_vals = [source_in]

            source_temp_in = inputs["Source_temp"]
            if isinstance(source_temp_in, list):
            # Optional safety: validate time vectors match
                temp_times = [t for t, _ in source_temp_in]
                if temp_times != source_time:
                    st.error("Source temperature time points must match source mass flow time points.")
                    st.stop()
                source_temp_vals_c = [v for _, v in source_temp_in]
            else:
                source_temp_vals_c = [source_temp_in] * len(source_time)

            # convert °C → K 
            source_temp_vals_k = [v + 273.15 for v in source_temp_vals_c]

            # --- VALVE ---
            valve_in = inputs["Valve_opening"]
            if isinstance(valve_in, list):
                valve_time = [t for t, _ in valve_in]
                valve_vals = [v for _, v in valve_in]
            else:
                valve_time = [0]
                valve_vals = [valve_in]


            # --- WELLHEAD ---
            wh_press_in = inputs["Wellhead_pressure"]
            if isinstance(wh_press_in, list):
                wh_time = [t for t, _ in wh_press_in]
                wh_press_vals_pa = [(p * 1e5) for _, p in wh_press_in]
            else:
                wh_time = [0]
                wh_press_vals_pa = [wh_press_in * 1e5]

            wh_temp_in = inputs["Wellhead_temp"]
            if isinstance(wh_temp_in, list):
                wh_temp_vals_c = [v for _, v in wh_temp_in]
            else:
                wh_temp_vals_c = [wh_temp_in] * len(wh_time)

            # convert °C → K
            wh_temp_vals_k = [v + 273.15 for v in wh_temp_vals_c]

            # === FINAL DICT USED BY TEMPLATE ENGINE ===
            template_inputs = {
                "SOURCE_TIME": source_time,
                "SOURCE_MFR": source_mfr_vals,
                "SOURCE_TEMP_K": source_temp_vals_k,

                "VALVE_TIME": valve_time,
                "VALVE_OPENING": valve_vals,

                "WH_TIME": wh_time,
                "WH_PRESS": wh_press_vals_pa,
                "WH_TEMP_K": wh_temp_vals_k,
            }

                
            save_inputs(template_inputs, result_folder) # simulation_pipeline function
        
            # 1. Build QS file
            qs_out = result_folder / "model.qs"
            build_qs_case(TEMPLATE_QS_PATH, qs_out, template_inputs) # simulation_pipeline function
            
            # Store path in session for reload
            st.session_state.qs_out = qs_out
                
            # Run the simulation
            uuid = run_single_case_simulation(qs_out, result_folder, lf, float(st.session_state.DYNAMIC_TIME)) # simulation_pipeline function
            
            # Mark simulation complete and store result folder 
            st.session_state.result_folder = result_folder
            st.session_state.simulation_done = True
            st.session_state.visualization_ready = True

            st.success("Single-case simulation completed!")
            st.toast("Ready to visualize results!", icon="🎉")
            st.rerun()
    
    
    
        # --- PARAMETER STUDY MODE --------------------
        
        # --- PARAMETER STUDY MODE --------------------
        if mode == "Parameter Study":

            study_values = st.session_state.get("study_values", {})
            if not study_values:
                st.error("No parameters selected for the parameter study.")
                st.stop()

            # Create result root folder (timestamped)
            root_folder = create_result_folder(RESULTS_DIR)

            lf = st.session_state.lf
            all_results = []

            # ---------- Build Base Inputs ----------
            base_inputs = {
                "SOURCE_TIME": [0],
                "SOURCE_MFR": inputs["Source_mfr"],
                "SOURCE_TEMP_K": inputs["Source_temp"] + 273.15,

                "VALVE_TIME": [0],
                "VALVE_OPENING": inputs["Valve_opening"],

                "WH_TIME": [0],
                "WH_PRESS": inputs["Wellhead_pressure"] * 1e5,
                "WH_TEMP_K": inputs["Wellhead_temp"] + 273.15,
            }

            # ---------- Generate ALL combinations ----------
            # study_values looks like:
            # { "SOURCE_MFR": [80, 100], "VALVE_OPENING": [0.2, 0.4] }

            import itertools

            varying_keys = list(study_values.keys())
            value_lists = [study_values[k] for k in varying_keys]
            all_combinations = list(itertools.product(*value_lists))

            # ---------- Save parameter study inputs ----------
            study_inputs = {
                "mode": "Parameter Study",
                "base_inputs": base_inputs,
                "varying_parameters": {k: study_values[k] for k in varying_keys},
                "total_combinations": len(all_combinations),
                "dynamic_time": float(st.session_state.DYNAMIC_TIME),
            }
            save_inputs(study_inputs, root_folder)

            # ---------- Run each case using centralized pipeline helper ----------
            # Run without a progress callback (UI will not show progress)
            all_results = run_parameter_study_simulation(
                base_inputs,
                varying_keys,
                all_combinations,
                TEMPLATE_QS_PATH,
                root_folder,
                lf,
                float(st.session_state.DYNAMIC_TIME),
                progress_callback=None,
            )

            # Save for visualization
            st.session_state.study_results = all_results
            st.session_state.simulation_done = True

            st.success("Parameter study completed!")
            st.toast("Ready to visualize results!", icon="🎉")

            # --- Verify exported data exists for each case and warn if missing ---
            missing_trends = []
            missing_profiles = []
            for r in all_results:
                folder = Path(r["folder"])
                trends_path = folder / "trends"
                profiles_path = folder / "profiles"

                # Trends
                has_trend = False
                if trends_path.exists() and trends_path.is_dir():
                    for f in trends_path.glob("*.csv"):
                        has_trend = True
                        break
                if not has_trend:
                    missing_trends.append(r["case_index"])

                # Profiles
                has_profile = False
                if profiles_path.exists() and profiles_path.is_dir():
                    for f in profiles_path.glob("*.csv"):
                        has_profile = True
                        break
                if not has_profile:
                    missing_profiles.append(r["case_index"])

            if missing_trends:
                st.warning(f"No trend CSV files found for cases: {missing_trends}")
            if missing_profiles:
                st.warning(f"No profile CSV files found for cases: {missing_profiles}")

            # Allow visualization to render (user requested no progress UI)
            st.session_state.visualization_ready = True
            st.rerun()

                    
    
# --- Ledaflow reload / placeholder fix ---
# Ensure we only show the 'Run a simulation...' placeholder when no results are available
if (
    mode == "Single Case"
    and st.session_state.simulation_done
    and st.session_state.result_folder
):
    try:
        lf = st.session_state.lf

        # --- RELOAD CASE + DATABASE ON EVERY STREAMLIT RERUN ---
        lf.load_case_by_qs(str(st.session_state.qs_out))

    except Exception as e:
        st.error(f"Failed to reload LedaFlow case: {e}")

elif (
    mode == "Parameter Study"
    and st.session_state.get("study_results")
    and len(st.session_state.get("study_results", [])) > 0
):
    # Parameter study has results — nothing to reload here. Keep the UI clear
    # and allow the parameter study visualization section below to render.
    st.session_state.visualization_ready = True

else:
    st.info("Run a simulation to visualize results.")
    st.markdown(
        """
        <div style='text-align:center; margin-top:150px; opacity:0.6;'>
            <img src='https://cdn-icons-png.flaticon.com/512/9217/9217306.png' width='200'>
            <p style='font-size:16px; margin-top:20px; color:#555;'>
                <i>No results yet — click <b>Run Simulation</b> in the sidebar to start.</i>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Note: CSV loading helper moved to `automation/simulation_pipeline.py` as `load_csv_with_units`


# ------------------------------------------------
# RESULT VISUALIZATION
# ------------------------------------------------


# --- SINGLE CASE RESULTS ------------------------

if mode == "Single Case" and st.session_state.visualization_ready:
    st.header("Single Case Results")
    
    result_folder = st.session_state.result_folder
    trends_path = result_folder / "trends"
    profiles_path = result_folder / "profiles"
    
    # Load trend csv files with units
    trend_files = {}
    trend_units = {}
    if trends_path.exists():
        for file in trends_path.glob("*.csv"):
            logger_name = file.stem
            try:
                df, units = load_csv_with_units(file)
                trend_files[logger_name] = df
                trend_units[logger_name] = units
            except Exception as e:
                st.error(f"Failed to read trend file: {file}\nError: {str(e)}")
              
    # load profile csv files with units
    profile_files = {}
    profile_units = {}
    if profiles_path.exists():
        for file in profiles_path.glob("*.csv"):
            logger_name = file.stem
            try:
                df, units = load_csv_with_units(file)
                profile_files[logger_name] = df
                profile_units[logger_name] = units
            except Exception as e:
                st.error(f"Failed to read profile file: {file}\nError: {str(e)}")
                
                         
    # --- Trend logger section ---
    # Initialize expander state if not set (allows natural collapse/expand)
    if "trend_open" not in st.session_state:
        st.session_state.trend_open = False
    
    with st.expander("Trend Loggers", expanded=st.session_state.trend_open):
        if not trend_files:
            st.warning("No trend CSV files found.")
        else: 
            st.subheader("Variable vs. Time")
            st.markdown("""1) Select which logger (boundary/device) to explore
                        2) Choose variable(s) to plot
                        3) Click "Add another logger" below to visualize variables from multiple loggers
                        """)

            logger_names = sorted([k for k in trend_files.keys() if k != "Global"])
       
            # Initialize counter for logger plot container
            if "trend_plot_count" not in st.session_state:
                st.session_state.trend_plot_count = 1
            
            # Loop through all logger sections
            for plot_idx in range(1, st.session_state.trend_plot_count + 1):
                selected_logger = st.selectbox(
                    f"Select logger:",
                    logger_names,
                    key=f"selected_trend_logger_{plot_idx}",
                )
                
                st.write(f"**{selected_logger} section**")
                
                df = trend_files[selected_logger]
                
                usable_columns = [col for col in df.columns if col.lower() not in ["time", "position"]]
          
                selected_vars = st.multiselect(
                    "Select variable(s) to plot:",
                    sorted(usable_columns),
                    key=f"selected_trend_vars_{plot_idx}",  
                )
                
                if not selected_vars:
                    st.info("Select one or more variables to plot.")
                else: 
                    cols = st.columns(2)
                    for j, var in enumerate(selected_vars):
                            # Get unit for this variable
                            unit = trend_units.get(selected_logger, {}).get(var, "?")
                            
                            fig = px.line(
                                df,
                                x="time",
                                y=var,
                                title=f"{selected_logger} — {var} ({unit}) vs. Time",
                                template="plotly_white",
                            )
                            

                            # Improve x-axis formatting
                            min_time = df["time"].min() if "time" in df.columns else 0
                            max_time = df["time"].max() if "time" in df.columns else 3600
                            
                            # Get y-axis range for this variable
                            min_y = df[var].min() if var in df.columns else 0
                            max_y = df[var].max() if var in df.columns else 1
                            y_range = max_y - min_y if max_y != min_y else 1
                            
                            fig.update_layout(
                                height=340, 
                                margin=dict(l=20, r=20, t=30, b=30),
                                yaxis_title=f"{var} ({unit})",
                                xaxis_title="time (s)",
                                xaxis=dict(
                                    range=[min_time, max_time],
                                    dtick=max(60, (max_time - min_time) / 10),  # Auto-scale ticks ~10 intervals
                                    showgrid=True,
                                ),
                                yaxis=dict(
                                    dtick=y_range / 8,  # Auto-scale y-ticks to ~8 intervals
                                    showgrid=True,
                                ),
                                hovermode="x unified",
                            )
                            with cols[j % 2]:
                                st.plotly_chart(fig, use_container_width=True)
                
                if plot_idx < st.session_state.trend_plot_count:
                    st.divider()
                        
    
        st.markdown("---")
        st.caption("Want to compare another logger?")
        if st.button("Add another logger section", width='stretch'):
            st.session_state.trend_plot_count += 1
            st.rerun()
        


    # --- Profile logger section ---
    # Initialize expander state if not set (allows natural collapse/expand)
    if "profile_open" not in st.session_state:
        st.session_state.profile_open = False
    
    with st.expander("Profile Loggers", expanded=st.session_state.profile_open):
        if not profile_files:
            st.warning("No profile CSV files found.")
        else: 
            st.subheader("Variable vs. Position")
            st.markdown("1) Select which profile (branch) to explore.\n2) Choose variable(s) to plot.\n3) Select time point(s) to visualize.")
            
            logger_names = sorted(profile_files.keys())
       
            selected_profile = st.selectbox(
                "Select profile:",
                sorted(logger_names),
                key="selected_profile_logger", 
            )
            
            df = profile_files[selected_profile]
            
            # Usable columns are all except 'time' and 'position'
            usable_columns = [col for col in df.columns if col.lower() not in ["time", "position"]]
                    
            # Category selector: Show all (default), Heat transfer, or PT, holdups and MFR
            category = st.radio(
                "Select variable category:",
                options=["Show all", "Heat transfer", "PT, holdups and MFR"],
                index=0,
                key="profile_var_category",
                horizontal=True,
            )

            # Define allowed variables per category (use exact display names where possible)
            heat_vars = [
                "Heat transfer - OHTC",
                "Temperature - average",
                "Temperature - gas",
                "Temperature - oil",
                "Temperature - surroundings",
            ]

            pt_vars = [
                "MFR - total gas",
                "MFR - total liquid",
                "Pipe elevation profile",
                "Pressure",
                "Temperature - average",
                "VF - total gas",
                "VF - total oil",
            ]

            if category == "Show all":
                options = sorted(usable_columns)
            elif category == "Heat transfer":
                options = [v for v in heat_vars if v in usable_columns]
            else:
                options = [v for v in pt_vars if v in usable_columns]

            # If none of the category-specific variables are present in the data,
            # fall back to showing all usable columns so user can still pick something.
            if not options:
                options = sorted(usable_columns)

            selected_vars = st.multiselect(
                "Select variable(s) to plot:",
                options,
                key="selected_profile_vars",
            )
            
            # Get unique time points in the data
            if "time" in df.columns:
                available_times = sorted(df["time"].unique())

                # Slider key per profile (stores the selected time value)
                slider_key = f"selected_profile_time_slider_{selected_profile}"

                # Use previous slider selection if present, otherwise default to first time
                if slider_key in st.session_state:
                    selected_time = st.session_state[slider_key]
                else:
                    selected_time = available_times[0]

                # format timestamp without decimals for display
                try:
                    display_time = str(int(round(selected_time)))
                except Exception:
                    display_time = str(selected_time)

                # Filter data for selected time
                df_filtered = df[df["time"] == selected_time].copy()

                if selected_vars:
                    for j, var in enumerate(selected_vars):
                        # Get unit for this variable
                        unit = profile_units.get(selected_profile, {}).get(var, "?")

                        fig = px.line(
                            df_filtered,
                            x="position",
                            y=var,
                            title=f"{selected_profile} — {var} ({unit}) at t={display_time}s",
                            template="plotly_white",
                        )

                        # Connect datapoints with lines and include markers
                        fig.update_traces(mode='lines+markers', connectgaps=True)

                        # Scale y-axis to the values at this timepoint (with small padding)
                        if var in df_filtered.columns and not df_filtered[var].isna().all():
                            min_y = float(df_filtered[var].min())
                            max_y = float(df_filtered[var].max())
                            if min_y == max_y:
                                pad = abs(min_y) * 0.05 if min_y != 0 else 0.5
                                y_range = [min_y - pad, max_y + pad]
                            else:
                                pad = (max_y - min_y) * 0.06
                                y_range = [min_y - pad, max_y + pad]
                            fig.update_yaxes(range=y_range)

                        # Tidy layout and render full-width (one plot per row)
                        fig.update_layout(
                            height=360,
                            margin=dict(l=20, r=20, t=30, b=10),
                            yaxis_title=f"{var} ({unit})",
                            xaxis_title="position (m)",
                            hovermode="x unified",
                        )

                        st.plotly_chart(fig, use_container_width=True)

                    # Discrete slider underneath plots (shows timestamps without decimals)
                    st.markdown(f"**Selected time:** {display_time} s")
                    st.select_slider(
                        "Select time point:",
                        options=available_times,
                        value=selected_time,
                        format_func=lambda t: str(int(round(t))),
                        key=slider_key,
                    )
                else:
                    st.info("Select one or more variables to plot.")
            else:
                st.error("Profile CSV missing 'time' column.")


# --- PARAMETER STUDY RESULTS -------------------

if mode == "Parameter Study" and "study_results" in st.session_state:
    st.header("Parameter Study Results")
    
    study_results = st.session_state.study_results


    # Visualization mode selector
    viz_mode = st.radio(
        "**Choose visualization mode:**", 
        ["Single Study", "Compare Cases"],
        horizontal=True
    )

    # Map case labels to data
    case_map = {
        f"Case {r['case_index']} — {r['parameters']}": r
        for r in study_results
    }

    
    # --- MODE 1 — SINGLE STUDY ---
   
    if viz_mode == "Single Study":

        case_label = st.selectbox("Select a case:", list(case_map.keys()))
        
        # Track case changes and show success message
        if "ps_selected_case" not in st.session_state:
            st.session_state.ps_selected_case = case_label
        elif st.session_state.ps_selected_case != case_label:
            st.toast(f"Switched to {case_label}")
            st.session_state.ps_selected_case = case_label
        
        selected_case = case_map[case_label]
        case_folder = Path(selected_case["folder"])

        # Load trend and profile data
        trends_path = case_folder / "trends"
        profiles_path = case_folder / "profiles"

        trend_data = {}
        profile_data = {}
        trend_units = {}
        profile_units = {}

        if trends_path.exists():
            for f in trends_path.glob("*.csv"):
                df, units = load_csv_with_units(f)
                trend_data[f.stem] = df
                trend_units[f.stem] = units

        if profiles_path.exists():
            for f in profiles_path.glob("*.csv"):
                df, units = load_csv_with_units(f)
                profile_data[f.stem] = df
                profile_units[f.stem] = units


        # Initialize expander state if not set
        if "ps_trend_open" not in st.session_state:
            st.session_state.ps_trend_open = False
        
        with st.expander("Trend Loggers", expanded=st.session_state.ps_trend_open):
            if not trend_data:
                st.warning("No trend CSV files found.")
            else:
                st.subheader("Variable vs. Time")
                st.markdown("""1) Select which logger (boundary/device) to explore
                            2) Choose variable(s) to plot
                            3) Click "Add another logger" below to visualize variables from multiple loggers
                            """)

                logger_names = sorted([k for k in trend_data.keys() if k != "Global"])

                # Initialize counter for logger plot container (parameter-study scoped)
                if "ps_trend_plot_count" not in st.session_state:
                    st.session_state.ps_trend_plot_count = 1

                # Loop through all logger sections
                for plot_idx in range(1, st.session_state.ps_trend_plot_count + 1):
                    selected_logger = st.selectbox(
                        f"Select logger:",
                        logger_names,
                        key=f"selected_ps_trend_logger_{plot_idx}",
                    )

                    df = trend_data[selected_logger]

                    usable_columns = [col for col in df.columns if col.lower() not in ["time", "position"]]

                    selected_vars = st.multiselect(
                        "Select variable(s) to plot:",
                        sorted(usable_columns),
                        key=f"selected_ps_trend_vars_{plot_idx}",
                    )

                    if not selected_vars:
                        st.info("Select one or more variables to plot.")
                    else:
                        cols = st.columns(2)
                        for j, var in enumerate(selected_vars):
                            # Get unit for this variable
                            unit = trend_units.get(selected_logger, {}).get(var, "?")

                            fig = px.line(
                                df,
                                x="time",
                                y=var,
                                title=f"{selected_logger} — {var} ({unit}) vs. Time",
                                template="plotly_white",
                            )

                            # Improve x-axis formatting
                            min_time = df["time"].min() if "time" in df.columns else 0
                            max_time = df["time"].max() if "time" in df.columns else 3600

                            # Get y-axis range for this variable
                            min_y = df[var].min() if var in df.columns else 0
                            max_y = df[var].max() if var in df.columns else 1
                            y_range = max_y - min_y if max_y != min_y else 1

                            fig.update_layout(
                                height=340,
                                margin=dict(l=20, r=20, t=30, b=30),
                                yaxis_title=f"{var} ({unit})",
                                xaxis_title="time (s)",
                                xaxis=dict(
                                    range=[min_time, max_time],
                                    dtick=max(60, (max_time - min_time) / 10),  # Auto-scale ticks ~10 intervals
                                    showgrid=True,
                                ),
                                yaxis=dict(
                                    dtick=y_range / 8,  # Auto-scale y-ticks to ~8 intervals
                                    showgrid=True,
                                ),
                                hovermode="x unified",
                            )
                            with cols[j % 2]:
                                st.plotly_chart(fig, use_container_width=True)

                    if plot_idx < st.session_state.ps_trend_plot_count:
                        st.divider()

                st.markdown("---")
                st.caption("Want to compare another logger?")
                if st.button("Add another logger section", key="ps_add_logger", width='stretch'):
                    st.session_state.ps_trend_plot_count += 1
                    st.rerun()


        # Initialize expander state if not set
        if "ps_profile_open" not in st.session_state:
            st.session_state.ps_profile_open = False
        
        with st.expander("Profile Loggers", expanded=st.session_state.ps_profile_open):
            if profile_data:
                logger = st.selectbox("Profile Logger:", list(profile_data.keys()))
                df = profile_data[logger]
                vars = [c for c in df.columns if c not in ["time", "position"]]
                var = st.selectbox("Profile Variable:", vars)

                # Ensure numeric time and position for robust selection and plotting
                try:
                    df = df.copy()
                    df["time"] = pd.to_numeric(df["time"], errors='coerce')
                    df["position"] = pd.to_numeric(df["position"], errors='coerce')
                except Exception:
                    pass

                unique_times = sorted(df["time"].dropna().unique())
                if not unique_times:
                    st.info("No time points available in this profile logger.")
                else:
                    # Only show slider if more than one time point
                    if len(unique_times) > 1:
                        t_sel = st.select_slider("Time:", options=unique_times)
                    else:
                        st.info(f"Only one time point available: {unique_times[0]}")
                        t_sel = unique_times[0]

                    df_t = df[df["time"] == t_sel].copy()
                    unit = profile_units.get(logger, {}).get(var, "?")

                    # Defensive checks before plotting
                    if df_t.empty or var not in df_t.columns or df_t[var].dropna().empty:
                        st.info(f"No profile data for variable '{var}' at t={t_sel}s.")
                    else:
                        # If position has a single unique value, add tiny jitter to avoid Plotly range errors
                        try:
                            pos_unique = df_t["position"].dropna().unique()
                        except Exception:
                            pos_unique = []

                        if len(pos_unique) == 0:
                            st.info("Profile data has no position information to plot.")
                        else:
                            if len(pos_unique) == 1:
                                try:
                                    df_t = df_t.copy()
                                    df_t["position"] = df_t["position"].astype(float) + np.linspace(-1e-6, 1e-6, len(df_t))
                                except Exception:
                                    pass

                            try:
                                df_t[var] = pd.to_numeric(df_t[var], errors='coerce')
                            except Exception:
                                pass

                            if df_t[var].dropna().empty:
                                st.info(f"No numeric data for '{var}' at t={t_sel}s.")
                            else:
                            

                                # Choose x-axis: position if it varies, otherwise fallback to index
                                if df_t["position"].dropna().nunique() <= 1:
                                    x_col = None
                                    x_vals = list(range(len(df_t)))
                                    x_label = "row index"
                                else:
                                    x_col = "position"
                                    x_vals = None
                                    x_label = "position (m)"

                                if x_col:
                                    fig = px.line(df_t, x="position", y=var,
                                                title=f"{logger} — {var} ({unit}) @ t={t_sel}s")
                                else:
                                    fig = px.line(df_t, x=x_vals, y=var,
                                                title=f"{logger} — {var} ({unit}) @ t={t_sel}s (index used as x)")

                                # show markers and lines
                                fig.update_traces(mode='lines+markers', connectgaps=True)
                                fig.update_layout(xaxis_title=x_label)
                                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No profile data for this case.")


    #  --- MODE 2 — MULTI-CASE COMPARISON ---
    if viz_mode == "Compare Cases":

        selected_labels = st.multiselect(
            "**Select cases to compare:**",
            list(case_map.keys()),
            default=list(case_map.keys())  # show all by default
        )

        if len(selected_labels) < 2:
            st.info("Select at least two cases to compare.")
            st.stop()

        # Load trend data for each case
        all_trends = {}
        all_units = {}
        for label in selected_labels:
            r = case_map[label]
            folder = Path(r["folder"]) / "trends"
            case_logs = {}
            case_units = {}
            for f in folder.glob("*.csv"):
                df, units = load_csv_with_units(f)
                case_logs[f.stem] = df
                case_units[f.stem] = units
            all_trends[label] = case_logs
            all_units[label] = case_units

        # Determine common loggers across selected cases
        common_loggers = set.intersection(
            *[set(all_trends[label].keys()) for label in selected_labels]
        )

        if not common_loggers:
            st.error("No common loggers across cases.")
            st.stop()

        # --- Section 1: Case Metrics Overview ---
        # Initialize expander state if not set
        if "metrics_open" not in st.session_state:
            st.session_state.metrics_open = False
        
        with st.expander("Case Metrics Overview", expanded=st.session_state.metrics_open):
            logger_for_metrics = st.selectbox("Select logger for metrics:", sorted([k for k in common_loggers if k != "Global"]), key="metrics_logger_select")

            # Determine common variables (exclude time)
            vars_common = set.intersection(
                *[set(all_trends[label][logger_for_metrics].columns) for label in selected_labels]
            )
            vars_common.discard("time")

            if not vars_common:
                st.info("No comparable variables for metrics in the selected logger.")
            else:
                selected_metrics_vars = st.multiselect("Select variable(s) to tabulate:", sorted(vars_common))
                if selected_metrics_vars:
                    # Build a summary DataFrame: rows = cases, cols = var_min/var_max/mean/std
                    rows = []
                    for label in selected_labels:
                        r = {"Case": label}
                        df = all_trends[label][logger_for_metrics]
                        for v in selected_metrics_vars:
                            try:
                                arr = pd.to_numeric(df[v], errors='coerce').dropna()
                                if arr.empty:
                                    r[f"{v} - min"] = None
                                    r[f"{v} - max"] = None
                                    r[f"{v} - mean"] = None
                                    r[f"{v} - std"] = None
                                else:
                                    r[f"{v} - min"] = float(arr.min())
                                    r[f"{v} - max"] = float(arr.max())
                                    r[f"{v} - mean"] = float(arr.mean())
                                    r[f"{v} - std"] = float(arr.std())
                            except Exception:
                                r[f"{v} - min"] = None
                                r[f"{v} - max"] = None
                                r[f"{v} - mean"] = None
                                r[f"{v} - std"] = None
                        rows.append(r)

                    summary_tbl = pd.DataFrame(rows)
                    st.dataframe(summary_tbl, use_container_width=True)

        # --- Section 2: Trend Comparison (expander-based, multi-variable) ---
        # Initialize expander state if not set
        if "trend_compare_open" not in st.session_state:
            st.session_state.trend_compare_open = False
        
        with st.expander("Trend Comparison", expanded=st.session_state.trend_compare_open):
            st.markdown("""1) Select logger(s) to compare
                        \n2) Choose variable(s) to plot
                        \n3) Click "Add another logger section" below to compare additional loggers""")
            # allow multiple logger sections (like single-case UI)
            if "compare_trend_plot_count" not in st.session_state:
                st.session_state.compare_trend_plot_count = 1

            for sec_idx in range(1, st.session_state.compare_trend_plot_count + 1):
                logger_sel = st.selectbox(f"Logger:", sorted([k for k in common_loggers if k != "Global"]), key=f"compare_logger_{sec_idx}")

                # compute available variables for this logger across selected cases
                vars_available = set.intersection(*[set(all_trends[label][logger_sel].columns) for label in selected_labels])
                vars_available.discard("time")

                if not vars_available:
                    st.info("No common variables for this logger across selected cases.")
                else:
                    vars_chosen = st.multiselect(f"Variables to plot:", sorted(vars_available), key=f"compare_vars_{sec_idx}")

                    if vars_chosen:
                        # build common time base for this logger across cases
                        all_times = np.unique(np.concatenate([
                            all_trends[label][logger_sel]["time"].to_numpy() for label in selected_labels
                        ]))
                        common_t = np.sort(all_times)

                        for v in vars_chosen:
                            fig = go.Figure()
                            # Plot each case on same axes for variable v
                            for label in selected_labels:
                                df = all_trends[label][logger_sel]
                                # safe numeric conversion
                                t_arr = pd.to_numeric(df["time"], errors='coerce')
                                y_arr = pd.to_numeric(df[v], errors='coerce')
                                # simple interpolation onto common_t where possible
                                try:
                                    y_interp = np.interp(common_t, t_arr.fillna(method='ffill').fillna(0), y_arr.fillna(0))
                                except Exception:
                                    y_interp = np.full_like(common_t, np.nan, dtype=float)
                                
                                # Add trace for this case
                                fig.add_trace(go.Scatter(
                                    x=common_t,
                                    y=y_interp,
                                    mode='lines',
                                    name=label
                                ))

                            # Get unit from first case's units dict
                            unit = all_units[selected_labels[0]].get(logger_sel, {}).get(v, "?")
                            fig.update_layout(template='plotly_white', title=f"{logger_sel} — {v} ({unit})", xaxis_title='Time [s]', yaxis_title=f"{v} ({unit})")
                            st.plotly_chart(fig, use_container_width=True)

                st.divider()

            if st.button("Add another logger section", key="add_compare_logger"):
                st.session_state.compare_trend_plot_count += 1
                st.rerun()

      
        # ======================================================================
        # PROFILE COMPARISON (Safe, No RangeError, No NaN axis errors)
        # ======================================================================
        # Initialize expander state if not set
        if "profile_compare_open" not in st.session_state:
            st.session_state.profile_compare_open = False
        
        with st.expander("Profile Comparison", expanded=st.session_state.profile_compare_open):
            # Load all profile files across selected cases
            all_profiles = {}
            profile_units = {}

            for label in selected_labels:
                r = case_map[label]
                folder = Path(r["folder"]) / "profiles"
                logs = {}
                units = {}
                for f in folder.glob("*.csv"):
                    df, u = load_csv_with_units(f)
                    logs[f.stem] = df
                    units[f.stem] = u
                all_profiles[label] = logs
                profile_units[label] = units

            # Determine common profile loggers
            common_pl = set.intersection(
                *[set(all_profiles[label].keys()) for label in selected_labels]
            )

            if not common_pl:
                st.info("No common profile loggers across selected cases.")
                st.stop()

            profile = st.selectbox(
                "Select profile:", 
                sorted(common_pl), 
                key="compare_profile_logger"
            )

            # --- Determine common profile variables ---
            # Only keep variables with *some* numeric data across cases
            common_pvars = set.intersection(
                *[set(all_profiles[label][profile].columns) for label in selected_labels]
            )
            common_pvars -= {"time", "position", "Time", "Position"}

            available_pvars = []
            for v in sorted(common_pvars):
                for label in selected_labels:
                    try:
                        arr = pd.to_numeric(all_profiles[label][profile][v], errors='coerce').dropna()
                        if len(arr) > 0:
                            available_pvars.append(v)
                            break
                    except Exception:
                        continue

            if not available_pvars:
                st.info("No usable profile variables for comparison.")
                st.stop()
                
            # Category selector: Show all (default), Heat transfer, or PT, holdups and MFR
            category = st.radio(
                "Select variable category:",
                options=["Show all", "Heat transfer", "PT, holdups and MFR"],
                index=0,
                key="profile_var_category",
                horizontal=True,
            )

            # Define allowed variables per category (use exact display names where possible)
            heat_vars = [
                "Heat transfer - OHTC",
                "Temperature - average",
                "Temperature - gas",
                "Temperature - oil",
                "Temperature - surroundings",
            ]

            pt_vars = [
                "MFR - total gas",
                "MFR - total liquid",
                "Pipe elevation profile",
                "Pressure",
                "Temperature - average",
                "VF - total gas",
                "VF - total oil",
            ]

            if category == "Show all":
                options = sorted(available_pvars)
            elif category == "Heat transfer":
                options = [v for v in heat_vars if v in available_pvars]
            else:
                options = [v for v in pt_vars if v in available_pvars]
            # If none of the category-specific variables are present in the data,
            # fall back to showing all usable columns so user can still pick something.
            if not options:
                options = sorted(available_pvars)

            selected_pvars = st.multiselect(
                "Profile Variable(s):", 
                options, 
                format_func=str,
                key="compare_profile_vars"
                )

            # --- Determine common time base ---
            # Collect all unique times from all cases and create a unified grid
            all_times_list = []
            for label in selected_labels:
                try:
                    times = pd.to_numeric(all_profiles[label][profile]["time"], errors='coerce').dropna()
                    all_times_list.extend(times.tolist())
                except Exception as e:
                    st.warning(f"Error loading times for {label}: {e}")

            if not all_times_list:
                st.info("No time data available.")
                st.stop()

            # Create a unified time grid by taking all unique times and sorting them
            # Round to 2 decimals to group similar times
            unique_times = sorted(set(round(t, 2) for t in all_times_list))
            common_times = unique_times
            
            st.info(f"**Note:** Cases have different simulation time points. Data will be interpolated to {len(common_times)} time points for comparison.")

            if not common_times:
                st.info("No valid time points across selected cases.")
                st.stop()

            if not selected_pvars:
                st.info("Select one or more variables to plot.")
            else:
                # Default to second time point if available, otherwise first
                default_time = common_times[1] if len(common_times) > 1 else common_times[0]
                
                # Slider for time selection (only if more than one time point)
                if len(common_times) > 1:
                    t_sel = st.select_slider(
                        "Select time point:",
                        options=common_times,
                        value=default_time,
                        format_func=lambda t: str(int(round(t))),
                    )
                else:
                    st.info(f"Only one time point available: {int(round(common_times[0]))} s")
                    t_sel = common_times[0]

                # Utility function
                def isnan_or_none(x):
                    return x is None or (isinstance(x, float) and np.isnan(x))

                # ==================================================================
                # PLOTS FOR EACH PROFILE VARIABLE
                # ==================================================================
                for pvar in selected_pvars:
                    fig2 = go.Figure()
                    skipped = []

                    # Get unit from first case that has this variable
                    pvar_unit = "?"
                    for label in selected_labels:
                        u = profile_units.get(label, {}).get(profile, {}).get(pvar)
                        if u:
                            pvar_unit = u
                            break

                    # Global bounds for padding
                    global_min_x = None
                    global_max_x = None
                    global_min_y = None
                    global_max_y = None

                    x_label = "position (m)"

                    for label in selected_labels:

                        # --- CLEAN COPY ---
                        df_raw = all_profiles[label][profile]
                        df = df_raw.copy(deep=True)

                        # Convert to numeric safely
                        for col in ["time", "position", pvar]:
                            if col in df.columns:
                                df[col] = pd.to_numeric(df[col], errors="coerce")

                        # Find the closest available time point to t_sel
                        available_times = df["time"].dropna().unique()
                        if len(available_times) == 0:
                            skipped.append(label)
                            continue
                        
                        # Find closest time to t_sel
                        closest_time = min(available_times, key=lambda t: abs(t - t_sel))
                        
                        # Filter at closest time
                        df_t = df.loc[df["time"] == closest_time].dropna(subset=[pvar]).copy()

                        if df_t.empty:
                            skipped.append(label)
                            continue

                        # --- X handling (position or fallback) ---
                        pos_vals = df_t["position"].dropna()

                        if pos_vals.nunique() <= 1:
                            # Use index + jitter
                            x_vals = np.arange(len(df_t), dtype=float)
                            x_jitter = x_vals + np.random.uniform(-1e-6, 1e-6, size=len(df_t))
                            x_plot = x_jitter
                            x_label = "row index"
                        else:
                            x_plot = pos_vals.to_numpy(dtype=float)
                            x_label = "position (m)"

                        # --- Y values ---
                        y_vals = df_t[pvar].to_numpy(dtype=float)

                        # --- Track global bounds (skip NaN) ---
                        if not np.isnan(x_plot).any():
                            xmin, xmax = x_plot.min(), x_plot.max()
                            if not isnan_or_none(xmin):
                                global_min_x = xmin if global_min_x is None else min(global_min_x, xmin)
                            if not isnan_or_none(xmax):
                                global_max_x = xmax if global_max_x is None else max(global_max_x, xmax)

                        if not np.isnan(y_vals).any():
                            ymin, ymax = y_vals.min(), y_vals.max()
                            if not isnan_or_none(ymin):
                                global_min_y = ymin if global_min_y is None else min(global_min_y, ymin)
                            if not isnan_or_none(ymax):
                                global_max_y = ymax if global_max_y is None else max(global_max_y, ymax)

                        # --- Add trace ---
                        fig2.add_trace(go.Scatter(
                            x=x_plot,
                            y=y_vals,
                            mode="lines+markers",
                            name=label
                        ))

                    # Warn for skipped cases
                    if skipped:
                        st.warning(f"Skipped cases with no {pvar} data at t={t_sel}s: {skipped}")

                    # If no data, skip plot
                    if len(fig2.data) == 0:
                        st.info(f"No usable data available for '{pvar}' at t={t_sel}s.")
                        continue

                    # ==================================================================
                    # AXIS RANGE PADDING (NaN-safe)
                    # ==================================================================

                    # --- X range ---
                    if not isnan_or_none(global_min_x) and not isnan_or_none(global_max_x):
                        if global_min_x == global_max_x:
                            pad = abs(global_min_x) * 0.05 if global_min_x != 0 else 0.5
                            x_range = [global_min_x - pad, global_max_x + pad]
                        else:
                            pad = (global_max_x - global_min_x) * 0.06
                            x_range = [global_min_x - pad, global_max_x + pad]

                        fig2.update_xaxes(range=x_range)

                    # --- Y range ---
                    if not isnan_or_none(global_min_y) and not isnan_or_none(global_max_y):
                        if global_min_y == global_max_y:
                            pad = abs(global_min_y) * 0.05 if global_min_y != 0 else 0.5
                            y_range = [global_min_y - pad, global_max_y + pad]
                        else:
                            pad = (global_max_y - global_min_y) * 0.06
                            y_range = [global_min_y - pad, global_max_y + pad]

                        fig2.update_yaxes(range=y_range)

                    # Final layout
                    fig2.update_layout(
                        template="plotly_white",
                        xaxis_title=x_label,
                        yaxis_title=f"{pvar} ({pvar_unit})",
                        title=f"Profile Comparison — {profile} — {pvar} ({pvar_unit}) @ t={int(round(t_sel))} s"
                    )

                    st.plotly_chart(fig2, use_container_width=True)
