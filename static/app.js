(() => {
  const $ = (id) => document.getElementById(id);
  const enc = encodeURIComponent;
  const money = new Intl.NumberFormat("es", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

  const state = {
    tree: null,          // árbol anidado tal como lo devuelve la API
    byId: {},            // id -> nodo, para búsquedas locales
    parentOf: {},        // id -> id del jefe (null en la raíz)
    selected: null,      // id de la persona seleccionada
    detail: null,        // respuesta de GET /api/empleados/<id>
    chainIds: new Set(), // cadena de mando de la selección
    collapsed: new Set(),
    matches: new Set(),
    approverId: null,
    editing: null,
  };

  // ---------- Utilidades ----------

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  async function api(method, path, body) {
    const options = { method, headers: {} };
    if (body !== undefined) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    const response = await fetch(path, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "No se pudo completar la acción");
    return data;
  }

  let toastTimer;
  function toast(message, isError = false) {
    const node = $("toast");
    node.textContent = message;
    node.className = "toast" + (isError ? " error" : "");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => node.classList.add("hidden"), 3500);
  }

  function newId() {
    return "E" + Date.now().toString(36).toUpperCase();
  }

  function sortedPeople() {
    return Object.values(state.byId).sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));
  }

  function indexTree(node, parentId = null) {
    state.byId[node.id] = node;
    state.parentOf[node.id] = parentId;
    node.hijos.forEach((child) => indexTree(child, node.id));
  }

  // ---------- Carga ----------

  async function loadChart() {
    const data = await api("GET", "/api/organigrama");
    state.tree = data.arbol;
    state.byId = {};
    state.parentOf = {};
    if (state.tree) indexTree(state.tree);

    renderStats(data.estadisticas);
    renderManagerOptions();
    renderPairOptions();
    renderAreaTable(data.estadisticas.por_area);

    if (state.selected && state.byId[state.selected]) {
      await loadDetail(state.selected);
    } else {
      state.selected = null;
      state.detail = null;
      state.chainIds = new Set();
      renderTree();
      renderDetail();
    }
  }

  async function loadDetail(id) {
    state.detail = await api("GET", `/api/empleados/${enc(id)}`);
    state.selected = id;
    state.chainIds = new Set(state.detail.cadena.map((p) => p.id));
    renderTree();
    renderDetail();
  }

  function select(id) {
    loadDetail(id).catch((error) => toast(error.message, true));
  }

  // ---------- Estadísticas ----------

  function renderStats(stats) {
    const item = (label, value) => {
      const wrap = el("span", "stat");
      wrap.append(el("span", "", label), el("span", "stat-value", value));
      return wrap;
    };
    $("stats").replaceChildren(
      item("Empleados", String(stats.total)),
      item("Niveles", String(stats.altura)),
      item("Presupuesto total", money.format(stats.presupuesto_total)),
    );
  }

  // ---------- Árbol ----------

  function renderTree() {
    const container = $("tree");
    if (!state.tree) {
      container.replaceChildren(el("p", "muted", "No hay empleados todavía. Agregue al director general."));
      return;
    }
    const list = el("ul", "tree-list");
    list.append(buildNode(state.tree));
    container.replaceChildren(list);
  }

  function buildNode(node) {
    const item = el("li");
    const hasReports = node.hijos.length > 0;
    const collapsed = state.collapsed.has(node.id);

    const line = el("div", "tree-line");

    if (hasReports) {
      const toggle = el("button", "toggle");
      toggle.type = "button";
      toggle.setAttribute("aria-expanded", String(!collapsed));
      toggle.setAttribute("aria-label", `${collapsed ? "Expandir" : "Contraer"} a ${node.nombre}`);
      toggle.append(el("span", collapsed ? "chevron closed" : "chevron"));
      toggle.addEventListener("click", (event) => {
        event.stopPropagation();
        toggleNode(node.id);
      });
      line.append(toggle);
    } else {
      line.append(el("span", "toggle-spacer"));
    }

    const row = el("button", "row");
    row.type = "button";
    row.classList.toggle("selected", node.id === state.selected);
    row.classList.toggle("on-path", state.chainIds.has(node.id) && node.id !== state.selected);
    row.classList.toggle("approver", node.id === state.approverId);
    row.classList.toggle("match", state.matches.has(node.id));
    if (node.id === state.selected) row.setAttribute("aria-current", "true");
    row.append(el("span", "name", node.nombre), el("span", "meta", `${node.cargo} · ${node.area}`));
    row.addEventListener("click", () => select(node.id));
    line.append(row);

    item.append(line);

    if (hasReports && !collapsed) {
      const list = el("ul");
      node.hijos.forEach((child) => list.append(buildNode(child)));
      item.append(list);
    }
    return item;
  }

  function toggleNode(id) {
    if (state.collapsed.has(id)) state.collapsed.delete(id);
    else state.collapsed.add(id);
    renderTree();
  }

  function expandAll() {
    state.collapsed.clear();
    renderTree();
  }

  function collapseAll() {
    Object.values(state.byId).forEach((node) => {
      if (node.hijos.length && node.id !== state.tree.id) state.collapsed.add(node.id);
    });
    renderTree();
  }

  function expandAncestors(id) {
    let parent = state.parentOf[id];
    while (parent) {
      state.collapsed.delete(parent);
      parent = state.parentOf[parent];
    }
  }

  // ---------- Búsqueda ----------

  let searchTimer;
  $("search").addEventListener("input", (event) => {
    clearTimeout(searchTimer);
    const text = event.target.value;
    searchTimer = setTimeout(() => runSearch(text), 200);
  });

  async function runSearch(text) {
    const query = text.trim();
    if (!query) {
      state.matches = new Set();
      $("search-info").textContent = "";
      renderTree();
      return;
    }
    try {
      const results = await api("GET", `/api/buscar?q=${enc(query)}`);
      state.matches = new Set(results.map((r) => r.id));
      results.forEach((r) => expandAncestors(r.id));
      $("search-info").textContent = results.length
        ? `${results.length} ${results.length === 1 ? "resultado" : "resultados"}`
        : "Sin resultados";
      renderTree();
    } catch (error) {
      toast(error.message, true);
    }
  }

  // ---------- Detalle ----------

  function renderDetail() {
    const box = $("detail");
    const d = state.detail;
    if (!d) {
      box.replaceChildren(el("p", "muted", "Seleccione un empleado para ver su posición en la jerarquía."));
      return;
    }

    const head = el("div", "detail-head");
    head.append(el("h2", "", d.nombre), el("p", "muted", `${d.cargo} · ${d.area}`));

    const chain = el("nav", "chain");
    chain.setAttribute("aria-label", "Cadena de mando");
    const path = d.cadena.slice().reverse();
    path.forEach((persona, index) => {
      const link = el("button", "chain-link", persona.nombre);
      link.type = "button";
      if (persona.id === d.id) link.setAttribute("aria-current", "true");
      link.addEventListener("click", () => select(persona.id));
      chain.append(link);
      if (index < path.length - 1) chain.append(el("span", "sep", "/"));
    });

    const reports = state.byId[d.id].hijos;
    const kpis = el("dl", "kpis");
    [
      ["Salario anual", money.format(d.salario)],
      ["Presupuesto del equipo", money.format(d.presupuesto_equipo)],
      ["Reportes directos", String(reports.length)],
      ["Nivel", d.profundidad === 0 ? "Dirección" : `Nivel ${d.profundidad + 1}`],
    ].forEach(([label, value]) => {
      const kpi = el("div", "kpi");
      kpi.append(el("dt", "", label), el("dd", "", value));
      kpis.append(kpi);
    });

    const nodes = [head, chain, kpis];

    if (reports.length) {
      nodes.push(el("h3", "section-title", "Reportes directos"));
      const list = el("ul", "report-list");
      reports.forEach((persona) => {
        const item = el("li");
        const button = el("button");
        button.type = "button";
        button.append(document.createTextNode(persona.nombre), el("span", "meta", persona.cargo));
        button.addEventListener("click", () => select(persona.id));
        item.append(button);
        list.append(item);
      });
      nodes.push(list);
    }

    const actions = el("div", "actions");
    const edit = el("button", "ghost small", "Editar datos");
    edit.type = "button";
    edit.addEventListener("click", () => startEdit(d));
    const remove = el("button", "danger small", "Eliminar");
    remove.type = "button";
    remove.addEventListener("click", () => removeEmployee(d));
    actions.append(edit, remove);
    nodes.push(actions);

    if (d.jefe_id) {
      nodes.push(buildMoveForm(d));
    }

    box.replaceChildren(...nodes);
  }

  function buildMoveForm(d) {
    const excluded = new Set([d.id, ...d.subordinados.map((p) => p.id)]);
    const wrap = el("form", "move");
    wrap.append(el("h3", "section-title", "Mover equipo bajo otro jefe"));

    const row = el("div", "move-row");
    const label = el("label", "", "Nuevo jefe");
    const picker = document.createElement("select");
    sortedPeople()
      .filter((p) => !excluded.has(p.id))
      .forEach((p) => picker.append(new Option(`${p.nombre} · ${p.cargo}`, p.id)));
    picker.value = d.jefe_id;
    label.append(picker);

    const submit = el("button", "ghost small", "Mover");
    submit.type = "submit";
    row.append(label, submit);
    wrap.append(row);

    wrap.addEventListener("submit", (event) => {
      event.preventDefault();
      moveEmployee(d.id, picker.value);
    });
    return wrap;
  }

  async function moveEmployee(id, newManagerId) {
    try {
      await api("POST", `/api/empleados/${enc(id)}/mover`, { jefe_id: newManagerId });
      toast("Equipo movido");
      await loadChart();
    } catch (error) {
      toast(error.message, true);
    }
  }

  async function removeEmployee(d) {
    if (!confirm(`¿Eliminar a ${d.nombre}? Sus reportes directos pasarán a su jefe.`)) return;
    try {
      await api("DELETE", `/api/empleados/${enc(d.id)}`);
      if (state.editing === d.id) resetForm();
      state.selected = null;
      state.detail = null;
      state.chainIds = new Set();
      toast("Empleado eliminado");
      await loadChart();
    } catch (error) {
      toast(error.message, true);
    }
  }

  // ---------- Formulario de alta y edición ----------

  function startEdit(d) {
    const form = $("employee-form");
    state.editing = d.id;
    form.elements.nombre.value = d.nombre;
    form.elements.cargo.value = d.cargo;
    form.elements.area.value = d.area;
    form.elements.salario.value = d.salario;
    $("form-title").textContent = "Editar empleado";
    $("manager-field").classList.add("hidden");
    $("cancel-edit").classList.remove("hidden");
    form.elements.nombre.focus();
  }

  function resetForm() {
    state.editing = null;
    $("employee-form").reset();
    $("form-title").textContent = "Nuevo empleado";
    $("manager-field").classList.remove("hidden");
    $("cancel-edit").classList.add("hidden");
  }

  $("cancel-edit").addEventListener("click", resetForm);

  $("employee-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const body = {
      nombre: form.elements.nombre.value.trim(),
      cargo: form.elements.cargo.value.trim(),
      area: form.elements.area.value.trim(),
      salario: Number(form.elements.salario.value),
    };
    try {
      if (state.editing) {
        await api("PUT", `/api/empleados/${enc(state.editing)}`, body);
        toast("Datos actualizados");
      } else {
        const id = newId();
        body.id = id;
        body.jefe_id = form.elements.jefe_id.value || null;
        await api("POST", "/api/empleados", body);
        state.selected = id;
        toast("Empleado agregado");
      }
      resetForm();
      await loadChart();
    } catch (error) {
      toast(error.message, true);
    }
  });

  function renderManagerOptions() {
    const picker = $("manager-select");
    const current = picker.value;
    const options = [new Option("Sin jefe (director general)", "")];
    sortedPeople().forEach((p) => options.push(new Option(`${p.nombre} · ${p.cargo}`, p.id)));
    picker.replaceChildren(...options);
    picker.value = current;
  }

  // ---------- ¿Quién aprueba? ----------

  function renderPairOptions() {
    ["pair-a", "pair-b"].forEach((id) => {
      const picker = $(id);
      const current = picker.value;
      const options = [new Option("Seleccione una persona", "")];
      sortedPeople().forEach((p) => options.push(new Option(p.nombre, p.id)));
      picker.replaceChildren(...options);
      picker.value = current;
    });
  }

  async function comparePair() {
    const a = $("pair-a").value;
    const b = $("pair-b").value;
    const result = $("pair-result");
    state.approverId = null;

    if (!a || !b) {
      result.textContent = "";
    } else if (a === b) {
      result.textContent = "Seleccione dos personas distintas.";
    } else {
      try {
        const { ancestro } = await api("GET", `/api/comun?a=${enc(a)}&b=${enc(b)}`);
        if (ancestro) {
          state.approverId = ancestro.id;
          result.replaceChildren(
            document.createTextNode("Aprueba: "),
            el("strong", "", ancestro.nombre),
            document.createTextNode(` · ${ancestro.cargo}`),
          );
        }
      } catch (error) {
        toast(error.message, true);
      }
    }
    renderTree();
  }

  $("pair-a").addEventListener("change", comparePair);
  $("pair-b").addEventListener("change", comparePair);

  // ---------- Presupuesto por área ----------

  function renderAreaTable(totals) {
    const head = el("tr");
    head.append(el("th", "", "Área"), el("th", "num", "Salarios anuales"));
    const thead = el("thead");
    thead.append(head);

    const tbody = el("tbody");
    Object.entries(totals)
      .sort((x, y) => y[1] - x[1])
      .forEach(([area, total]) => {
        const row = el("tr");
        row.append(el("td", "", area), el("td", "num", money.format(total)));
        tbody.append(row);
      });

    $("area-table").replaceChildren(thead, tbody);
  }

  // ---------- Arranque ----------

  $("expand-all").addEventListener("click", expandAll);
  $("collapse-all").addEventListener("click", collapseAll);

  loadChart().catch((error) => toast(error.message, true));
})();
