/******************************************************************************
  Input file generated with LedaFlow Engineering 2.11.271.018
*******************************************************************************/

/**********************************************************************
                      PVT
***********************************************************************/
var PVT1 = new LEDA_PVT("CO2");
  PVT1.type                  = "Multiflash";
  PVT1.hydrateObj            = "None";
  PVT1.waxCurve              = "None";
  PVT1.model                 = "CPA";
  PVT1.modelViscosity        = "Pedersen";
  PVT1.species               = "CO2" ;
  PVT1.mfVersion             = "AUTO" ;

var PVT2 = new LEDA_PVT("default pvt object");
  PVT2.type                  = "ConstantProperties";
  PVT2.hydrateObj            = "None";
  PVT2.waxCurve              = "None";
  PVT2.Pref                  = 8e+06;
  PVT2.Tref                  = 288.75;
  PVT2.densities             = [64,818.7];
  PVT2.viscosities           = [1.5e-05,0.002];
  PVT2.sigmas                = [0.0207];
  PVT2.conductivities        = [0.0242,0.138];
  PVT2.heatCapacities        = [2300,2000];
  PVT2.dRhodP                = [8.000000000000001e-06,3.9100000000000005e-07];
  PVT2.dRhodT                = [8e-06,3.91e-07,3.91e-07,0];

var STDVOLUME1 = new LEDA_STDVOLUME();
  STDVOLUME1.standardP   = 101325;
  STDVOLUME1.standardT   = 288.706;
  STDVOLUME1.stockTankPs = [200000];
  STDVOLUME1.stockTankTs = [298.15];


/**********************************************************************
                      OPTIONS
***********************************************************************/
var OPT1 = new LEDA_OPTIONS();
  OPT1.name                       = "Options";
  OPT1.temperatureCalculations    = "YES";
  OPT1.heatTransfer               = "DYNAMICWALLS";
  OPT1.fastWall                   = "NO";
  OPT1.energyInsideLoop           = "YES";
  OPT1.compMassTransfer           = "YES";
  OPT1.flexibleWall               = "NO";
  OPT1.initializationType         = "SSPP";
  OPT1.mfMin                      = 1;
  OPT1.mfMax                      = 200;
  OPT1.corrosion_CO2              = 0.1;
  OPT1.corrosion_pH               = 5;
  OPT1.corrosion_Fe               = [107,0.32,0.022];
  OPT1.corrosion_MEG              = "YES";
  OPT1.apiErosionFactor           = 122;
  OPT1.flip_a1                    = 0;
  OPT1.flip_a2                    = 0.4;
  OPT1.flip_R1                    = 0.002;
  OPT1.flip_R2                    = 0.002;
  OPT1.flip_RC1                   = 0.9;
  OPT1.flip_RC2                   = 0.9;
  OPT1.flip_L                     = 0.02;
  OPT1.flip_W                     = 0.001;


/**********************************************************************
                      NUMERICAL SETTINGS
***********************************************************************/
var NUMERICAL = new LEDA_NUMERICAL();
  NUMERICAL.name               = "Numerical";
  NUMERICAL.timeAdvance        = 3600;
  NUMERICAL.cfl                = [0.8];
  NUMERICAL.time               = [0];
  NUMERICAL.dtMax              = [100];
  NUMERICAL.dtSoundSpeed       = ["Off"];
  NUMERICAL.solverSettings     = "OLD";
  NUMERICAL.discretization     = "LOWERORDER";
  NUMERICAL.nCPUs              = 2;
  NUMERICAL.limitDtHydraulic   = "NO";


/**********************************************************************
                      LOGGERS
***********************************************************************/
var LOGGERSETTINGS = new LEDA_LOGGER_GENERAL_SETTINGS();
  LOGGERSETTINGS.profileInterval = [60];
  LOGGERSETTINGS.sampleInterval  = [3600];
  LOGGERSETTINGS.time            = [0];
  LOGGERSETTINGS.trendInterval   = [10];

var LOGGER1 = new LEDA_LOGGER("Wellhead","Wellhead");
  LOGGER1.position   = 1000;
  LOGGER1.properties = "Accumulated volume,Average temperature,Mass flow rate,Mass fraction,Pressure,Standard volume flow rate,Temperature,Volume fraction";
  LOGGER1.type       = "Trend";

var LOGGER2 = new LEDA_LOGGER("Global","LedaImplicitNetwork");
  LOGGER2.position   = 0;
  LOGGER2.properties = "Iterations,Residual,Restarts,Time consumption,Time step";
  LOGGER2.type       = "Trend";

