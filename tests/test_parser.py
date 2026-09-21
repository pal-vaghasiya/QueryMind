"""Unit tests for SQL parser and Relational Algebra AST generation."""

import pytest
from src.parser.sql_parser import SQLParser
from src.parser.ast import Projection, Selection, Join, TableScan

def test_sql_parser_simple_select():
    parser = SQLParser()
    sql = "SELECT name, age FROM students s WHERE s.cgpa > 8.0;"
    ast = parser.parse(sql)

    assert isinstance(ast, Projection)
    assert ast.columns == ["name", "age"]
    
    sel = ast.children[0]
    assert isinstance(sel, Selection)
    assert sel.column == "s.cgpa"
    assert sel.operator == ">"
    assert sel.value == 8.0

    scan = sel.children[0]
    assert isinstance(scan, TableScan)
    assert scan.table_name == "students"
    assert scan.alias == "s"

def test_sql_parser_join():
    parser = SQLParser()
    sql = "SELECT s.name, e.grade FROM students s JOIN enrollments e ON s.id = e.student_id;"
    ast = parser.parse(sql)

    assert isinstance(ast, Projection)
    join_node = ast.children[0]
    assert isinstance(join_node, Join)
    assert join_node.left.table_name == "students"
    assert join_node.right.table_name == "enrollments"
    assert join_node.left_key == "s.id"
    assert join_node.right_key == "e.student_id"
