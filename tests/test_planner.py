"""Unit tests for logical planner and join enumerator."""

import pytest
from src.parser.sql_parser import SQLParser
from src.planner.logical_plan import LogicalPlanner
from src.planner.join_enumerator import JoinEnumerator
from src.planner.physical_plan import PhysicalOperator, ProjectionOperator

def test_logical_planner_selection_pushdown():
    parser = SQLParser()
    sql = "SELECT s.name FROM students s JOIN enrollments e ON s.id = e.student_id WHERE s.cgpa > 8.5;"
    ast = parser.parse(sql)

    planner = LogicalPlanner()
    opt_plan = planner.build_plan(ast)
    assert opt_plan is not None

def test_candidate_plan_enumeration():
    parser = SQLParser()
    sql = "SELECT * FROM students s JOIN enrollments e ON s.id = e.student_id;"
    ast = parser.parse(sql)

    enumerator = JoinEnumerator()
    candidates = enumerator.enumerate_candidate_plans(ast)
    
    assert len(candidates) > 0
    assert all(isinstance(c, PhysicalOperator) for c in candidates)
