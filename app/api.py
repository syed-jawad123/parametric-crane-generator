"""
FastAPI REST API Routes.
Exposes calculation engine, database persistence, validation errors, and SVG exports.
"""
from fastapi import APIRouter, HTTPException, Response, Query
from typing import List, Optional
from app.models import (
    CraneInputSchema,
    CraneCalculations,
    CraneDesignResponse,
    CraneDesignSummary
)
from app.engineering import calculate_crane_engineering
from app.svg_generator import CraneSVGGenerator
from app import database

router = APIRouter(prefix="/api", tags=["crane-generator"])


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "Parametric Crane Generator API", "version": "1.0.0"}


@router.post("/calculate")
def calculate_crane(inputs: CraneInputSchema, view: str = Query("both", regex="^(both|elevation|plan)$")):
    """
    Validates input parameters and computes derived engineering dimensions,
    clearances, wheel loads, and parametric 2D SVG vector drawing.
    """
    calcs = calculate_crane_engineering(inputs)
    svg_gen = CraneSVGGenerator(inputs, calcs)
    svg_markup = svg_gen.generate_full_ga_svg(view_mode=view)

    return {
        "inputs": inputs,
        "calculations": calcs,
        "svg": svg_markup
    }


@router.get("/designs", response_model=List[CraneDesignSummary])
def list_saved_designs():
    """Returns all saved crane designs from SQLite ordered by last updated date."""
    rows = database.list_designs()
    return [
        CraneDesignSummary(
            id=r["id"],
            name=r["name"],
            customer=r["customer"],
            crane_type=r["crane_type"],
            capacity_ton=r["capacity_ton"],
            span_mm=r["span_mm"],
            lifting_height_mm=r["lifting_height_mm"],
            created_at=r["created_at"],
            updated_at=r["updated_at"]
        ) for r in rows
    ]


@router.post("/designs", status_code=201)
def create_new_design(inputs: CraneInputSchema):
    """Validates inputs server-side and stores a new crane design in SQLite."""
    design_id = database.create_design(inputs)
    calcs = calculate_crane_engineering(inputs)
    svg_gen = CraneSVGGenerator(inputs, calcs)
    svg_markup = svg_gen.generate_full_ga_svg()

    row = database.get_design(design_id)
    return {
        "id": design_id,
        "message": "Design successfully saved.",
        "input": inputs,
        "calculations": calcs,
        "svg": svg_markup,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }


@router.get("/designs/{design_id}")
def get_saved_design(design_id: int):
    """Retrieves an existing saved design by ID with full calculations and SVG."""
    row = database.get_design(design_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Crane design with ID {design_id} not found.")

    inputs = CraneInputSchema(
        name=row["name"],
        customer=row["customer"],
        crane_type=row["crane_type"],
        capacity_ton=row["capacity_ton"],
        span_mm=row["span_mm"],
        lifting_height_mm=row["lifting_height_mm"],
        rail_height_mm=row["rail_height_mm"],
        building_clearance_left_mm=row["building_clearance_left_mm"],
        building_clearance_right_mm=row["building_clearance_right_mm"],
        roof_clearance_mm=row["roof_clearance_mm"],
        notes=row["notes"]
    )
    calcs = calculate_crane_engineering(inputs)
    svg_gen = CraneSVGGenerator(inputs, calcs)
    svg_markup = svg_gen.generate_full_ga_svg()

    return {
        "id": row["id"],
        "input": inputs,
        "calculations": calcs,
        "svg": svg_markup,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }


@router.put("/designs/{design_id}")
def update_saved_design(design_id: int, inputs: CraneInputSchema):
    """Updates an existing design in the database with strict server validation."""
    existing = database.get_design(design_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Crane design with ID {design_id} not found.")

    database.update_design(design_id, inputs)
    calcs = calculate_crane_engineering(inputs)
    svg_gen = CraneSVGGenerator(inputs, calcs)
    svg_markup = svg_gen.generate_full_ga_svg()

    row = database.get_design(design_id)
    return {
        "id": design_id,
        "message": "Design successfully updated.",
        "input": inputs,
        "calculations": calcs,
        "svg": svg_markup,
        "updated_at": row["updated_at"]
    }


@router.delete("/designs/{design_id}")
def delete_saved_design(design_id: int):
    """Deletes a design from the SQLite database."""
    try:
        deleted = database.delete_design(design_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Crane design with ID {design_id} not found.")
        return {"status": "success", "message": f"Design {design_id} has been deleted."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/designs/{design_id}/export/svg")
def export_design_svg(design_id: int, view: str = Query("both", regex="^(both|elevation|plan)$")):
    """Exports the technical drawing as a standalone downloadable SVG CAD vector file."""
    row = database.get_design(design_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Crane design with ID {design_id} not found.")

    inputs = CraneInputSchema(
        name=row["name"],
        customer=row["customer"],
        crane_type=row["crane_type"],
        capacity_ton=row["capacity_ton"],
        span_mm=row["span_mm"],
        lifting_height_mm=row["lifting_height_mm"],
        rail_height_mm=row["rail_height_mm"],
        building_clearance_left_mm=row["building_clearance_left_mm"],
        building_clearance_right_mm=row["building_clearance_right_mm"],
        roof_clearance_mm=row["roof_clearance_mm"],
        notes=row["notes"]
    )
    calcs = calculate_crane_engineering(inputs)
    svg_gen = CraneSVGGenerator(inputs, calcs)
    svg_content = svg_gen.generate_full_ga_svg(view_mode=view)

    safe_name = "".join(c for c in inputs.name if c.isalnum() or c in ("-", "_")).rstrip()
    filename = f"ModernCrane_{safe_name}_{design_id}.svg"

    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
