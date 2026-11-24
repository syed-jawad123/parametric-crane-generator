"""
SQLite Database Layer for Crane Design Persistence.
Implements full CRUD lifecycle with transaction safety and seed presets.
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from app.models import CraneInputSchema

DB_PATH = Path("crane_designs.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes SQLite schema and seeds standard engineering presets."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crane_designs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                customer TEXT,
                crane_type TEXT NOT NULL,
                capacity_ton REAL NOT NULL,
                span_mm REAL NOT NULL,
                lifting_height_mm REAL NOT NULL,
                rail_height_mm REAL NOT NULL,
                building_clearance_left_mm REAL NOT NULL DEFAULT 300.0,
                building_clearance_right_mm REAL NOT NULL DEFAULT 300.0,
                roof_clearance_mm REAL NOT NULL DEFAULT 300.0,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        conn.commit()

        # Seed initial sample designs if database is newly initialized
        cursor.execute("SELECT COUNT(*) FROM crane_designs")
        count = cursor.fetchone()[0]
        if count == 0:
            seed_initial_presets(cursor)
            conn.commit()


def seed_initial_presets(cursor: sqlite3.Cursor):
    now = datetime.utcnow().isoformat()
    presets = [
        (
            "Standard 10t Workshop EOT Crane",
            "General Fabrication Bay",
            "single_girder",
            10.0,
            20000.0,
            7500.0,
            8500.0,
            300.0,
            300.0,
            300.0,
            "Standard Class A5 workshop bridge crane with wire rope hoist.",
            now,
            now
        ),
        (
            "Heavy 25t Heavy Assembly Crane",
            "Turbine & Heavy Equipment Hall",
            "double_girder",
            25.0,
            25000.0,
            9000.0,
            10500.0,
            350.0,
            350.0,
            400.0,
            "Double box girder with top-running crab trolley and auxiliary maintenance walkway.",
            now,
            now
        ),
        (
            "Compact 5t Warehouse Crane",
            "Raw Materials Staging Area",
            "single_girder",
            5.0,
            14000.0,
            6000.0,
            7000.0,
            250.0,
            250.0,
            250.0,
            "Cost-effective monorail bridge crane for agile material handling.",
            now,
            now
        )
    ]
    cursor.executemany("""
        INSERT INTO crane_designs (
            name, customer, crane_type, capacity_ton, span_mm,
            lifting_height_mm, rail_height_mm, building_clearance_left_mm,
            building_clearance_right_mm, roof_clearance_mm, notes,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, presets)


def create_design(data: CraneInputSchema) -> int:
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO crane_designs (
                name, customer, crane_type, capacity_ton, span_mm,
                lifting_height_mm, rail_height_mm, building_clearance_left_mm,
                building_clearance_right_mm, roof_clearance_mm, notes,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.name,
            data.customer,
            data.crane_type,
            data.capacity_ton,
            data.span_mm,
            data.lifting_height_mm,
            data.rail_height_mm,
            data.building_clearance_left_mm,
            data.building_clearance_right_mm,
            data.roof_clearance_mm,
            data.notes,
            now,
            now
        ))
        conn.commit()
        return cursor.lastrowid


def get_design(design_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM crane_designs WHERE id = ?", (design_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return dict(row)


def list_designs() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, customer, crane_type, capacity_ton, span_mm,
                   lifting_height_mm, created_at, updated_at
            FROM crane_designs
            ORDER BY updated_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]


def update_design(design_id: int, data: CraneInputSchema) -> bool:
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE crane_designs
            SET name = ?, customer = ?, crane_type = ?, capacity_ton = ?,
                span_mm = ?, lifting_height_mm = ?, rail_height_mm = ?,
                building_clearance_left_mm = ?, building_clearance_right_mm = ?,
                roof_clearance_mm = ?, notes = ?, updated_at = ?
            WHERE id = ?
        """, (
            data.name,
            data.customer,
            data.crane_type,
            data.capacity_ton,
            data.span_mm,
            data.lifting_height_mm,
            data.rail_height_mm,
            data.building_clearance_left_mm,
            data.building_clearance_right_mm,
            data.roof_clearance_mm,
            data.notes,
            now,
            design_id
        ))
        conn.commit()
        return cursor.rowcount > 0


def delete_design(design_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM crane_designs")
        count = cursor.fetchone()[0]
        # Prevent deleting the last design so database always has something
        if count <= 1:
            raise ValueError("Cannot delete the last remaining design template.")

        cursor.execute("DELETE FROM crane_designs WHERE id = ?", (design_id,))
        conn.commit()
        return cursor.rowcount > 0
