try {
  var CASES = ledaModules.CASES();
  var c = CASES.createCaseFrom("C:/Users/amand/Documents/Prosjektoppgave/Ledarunnerns/24_11_25/run_13_36/model.qs");
  print("UUID:", c.uuid);
  print("CASE_DIR:", c.caseFolder);
} catch (e) {
  try { print("CASES_ERROR:", e.toString()); } catch (ee) {}
  try { if (e.stack) print("CASES_STACK:", e.stack); } catch (ee) {}
  throw e;
}