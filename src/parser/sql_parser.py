"""SQL parser converting raw SQL strings into Relational Algebra AST trees."""

import re
from typing import List, Dict, Tuple, Optional, Any
from .ast import Node, TableScan, Selection, Projection, Join

class SQLParser:
    """Parses standard SQL queries into Relational Algebra AST trees."""
    
    def __init__(self):
        pass

    def parse(self, sql_string: str) -> Node:
        """Parses a SELECT query string into a Relational Algebra AST node.
        
        Supports queries of the form:
          SELECT col1, col2
          FROM tableA a
          JOIN tableB b ON a.id = b.a_id
          WHERE a.val > 10;
        """
        sql = sql_string.strip().rstrip(";")
        
        # Regex patterns for query clauses
        select_match = re.search(r"SELECT\s+(.*?)\s+FROM\s+(.*)", sql, re.IGNORECASE | re.DOTALL)
        if not select_match:
            raise ValueError(f"Invalid SQL: missing SELECT...FROM in '{sql_string}'")

        select_cols_str = select_match.group(1).strip()
        rest = select_match.group(2).strip()

        # Split rest into FROM/JOIN part and WHERE part
        where_match = re.search(r"^(.*?)\s+WHERE\s+(.*)$", rest, re.IGNORECASE | re.DOTALL)
        if where_match:
            from_join_str = where_match.group(1).strip()
            where_str = where_match.group(2).strip()
        else:
            from_join_str = rest.strip()
            where_str = None

        # Parse FROM and JOINs
        root_relation = self._parse_from_joins(from_join_str)

        # Apply Selection (WHERE) if present
        if where_str:
            root_relation = self._parse_where(root_relation, where_str)

        # Apply Projection (SELECT)
        cols = [c.strip() for c in select_cols_str.split(",")]
        ast_root = Projection(child=root_relation, columns=cols)
        
        return ast_root

    def _parse_from_joins(self, from_join_str: str) -> Node:
        """Parses FROM clause and any JOIN clauses."""
        # Split by JOIN
        parts = re.split(r"\s+JOIN\s+", from_join_str, flags=re.IGNORECASE)
        
        # First part is main FROM table
        main_table_str = parts[0].replace("FROM", "").strip()
        current_node = self._parse_table_spec(main_table_str)

        # Subsequent parts are JOIN table ON join_condition
        for join_part in parts[1:]:
            on_match = re.search(r"^(.*?)\s+ON\s+(.*)$", join_part, re.IGNORECASE)
            if not on_match:
                raise ValueError(f"Invalid JOIN syntax in: '{join_part}'")
            
            table_spec = on_match.group(1).strip()
            join_cond = on_match.group(2).strip()
            
            join_table_node = self._parse_table_spec(table_spec)
            
            # Parse join condition (e.g. s.course_id = c.id)
            cond_match = re.match(r"([\w\.]+)\s*=\s*([\w\.]+)", join_cond)
            if cond_match:
                left_key = cond_match.group(1)
                right_key = cond_match.group(2)
            else:
                left_key = join_cond
                right_key = join_cond

            current_node = Join(
                left=current_node,
                right=join_table_node,
                left_key=left_key,
                right_key=right_key
            )

        return current_node

    def _parse_table_spec(self, table_spec: str) -> TableScan:
        """Parses a table specification like 'Students S' or 'Students AS S' or 'Students'."""
        tokens = table_spec.split()
        if len(tokens) == 1:
            return TableScan(table_name=tokens[0], alias=tokens[0])
        elif len(tokens) == 2:
            return TableScan(table_name=tokens[0], alias=tokens[1])
        elif len(tokens) == 3 and tokens[1].upper() == "AS":
            return TableScan(table_name=tokens[0], alias=tokens[2])
        else:
            return TableScan(table_name=tokens[0], alias=tokens[0])

    def _parse_where(self, root: Node, where_str: str) -> Node:
        """Parses WHERE condition clause into Selection nodes."""
        # Handle multiple AND predicates
        predicates = re.split(r"\s+AND\s+", where_str, flags=re.IGNORECASE)
        
        current_node = root
        for pred in predicates:
            pred = pred.strip()
            # Match operators: =, !=, >, <, >=, <=
            m = re.match(r"([\w\.]+)\s*(=|!=|>=|<=|>|<)\s*(.*)", pred)
            if m:
                col = m.group(1)
                op = m.group(2)
                raw_val = m.group(3).strip("'\" ")
                # Try converting raw_val to float/int if possible
                try:
                    val = float(raw_val) if '.' in raw_val else int(raw_val)
                except ValueError:
                    val = raw_val

                current_node = Selection(
                    child=current_node,
                    predicate=pred,
                    column=col,
                    operator=op,
                    value=val
                )
            else:
                current_node = Selection(
                    child=current_node,
                    predicate=pred,
                    column=pred,
                    operator="=",
                    value=1
                )
        return current_node
