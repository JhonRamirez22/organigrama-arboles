"""N-ary tree that models a company's organization chart.

Each employee is a node. The root is the general director and every node
has exactly one manager (parent) and a list of direct reports (children).
"""

import json


class Employee:
    """Tree node: a person and their position in the hierarchy."""

    def __init__(self, id, name, role, area, salary):
        self.id = id
        self.name = name
        self.role = role
        self.area = area
        self.salary = salary
        self.manager = None   # parent node
        self.reports = []     # direct children

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.name,
            "cargo": self.role,
            "area": self.area,
            "salario": self.salary,
        }


class OrgChart:
    """Employee tree with hierarchy operations.

    `_nodes` is an index (dict id -> Employee) to reach a node in O(1)
    without walking the tree. The actual hierarchy always lives in the
    `manager` and `reports` pointers.
    """

    def __init__(self):
        self.root = None
        self._nodes = {}

    # ------------------------------------------------------------------
    # Basic lookup
    # ------------------------------------------------------------------

    def __len__(self):
        return len(self._nodes)

    def __contains__(self, id):
        return id in self._nodes

    def get(self, id):
        if id not in self._nodes:
            raise KeyError(f"No existe el empleado '{id}'")
        return self._nodes[id]

    # ------------------------------------------------------------------
    # Modification
    # ------------------------------------------------------------------

    def add(self, id, name, role, area, salary, manager_id=None):
        """Insert an employee under `manager_id`. Without a manager only the root is allowed."""
        if id in self._nodes:
            raise ValueError(f"Ya existe el empleado '{id}'")
        if not name or not str(name).strip():
            raise ValueError("El nombre es obligatorio")
        if salary < 0:
            raise ValueError("El salario no puede ser negativo")

        node = Employee(id, name.strip(), role, area, salary)

        if manager_id is None:
            if self.root is not None:
                raise ValueError("Ya existe un director; indique el jefe del nuevo empleado")
            self.root = node
        else:
            manager = self.get(manager_id)
            node.manager = manager
            manager.reports.append(node)

        self._nodes[id] = node
        return node

    def update(self, id, **fields):
        node = self.get(id)
        if "salary" in fields and fields["salary"] < 0:
            raise ValueError("El salario no puede ser negativo")
        for key in ("name", "role", "area", "salary"):
            if key in fields:
                setattr(node, key, fields[key])
        return node

    def move(self, id, new_manager_id):
        """Reassign an employee (with their whole team) under another manager.

        Cycles must be prevented: the new manager cannot be inside the
        subtree of the employee being moved.
        """
        node = self.get(id)
        if node is self.root:
            raise ValueError("No se puede mover al director general")

        new_manager = self.get(new_manager_id)
        if new_manager is node or self._is_descendant(new_manager, node):
            raise ValueError("Movimiento inválido: crearía un ciclo en la jerarquía")

        node.manager.reports.remove(node)
        node.manager = new_manager
        new_manager.reports.append(node)
        return node

    def remove(self, id):
        """Remove an employee. Their direct reports move up to their manager."""
        node = self.get(id)
        if node is self.root:
            if node.reports:
                raise ValueError("No se puede eliminar al director con subordinados; muévalos antes")
            self.root = None
        else:
            manager = node.manager
            manager.reports.remove(node)
            for report in node.reports:
                report.manager = manager
                manager.reports.append(report)

        del self._nodes[id]
        return node

    # ------------------------------------------------------------------
    # Tree queries
    # ------------------------------------------------------------------

    def chain_of_command(self, id):
        """Path from the employee up to the root (walks upward)."""
        path = []
        current = self.get(id)
        while current is not None:
            path.append(current)
            current = current.manager
        return path

    def lowest_common_ancestor(self, id_a, id_b):
        """Lowest common ancestor (LCA) of two employees.

        This is who must approve anything that involves both of them.
        """
        ancestors_a = {e.id for e in self.chain_of_command(id_a)}
        current = self.get(id_b)
        while current is not None:
            if current.id in ancestors_a:
                return current
            current = current.manager
        return None

    def reports_of(self, id):
        """All descendants (depth-first traversal, iterative)."""
        result = []
        stack = list(reversed(self.get(id).reports))
        while stack:
            node = stack.pop()
            result.append(node)
            stack.extend(reversed(node.reports))
        return result

    def team_budget(self, id):
        """Sum of salaries for the employee and their whole team (postorder)."""
        def total(node):
            return node.salary + sum(total(r) for r in node.reports)

        return total(self.get(id))

    def budget_by_area(self):
        """Total salary per area (breadth-first over the whole tree)."""
        totals = {}
        for node in self.levels_order():
            totals[node.area] = totals.get(node.area, 0) + node.salary
        return totals

    def search(self, text):
        """Employees whose name, role or area contains `text`."""
        text = text.strip().lower()
        if not text or self.root is None:
            return []
        return [
            node for node in self.levels_order()
            if text in node.name.lower()
            or text in (node.role or "").lower()
            or text in (node.area or "").lower()
        ]

    def levels_order(self):
        """Breadth-first traversal: from the root downward, level by level."""
        if self.root is None:
            return []
        order = []
        queue = [self.root]
        start = 0
        while start < len(queue):
            node = queue[start]
            start += 1
            order.append(node)
            queue.extend(node.reports)
        return order

    def depth(self, id):
        """Number of managers above the employee (the root has 0)."""
        return len(self.chain_of_command(id)) - 1

    def height(self):
        """Number of levels in the organization chart."""
        if self.root is None:
            return 0
        return max(self.depth(n.id) for n in self.levels_order()) + 1

    def stats(self):
        return {
            "total": len(self),
            "altura": self.height(),
            "presupuesto_total": self.team_budget(self.root.id) if self.root else 0,
            "por_area": self.budget_by_area(),
        }

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self, node=None):
        """Nested tree as a dict (used by the API and the frontend)."""
        if node is None:
            if self.root is None:
                return None
            node = self.root
        data = node.to_dict()
        data["hijos"] = [self.to_dict(r) for r in node.reports]
        return data

    def save(self, path):
        """Save the flat employee list with each manager's id, as JSON."""
        flat = [
            {**n.to_dict(), "jefe_id": n.manager.id if n.manager else None}
            for n in self.levels_order()
        ]
        with open(path, "w", encoding="utf-8") as file:
            json.dump(flat, file, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path):
        """Rebuild the tree from JSON. Each manager must appear before their reports."""
        chart = cls()
        with open(path, encoding="utf-8") as file:
            for data in json.load(file):
                chart.add(
                    data["id"],
                    data["nombre"],
                    data["cargo"],
                    data["area"],
                    data["salario"],
                    data["jefe_id"],
                )
        return chart

    def _is_descendant(self, node, ancestor):
        """True if `node` is inside the subtree of `ancestor`."""
        current = node.manager
        while current is not None:
            if current is ancestor:
                return True
            current = current.manager
        return False