var LOGGER3 = new LEDA_LOGGER("Flowline","Flowline");
  LOGGER3.position   = 0;
  LOGGER3.properties = "Compositional mass fractions,Densities,Elevation profile,Heat transfer coefficients,Mass flow rate,Physical regime id,Pressure,Superficial velocities,Temperature,Temperature - average,Temperature - surroundings,Velocities,Volume fraction,Wall temperature - inner surface";
  LOGGER3.type       = "Profile";

var LOGGER4 = new LEDA_LOGGER("Valve","Valve");
  LOGGER4.position   = 966.666666667;
  LOGGER4.properties = "Mass flow rate,Opening fraction,Pressure Left,Pressure Right,Pressure drop";
  LOGGER4.type       = "Trend";

var LOGGER5 = new LEDA_LOGGER("InjectionPoint","InjectionPoint");
  LOGGER5.position   = 0;
  LOGGER5.properties = "Average temperature,Mass flow rate,Pressure";
  LOGGER5.type       = "Trend";

var LOGGER6 = new LEDA_LOGGER("Upstream","Flowline");
  LOGGER6.position   = 965;
  LOGGER6.properties = "Pressure drop,Total masses,Total volumes";
  LOGGER6.type       = "Trend";

var LOGGER7 = new LEDA_LOGGER("Downstream","Flowline");
  LOGGER7.position   = 968;
  LOGGER7.properties = "Pressure drop,Total masses,Total volumes";
  LOGGER7.type       = "Trend";


/**********************************************************************
                      BOUNDARY CONDITIONS
***********************************************************************/
var BC1 = new LEDA_BC();
  BC1.composition   = [[1]];
  BC1.expansionLoss = "NO";
  BC1.markAsInlet   = "NO";
  BC1.massmoleflag  = "MASS_FRACTIONS";
  BC1.phaseSplit    = "FLASH";
  BC1.pressure      = [8000000];
  BC1.temperature   = [277.15];
  BC1.time          = [0];
  BC1.type          = "PRESSURE_1D";

var BC2 = new LEDA_BC();
  BC2.composition   = [[1]];
  BC2.massFlowrate  = [40];
  BC2.massFractions = [[0,1]];
  BC2.massmoleflag  = "MASS_FRACTIONS";
  BC2.phaseSplit    = "MASS_FRACTIONS";
  BC2.temperature   = [273.15];
  BC2.time          = [0];
  BC2.type          = "MASSIN_1D";


/**********************************************************************
                      WALLS & MATERIALS
***********************************************************************/
var MATERIAL1 = new LEDA_MATERIAL("Steel (carbon)");
  MATERIAL1.type          = "Solid";
  MATERIAL1.conductivity  = 45;
  MATERIAL1.density       = 7850;
  MATERIAL1.heatCapacity  = 470;
  MATERIAL1.emissivity    = 0.8;
  MATERIAL1.youngs        = 2e+11;
  MATERIAL1.viscosity     = 0;
  MATERIAL1.expansion     = 0;

var MATERIAL2 = new LEDA_MATERIAL("Steel (stainless)");
  MATERIAL2.type          = "Solid";
  MATERIAL2.conductivity  = 15;
  MATERIAL2.density       = 8100;
  MATERIAL2.heatCapacity  = 500;
  MATERIAL2.emissivity    = 0.12;
  MATERIAL2.youngs        = 1.8e+11;
  MATERIAL2.viscosity     = 0;
  MATERIAL2.expansion     = 0;

var MATERIAL3 = new LEDA_MATERIAL("Aerogel");
  MATERIAL3.type          = "Solid";
  MATERIAL3.conductivity  = 0.013;
  MATERIAL3.density       = 90;
  MATERIAL3.heatCapacity  = 1050;
  MATERIAL3.emissivity    = 0.8;
  MATERIAL3.youngs        = 1e+06;
  MATERIAL3.viscosity     = 0;
  MATERIAL3.expansion     = 0;

var MATERIAL4 = new LEDA_MATERIAL("Epoxy");
  MATERIAL4.type          = "Solid";
  MATERIAL4.conductivity  = 0.3;
  MATERIAL4.density       = 1440;
  MATERIAL4.heatCapacity  = 2000;
  MATERIAL4.emissivity    = 0.81;
  MATERIAL4.youngs        = 3.5e+09;
  MATERIAL4.viscosity     = 0;
  MATERIAL4.expansion     = 0;

