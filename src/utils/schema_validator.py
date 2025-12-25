"""
Database Schema Validator for OnSide
Following Semantic Seed BDD/TDD Coding Standards V2.0

This module provides utilities to validate database schema against expected structure,
helping to identify missing columns or tables early in the development process.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.sql import text
import json
import os
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


class SchemaValidator:
    """
    Database schema validator that checks the actual database schema
    against expected structure to identify issues early.
    
    This helps prevent runtime errors caused by missing columns or tables.
    """
    
    def __init__(self, engine: AsyncEngine):
        """Initialize the schema validator with a database engine."""
        self.engine = engine
        self.validation_results: Dict[str, Dict[str, Any]] = {}
        logger.info("Schema validator initialized")
    
    async def get_tables(self) -> List[str]:
        """Get all table names from the database."""
        async with self.engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result.fetchall()]
            return tables
    
    async def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get all column details for a table."""
        async with self.engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = :table_name
            """), {"table_name": table_name})
            
            columns = []
            for row in result.fetchall():
                columns.append({
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2] == "YES",
                    "default": row[3]
                })
            
            return columns
    
    async def validate_table_columns(
        self, 
        table_name: str, 
        expected_columns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate that a table has all expected columns.
        
        Args:
            table_name: Name of the table to validate
            expected_columns: List of expected column definitions with name, type, nullable, and default
            
        Returns:
            Dictionary with validation results including missing or mismatched columns
        """
        actual_columns = await self.get_columns(table_name)
        actual_column_names = {col["name"] for col in actual_columns}
        expected_column_names = {col["name"] for col in expected_columns}
        
        missing_columns = expected_column_names - actual_column_names
        extra_columns = actual_column_names - expected_column_names
        
        # Check for type mismatches in columns that exist in both
        type_mismatches = []
        for exp_col in expected_columns:
            if exp_col["name"] in actual_column_names:
                act_col = next(col for col in actual_columns if col["name"] == exp_col["name"])
                
                # Check if types are compatible (simplified check)
                if not self._types_compatible(exp_col["type"], act_col["type"]):
                    type_mismatches.append({
                        "column": exp_col["name"],
                        "expected_type": exp_col["type"],
                        "actual_type": act_col["type"]
                    })
        
        result = {
            "table_name": table_name,
            "valid": len(missing_columns) == 0 and len(type_mismatches) == 0,
            "missing_columns": list(missing_columns),
            "type_mismatches": type_mismatches,
            "extra_columns": list(extra_columns)
        }
        
        self.validation_results[table_name] = result
        return result
    
    def _types_compatible(self, expected_type: str, actual_type: str) -> bool:
        """
        Check if two column types are compatible.
        
        This is a simplified check that normalizes common type variations.
        """
        # Normalize types for comparison
        expected_type = expected_type.lower()
        actual_type = actual_type.lower()
        
        # Direct match
        if expected_type == actual_type:
            return True
        
        # Common compatible types
        compatible_types = {
            "integer": ["int", "int4", "integer"],
            "bigint": ["int8", "bigint"],
            "text": ["text", "varchar", "character varying"],
            "boolean": ["bool", "boolean"],
            "timestamp": ["timestamp", "timestamp without time zone", "timestamp with time zone", 
                          "timestamptz"],
            "float": ["float", "float8", "double precision", "real"]
        }
        
        for type_group, variations in compatible_types.items():
            if expected_type in variations and actual_type in variations:
                return True
        
        return False
    
    async def validate_schema(
        self, 
        expected_schema: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Validate the entire database schema against expected structure.
        
        Args:
            expected_schema: Dictionary mapping table names to lists of expected columns
            
        Returns:
            Dictionary with validation results for all tables
        """
        results = {}
        for table_name, expected_columns in expected_schema.items():
            try:
                table_result = await self.validate_table_columns(table_name, expected_columns)
                results[table_name] = table_result
            except Exception as e:
                results[table_name] = {
                    "table_name": table_name,
                    "valid": False,
                    "error": str(e)
                }
                logger.error(f"Error validating table {table_name}: {str(e)}")
        
        return results
    
    async def generate_migration_sql(self) -> str:
        """
        Generate SQL statements to fix schema issues identified in the last validation.
        
        Returns:
            SQL script with ALTER TABLE statements to add missing columns
        """
        if not self.validation_results:
            return "-- No validation results available. Run validate_schema first."
        
        sql_lines = ["-- Generated schema migration script", 
                    f"-- Generated at: {datetime.now().isoformat()}", ""]
        
        for table_name, result in self.validation_results.items():
            if not result.get("valid", True):
                # Add missing columns
                for column in result.get("missing_columns", []):
                    # Since we don't have the full column details, use a placeholder
                    sql_lines.append(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column} TEXT;")
                    sql_lines.append(f"-- TODO: Update the column type and constraints for {column}")
                    sql_lines.append("")
                
                # Fix type mismatches
                for mismatch in result.get("type_mismatches", []):
                    column = mismatch["column"]
                    expected_type = mismatch["expected_type"]
                    sql_lines.append(f"ALTER TABLE {table_name} ALTER COLUMN {column} TYPE {expected_type};")
                    sql_lines.append("")
        
        return "\n".join(sql_lines)
    
    async def export_current_schema(self, output_file: str) -> None:
        """
        Export the current database schema to a JSON file.
        
        Args:
            output_file: Path to the output JSON file
        """
        tables = await self.get_tables()
        schema = {}
        
        for table in tables:
            columns = await self.get_columns(table)
            schema[table] = columns
        
        with open(output_file, 'w') as f:
            json.dump(schema, f, indent=2)
        
        logger.info(f"Schema exported to {output_file}")


# Constants for common expected schemas
LINKS_TABLE_SCHEMA = [
    {"name": "id", "type": "integer", "nullable": False, "default": "nextval('links_id_seq'::regclass)"},
    {"name": "url", "type": "text", "nullable": False, "default": None},
    {"name": "domain_id", "type": "integer", "nullable": False, "default": None},
    {"name": "created_at", "type": "timestamp with time zone", "nullable": True, "default": "CURRENT_TIMESTAMP"}
]

REPORTS_TABLE_SCHEMA = [
    {"name": "id", "type": "integer", "nullable": False, "default": "nextval('reports_id_seq'::regclass)"},
    {"name": "user_id", "type": "integer", "nullable": False, "default": None},
    {"name": "type", "type": "text", "nullable": False, "default": None},
    {"name": "status", "type": "text", "nullable": False, "default": "'QUEUED'::text"},
    {"name": "created_at", "type": "timestamp with time zone", "nullable": True, "default": "CURRENT_TIMESTAMP"},
    {"name": "updated_at", "type": "timestamp with time zone", "nullable": True, "default": "CURRENT_TIMESTAMP"},
    {"name": "file_path", "type": "text", "nullable": True, "default": None}
]

# Full schema definition
EXPECTED_SCHEMA = {
    "links": LINKS_TABLE_SCHEMA,
    "reports": REPORTS_TABLE_SCHEMA,
    # Add more tables as needed
}
