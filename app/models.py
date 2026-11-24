"""
Pydantic Models and Schemas with Strict Server-Side Validation.
Defines input payloads, engineering constraints, and response structures.
"""
from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator


class CraneInputSchema(BaseModel):
    name: str = Field(
        default="Standard EOT Crane Design",
        min_length=2,
        max_length=100,
        description="Design name or reference identifier"
    )
    customer: Optional[str] = Field(
        default="Industrial Client",
        max_length=100,
        description="Client name or workshop location"
    )
    crane_type: Literal["single_girder", "double_girder"] = Field(
        default="single_girder",
        description="Type of bridge girder system"
    )
    capacity_ton: float = Field(
        default=10.0,
        ge=1.0,
        le=50.0,
        description="Safe Working Load (SWL) capacity in metric tons (1.0 - 50.0 t)"
    )
    span_mm: float = Field(
        default=20000.0,
        ge=6000.0,
        le=35000.0,
        description="Rail-to-rail center distance / span in millimeters (6,000 - 35,000 mm)"
    )
    lifting_height_mm: float = Field(
        default=7500.0,
        ge=3000.0,
        le=24000.0,
        description="Effective hook vertical travel / lifting height (3,000 - 24,000 mm)"
    )
    rail_height_mm: float = Field(
        default=8500.0,
        ge=3500.0,
        le=28000.0,
        description="Top of runway rail elevation from finished floor level (3,500 - 28,000 mm)"
    )
    building_clearance_left_mm: float = Field(
        default=300.0,
        ge=150.0,
        le=2000.0,
        description="Lateral safety clearance between crane end and left column/wall (min 150 mm)"
    )
    building_clearance_right_mm: float = Field(
        default=300.0,
        ge=150.0,
        le=2000.0,
        description="Lateral safety clearance between crane end and right column/wall (min 150 mm)"
    )
    roof_clearance_mm: float = Field(
        default=300.0,
        ge=150.0,
        le=2000.0,
        description="Vertical safety clearance between crane top and roof truss/obstruction (min 150 mm)"
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Additional technical notes or customer requirements"
    )

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Design name cannot be blank or whitespace only.")
        return cleaned

    @model_validator(mode="after")
    def validate_engineering_constraints(self):
        # 1. Rail height must be sufficient for required hook lifting height
        if self.rail_height_mm < (self.lifting_height_mm + 400.0):
            raise ValueError(
                f"Rail height ({self.rail_height_mm:,.0f} mm) is too low for the requested lifting height "
                f"({self.lifting_height_mm:,.0f} mm). Minimum rail height must be at least "
                f"{self.lifting_height_mm + 400.0:,.0f} mm to accommodate hoist headroom."
            )

        # 2. Heavy capacities (> 20t) generally require double girder for structural stability
        if self.capacity_ton > 25.0 and self.crane_type == "single_girder":
            raise ValueError(
                f"Single girder crane configuration is not recommended for heavy loads ({self.capacity_ton:.1f} t > 25 t). "
                f"Please select 'Double Girder' crane type for safety and torsional deflection limits."
            )

        # 3. High spans (> 28m) with heavy load should also use double girder
        if self.span_mm > 28000.0 and self.capacity_ton > 15.0 and self.crane_type == "single_girder":
            raise ValueError(
                f"For large span ({self.span_mm / 1000:.1f} m) and capacity ({self.capacity_ton:.1f} t), "
                f"single girder exhibits excessive lateral deflection. Please select Double Girder."
            )

        return self


class CraneCalculations(BaseModel):
    """Derived engineering dimensions, estimated weights, and wheel loads."""
    # Primary structural dimensions (in mm)
    girder_depth_mm: float
    girder_width_mm: float
    wheelbase_mm: float
    end_carriage_length_mm: float
    overall_width_mm: float
    total_crane_height_mm: float
    hook_approach_left_mm: float
    hook_approach_right_mm: float
    trolley_travel_mm: float
    hoist_headroom_mm: float

    # Engineering estimations
    girder_estimated_weight_kg: float
    hoist_trolley_weight_kg: float
    end_carriages_weight_kg: float
    total_crane_deadweight_kg: float
    total_lifted_load_kg: float

    # Wheel load estimations (in kN)
    number_of_wheels: int
    max_static_wheel_load_kn: float
    min_static_wheel_load_kn: float

    # Compliance and standards reference
    structural_standard: str
    deflection_limit_ratio: str
    notes_and_assumptions: list[str]


class CraneDesignResponse(BaseModel):
    """Full design object with database record and derived calculations."""
    id: Optional[int] = None
    input: CraneInputSchema
    calculations: CraneCalculations
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CraneDesignSummary(BaseModel):
    """Compact summary for list view."""
    id: int
    name: str
    customer: Optional[str]
    crane_type: str
    capacity_ton: float
    span_mm: float
    lifting_height_mm: float
    created_at: str
    updated_at: str