var MATERIAL5 = new LEDA_MATERIAL("LDPE");
  MATERIAL5.type          = "Solid";
  MATERIAL5.conductivity  = 0.33;
  MATERIAL5.density       = 900;
  MATERIAL5.heatCapacity  = 2000;
  MATERIAL5.emissivity    = 0.92;
  MATERIAL5.youngs        = 3e+08;
  MATERIAL5.viscosity     = 0;
  MATERIAL5.expansion     = 0;

var MATERIAL6 = new LEDA_MATERIAL("Cement");
  MATERIAL6.type          = "Solid";
  MATERIAL6.conductivity  = 1;
  MATERIAL6.density       = 1600;
  MATERIAL6.heatCapacity  = 900;
  MATERIAL6.emissivity    = 0.96;
  MATERIAL6.youngs        = 1.4e+10;
  MATERIAL6.viscosity     = 0;
  MATERIAL6.expansion     = 0;

var MATERIAL7 = new LEDA_MATERIAL("Concrete");
  MATERIAL7.type          = "Solid";
  MATERIAL7.conductivity  = 2.3;
  MATERIAL7.density       = 2300;
  MATERIAL7.heatCapacity  = 1000;
  MATERIAL7.emissivity    = 0.94;
  MATERIAL7.youngs        = 3e+10;
  MATERIAL7.viscosity     = 0;
  MATERIAL7.expansion     = 0;

var MATERIAL8 = new LEDA_MATERIAL("Rock");
  MATERIAL8.type          = "Solid";
  MATERIAL8.conductivity  = 2;
  MATERIAL8.density       = 2300;
  MATERIAL8.heatCapacity  = 900;
  MATERIAL8.emissivity    = 0.93;
  MATERIAL8.youngs        = 5e+10;
  MATERIAL8.viscosity     = 0;
  MATERIAL8.expansion     = 0;

var MATERIAL9 = new LEDA_MATERIAL("Soil");
  MATERIAL9.type          = "Solid";
  MATERIAL9.conductivity  = 0.5;
  MATERIAL9.density       = 1635;
  MATERIAL9.heatCapacity  = 753;
  MATERIAL9.emissivity    = 0.66;
  MATERIAL9.youngs        = 5e+07;
  MATERIAL9.viscosity     = 0;
  MATERIAL9.expansion     = 0;

var MATERIAL10 = new LEDA_MATERIAL("Air");
  MATERIAL10.type          = "Fluid";
  MATERIAL10.conductivity  = 0.0257;
  MATERIAL10.density       = 1.205;
  MATERIAL10.heatCapacity  = 1005;
  MATERIAL10.emissivity    = 0;
  MATERIAL10.youngs        = 100000;
  MATERIAL10.viscosity     = 1.8e-05;
  MATERIAL10.expansion     = 0.00343;

var WALL1 = new LEDA_WALL("Wall1");
  WALL1.materials         = "Steel (carbon)" ;
  WALL1.thicknesses       = [0.02];


/**********************************************************************
                      AMBIENT PROPERTIES
***********************************************************************/

/**********************************************************************
                      DEVICES
***********************************************************************/
var VALVE1 = new LEDA_VALVE();
  VALVE1.cd                      = 0.1;
  VALVE1.dissipationlengthfactor = 6.5;
  VALVE1.mode                    = "CD";
  VALVE1.model                   = "PERKINS";
  VALVE1.name                    = "Valve";
  VALVE1.opening                 = [0.2];
  VALVE1.position                = 966.666666667;
  VALVE1.time                    = [0];


/**********************************************************************
                      PIPES
***********************************************************************/
var PIPEPROPS1 = new LEDA_PIPEPROPERTIES();
  PIPEPROPS1.X           = [0,1000];
  PIPEPROPS1.Y           = [0,0];
  PIPEPROPS1.Z           = [0,0];
  PIPEPROPS1.buried      = "NO";
  PIPEPROPS1.constraint  = [1];
  PIPEPROPS1.convcorr    = [1,0];
  PIPEPROPS1.diameter    = [0.16];
  PIPEPROPS1.hinnerMin   = [0,0];
  PIPEPROPS1.hout        = [1000,1000];
  PIPEPROPS1.l_ambient   = [0.0000000000000000,1000.0000000000000000];
  PIPEPROPS1.l_geometry  = [0.0000000000000000];
  PIPEPROPS1.l_mesh      = [0.0000000000000000,33.3333333333333357,66.6666666666666714,100.0000000000000000,133.3333333333333428,166.6666666666666856,200.0000000000000284,233.3333333333333712,266.6666666666666856,300.0000000000000000,333.3333333333333144,366.6666666666666288,399.9999999999999432,433.3333333333332575,466.6666666666665719,499.9999999999998863,533.3333333333332575,566.6666666666666288,600.0000000000000000,633.3333333333333712,666.6666666666667425,700.0000000000001137,733.3333333333334849,766.6666666666668561,800.0000000000002274,833.3333333333335986,866.6666666666669698,900.0000000000003411,933.3333333333337123,966.6666666666670835,1000.0000000000004547];
  PIPEPROPS1.nparallel   = [1];
  PIPEPROPS1.roughness   = [4.5e-05];
  PIPEPROPS1.tout        = [277.15,277.15];
  PIPEPROPS1.tout_interp = "L-interp,L-interp";
  PIPEPROPS1.uout        = [0.1,0.1];
  PIPEPROPS1.walls       = "Wall1";


