import json
import os
import subprocess
import winreg

class LedaFlow:
    '''
    A class containing methods for working with LedaFlow Engineering.
    '''

    def __init__(self, version):
        '''
        Initializes the LedaFlow Engineering Python API.
        
        Parameters
        ----------
        version : str
            A specific version of LedaFlow.

        Example
        -------
        from LedaFlow import LedaFlow
        lf = LedaFlow("2.6.260.021")
        '''
        self.caseId = ""
        self.softsh = ""

        # Get the list of installed LedaFlow versions from the registry
        mykey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'Software\Wow6432Node\Kongsberg Oil & Gas Technologies\LedaFlow Installations')
        nversions = winreg.QueryInfoKey(mykey)[1]
        
        if version=="":
            print('> ERROR: Please specify a LedaFlow version (e.g. 2.6.260.021)')
        else:
            # Find the LedaFlow version specified by the user
            for i in range(nversions):
                if winreg.EnumValue(mykey, i)[0] == version:
                    self.softsh = winreg.EnumValue(mykey, i)[1] + "\\softsh.exe"
                    return    # Success
        
            print('> ERROR: LedaFlow version not found: ', version)

    def __caseidinvalid(self):
        if self.caseId=="":
            print('ERROR: No LedaFlow case selected. Please use "LEDAFLOW.selectcase(UUID)" to select a LedaFlow case.')
            return True
        else:
            # Create dummy script, just to see if the case is valid
            with open('LedaFlowPython.js', mode='w') as handle:
                handle.write(f'var caseId = "{self.caseId}";\n')
                handle.write('caseObj = ledaModules.CASES().caseobj(caseId);\n')
                handle.write('if (caseObj.name=="") throw("ERROR: Invalid case ID. Please use LEDAFLOW.selectcase(UUID) to select a LedaFlow case.");\n')

            # Execute script
            proc = subprocess.run([self.softsh, 'LedaFlowPython.js'], capture_output=True)
            os.remove('LedaFlowPython.js')

            if not (proc.returncode==0):
                print('ERROR: Invalid case ID. Please use LEDAFLOW.selectcase(UUID) to select a LedaFlow case.')
                return True

        return False

    def selectcase(self, caseId):
        '''
        Selects a LedaFlow case from the database.
        
        Parameters
        ----------
        caseId : str
            The case ID of a LedaFlow case. This can be obtained from the GUI 
            by right-clicking on a case in the case browser and selecting
            "Show case ID"
        '''
        self.caseId = caseId
        self.__caseidinvalid()

    def initialize(self, purge = True):
        '''
        Initializes a LedaFlow case using the Steady-State Pre-Processor.
        
        Parameters
        ----------
        purge : bool, optional
            When True (default value) removes all simulation results and resets
            the time to zero.
        '''
        if self.__caseidinvalid():
            return
    
        # Create script for initialization
        with open('LedaFlowPython.js', mode='w') as handle:
            handle.write(f'var caseId = "{self.caseId}";\n')
            if (purge):
                handle.write('ledaModules.CALCULATE().purge("KeepFirst",1,caseId);\n')
            handle.write('ledaModules.CALCULATE().calculateSS(caseId);\n')

        # Execute script
        print('> LedaFlow: initializing...')
        proc = subprocess.run([self.softsh, 'LedaFlowPython.js'])
        os.remove('LedaFlowPython.js')
        
    def rundynamic(self, timeAdvance):
        '''
        Runs a dynamic simulation for a given time period.
        
        Note that LedaFlow automatically saves the state of the model after
        every run. So every time this command is called the simulation advances
        further in time.
        
        Parameters
        ----------
        timeAdvance : float
            The time to advance the dynamic simulation.
            
        Example
        -------
        lf.rundynamic(3600.0)
            Advance the dynamic simulation for one hour.
        '''
        if self.__caseidinvalid():
            return

        # Create script for running a dynamic simulation
        with open('LedaFlowPython.js', mode='w') as handle:
            handle.write(f'var caseId = "{self.caseId}";\n')
            handle.write('var t = new LedaGeneralCase(caseId);\n')
            handle.write(f't.mycase.setTimeAdvance({timeAdvance});\n')
            handle.write('ledaModules.CALCULATE().calculate(caseId);\n')

        # Execute script
        print('> LedaFlow: starting dynamic simulation...')
        proc = subprocess.run([self.softsh, 'LedaFlowPython.js'])
        os.remove('LedaFlowPython.js')

    def availabletrends(self, loggerName = ""):
        '''
        Returns an array of available trend loggers or logger properties for
        the specified logger.
        
        Parameters
        ----------
        loggerName : str, optional
            When a logger name is specified, this method returns the available
            logger properties for the specified trend logger. Otherwise the
            method returns the available trend loggers.
            
        Example
        -------
        lf.availabletrends()
            Returns all trend loggers available in the selected LedaFlow case.

        lf.availabletrends("Pipe 1")
            Returns the properties available for profile logger "Pipe 1"
        '''
        if self.__caseidinvalid():
            return

        # Create script for extracting information about the trend loggers
        with open('LedaFlowPython.js', mode='w') as handle:
            handle.write(f'var caseId = "{self.caseId}";\n')
            handle.write('var extractor = ledaModules.RESULTS().makeExtractor(caseId);\n')

            if (loggerName==""):  # Show logger names
                handle.write(f'var filter = extractor.catalog.trends;\n')
                handle.write('var key = "loggerName";\n')
            else:                 # Show logger properties
                handle.write(f'var filter = extractor.catalog.filterTrends({{loggerName:["{loggerName}"]}}, true);\n')
                handle.write('var key = "displayName";\n')

            handle.write('var previous = "";\n')
            handle.write('var loggerObject = [];\n')
            handle.write('for (j = 0; j < filter.length; j++) {\n')
            handle.write('  if (filter[j][key]!=previous) {\n')
            handle.write('    loggerObject.push(filter[j][key]);\n')
            handle.write('    previous = filter[j][key];\n')
            handle.write('  }\n')
            handle.write('}\n')
            handle.write('ledaModules.FILE().writeJsonfileFromObject(loggerObject,"LedaFlowPython.json");\n')
            
        # Execute script
        proc = subprocess.run([self.softsh, 'LedaFlowPython.js'], capture_output=True)
        os.remove('LedaFlowPython.js')

        # Read json file
        with open('LedaFlowPython.json') as json_file:
            data = json.load(json_file)
        os.remove('LedaFlowPython.json')
        
        return data

    def availableprofiles(self, loggerName = ""):
        '''
        Returns an array of available profile loggers or logger properties
        for the specified logger.
        
        Parameters
        ----------
        loggerName : str, optional
            When a logger name is specified, this method returns the available
            logger properties for the specified profile logger. Otherwise the
            method returns the available profile loggers.
            
        Example
        -------
        lf.availableprofiles()
            Returns all profile loggers available in the selected LedaFlow case.

        lf.availableprofiles("Pipe 1")
            Returns the properties available for profile logger "Pipe 1"
        '''
        if self.__caseidinvalid():
            return

        # Create script for extracting information about the profile loggers
        with open('LedaFlowPython.js', mode='w') as handle:
            handle.write(f'var caseId = "{self.caseId}";\n')
            handle.write('var extractor = ledaModules.RESULTS().makeExtractor(caseId);\n')

            if (loggerName==""):  # Show logger names
                handle.write(f'var filter = extractor.catalog.profiles;\n')
                handle.write('var key = "loggerName";\n')
            else:                 # Show logger properties
                handle.write(f'var filter = extractor.catalog.filterProfiles({{loggerName:["{loggerName}"]}}, true);\n')
                handle.write('var key = "displayName";\n')

            handle.write('var previous = "";\n')
            handle.write('var loggerObject = [];\n')
            handle.write('for (j = 0; j < filter.length; j++) {\n')
            handle.write('  if (filter[j][key]!=previous) {\n')
            handle.write('    loggerObject.push(filter[j][key]);\n')
            handle.write('    previous = filter[j][key];\n')
            handle.write('  }\n')
            handle.write('}\n')
            handle.write('ledaModules.FILE().writeJsonfileFromObject(loggerObject,"LedaFlowPython.json");\n')
            
        # Execute script
        proc = subprocess.run([self.softsh, 'LedaFlowPython.js'], capture_output=True)
        os.remove('LedaFlowPython.js')

        # Read json file
        with open('LedaFlowPython.json') as json_file:
            data = json.load(json_file)
        os.remove('LedaFlowPython.json')
        
        return data

    def extracttrend(self, loggerName, loggerProperty):
        '''
        Returns a trend for a specific logger property as a dictionary.
        
        Parameters
        ----------
        loggerName : str
            The name of a trend logger.
            
        loggerProperty : str
            The display name of a property associated with the logger.
            
        Example
        -------
        lf.extractttrend("Node 1", "Pressure")
            Returns the pressure trend for flow boundary "Node 1".
        '''
        if self.__caseidinvalid():
            return

        # Create script for extracting a trend logger as a json file
        with open('LedaFlowPython.js', mode='w') as handle:
            handle.write(f'var caseId = "{self.caseId}";\n')
            handle.write('var extractor = ledaModules.RESULTS().makeExtractor(caseId);\n')
            handle.write(f'var filter = extractor.catalog.filterTrends({{loggerName:["{loggerName}"], displayName:["{loggerProperty}"]}}, true);\n')
            handle.write('if (filter.length>0) {{\n')
            handle.write('  var loggerObject = extractor.getTrendValuesForAllTimes(filter[0]);\n')
            handle.write('  ledaModules.FILE().writeJsonfileFromObject(loggerObject,"LedaFlowPython.json");\n')
            handle.write('}} else {{\n')
            handle.write('  throw("ERROR: invalid loggerName or loggerProperty.");\n')
            handle.write('}}\n')

        # Execute script
        print(f'> LedaFlow: extracting property {loggerProperty} from logger {loggerName}')
        proc = subprocess.run([self.softsh, 'LedaFlowPython.js'], capture_output=True)
        os.remove('LedaFlowPython.js')
        
        # Check for success
        if not (proc.returncode==0):
            print('ERROR: invalid loggerName or loggerProperty.')
            return dict()
        
        # Read json file
        with open('LedaFlowPython.json') as json_file:
            data = json.load(json_file)
        os.remove('LedaFlowPython.json')

        return data

    def extractprofile(self, loggerName, loggerProperty, alltimepoints = False):
        '''
        Returns a profile for a specific logger property as a dictionary.
        
        Parameters
        ----------
        loggerName : str
            The name of a profile logger.
            
        loggerProperty : str
            The display name of a property associated with the logger.
            
        alltimepoints : bool, optional
            When False (default value) extracts only the profile at the last
            time point. When True all profiles for the entire case are 
            returned.
            
        Example
        -------
        lf.extractprofile("Pipe 1", "Volume fraction - total liquid")
            Returns the profile of the liquid hold-up for pipe "Pipe 1".
        '''
        if self.__caseidinvalid():
            return

        # Create script for extracting a profile logger as a json file
        with open('LedaFlowPython.js', mode='w') as handle:
            handle.write(f'var caseId = "{self.caseId}";\n')
            handle.write('var extractor = ledaModules.RESULTS().makeExtractor(caseId);\n')
            handle.write(f'var filter = extractor.catalog.filterProfiles({{loggerName:["{loggerName}"], displayName:["{loggerProperty}"]}}, true);\n')
            handle.write('if (filter.length>0) {{\n')
            handle.write('  var loggerObject = extractor.getProfileValuesForAllTimes(filter[0]);\n')
            handle.write('  ledaModules.FILE().writeJsonfileFromObject(loggerObject,"LedaFlowPython.json");\n')
            handle.write('}} else {{\n')
            handle.write('  throw("ERROR: invalid loggerName, loggerProperty or field.");\n')
            handle.write('}}\n')

        # Execute script
        print(f'> LedaFlow: extracting property {loggerProperty} from logger {loggerName}')
        proc = subprocess.run([self.softsh, 'LedaFlowPython.js'], capture_output=True)
        os.remove('LedaFlowPython.js')
    
        # Check for success
        if not (proc.returncode==0):
            print('ERROR: invalid loggerName or loggerProperty.')
            return dict()
        
        # Read json file
        with open('LedaFlowPython.json') as json_file:
            data = json.load(json_file)
        os.remove('LedaFlowPython.json')
        
        if alltimepoints:
            # Return everything
            return data
        else:    
            # Return only the last time point (more manageable)
            i = len(data['values'])-1
            data2 = dict()
            data2['property'] = data['property']
            data2['mesh'] = data['mesh']
            data2['time'] = data['values'][i]['time']
            data2['value'] = data['values'][i]['valueForGivenTime']
            return data2
            
            
    def changeinput(self, objectName, propertyName, value):
        '''
        Changes one of the input properties for a boundary node or device.
        
        Parameters
        ----------
        objectName : str
            The name of a device or boundary node.

        propertyName : str
            The name of a property associated with the object.
            
        value : str
            The new input. Note that all values should be in SI units, regardless of the user preferences in the GUI.

        Example
        -------
        lf.changeinput("Node 1", "MF", "[10.0]")
            Changes the mass flow rate of the flow boundary "Node 1". Note that the brackets are necessary, since this 
            is a time-dependent property.
        '''
        if self.__caseidinvalid():
            return
            
        if len(propertyName)<1:
            print('[Error] propertyName is empty')
            return

        # Need to make first character of objectName a capital letter because of javascript syntax
        propertyName2 = propertyName[0].capitalize()
        if len(propertyName)>1:
            propertyName2 = propertyName2 + propertyName[1:]

        # Create script for extracting a trend logger as a json file
        with open('LedaFlowPython.js', mode='w') as handle:
            handle.write(f'var cc = new Compound("{self.caseId}");\n')
            handle.write('var componentsToCheck = ["LedaNwNode_nPh_b_1D_massInlet","LedaNwNode_nPh_b_1D_pressureInlet", "LedaNwNode_nph_c_1D_Pid", "Leda1DnPhValve", "Leda1DnPhExternalMass", "Leda1DnPhPump", "Leda1DnPhPIWells"];\n')
            handle.write('var objectFound = false;\n')
            handle.write('for(var i=0; i<componentsToCheck.length; i++) {\n')
            handle.write('  var devices = cc.relation("child", componentsToCheck[i], true);\n')
            handle.write('  _.each(devices, function (device) {\n')
            handle.write(f'    if (device.getName()=="{objectName}") {{\n')
            handle.write('      objectFound = true;\n')
            handle.write(f'      try {{var oldStr = device.get{propertyName2}().toString();}} catch(err) {{ throw "propertyName does not exist." }}\n')
            handle.write(f'      var newStr = "{value}";\n')
            handle.write('      for(var dimOld=0; dimOld<oldStr.length; dimOld++) {if (!(oldStr[dimOld]=="[")) break;}\n')
            handle.write('      for(var dimNew=0; dimNew<newStr.length; dimNew++) {if (!(newStr[dimNew]=="[")) break;}\n')
            handle.write('      if (!(dimOld==dimNew)) throw "Wrong array dimension";\n')
            handle.write('      if (!(oldStr.split("[").length==newStr.split("[").length && newStr.split(",").length==oldStr.split(",").length)) throw "Wrong array size";\n')
            handle.write(f'      device.set{propertyName2}({value});\n')
            handle.write('    }\n')
            handle.write('  });\n')
            handle.write('}\n')
            handle.write('if(!objectFound) throw "objectName does not exist."\n')

        # Execute script
        proc = subprocess.run([self.softsh, 'LedaFlowPython.js'], capture_output=True)
        os.remove('LedaFlowPython.js')
        
        # Display error message when not succesfull
        if not (proc.returncode==0):
            stderr = proc.stderr.decode("utf-8")
            i = stderr.find('[Error]')
            j = stderr.find('\r\n[STACKTRACE]')
            print(stderr[i:j])            