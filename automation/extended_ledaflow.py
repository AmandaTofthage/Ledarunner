"""
Extended LedaFlow API
----------------------
Extension of the official LedaFlow API to support:
    - loading QS-based cases (created by SoftSH)
    - running initialization + dynamic simulation
    - extracting trends and profiles
    - exporting results
    
Note:
This class does *not* modify inputs in the case.    
All input modification is done via .qs templating before running SoftSH.
"""

import csv
from LedaFlow import LedaFlow
from pathlib import Path


class ExtendedLedaFlow(LedaFlow):
    
    # SI unit mappings for LedaFlow properties
    PROPERTY_UNITS = {
        # Time (base unit)
        "time": "s",
        "Time": "s",
        "Time step": "s",
        
        # Pressure
        "Pressure": "Pa",
        "Pressure drop": "Pa",
        "Pressure drop - total": "Pa",
        "Pressure drop - gravity": "Pa",
        "Pressure drop - friction": "Pa",
        "Pressure Left": "Pa",
        "Pressure Right": "Pa",
        "Pressure (inlet)": "Pa",
        "Pressure (outlet)": "Pa",
        
        # Temperature
        "Temperature": "C",
        "Temperature - gas": "C",
        "Temperature - oil": "C",
        "Temperature - average": "C",
        "Temperature - surroundings": "C",
        "Wall temperature - inner surface": "C",
        "Average temperature": "C",
        
        # Mass flow rate
        "Mass flow rate": "kg/s",
        "MFR - continuous gas": "kg/s",
        "MFR - continuous oil": "kg/s",
        "MFR - bubbles": "kg/s",
        "MFR - droplets": "kg/s",
        "MFR - total gas": "kg/s",
        "MFR - total liquid": "kg/s",
        "MFR - total": "kg/s",
        "MFR - gas": "kg/s",
        "MFR - oil": "kg/s",
        "MFR - liquid - 2 phase": "kg/s",
        "MFR - total - 2 phase": "kg/s",
        
        # Mass fractions
        "CO2 mass frac. - gas": "-",
        "CO2 mass frac. gas": "-",
        "CO2 mass frac. - oil": "-",
        "CO2 mass frac. oil": "-",
        "Mass fraction": "-",
        "Mass fractions": "-",
        "Compositional mass fractions": "-",
        "MF - gas": "-",
        "MF - oil": "-",
        "MF - bubbles": "-",
        "MF - droplets": "-",
        "MF - total gas - 2ph": "-",
        "MF - total oil - 2ph": "-",
        
        # Mass/Volume
        "Total mass - gas": "kg",
        "Total mass - oil": "kg",
        "Total mass - total": "kg",
        "Total volume - gas": "m³",
        "Total volume - oil": "m³",
        "Total volume - total": "m³",
        "Volume - gas": "m³",
        "Volume - oil": "m³",
        "Volume - bubbles": "m³",
        "Volume - droplets": "m³",
        "Volume - total gas": "m³",
        "Volume - total liquid": "m³",
        "Volume - total": "m³",
        "Accumulated volume": "m³",
        "Standard volume flow rate": "m³/s",
        "Std VFR - gas": "Sm³/d",
        "Std VFR - oil": "Sm³/d",
        
        # Velocity
        "Velocities": "m/s",
        "Velocity - gas": "m/s",
        "Velocity - oil": "m/s",
        "Superficial velocities": "m/s",
        "Superficial velocity - gas": "m/s",
        "Superficial velocity - oil": "m/s",
        "Superficial velocity - bubbles": "m/s",
        "Superficial velocity - droplets": "m/s",
        "Superficial velocity - total gas": "m/s",
        "Superficial velocity - total liquid": "m/s",
        "Superficial velocity - total": "m/s",
        
        # Volume fractions
        "Volume fraction": "-",
        "VF - gas": "-",
        "VF - oil": "-",
        "VF - bubbles": "-",
        "VF - droplets": "-",
        "VF - total gas": "-",
        "VF - total oil": "-",
        "VF - total gas - 2ph": "-",
        "VF - total oil - 2ph": "-",
        "VF - total gas - 2ph - pressure node": "-",
        "VF - total oil - 2ph - pressure node": "-",
        
        # Position/Geometry
        "Elevation profile": "m",
        "Mesh boundaries": "m",
        "Mesh centers": "m",
        "Position": "m",
        "position": "m",
        "Pipe elevation profile": "m",
        
        # Heat transfer
        "Heat transfer - gas-wall": "W/m²-K",
        "Heat transfer - oil-wall": "W/m²-K",
        "Heat transfer - gas-oil": "W/m²-K",
        "Heat transfer - average-wall": "W/m²-K",
        "Heat transfer - OHTC": "W/m²-K",
        "Heat transfer - surroundings": "W/m²-K",
        "Heat transfer coefficients": "W/m²-K",
        
        # Iterations/Residuals
        "Hydrodynamics": "-",
        "Hydrodynamics iterations": "-",
        "MVP total": "-",
        "MVP total iterations": "-",
        "MVP last": "-",
        "MVP last iterations": "-",
        "Energy": "-",
        "Energy iterations": "-",
        "Custom fluid": "-",
        "Custom fluid iterations": "-",
        "Compositional": "-",
        "Compositional iterations": "-",
        "Iterations": "-",
        "Mass residual": "kg/s",
        "Momentum residual": "N",
        "Energy residual": "K",
        "Residual": "-",
        "Restarts": "-",
        
        # Time consumption
        "Time - properties": "s",
        "Time - point model": "s",
        "Time - momentum": "s",
        "Time - MVP total": "s",
        "Time - composition": "s",
        "Time - single component": "s",
        "Time - energy total": "s",
        "Time - energy wall": "s",
        "Time - output": "s",
        "Time - total": "s",
        "Time - momentum matrix": "s",
        "Time - MVP matrix": "s",
        "Time - composition matrix": "s",
        "Time - single component matrix": "s",
        "Time - energy matrix": "s",
        "Time consumption": "s",
        
        # Time steps
        "Time step": "s",
        "Max time step": "s",
        "Min time step": "s",
        "Average time step": "s",
        "CFL max time step": "s",
        
        # Other
        "Opening fraction": "-",
        "Physical flow regime id - gas-liquid": "-",
        "Physical regime id": "-",
    }
    
    @staticmethod
    def get_property_units(logger_name: str, variable_name: str) -> str:
        """
        Get SI unit for a property name from the mapping.
        Returns the unit string or '?' if unknown.
        """
        return ExtendedLedaFlow.PROPERTY_UNITS.get(variable_name, "?")
 
   
    # --- CASE LOADING USING THE OFFICIAL API ---

    def load_case_by_qs(self, case_path: str) -> str:
        """
        Load a QS-generated case into the LedaFlow database.
        """
        case_path = str(Path(case_path).resolve()).replace("\\", "/")
        print(f"> Loading case from QS: {case_path}")

        # Run the JS script inside the LEDAFLOW environment
        import subprocess, os

        with open("LedaFlowPython.js", "w") as f:
            f.write(f"""
            var CASES = ledaModules.CASES();
            var myCase = CASES.createCaseFrom("{case_path}");
            print("UUID:", myCase.uuid);
            """)

        proc = subprocess.run([self.softsh, "LedaFlowPython.js"], capture_output=True, text=True)
        os.remove("LedaFlowPython.js")

        uuid = None
        for line in (proc.stdout + proc.stderr).splitlines():
            if "UUID:" in line:
                uuid = line.split("UUID:")[-1].strip()

        if not uuid:
            raise RuntimeError("Could not load case via QS.")

        print(f"> Case loaded with UUID: {uuid}")
        self.selectcase(uuid) # LedaFlow API method
        return uuid
    


    # --- INITIALIZATION WRAPPER ---
    def initialize_case(self):
        """
        Run the correct steady-state initialization function for this 
        version of LedaFlow. LedaFlow changes naming between versions, 
        so we safely detect the right one.
        """

        # Case 1: New API: runsteady()
        if hasattr(self, "runsteady"):
            print("> LedaFlow: running steady-state (runsteady)...")
            return self.runsteady()

        # Case 2: Older API: runinitialization()
        if hasattr(self, "runinitialization"):
            print("> LedaFlow: running initialization (runinitialization)...")
            return self.runinitialization()

        # Case 3: Very old API: initialize()
        if hasattr(self, "initialize"):
            print("> LedaFlow: running initialize()...")
            return self.initialize()

        raise RuntimeError(
            "No supported initialization function found. "
            "Expected one of: runsteady(), runinitialization(), initialize()"
        )


    # ----------------------------------------------------------------------
    # --- LOGGER ACCESS ----------------------------------------------------
    # ----------------------------------------------------------------------

    def safe_available_trends(self): 
        """ 
        Returns list of available trend loggers (or an empty list). 
        """ 
        try: 
            loggers = self.availabletrends() # LedaFlow API method
            return loggers if loggers else []
        except Exception as e: 
            print(f"[WARNING] Could not retrieve trend loggers: {e}") 
            return [] 
    
    def safe_available_profiles(self): 
        """ 
        Returns available profile loggers (or an empty list)
        """ 
        try: 
            loggers = self.availableprofiles() # LedaFlow API method
            return loggers if loggers else []
        except Exception as e: 
            print(f"[WARNING] Could not retrieve profile loggers: {e}") 
            return [] 
    


    # ----------------------------------------------------------------------
    # --- EXPORT TRENDs & PROFILES -----------------------------------------
    # ----------------------------------------------------------------------

    def export_all_trends(self, output_dir):
        """
        Export ALL trend loggers to CSV files.
        
        Creates:
            <output_dir>/<LOGGER>.csv

        Each CSV contains:
            time, var1, var2, ..., varN
        """

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        loggers = self.safe_available_trends()
        # Filter out Global logger to speed up exports
        loggers = [l for l in loggers if l != "Global"]
        print(f"> Found {len(loggers)} trend loggers (excluding Global)")

        for logger in loggers:
            try:
                variables = self.availabletrends(logger) # LedaFlow API method
                logger_file = output_dir / f"{logger}.csv"

                print(f"> Exporting trend logger: {logger}")

                # Collect all trend data
                variable_data = {}
                all_times = set()

                for var in variables:
                    try:
                        raw = self.extracttrend(logger, var) # LedaFlow API method

                        # Format 1: {"time": [...], "value": [...]}
                        if "time" in raw and "value" in raw:
                            times = raw["time"]
                            vals = raw["value"]

                        # Format 2: {"values": [{time:..., valueForGivenTime:...}, ...]}
                        elif "values" in raw:
                            times  = [row["time"] for row in raw["values"]]
                            vals   = [row["valueForGivenTime"] for row in raw["values"]]

                        else:
                            print(f"[Skip] Unknown trend format for {logger}/{var}")
                            continue

                        variable_data[var] = dict(zip(times, vals))
                        all_times.update(times)

                    except Exception as e:
                        print(f"[Skip] Error reading trend {logger}/{var}: {e}")

                all_times = sorted(all_times)

                # Write CSV with units in header
                with open(logger_file, "w", newline="") as f:
                    writer = csv.writer(f)
                    # Header row 1: Variable names
                    writer.writerow(["time"] + variables)
                    # Header row 2: SI units (queried from case or fallback)
                    units = [self.get_property_units(logger, var) for var in variables]
                    writer.writerow(["[s]"] + [f"[{u}]" for u in units])

                    for t in all_times:
                        row = [t] + [
                            variable_data.get(var, {}).get(t, "")
                            for var in variables
                        ]
                        writer.writerow(row)

            except Exception as e:
                print(f"[WARNING] Could not export trend logger {logger}: {e}")

        print(f"> Trend export complete → {output_dir}")


    def export_all_profiles(self, output_dir, profile_name):
        """
        Export ALL profile variables of a specified profile logger to a single CSV.
        
        Creates:
            <output_dir>/<profile_name>.csv

        Format:
            Each variable gets its own column
            Rows are positions (at each time point)
        
        Structure:
            time, position, variable1, variable2, ..., variableN
            [s], [m], [unit1], [unit2], ..., [unitN]
            t1, pos1, val1, val2, ..., valN
            ...
        """

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        out_file = output_dir / f"{profile_name}.csv"
        
        try:
            variables = self.availableprofiles(profile_name) # LedaFlow API method
        except:
            print(f"[ERROR] No profile logger named '{profile_name}'")
            return

        print(f"> Exporting profile logger '{profile_name}' with {len(variables)} variables")

        # Collect all data organized by (time, position)
        data_by_time_pos = {}  # {(time, position): {var_name: value}}
        all_times = set()
        all_positions = set()

        for var in variables:
            try:
                raw = self.extractprofile(profile_name, var, alltimepoints=True) # LedaFlow API method
            except Exception as e:
                print(f"[Skip] Could not extract profile {var}: {e}")
                continue

            mesh = raw["mesh"]      # list of positions
            entries = raw["values"] # list of {time, valueForGivenTime}

            for entry in entries:
                t = entry["time"]
                vals = entry["valueForGivenTime"]
                
                all_times.add(t)
                for pos, val in zip(mesh, vals):
                    all_positions.add(pos)
                    key = (t, pos)
                    if key not in data_by_time_pos:
                        data_by_time_pos[key] = {}
                    data_by_time_pos[key][var] = val

        # Write CSV with variables as columns
        with open(out_file, "w", newline="") as f:
            writer = csv.writer(f)
            
            # Header row 1: Column names
            writer.writerow(["time", "position"] + variables)
            
            # Header row 2: SI units
            units = [self.get_property_units(profile_name, var) for var in variables]
            writer.writerow(["[s]", "[m]"] + [f"[{u}]" for u in units])

            # Data rows: sorted by time, then position
            for t in sorted(all_times):
                for pos in sorted(all_positions):
                    key = (t, pos)
                    if key in data_by_time_pos:
                        row_data = data_by_time_pos[key]
                        row = [t, pos] + [row_data.get(var, "") for var in variables]
                        writer.writerow(row)

        print(f"> Profile export complete → {out_file}")
            