"""Catalog Statistics collector extracting database table and column level metrics."""

import sqlite3
import numpy as np
from typing import Dict, Any, List, Optional

class CatalogStatistics:
    """Manages database statistics used for cardinality estimation and feature extraction."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.stats: Dict[str, Dict[str, Any]] = {}

    def collect_from_sqlite(self, conn: sqlite3.Connection):
        """Collects statistics directly from a SQLite database connection."""
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]

            cursor.execute(f"PRAGMA table_info({table})")
            columns_info = cursor.fetchall()
            
            column_stats = {}
            for col in columns_info:
                col_name = col[1]
                col_type = col[2]

                # Sample column data for statistics
                try:
                    cursor.execute(f"SELECT COUNT(DISTINCT {col_name}), COUNT(*) - COUNT({col_name}) FROM {table}")
                    distinct_cnt, null_cnt = cursor.fetchone()
                    
                    null_fraction = null_cnt / max(row_count, 1)
                    
                    # Numeric column stats
                    mean_val, var_val, min_val, max_val = 0.0, 0.0, 0.0, 0.0
                    if "INT" in col_type.upper() or "FLOAT" in col_type.upper() or "NUMERIC" in col_type.upper() or "REAL" in col_type.upper():
                        cursor.execute(f"SELECT AVG({col_name}), MIN({col_name}), MAX({col_name}) FROM {table} WHERE {col_name} IS NOT NULL")
                        avg_r, min_r, max_r = cursor.fetchone()
                        mean_val = float(avg_r) if avg_r is not None else 0.0
                        min_val = float(min_r) if min_r is not None else 0.0
                        max_val = float(max_r) if max_r is not None else 0.0

                    column_stats[col_name] = {
                        "distinct_values": distinct_cnt,
                        "null_fraction": null_fraction,
                        "mean": mean_val,
                        "variance": var_val,
                        "minimum": min_val,
                        "maximum": max_val
                    }
                except Exception:
                    column_stats[col_name] = {
                        "distinct_values": 1,
                        "null_fraction": 0.0,
                        "mean": 0.0,
                        "variance": 0.0,
                        "minimum": 0.0,
                        "maximum": 0.0
                    }

            # Indexes info
            cursor.execute(f"PRAGMA index_list({table})")
            indexes = [idx[1] for idx in cursor.fetchall()]

            self.stats[table] = {
                "row_count": row_count,
                "num_columns": len(columns_info),
                "num_indexes": len(indexes),
                "columns": column_stats,
                "indexes": indexes
            }

    def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """Returns statistics dictionary for a table."""
        return self.stats.get(table_name, {
            "row_count": 1000,
            "num_columns": 5,
            "num_indexes": 1,
            "columns": {},
            "indexes": []
        })

    def get_column_stats(self, table_name: str, col_name: str) -> Dict[str, Any]:
        """Returns column-level statistics."""
        t_stats = self.get_table_stats(table_name)
        return t_stats.get("columns", {}).get(col_name, {
            "distinct_values": 10,
            "null_fraction": 0.0,
            "mean": 0.0,
            "variance": 0.0,
            "minimum": 0.0,
            "maximum": 100.0
        })
