try {
  var CASES = ledaModules.CASES();
  var c = CASES.createCaseFrom("C:/Users/amand/Documents/Prosjektoppgave/Ledarunner/runs/04_12_25/run_17_27/model.qs");
  print("UUID:", c.uuid);
  print("CASE_DIR:", c.caseFolder);
} catch (e) {
  try { print("CASES_ERROR:", e.toString()); } catch (ee) {}
  try { if (e.stack) print("CASES_STACK:", e.stack); } catch (ee) {}
  throw e;
}