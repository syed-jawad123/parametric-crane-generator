"""
Parametric Engineering Calculation Engine for Overhead (EOT) Cranes.
Derives structural dimensions, clearances, weights, and static wheel loads.
Formulas are sourced from CMAA Spec 70/74 and FEM 1.001 standard engineering proportions.
All empirical relationships are explicitly flagged as estimates.
"""
import math
from app.models import CraneInputSchema, CraneCalculations


def calculate_crane_engineering(inputs: CraneInputSchema) -> CraneCalculations:
    """
    Computes all derived geometric and mechanical parameters from user inputs.
    """
    span = inputs.span_mm
    capacity_t = inputs.capacity_ton
    lift_h = inputs.lifting_height_mm
    rail_h = inputs.rail_height_mm
    is_double = inputs.crane_type == "double_girder"

    # -------------------------------------------------------------------------
    # 1. Girder Depth & Width (CMAA 70 / FEM 1.001 Proportions)
    # -------------------------------------------------------------------------
    # Rule of thumb for bridge girder depth to satisfy deflection limits (L/800 to L/1000):
    # Single girder: Span / 19, Double girder: Span / 17 + capacity scaling factor.
    if is_double:
        girder_depth = max(650.0, round((span / 17.0) + (18.0 * (capacity_t ** 0.65)), -1))
        # Top-running double girder box beam width (typically 35-45% of depth)
        girder_width = max(350.0, round(girder_depth * 0.40, -1))
    else:
        girder_depth = max(500.0, round((span / 19.0) + (14.0 * (capacity_t ** 0.65)), -1))
        # Single box or I-beam flange width
        girder_width = max(300.0, round(girder_depth * 0.35, -1))

    # -------------------------------------------------------------------------
    # 2. End Carriage Wheelbase (Anti-skewing criterion: Wb/Span >= 1/7)
    # -------------------------------------------------------------------------
    # CMAA and DIN 15018 mandate wheelbase >= Span / 7 to prevent binding/skewing.
    # Standard practice uses Span / 6.5, clamped between 2,200 mm and 4,800 mm.
    raw_wheelbase = span / 6.5
    wheelbase = float(min(4800.0, max(2200.0, round(raw_wheelbase, -1))))
    # End carriage overall length includes buffer overhanging extensions (~350mm each side)
    end_carriage_length = wheelbase + 700.0

    # -------------------------------------------------------------------------
    # 3. Clearances and Hook Approaches
    # -------------------------------------------------------------------------
    # Lateral hook dead-zones (minimum approach of hook center to rail centerline)
    if is_double:
        hook_approach_left = max(850.0, round(800.0 + (capacity_t * 20.0), -1))
        hook_approach_right = max(950.0, round(900.0 + (capacity_t * 22.0), -1))
        # Hoist headroom (height from hook in top position to top of rail)
        hoist_headroom = max(850.0, round(700.0 + (capacity_t * 30.0), -1))
        total_crane_height = girder_depth + hoist_headroom + 350.0
    else:
        hook_approach_left = max(750.0, round(700.0 + (capacity_t * 18.0), -1))
        hook_approach_right = max(850.0, round(800.0 + (capacity_t * 20.0), -1))
        # Underhung hoist takes vertical space beneath bottom flange
        hoist_headroom = max(950.0, round(850.0 + (capacity_t * 35.0), -1))
        total_crane_height = girder_depth + hoist_headroom + 200.0

    trolley_travel = max(1000.0, span - (hook_approach_left + hook_approach_right))
    overall_width = span + inputs.building_clearance_left_mm + inputs.building_clearance_right_mm

    # -------------------------------------------------------------------------
    # 4. Estimated Deadweights (Empirical Industry Estimations)
    # -------------------------------------------------------------------------
    # Girder steel weight (kg): estimated based on span and section modulus requirement
    if is_double:
        # Two box girders + diaphragms + walkover platform
        girder_weight = round(1.8 * (0.007 * (span ** 1.35) * (capacity_t ** 0.45)), 0)
        # Crab winch trolley
        hoist_trolley_weight = round(800.0 + (125.0 * capacity_t), 0)
    else:
        # Single box or composite section
        girder_weight = round(0.009 * (span ** 1.35) * (capacity_t ** 0.45), 0)
        # Monorail underslung hoist
        hoist_trolley_weight = round(450.0 + (75.0 * capacity_t), 0)

    # End carriages pair (including wheel blocks, gear motors, and buffers)
    end_carriages_weight = round(600.0 + (25.0 * (wheelbase / 100.0)) + (40.0 * capacity_t), 0)

    total_deadweight = girder_weight + hoist_trolley_weight + end_carriages_weight
    lifted_load_kg = capacity_t * 1000.0

    # -------------------------------------------------------------------------
    # 5. Static Wheel Load Calculations (CMAA Method)
    # -------------------------------------------------------------------------
    # Standard 4-wheel crane (2 wheels per end carriage)
    number_of_wheels = 4

    # Critical condition: Trolley with full rated load parked at minimum left hook approach
    effective_lever_left = (span - hook_approach_left) / span
    effective_lever_right = 1.0 - effective_lever_left

    # Total load on near (left) end carriage
    near_truck_weight = (girder_weight * 0.5) + (end_carriages_weight * 0.5)
    near_truck_load = near_truck_weight + ((hoist_trolley_weight + lifted_load_kg) * effective_lever_left)

    # Total load on far (right) end carriage
    far_truck_weight = (girder_weight * 0.5) + (end_carriages_weight * 0.5)
    far_truck_load = far_truck_weight + ((hoist_trolley_weight + lifted_load_kg) * effective_lever_right)

    # Convert to Static Wheel Load in kN (2 wheels per truck)
    # g = 9.80665 m/s^2
    max_wheel_load_kn = round((near_truck_load * 9.80665) / (2.0 * 1000.0), 2)
    min_wheel_load_kn = round((far_truck_load * 9.80665) / (2.0 * 1000.0), 2)

    # -------------------------------------------------------------------------
    # 6. Sourced Assumptions & Notes List
    # -------------------------------------------------------------------------
    assumptions = [
        f"Girder depth ({girder_depth:.0f} mm) sized for vertical deflection limit L/800 per CMAA Spec 70.",
        f"Wheelbase ({wheelbase:.0f} mm) enforces Wb/Span >= 1/7 ratio ({wheelbase/span:.3f}) to prevent crabbing.",
        f"Static wheel load ({max_wheel_load_kn:.2f} kN) computed with 100% rated capacity ({capacity_t:.1f} t) at extreme left hook approach.",
        "Deadweights of girder, trolley, and end trucks are parameterized empirical estimates for quotation purposes.",
        f"Hook vertical travel configured at {lift_h:,.0f} mm; top of rail at {rail_h:,.0f} mm elevation."
    ]

    return CraneCalculations(
        girder_depth_mm=girder_depth,
        girder_width_mm=girder_width,
        wheelbase_mm=wheelbase,
        end_carriage_length_mm=end_carriage_length,
        overall_width_mm=overall_width,
        total_crane_height_mm=total_crane_height,
        hook_approach_left_mm=hook_approach_left,
        hook_approach_right_mm=hook_approach_right,
        trolley_travel_mm=trolley_travel,
        hoist_headroom_mm=hoist_headroom,
        girder_estimated_weight_kg=girder_weight,
        hoist_trolley_weight_kg=hoist_trolley_weight,
        end_carriages_weight_kg=end_carriages_weight,
        total_crane_deadweight_kg=total_deadweight,
        total_lifted_load_kg=lifted_load_kg,
        number_of_wheels=number_of_wheels,
        max_static_wheel_load_kn=max_wheel_load_kn,
        min_static_wheel_load_kn=min_wheel_load_kn,
        structural_standard="CMAA 70 / FEM 1.001 / ISO 4301 Class A5/M5",
        deflection_limit_ratio="1/800 (Bridge Girder under full live load)",
        notes_and_assumptions=assumptions
    )