/**********************************************************************
                      INITIAL CONDITIONS
***********************************************************************/
var INITIALIZATIONZONES1 = new LEDA_INITIALIZATIONZONES();
  INITIALIZATIONZONES1.T              = [278.15];
  INITIALIZATIONZONES1.compositions   = [[1]];
  INITIALIZATIONZONES1.customFluids   = "None";
  INITIALIZATIONZONES1.customFluidsMF = [0];
  INITIALIZATIONZONES1.enabled        = "YES";
  INITIALIZATIONZONES1.enabledT       = "YES";
  INITIALIZATIONZONES1.massmoleflag   = "MASS";
  INITIALIZATIONZONES1.positionT      = [0];
  INITIALIZATIONZONES1.zones          = [[0,1000]];

var CLOSEDZONESPRESSURE = new LEDA_CLOSEDZONESPRESSURE();
  CLOSEDZONESPRESSURE.enabled   = "YES";
  CLOSEDZONESPRESSURE.pipeNames = "Pipe 1";
  CLOSEDZONESPRESSURE.positions = [0];
  CLOSEDZONESPRESSURE.pressures = [8000000];


/**********************************************************************
                      ANNULUS NODES
***********************************************************************/

/**********************************************************************
                      TUNERS
***********************************************************************/

/**********************************************************************
                      LEDAFLOW CLIENT
***********************************************************************/
var NWVIEWER1 = new LEDACLIENT_NWVIEWER();
NWVIEWER1.positions["InjectionPoint"] = [5000.5,5000.5];
NWVIEWER1.positions["Wellhead"] = [5300.5,5000.5];

/**********************************************************************
                      CREATE AND SET THE CASE
***********************************************************************/
var t = defaultCase("CO2_pipe");
t.setNPhase(2);
/*************************
Construct network
*************************/
t.addPipe("Flowline","new:InjectionPoint","new:Wellhead");

/*************************
//Pvt
*************************/
t.addPVT(PVT1);
t.addPVT(PVT2);
t.setPVT("CO2","Flowline");
t.setSTDVOLUME(STDVOLUME1);

/*************************
//Options
*************************/
t.setOPTIONS(OPT1);

/*************************
//Numerical settings
*************************/
t.setNUMERICAL(NUMERICAL);

/*************************
//Walls and materials
*************************/
t.addMATERIAL(MATERIAL1);
t.addMATERIAL(MATERIAL2);
t.addMATERIAL(MATERIAL3);
t.addMATERIAL(MATERIAL4);
t.addMATERIAL(MATERIAL5);
t.addMATERIAL(MATERIAL6);
t.addMATERIAL(MATERIAL7);
t.addMATERIAL(MATERIAL8);
t.addMATERIAL(MATERIAL9);
t.addMATERIAL(MATERIAL10);
t.addWALL(WALL1);

/*************************
//Ambient properties
*************************/

/*************************
Devices
*************************/
t.addVALVE(VALVE1, "Flowline");

/*************************
Boundary conditions
*************************/
t.setBC(BC1,"Wellhead");
t.setBC(BC2,"InjectionPoint");

/*************************
Pipe geometry/mesh
*************************/
t.setPIPEPROPERTIES(PIPEPROPS1, "Flowline");

/*************************
Loggers
*************************/
t.setLOGGER_GENERAL_SETTINGS(LOGGERSETTINGS);
t.addLOGGER(LOGGER1);
t.addLOGGER(LOGGER2);
t.addLOGGER(LOGGER3);
t.addLOGGER(LOGGER4);
t.addLOGGER(LOGGER5);
t.addLOGGER(LOGGER6);
t.addLOGGER(LOGGER7);

/*************************
Initial Conditions
****************************/
t.setINITIALIZATIONZONES(INITIALIZATIONZONES1, "Flowline");
t.setCLOSEDZONESPRESSURE(CLOSEDZONESPRESSURE);

/*************************
LedaFlow client
*************************/
t.setNWVIEWER(NWVIEWER1);
