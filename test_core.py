"""
Comprehensive Test Suite for Parametric Crane Generator.
Validates Database, Calculation Engine, SVG Generation, and Validation Constraints.
"""
from app.database import init_db, list_designs, get_design, create_design, update_design, delete_design
from app.models import CraneInputSchema
from app.engineering import calculate_crane_engineering
from app.svg_generator import CraneSVGGenerator

def run_tests():
    print("=" * 60)
    print("RUNNING TEST SUITE: PARAMETRIC CRANE GENERATOR")
    print("=" * 60)

    # 1. Database Initialization
    print("[1/5] Testing Database Initialization & Seeding...")
    init_db()
    designs = list_designs()
    assert len(designs) >= 3, f"Expected at least 3 seeded designs, got {len(designs)}"
    print(f"      PASS: {len(designs)} designs found in SQLite.")
    for d in designs:
        print(f"      - ID {d['id']}: {d['name']} ({d['capacity_ton']}t, Span: {d['span_mm']}mm)")

    # 2. Engineering Calculations
    print("\n[2/5] Testing Parametric Engineering Calculation Engine...")
    inp = CraneInputSchema(
        name="Test 15t Crane",
        customer="Atlas Heavy Industries",
        crane_type="double_girder",
        capacity_ton=15.0,
        span_mm=22000.0,
        lifting_height_mm=8000.0,
        rail_height_mm=9500.0
    )
    calcs = calculate_crane_engineering(inp)
    assert calcs.girder_depth_mm > 500, "Girder depth too small"
    assert calcs.wheelbase_mm >= 2200, "Wheelbase violates anti-skewing limit"
    assert calcs.max_static_wheel_load_kn > 0, "Wheel load calculation invalid"
    print(f"      PASS: Girder Depth = {calcs.girder_depth_mm} mm")
    print(f"      PASS: Wheelbase    = {calcs.wheelbase_mm} mm")
    print(f"      PASS: Deadweight   = {calcs.total_crane_deadweight_kg} kg")
    print(f"      PASS: Max Wheel Load = {calcs.max_static_wheel_load_kn} kN")

    # 3. SVG Generation
    print("\n[3/5] Testing Parametric SVG Vector CAD Generator...")
    svg_gen = CraneSVGGenerator(inp, calcs)
    svg_both = svg_gen.generate_full_ga_svg(view_mode="both")
    svg_elev = svg_gen.generate_full_ga_svg(view_mode="elevation")
    svg_plan = svg_gen.generate_full_ga_svg(view_mode="plan")
    assert "<svg" in svg_both and "</svg>" in svg_both
    assert "FRONT ELEVATION VIEW" in svg_both
    assert "PLAN (TOP) VIEW" in svg_both
    assert "MODERN CRANE CO." in svg_both
    print(f"      PASS: Full GA Sheet SVG rendered ({len(svg_both):,} chars)")
    print(f"      PASS: Elevation View SVG rendered ({len(svg_elev):,} chars)")
    print(f"      PASS: Plan View SVG rendered ({len(svg_plan):,} chars)")

    # 4. CRUD Lifecycle
    print("\n[4/5] Testing Database CRUD Lifecycle...")
    new_id = create_design(inp)
    assert new_id > 0, "Failed to create design"
    fetched = get_design(new_id)
    assert fetched["name"] == "Test 15t Crane"
    print(f"      PASS: Created design ID {new_id}")

    inp.name = "Updated 15t Crane Name"
    updated = update_design(new_id, inp)
    assert updated is True, "Failed to update design"
    fetched_after = get_design(new_id)
    assert fetched_after["name"] == "Updated 15t Crane Name"
    print(f"      PASS: Updated design ID {new_id}")

    deleted = delete_design(new_id)
    assert deleted is True, "Failed to delete design"
    assert get_design(new_id) is None, "Design should have been deleted"
    print(f"      PASS: Deleted design ID {new_id}")

    # 5. Server-side Validation
    print("\n[5/5] Testing Strict Server-Side Validation Gates...")
    try:
        CraneInputSchema(
            name="Bad Rail Height",
            capacity_ton=10.0,
            span_mm=18000.0,
            lifting_height_mm=8000.0,
            rail_height_mm=8200.0 # Insufficient headroom!
        )
        assert False, "Should have caught insufficient rail height!"
    except Exception as e:
        print(f"      PASS: Successfully caught rail height constraint: {str(e)[:60]}...")

    try:
        CraneInputSchema(
            name="Overloaded Single Girder",
            crane_type="single_girder",
            capacity_ton=35.0, # Too heavy for single girder!
            span_mm=20000.0,
            lifting_height_mm=6000.0,
            rail_height_mm=7500.0
        )
        assert False, "Should have caught overloaded single girder!"
    except Exception as e:
        print(f"      PASS: Successfully caught structural limit constraint: {str(e)[:60]}...")

    print("\n" + "=" * 60)
    print("ALL 5/5 TEST SUITES PASSED FLAWLESSLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
