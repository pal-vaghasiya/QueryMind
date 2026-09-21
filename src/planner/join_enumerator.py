"""Join enumerator and candidate physical plan generator."""

import itertools
from typing import List, Dict, Set, Tuple, Optional, Any
from ..parser.ast import Node, TableScan, Selection, Projection, Join
from .physical_plan import (
    PhysicalOperator, SeqScan, IndexScan, NestedLoopJoin, HashJoin,
    FilterOperator, ProjectionOperator
)

class JoinEnumerator:
    """Enumerates candidate physical plans (join orderings and operator choices)."""

    def __init__(self, catalog_stats: Optional[Dict[str, Any]] = None):
        self.catalog_stats = catalog_stats or {}

    def enumerate_candidate_plans(self, logical_root: Node) -> List[PhysicalOperator]:
        """Generates multiple candidate physical execution plans for a logical AST."""
        # 1. Extract base tables and filters
        tables_with_filters, joins, projections = self._extract_query_components(logical_root)

        if not tables_with_filters:
            # Single scan fallback
            base_phys = SeqScan("dual", "dual")
            return [base_phys]

        table_aliases = list(tables_with_filters.keys())
        candidate_plans = []

        # Generate physical access paths for each base table (SeqScan vs IndexScan)
        table_access_options: Dict[str, List[PhysicalOperator]] = {}
        for alias, info in tables_with_filters.items():
            t_name = info["table_name"]
            filters = info["filters"]
            
            scans = []
            # Option 1: SeqScan
            seq = SeqScan(t_name, alias)
            node: PhysicalOperator = seq
            for f in filters:
                node = FilterOperator(node, f["predicate"], f["column"], f["operator"], f["value"])
            scans.append(node)

            # Option 2: IndexScan if column indexed
            has_idx = self._table_has_index(t_name, filters)
            if has_idx:
                idx_col = has_idx
                idx_scan = IndexScan(t_name, idx_col, alias)
                idx_node: PhysicalOperator = idx_scan
                for f in filters:
                    if f["column"] != idx_col:
                        idx_node = FilterOperator(idx_node, f["predicate"], f["column"], f["operator"], f["value"])
                scans.append(idx_node)

            table_access_options[alias] = scans

        # If no joins (single table query)
        if len(table_aliases) == 1:
            alias = table_aliases[0]
            for access_op in table_access_options[alias]:
                final_op = ProjectionOperator(access_op, projections) if projections else access_op
                candidate_plans.append(final_op)
            return candidate_plans

        # Generate join orders (permutations)
        # Limit to max 4 tables to prevent combinatorial explosion in enumeration
        perm_limit = min(len(table_aliases), 4)
        for perm in itertools.permutations(table_aliases[:perm_limit]):
            # Build physical join tree for permutation
            join_trees = self._build_join_trees_for_order(list(perm), table_access_options, joins)
            for tree in join_trees:
                final_op = ProjectionOperator(tree, projections) if projections else tree
                candidate_plans.append(final_op)

        return candidate_plans if candidate_plans else [SeqScan("fallback")]

    def _extract_query_components(self, node: Node) -> Tuple[Dict[str, Dict], List[Dict], List[str]]:
        tables: Dict[str, Dict] = {}
        joins: List[Dict] = []
        projections: List[str] = []

        def _traverse(curr: Node):
            nonlocal projections
            if isinstance(curr, Projection):
                projections = curr.columns
                _traverse(curr.children[0])
            elif isinstance(curr, Selection):
                # Attach filter to table
                child_sub = curr.children[0]
                if isinstance(child_sub, TableScan):
                    alias = child_sub.alias
                    if alias not in tables:
                        tables[alias] = {"table_name": child_sub.table_name, "filters": []}
                    tables[alias]["filters"].append({
                        "predicate": curr.predicate,
                        "column": curr.column,
                        "operator": curr.operator,
                        "value": curr.value
                    })
                else:
                    _traverse(child_sub)
            elif isinstance(curr, Join):
                joins.append({
                    "left_key": curr.left_key,
                    "right_key": curr.right_key,
                    "join_type": curr.join_type
                })
                _traverse(curr.left)
                _traverse(curr.right)
            elif isinstance(curr, TableScan):
                if curr.alias not in tables:
                    tables[curr.alias] = {"table_name": curr.table_name, "filters": []}

        _traverse(node)
        return tables, joins, projections

    def _table_has_index(self, table_name: str, filters: List[Dict]) -> Optional[str]:
        # Check catalog stats for index
        t_info = self.catalog_stats.get(table_name, {})
        indexes = t_info.get("indexes", ["id", f"{table_name[:-1]}_id", "cgpa", "amount"])
        for f in filters:
            col_short = f["column"].split(".")[-1]
            if col_short in indexes:
                return col_short
        return None

    def _build_join_trees_for_order(
        self,
        order: List[str],
        access_map: Dict[str, List[PhysicalOperator]],
        joins: List[Dict]
    ) -> List[PhysicalOperator]:
        trees = []
        first_alias = order[0]
        second_alias = order[1]

        left_ops = access_map[first_alias]
        right_ops = access_map[second_alias]

        join_info = self._find_join_condition(first_alias, second_alias, joins)
        left_key = join_info.get("left_key", f"{first_alias}.id")
        right_key = join_info.get("right_key", f"{second_alias}.id")

        base_joins = []
        for l_op in left_ops:
            for r_op in right_ops:
                # Option A: NestedLoopJoin
                base_joins.append(NestedLoopJoin(l_op, r_op, left_key, right_key))
                # Option B: HashJoin
                base_joins.append(HashJoin(l_op, r_op, left_key, right_key))

        current_trees = base_joins

        for i in range(2, len(order)):
            next_alias = order[i]
            next_ops = access_map[next_alias]
            next_trees = []
            for curr_t in current_trees:
                j_info = self._find_join_condition(order[i-1], next_alias, joins)
                l_k = j_info.get("left_key", f"{order[i-1]}.id")
                r_k = j_info.get("right_key", f"{next_alias}.id")
                for n_op in next_ops:
                    next_trees.append(NestedLoopJoin(curr_t, n_op, l_k, r_k))
                    next_trees.append(HashJoin(curr_t, n_op, l_k, r_k))
            current_trees = next_trees

        return current_trees

    def _find_join_condition(self, alias1: str, alias2: str, joins: List[Dict]) -> Dict:
        for j in joins:
            lk = j["left_key"]
            rk = j["right_key"]
            if (alias1 in lk and alias2 in rk) or (alias2 in lk and alias1 in rk):
                return j
        return {"left_key": f"{alias1}.id", "right_key": f"{alias2}.id"}
