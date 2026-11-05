/* PharmaSuite Pro - offline API. Runs entirely in the browser, no server needed. */
(function () {
  if (!localStorage.getItem("ps_token")) localStorage.setItem("ps_token", "offline");

  let RDKit = null;
  const rdkitReady = typeof initRDKitModule === "function"
    ? initRDKitModule().then((m) => { RDKit = m; }).catch(() => {})
    : Promise.resolve();

  const loadJson = (path, fallback) =>
    fetch(path).then((r) => (r.ok ? r.json() : fallback)).catch(() => fallback);

  const dataReady = Promise.all([
    loadJson("data/elements.json", []),
    loadJson("data/drugs.json", []),
    loadJson("data/formulation.json", { excipients: [], rules: [], advice: {} }),
  ]).then(([elements, drugs, formulation]) => ({ elements, drugs, formulation }));

  const fail = (msg) => { throw new Error(msg); };
  const round4 = (x) => Math.round(x * 10000) / 10000;
  const isInt = (s) => /^\d+$/.test(s);

  /* ---------- chemistry without RDKit: formulas, balancing ---------- */
  const TOKEN = /[A-Z][a-z]?|\(|\)|\d+/g;

  function parseFormula(formula) {
    const f = formula.replace(/ /g, "");
    if (!f) fail("Empty formula");
    const tokens = f.match(TOKEN) || [];
    if (tokens.join("") !== f) fail("Invalid formula: " + f);
    const stack = [{}];
    for (let i = 0; i < tokens.length; i++) {
      const tok = tokens[i];
      const top = stack[stack.length - 1];
      if (tok === "(") {
        stack.push({});
      } else if (tok === ")") {
        if (stack.length === 1) fail("Unbalanced parentheses");
        const group = stack.pop();
        let mult = 1;
        if (i + 1 < tokens.length && isInt(tokens[i + 1])) { mult = Number(tokens[i + 1]); i++; }
        const target = stack[stack.length - 1];
        for (const el in group) target[el] = (target[el] || 0) + group[el] * mult;
      } else if (isInt(tok)) {
        fail("Unexpected number in formula: " + f);
      } else {
        let cnt = 1;
        if (i + 1 < tokens.length && isInt(tokens[i + 1])) { cnt = Number(tokens[i + 1]); i++; }
        top[tok] = (top[tok] || 0) + cnt;
      }
    }
    if (stack.length !== 1) fail("Unbalanced parentheses");
    return stack[0];
  }

  const gcd = (a, b) => { a = Math.abs(a); b = Math.abs(b); while (b) { [a, b] = [b, a % b]; } return a; };
  const fr = (n, d = 1) => { if (d < 0) { n = -n; d = -d; } const g = gcd(n, d) || 1; return { n: n / g, d: d / g }; };
  const fsub = (a, b) => fr(a.n * b.d - b.n * a.d, a.d * b.d);
  const fmul = (a, b) => fr(a.n * b.n, a.d * b.d);
  const fdiv = (a, b) => fr(a.n * b.d, a.d * b.n);
  const isZero = (a) => a.n === 0;

  function nullspace(matrix, n) {
    const m = matrix.map((row) => row.slice());
    const pivots = [];
    let r = 0;
    for (let c = 0; c < n; c++) {
      let p = -1;
      for (let i = r; i < m.length; i++) if (!isZero(m[i][c])) { p = i; break; }
      if (p < 0) continue;
      [m[r], m[p]] = [m[p], m[r]];
      const pv = m[r][c];
      m[r] = m[r].map((x) => fdiv(x, pv));
      for (let i = 0; i < m.length; i++) {
        if (i !== r && !isZero(m[i][c])) {
          const f = m[i][c];
          m[i] = m[i].map((a, j) => fsub(a, fmul(f, m[r][j])));
        }
      }
      pivots.push(c);
      r++;
      if (r === m.length) break;
    }
    const free = [];
    for (let c = 0; c < n; c++) if (!pivots.includes(c)) free.push(c);
    return free.map((fc) => {
      const v = Array.from({ length: n }, () => fr(0));
      v[fc] = fr(1);
      pivots.forEach((pc, i) => { v[pc] = fr(-m[i][fc].n, m[i][fc].d); });
      return v;
    });
  }

  function balanceJS(equation) {
    const eq = equation.replace(/→/g, "->").replace(/=/g, "->");
    const parts = eq.split("->");
    if (parts.length !== 2) fail("Use exactly one arrow: reactants -> products");
    const split = (side) => side.split("+").map((s) => s.replace(/ /g, "").replace(/^\d+/, "")).filter(Boolean);
    const reactants = split(parts[0]);
    const products = split(parts[1]);
    if (!reactants.length || !products.length) fail("Both sides need at least one species");
    const species = reactants.concat(products);
    const parsed = species.map(parseFormula);
    const elements = Array.from(new Set(parsed.flatMap((p) => Object.keys(p)))).sort();
    const n = species.length;
    const matrix = elements.map((el) => parsed.map((p, i) => fr((p[el] || 0) * (i < reactants.length ? 1 : -1))));
    const basis = nullspace(matrix, n);
    if (!basis.length) fail("This equation cannot be balanced");
    if (basis.length > 1) fail("More than one solution exists; check the species");
    const vec = basis[0];
    let lcm = 1;
    for (const x of vec) lcm = (lcm * x.d) / gcd(lcm, x.d);
    let ints = vec.map((x) => (x.n * lcm) / x.d);
    if (ints.every((c) => c <= 0)) ints = ints.map((c) => -c);
    if (ints.some((c) => c <= 0)) fail("Equation cannot be balanced with positive coefficients");
    let g = 0;
    for (const c of ints) g = gcd(g, c);
    ints = ints.map((c) => c / g);
    const fmt = (items) => items.map(([s, c]) => (c !== 1 ? c : "") + s).join(" + ");
    const left = species.slice(0, reactants.length).map((s, i) => [s, ints[i]]);
    const right = species.slice(reactants.length).map((s, i) => [s, ints[reactants.length + i]]);
    return { coefficients: ints, balanced: fmt(left) + " -> " + fmt(right) };
  }

  /* ---------- RDKit helpers ---------- */
  function withMol(smiles, fn) {
    if (!RDKit) fail("The chemistry engine is still loading. Try again in a moment.");
    const mol = RDKit.get_mol(smiles || "");
    try {
      if (!mol || !mol.is_valid()) fail("Invalid SMILES string");
      return fn(mol);
    } finally {
      if (mol) mol.delete();
    }
  }

  function propertiesRoute(smiles) {
    return withMol(smiles, (mol) => {
      const d = JSON.parse(mol.get_descriptors());
      const viol = [d.MolWt > 500, d.MolLogP > 5, d.NumHBD > 5, d.NumHBA > 10].filter(Boolean).length;
      return {
        smiles: smiles,
        canonical_smiles: mol.get_smiles(),
        formula: "-",
        molecular_weight: round4(d.MolWt),
        log_p: round4(d.MolLogP),
        rotatable_bonds: d.NumRotatableBonds,
        h_bond_donors: d.NumHBD,
        h_bond_acceptors: d.NumHBA,
        lipinski_violations: viol,
        passes_lipinski: viol <= 1,
      };
    });
  }

  function substructureRoute(fragment, drugs) {
    if (!RDKit) fail("The chemistry engine is still loading. Try again in a moment.");
    const q = RDKit.get_qmol(fragment || "");
    try {
      if (!q || !q.is_valid()) fail("Invalid fragment. Try c1ccccc1 or C(=O)O.");
      const matches = [];
      for (const d of drugs) {
        const m = RDKit.get_mol(d.smiles);
        try {
          if (m && m.is_valid() && m.get_substruct_match(q) !== "{}") {
            matches.push({ name: d.en, smiles: d.smiles, key: d.key });
          }
        } finally {
          if (m) m.delete();
        }
      }
      return { matches: matches };
    } finally {
      if (q) q.delete();
    }
  }

  /* ---------- formulation, kinetics, stability ---------- */
  function formulationRoute(b, F, drugs) {
    const drug = drugs.find((d) => d.key === b.api);
    if (!drug) fail("Unknown active ingredient");
    const comps = [[b.api, Number(b.api_pct)]].concat((b.excipients || []).map((e) => [e.key, Number(e.pct)]));
    const total = comps.reduce((s, c) => s + c[1], 0);
    const ranges = [];
    for (const [k, p] of comps) {
      const ex = F.excipients.find((x) => x.key === k);
      if (ex) {
        const st = p >= ex.min && p <= ex.max ? "ok" : (p < ex.min ? "low" : "high");
        ranges.push([k, p, ex.min, ex.max, st]);
      }
    }
    const keys = new Set(comps.map((c) => c[0]));
    const alerts = F.rules
      .filter((r) => drug.tags.includes(r[0]) && keys.has(r[1]))
      .map((r) => [r[3], r[2], r[1]]);
    const advice = Array.from(new Set(drug.tags.filter((t) => F.advice[t]).map((t) => F.advice[t])));
    return { total: round4(total), total_ok: Math.abs(total - 100) < 0.01, ranges: ranges, alerts: alerts, advice: advice };
  }

  function kineticsRoute(b) {
    const order = Number(b.order), a0 = Number(b.a0), k = Number(b.k), t = b.t;
    if (!(a0 > 0 && k > 0)) fail("a0 and k must be greater than zero");
    let hl;
    if (order === 0) hl = a0 / (2 * k);
    else if (order === 1) hl = Math.log(2) / k;
    else if (order === 2) hl = 1 / (k * a0);
    else fail("order must be 0, 1 or 2");
    let conc = null;
    if (t !== null && t !== undefined && t !== "") {
      const tv = Number(t);
      if (tv < 0) fail("t must be zero or greater");
      if (order === 0) conc = Math.max(a0 - k * tv, 0);
      else if (order === 1) conc = a0 * Math.exp(-k * tv);
      else conc = 1 / (1 / a0 + k * tv);
    }
    return { half_life: hl, concentration: conc };
  }

  function shelfRoute(b) {
    const kRef = Number(b.k_ref), tRef = Number(b.t_ref_c), ea = Number(b.ea_kj), tSt = Number(b.t_storage_c);
    if (!(kRef > 0)) fail("k_ref must be greater than zero");
    const t1 = tRef + 273.15, t2 = tSt + 273.15;
    if (t1 <= 0 || t2 <= 0) fail("Temperature cannot be below absolute zero");
    const k = kRef * Math.exp(-(ea * 1000) / 8.314 * (1 / t2 - 1 / t1));
    return { k_storage: k, t90: -Math.log(0.9) / k, t_half: Math.log(2) / k };
  }

  /* ---------- favorites (stored in this phone's browser) ---------- */
  const FAV_KEY = "ps_favs";
  const getFavs = () => JSON.parse(localStorage.getItem(FAV_KEY) || "[]");
  const setFavs = (list) => localStorage.setItem(FAV_KEY, JSON.stringify(list));

  /* ---------- the router that replaces the server API ---------- */
  window.localApi = async function (path, body, method) {
    const D = await dataReady;
    await rdkitReady;
    const verb = (method || (body !== undefined && body !== null ? "POST" : "GET")).toUpperCase();
    const p = path.split("?")[0];

    if (p === "/api/v1/auth/me") return { id: 0, username: "offline", role: "student" };
    if ((p === "/api/v1/auth/login" || p === "/api/v1/auth/register") && verb === "POST") {
      return { token: "offline", user: { id: 0, username: (body && body.username) || "offline", role: "student" } };
    }
    if (p === "/api/v1/auth/logout") return { ok: true };
    if (p === "/api/v1/elements") return D.elements;
    if (p === "/api/v1/drugs") return D.drugs;
    if (p === "/api/v1/formulation/excipients") return D.formulation.excipients;
    if (p === "/api/v1/formulation/check") return formulationRoute(body, D.formulation, D.drugs);
    if (p === "/api/v1/equations/balance") {
      const r = balanceJS(body.equation || "");
      return { balanced: r.balanced, coefficients: r.coefficients };
    }
    if (p === "/api/v1/kinetics/rate") return kineticsRoute(body);
    if (p === "/api/v1/stability/shelf-life") return shelfRoute(body);
    if (p === "/api/v1/compounds/properties") return propertiesRoute(body.smiles);
    if (p === "/api/v1/compounds/svg") {
      return { svg: withMol(body.smiles, (mol) => mol.get_svg(400, 400)) };
    }
    if (p === "/api/v1/compounds/3d") fail("The 3D view needs the online version.");
    if (p === "/api/v1/substructure") return substructureRoute(body.fragment, D.drugs);
    if (p === "/api/v1/favorites" && verb === "GET") return getFavs();
    if (p === "/api/v1/favorites" && verb === "POST") {
      withMol(body.smiles, () => true);
      const item = { id: Date.now(), name: body.name, smiles: body.smiles };
      setFavs(getFavs().concat([item]));
      return item;
    }
    if (p.indexOf("/api/v1/favorites/") === 0 && verb === "DELETE") {
      const id = Number(p.split("/").pop());
      setFavs(getFavs().filter((f) => f.id !== id));
      return { ok: true };
    }
    if (p.indexOf("/api/v1/quizzes") === 0 || p.indexOf("/api/v1/assistant") === 0) {
      fail("This feature needs the online version (internet connection).");
    }
    fail("Not available offline.");
  };
})();
