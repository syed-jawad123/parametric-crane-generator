"""
Parametric 2D SVG CAD Drawing Engine for Overhead (EOT) Cranes.
Generates dimensioned technical General Arrangement (GA) drawings
including Front Elevation View, Plan (Top) View, and CAD Title Block.
Conforms to technical drawing standards (ISO 128 / ASME Y14).
"""
from typing import Dict, Any
from app.models import CraneInputSchema, CraneCalculations


class CraneSVGGenerator:
    """Generates technical vector SVG CAD drawings with parametric dimensions."""

    def __init__(self, inputs: CraneInputSchema, calcs: CraneCalculations):
        self.inputs = inputs
        self.calcs = calcs

    def generate_full_ga_svg(self, view_mode: str = "both") -> str:
        """
        view_mode: 'elevation', 'plan', or 'both'
        """
        # Canvas dimensions for high-resolution technical sheet (A3/A2 CAD proportion)
        width = 1600
        height = 1100 if view_mode == "both" else 750
        viewbox = f"0 0 {width} {height}"

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" width="100%" height="100%" '
            f'class="cad-svg-canvas" style="background-color: #0b132b; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;">',
            self._render_defs(),
            self._render_grid(width, height),
            self._render_border(width, height)
        ]

        if view_mode == "both":
            # Stacked layout: Elevation on top, Plan on bottom
            svg_parts.append(self._render_elevation_view(offset_x=120, offset_y=80, scale_w=1360, scale_h=460))
            svg_parts.append(self._render_plan_view(offset_x=120, offset_y=580, scale_w=1360, scale_h=340))
        elif view_mode == "elevation":
            svg_parts.append(self._render_elevation_view(offset_x=120, offset_y=90, scale_w=1360, scale_h=520))
        else: # plan
            svg_parts.append(self._render_plan_view(offset_x=120, offset_y=120, scale_w=1360, scale_h=480))

        # Add Title Block and Technical Data Table
        svg_parts.append(self._render_title_block(width, height))
        svg_parts.append(self._render_technical_table(x=width - 340, y=80))

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    def _render_defs(self) -> str:
        return """
        <defs>
            <!-- Dimension arrow markers -->
            <marker id="arrow-start" viewBox="0 0 10 10" refX="0" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 10 0 L 0 5 L 10 10 z" fill="#00f5d4" />
            </marker>
            <marker id="arrow-end" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#00f5d4" />
            </marker>
            <!-- Grid pattern -->
            <pattern id="cad-grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1c2541" stroke-width="0.7" />
            </pattern>
            <!-- Rail hatch pattern -->
            <pattern id="concrete-hatch" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M0 20 L20 0 M-5 5 L5 -5 M15 25 L25 15" stroke="#253252" stroke-width="0.8" />
            </pattern>
        </defs>
        """

    def _render_grid(self, width: int, height: int) -> str:
        return f'<rect width="{width}" height="{height}" fill="url(#cad-grid)" />'

    def _render_border(self, width: int, height: int) -> str:
        return f"""
        <!-- Sheet outer boundary & margin (ISO CAD Sheet) -->
        <rect x="15" y="15" width="{width - 30}" height="{height - 30}" fill="none" stroke="#3a506b" stroke-width="2" />
        <rect x="25" y="25" width="{width - 50}" height="{height - 50}" fill="none" stroke="#1c2541" stroke-width="1" />
        """

    def _render_elevation_view(self, offset_x: float, offset_y: float, scale_w: float, scale_h: float) -> str:
        """Draws the Front Elevation View."""
        span_val = self.inputs.span_mm
        is_double = self.inputs.crane_type == "double_girder"

        # Mapping physical coords into SVG coordinate frame
        span_px = scale_w * 0.70
        girder_x1 = offset_x + 90
        girder_x2 = girder_x1 + span_px
        center_x = (girder_x1 + girder_x2) / 2.0

        # Vertical reference levels
        rail_y = offset_y + 110
        girder_depth_px = min(65.0, max(35.0, (self.calcs.girder_depth_mm / 25.0)))
        girder_top_y = rail_y - girder_depth_px if is_double else rail_y - 20
        girder_bot_y = girder_top_y + girder_depth_px

        floor_y = offset_y + scale_h - 40
        hook_y = rail_y + min(scale_h - 190, max(120.0, (self.inputs.lifting_height_mm / 35.0)))

        svg = [f'<g id="elevation-view" class="cad-layer">']
        svg.append(f'<text x="{offset_x}" y="{offset_y + 15}" fill="#64dfdf" font-size="14" font-weight="bold">FRONT ELEVATION VIEW (CROSS-SECTION)</text>')

        # 1. Building Columns & Brackets (Corbels)
        col_width = 45
        # Left Column & Corbel
        svg.append(f'<rect x="{girder_x1 - col_width - 15}" y="{rail_y - 30}" width="{col_width}" height="{floor_y - (rail_y - 30)}" fill="url(#concrete-hatch)" stroke="#48cae4" stroke-width="1.5" />')
        svg.append(f'<path d="M {girder_x1 - 15} {rail_y} L {girder_x1 - 15} {rail_y + 50} L {girder_x1 - 40} {rail_y + 80} L {girder_x1 - 40} {rail_y} Z" fill="#1c2541" stroke="#48cae4" stroke-width="1.5" />')

        # Right Column & Corbel
        svg.append(f'<rect x="{girder_x2 + 15}" y="{rail_y - 30}" width="{col_width}" height="{floor_y - (rail_y - 30)}" fill="url(#concrete-hatch)" stroke="#48cae4" stroke-width="1.5" />')
        svg.append(f'<path d="M {girder_x2 + 15} {rail_y} L {girder_x2 + 15} {rail_y + 50} L {girder_x2 + 40} {rail_y + 80} L {girder_x2 + 40} {rail_y} Z" fill="#1c2541" stroke="#48cae4" stroke-width="1.5" />')

        # 2. Runway Rails (CR 80 / CR 100 rails on beams)
        svg.append(f'<rect x="{girder_x1 - 10}" y="{rail_y - 8}" width="20" height="8" fill="#ffd166" stroke="#ffd166" />')
        svg.append(f'<rect x="{girder_x2 - 10}" y="{rail_y - 8}" width="20" height="8" fill="#ffd166" stroke="#ffd166" />')

        # 3. End Carriages (Left & Right End Trucks)
        truck_w = 40
        truck_h = 32
        # Left End Truck
        svg.append(f'<rect x="{girder_x1 - (truck_w / 2)}" y="{rail_y - truck_h - 2}" width="{truck_w}" height="{truck_h}" rx="3" fill="#118ab2" stroke="#caf0f8" stroke-width="1.5" />')
        # Left Wheels
        svg.append(f'<circle cx="{girder_x1 - 12}" cy="{rail_y - 2}" r="7" fill="#073b4c" stroke="#ffd166" stroke-width="2" />')
        svg.append(f'<circle cx="{girder_x1 + 12}" cy="{rail_y - 2}" r="7" fill="#073b4c" stroke="#ffd166" stroke-width="2" />')

        # Right End Truck
        svg.append(f'<rect x="{girder_x2 - (truck_w / 2)}" y="{rail_y - truck_h - 2}" width="{truck_w}" height="{truck_h}" rx="3" fill="#118ab2" stroke="#caf0f8" stroke-width="1.5" />')
        # Right Wheels
        svg.append(f'<circle cx="{girder_x2 - 12}" cy="{rail_y - 2}" r="7" fill="#073b4c" stroke="#ffd166" stroke-width="2" />')
        svg.append(f'<circle cx="{girder_x2 + 12}" cy="{rail_y - 2}" r="7" fill="#073b4c" stroke="#ffd166" stroke-width="2" />')

        # 4. Bridge Girder(s)
        if is_double:
            # Double Box Girder (Two horizontal beams with top rails)
            g1_y = girder_top_y
            svg.append(f'<rect x="{girder_x1}" y="{g1_y}" width="{span_px}" height="{girder_depth_px}" rx="2" fill="#0f4c5c" stroke="#caf0f8" stroke-width="2" />')
            # Internal diaphragm lines / web stiffeners
            for step in range(1, 9):
                stiff_x = girder_x1 + (step * (span_px / 9.0))
                svg.append(f'<line x1="{stiff_x}" y1="{g1_y}" x2="{stiff_x}" y2="{g1_y + girder_depth_px}" stroke="#253252" stroke-width="1" stroke-dasharray="3,3" />')
            # Girder top rail
            svg.append(f'<line x1="{girder_x1 + 15}" y1="{g1_y - 2}" x2="{girder_x2 - 15}" y2="{g1_y - 2}" stroke="#ffd166" stroke-width="3" />')
        else:
            # Single Girder (Solid central box or rolled girder with hoist underhung)
            g1_y = girder_top_y
            svg.append(f'<rect x="{girder_x1}" y="{g1_y}" width="{span_px}" height="{girder_depth_px}" rx="2" fill="#0f4c5c" stroke="#caf0f8" stroke-width="2" />')
            # Stiffeners
            for step in range(1, 8):
                stiff_x = girder_x1 + (step * (span_px / 8.0))
                svg.append(f'<line x1="{stiff_x}" y1="{g1_y}" x2="{stiff_x}" y2="{g1_y + girder_depth_px}" stroke="#253252" stroke-width="1" stroke-dasharray="3,3" />')

        # 5. Hoist Crab / Trolley & Hook
        trolley_w = 64
        trolley_h = 42
        trolley_x = center_x - (trolley_w / 2.0)

        if is_double:
            trolley_y = girder_top_y - trolley_h + 4
            # Top-running crab trolley
            svg.append(f'<rect x="{trolley_x}" y="{trolley_y}" width="{trolley_w}" height="{trolley_h}" rx="3" fill="#e36414" stroke="#caf0f8" stroke-width="1.5" />')
            # Motor & rope drum details
            svg.append(f'<rect x="{trolley_x + 8}" y="{trolley_y + 8}" width="20" height="24" fill="#073b4c" stroke="#caf0f8" stroke-width="1" />')
            svg.append(f'<circle cx="{trolley_x + 44}" cy="{trolley_y + 20}" r="12" fill="#5c677d" stroke="#caf0f8" stroke-width="1" />')
            # Wire ropes descending
            svg.append(f'<line x1="{center_x - 5}" y1="{trolley_y + trolley_h}" x2="{center_x - 5}" y2="{hook_y}" stroke="#ffd166" stroke-width="1.5" stroke-dasharray="4,2" />')
            svg.append(f'<line x1="{center_x + 5}" y1="{trolley_y + trolley_h}" x2="{center_x + 5}" y2="{hook_y}" stroke="#ffd166" stroke-width="1.5" stroke-dasharray="4,2" />')
        else:
            # Underslung Monorail Hoist (suspended under bottom flange)
            trolley_y = girder_bot_y + 2
            svg.append(f'<rect x="{trolley_x}" y="{trolley_y}" width="{trolley_w}" height="{trolley_h}" rx="3" fill="#e36414" stroke="#caf0f8" stroke-width="1.5" />')
            # Motor
            svg.append(f'<rect x="{trolley_x + 6}" y="{trolley_y + 8}" width="22" height="22" fill="#073b4c" stroke="#caf0f8" stroke-width="1" />')
            # Wire ropes
            svg.append(f'<line x1="{center_x - 4}" y1="{trolley_y + trolley_h}" x2="{center_x - 4}" y2="{hook_y}" stroke="#ffd166" stroke-width="1.5" stroke-dasharray="4,2" />')
            svg.append(f'<line x1="{center_x + 4}" y1="{trolley_y + trolley_h}" x2="{center_x + 4}" y2="{hook_y}" stroke="#ffd166" stroke-width="1.5" stroke-dasharray="4,2" />')

        # Hook Block Assembly
        hook_block_w = 28
        hook_block_h = 24
        svg.append(f'<rect x="{center_x - (hook_block_w / 2)}" y="{hook_y}" width="{hook_block_w}" height="{hook_block_h}" rx="2" fill="#d90429" stroke="#caf0f8" stroke-width="1.2" />')
        # Hook shank & curved hook
        svg.append(f'<path d="M {center_x} {hook_y + hook_block_h} L {center_x} {hook_y + hook_block_h + 10} C {center_x + 14} {hook_y + hook_block_h + 16}, {center_x + 14} {hook_y + hook_block_h + 28}, {center_x} {hook_y + hook_block_h + 28} C {center_x - 14} {hook_y + hook_block_h + 28}, {center_x - 14} {hook_y + hook_block_h + 16}, {center_x - 5} {hook_y + hook_block_h + 16}" fill="none" stroke="#ffd166" stroke-width="3" stroke-linecap="round" />')

        # Capacity Badge on Bridge Girder
        badge_text = f"SWL: {self.inputs.capacity_ton:.1f}t"
        svg.append(f'<rect x="{center_x - 45}" y="{girder_top_y + (girder_depth_px / 2) - 10}" width="90" height="20" rx="3" fill="#073b4c" stroke="#00f5d4" stroke-width="1" />')
        svg.append(f'<text x="{center_x}" y="{girder_top_y + (girder_depth_px / 2) + 4}" fill="#00f5d4" font-size="11" font-weight="bold" text-anchor="middle">{badge_text}</text>')

        # 6. Floor Level Line (Datum Line)
        svg.append(f'<line x1="{offset_x}" y1="{floor_y}" x2="{offset_x + scale_w}" y2="{floor_y}" stroke="#48cae4" stroke-width="2" />')
        svg.append(f'<text x="{girder_x1 - 50}" y="{floor_y - 6}" fill="#48cae4" font-size="10" font-weight="bold">FLOOR ± 0.00</text>')
        # Ground hatching
        for gx in range(int(offset_x), int(offset_x + scale_w), 25):
            svg.append(f'<line x1="{gx}" y1="{floor_y}" x2="{gx - 10}" y2="{floor_y + 10}" stroke="#253252" stroke-width="1.2" />')

        # 7. Dimension Lines (ISO CAD Standard with Extension Lines and Arrowheads)
        # Dimension A: Span (Rail to Rail)
        dim_span_y = rail_y - 65
        svg.append(self._render_linear_dimension(
            x1=girder_x1, y1=rail_y,
            x2=girder_x2, y2=rail_y,
            offset_dist=-65,
            label=f"SPAN = {self.inputs.span_mm:,.0f} mm",
            orientation="horizontal"
        ))

        # Dimension B: Lifting Height (Floor to Hook Highest Reach)
        svg.append(self._render_linear_dimension(
            x1=girder_x1 + 60, y1=floor_y,
            x2=girder_x1 + 60, y2=hook_y,
            offset_dist=0,
            label=f"LIFT HEIGHT = {self.inputs.lifting_height_mm:,.0f} mm",
            orientation="vertical"
        ))

        # Dimension C: Rail Height (Floor to Top of Rail)
        svg.append(self._render_linear_dimension(
            x1=girder_x2 + 75, y1=floor_y,
            x2=girder_x2 + 75, y2=rail_y,
            offset_dist=0,
            label=f"RAIL ELEVATION = {self.inputs.rail_height_mm:,.0f} mm",
            orientation="vertical"
        ))

        # Dimension D: Girder Depth
        svg.append(self._render_linear_dimension(
            x1=girder_x1 + 180, y1=girder_top_y,
            x2=girder_x1 + 180, y2=girder_bot_y,
            offset_dist=0,
            label=f"{self.calcs.girder_depth_mm:,.0f} mm",
            orientation="vertical",
            text_size=9
        ))

        # Dimension E: Left Clearance to Wall
        svg.append(self._render_linear_dimension(
            x1=girder_x1 - col_width - 15, y1=rail_y - 20,
            x2=girder_x1 - (truck_w / 2), y2=rail_y - 20,
            offset_dist=0,
            label=f"MIN. {self.inputs.building_clearance_left_mm:,.0f}",
            orientation="horizontal",
            text_size=9
        ))

        # Dimension F: Right Clearance to Wall
        svg.append(self._render_linear_dimension(
            x1=girder_x2 + (truck_w / 2), y1=rail_y - 20,
            x2=girder_x2 + 15, y2=rail_y - 20,
            offset_dist=0,
            label=f"MIN. {self.inputs.building_clearance_right_mm:,.0f}",
            orientation="horizontal",
            text_size=9
        ))

        svg.append('</g>')
        return "\n".join(svg)

    def _render_plan_view(self, offset_x: float, offset_y: float, scale_w: float, scale_h: float) -> str:
        """Draws the Plan (Top) View showing runway beams, wheelbase, and end carriages."""
        is_double = self.inputs.crane_type == "double_girder"

        span_px = scale_w * 0.70
        rail_left_x = offset_x + 90
        rail_right_x = rail_left_x + span_px
        center_x = (rail_left_x + rail_right_x) / 2.0
        center_y = offset_y + (scale_h / 2.0)

        # End truck length & wheelbase proportional representation
        wheelbase_px = min(scale_h - 90, max(130.0, (self.calcs.wheelbase_mm / 22.0)))
        truck_length_px = wheelbase_px + 35.0
        truck_w = 26.0

        svg = [f'<g id="plan-view" class="cad-layer">']
        svg.append(f'<text x="{offset_x}" y="{offset_y + 15}" fill="#64dfdf" font-size="14" font-weight="bold">PLAN (TOP) VIEW</text>')

        # 1. Longitudinal Runway Beams (Crane Rails Running Continuously)
        runway_top_y = offset_y + 35
        runway_bot_y = offset_y + scale_h - 20

        # Left Runway Beam & Centerline Rail
        svg.append(f'<rect x="{rail_left_x - 14}" y="{runway_top_y}" width="28" height="{runway_bot_y - runway_top_y}" fill="#1c2541" stroke="#3a506b" stroke-width="1.2" />')
        svg.append(f'<line x1="{rail_left_x}" y1="{runway_top_y}" x2="{rail_left_x}" y2="{runway_bot_y}" stroke="#ffd166" stroke-width="2" />')

        # Right Runway Beam & Centerline Rail
        svg.append(f'<rect x="{rail_right_x - 14}" y="{runway_top_y}" width="28" height="{runway_bot_y - runway_top_y}" fill="#1c2541" stroke="#3a506b" stroke-width="1.2" />')
        svg.append(f'<line x1="{rail_right_x}" y1="{runway_top_y}" x2="{rail_right_x}" y2="{runway_bot_y}" stroke="#ffd166" stroke-width="2" />')

        # 2. End Carriages (Left and Right Trucks)
        truck_top_y = center_y - (truck_length_px / 2.0)

        # Left Truck Body
        svg.append(f'<rect x="{rail_left_x - (truck_w / 2.0)}" y="{truck_top_y}" width="{truck_w}" height="{truck_length_px}" rx="3" fill="#118ab2" stroke="#caf0f8" stroke-width="1.5" />')
        # Left Truck Wheels (Top and Bottom Wheels)
        wheel_y1 = center_y - (wheelbase_px / 2.0)
        wheel_y2 = center_y + (wheelbase_px / 2.0)
        svg.append(f'<rect x="{rail_left_x - 8}" y="{wheel_y1 - 10}" width="16" height="20" rx="2" fill="#073b4c" stroke="#ffd166" stroke-width="1.5" />')
        svg.append(f'<rect x="{rail_left_x - 8}" y="{wheel_y2 - 10}" width="16" height="20" rx="2" fill="#073b4c" stroke="#ffd166" stroke-width="1.5" />')
        # Left Rubber Buffers at ends
        svg.append(f'<rect x="{rail_left_x - 6}" y="{truck_top_y - 8}" width="12" height="8" rx="2" fill="#e63946" />')
        svg.append(f'<rect x="{rail_left_x - 6}" y="{truck_top_y + truck_length_px}" width="12" height="8" rx="2" fill="#e63946" />')

        # Right Truck Body
        svg.append(f'<rect x="{rail_right_x - (truck_w / 2.0)}" y="{truck_top_y}" width="{truck_w}" height="{truck_length_px}" rx="3" fill="#118ab2" stroke="#caf0f8" stroke-width="1.5" />')
        # Right Truck Wheels
        svg.append(f'<rect x="{rail_right_x - 8}" y="{wheel_y1 - 10}" width="16" height="20" rx="2" fill="#073b4c" stroke="#ffd166" stroke-width="1.5" />')
        svg.append(f'<rect x="{rail_right_x - 8}" y="{wheel_y2 - 10}" width="16" height="20" rx="2" fill="#073b4c" stroke="#ffd166" stroke-width="1.5" />')
        # Right Rubber Buffers
        svg.append(f'<rect x="{rail_right_x - 6}" y="{truck_top_y - 8}" width="12" height="8" rx="2" fill="#e63946" />')
        svg.append(f'<rect x="{rail_right_x - 6}" y="{truck_top_y + truck_length_px}" width="12" height="8" rx="2" fill="#e63946" />')

        # 3. Main Bridge Girder(s) in Plan View
        if is_double:
            girder_w_px = 24
            gap_px = 30
            # Girder A (North)
            svg.append(f'<rect x="{rail_left_x + 12}" y="{center_y - (gap_px/2) - girder_w_px}" width="{span_px - 24}" height="{girder_w_px}" rx="2" fill="#0f4c5c" stroke="#caf0f8" stroke-width="1.5" />')
            # Girder B (South)
            svg.append(f'<rect x="{rail_left_x + 12}" y="{center_y + (gap_px/2)}" width="{span_px - 24}" height="{girder_w_px}" rx="2" fill="#0f4c5c" stroke="#caf0f8" stroke-width="1.5" />')
            # Crab Trolley spanning across both girders
            trolley_w = 55
            trolley_h = gap_px + (girder_w_px * 2) - 8
            svg.append(f'<rect x="{center_x - (trolley_w/2)}" y="{center_y - (trolley_h/2)}" width="{trolley_w}" height="{trolley_h}" rx="3" fill="#e36414" stroke="#ffd166" stroke-width="1.5" />')
            svg.append(f'<circle cx="{center_x}" cy="{center_y}" r="9" fill="#073b4c" stroke="#caf0f8" stroke-width="1" />')
        else:
            girder_w_px = 34
            svg.append(f'<rect x="{rail_left_x + 12}" y="{center_y - (girder_w_px/2)}" width="{span_px - 24}" height="{girder_w_px}" rx="2" fill="#0f4c5c" stroke="#caf0f8" stroke-width="1.5" />')
            # Trolley on single girder
            trolley_w = 48
            trolley_h = girder_w_px + 16
            svg.append(f'<rect x="{center_x - (trolley_w/2)}" y="{center_y - (trolley_h/2)}" width="{trolley_w}" height="{trolley_h}" rx="3" fill="#e36414" stroke="#ffd166" stroke-width="1.5" />')
            svg.append(f'<circle cx="{center_x}" cy="{center_y}" r="8" fill="#073b4c" stroke="#caf0f8" stroke-width="1" />')

        # 4. Dimension Lines for Plan View
        # Dimension: Wheelbase (Distance between wheel axles)
        svg.append(self._render_linear_dimension(
            x1=rail_left_x - 38, y1=wheel_y1,
            x2=rail_left_x - 38, y2=wheel_y2,
            offset_dist=0,
            label=f"WHEELBASE = {self.calcs.wheelbase_mm:,.0f} mm",
            orientation="vertical",
            text_size=10
        ))

        # Dimension: Total Length over Buffers
        svg.append(self._render_linear_dimension(
            x1=rail_right_x + 35, y1=truck_top_y - 8,
            x2=rail_right_x + 35, y2=truck_top_y + truck_length_px + 8,
            offset_dist=0,
            label=f"END TRUCK = {self.calcs.end_carriage_length_mm:,.0f} mm",
            orientation="vertical",
            text_size=10
        ))

        # North Compass Indicator
        compass_x = offset_x + scale_w - 70
        compass_y = offset_y + 70
        svg.append(f"""
        <g id="compass" transform="translate({compass_x}, {compass_y})">
            <circle cx="0" cy="0" r="20" fill="#1c2541" stroke="#3a506b" stroke-width="1.2" />
            <polygon points="0,-16 5,-3 0,0 -5,-3" fill="#e63946" />
            <polygon points="0,16 5,3 0,0 -5,3" fill="#caf0f8" />
            <text x="0" y="-23" fill="#caf0f8" font-size="10" font-weight="bold" text-anchor="middle">N</text>
        </g>
        """)

        svg.append('</g>')
        return "\n".join(svg)

    def _render_linear_dimension(
        self, x1: float, y1: float, x2: float, y2: float,
        offset_dist: float, label: str, orientation: str = "horizontal",
        text_size: int = 11
    ) -> str:
        """Draws ISO CAD dimension line with leader/extension lines and arrows."""
        svg = []
        dim_color = "#00f5d4"

        if orientation == "horizontal":
            # Apply offset along Y axis
            dim_y = y1 + offset_dist
            # Extension lines
            svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x1}" y2="{dim_y + (5 if offset_dist < 0 else -5)}" stroke="#3a506b" stroke-width="0.8" />')
            svg.append(f'<line x1="{x2}" y1="{y2}" x2="{x2}" y2="{dim_y + (5 if offset_dist < 0 else -5)}" stroke="#3a506b" stroke-width="0.8" />')
            # Main dimension line with arrow markers
            svg.append(f'<line x1="{x1}" y1="{dim_y}" x2="{x2}" y2="{dim_y}" stroke="{dim_color}" stroke-width="1.2" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)" />')
            # Dimension text
            mid_x = (x1 + x2) / 2.0
            svg.append(f'<rect x="{mid_x - 55}" y="{dim_y - 8}" width="110" height="15" fill="#0b132b" />')
            svg.append(f'<text x="{mid_x}" y="{dim_y + 4}" fill="{dim_color}" font-size="{text_size}" font-weight="bold" text-anchor="middle">{label}</text>')
        else: # vertical
            dim_x = x1 + offset_dist
            # Extension lines
            svg.append(f'<line x1="{x1}" y1="{y1}" x2="{dim_x + (5 if offset_dist < 0 else -5)}" y2="{y1}" stroke="#3a506b" stroke-width="0.8" />')
            svg.append(f'<line x1="{x2}" y1="{y2}" x2="{dim_x + (5 if offset_dist < 0 else -5)}" y2="{y2}" stroke="#3a506b" stroke-width="0.8" />')
            # Main line
            svg.append(f'<line x1="{dim_x}" y1="{y1}" x2="{dim_x}" y2="{y2}" stroke="{dim_color}" stroke-width="1.2" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)" />')
            # Vertical text rotated 90 degrees or centered
            mid_y = (y1 + y2) / 2.0
            svg.append(f'<g transform="translate({dim_x}, {mid_y}) rotate(-90)">')
            svg.append(f'<rect x="-55" y="-7" width="110" height="14" fill="#0b132b" />')
            svg.append(f'<text x="0" y="4" fill="{dim_color}" font-size="{text_size}" font-weight="bold" text-anchor="middle">{label}</text>')
            svg.append('</g>')

        return "\n".join(svg)

    def _render_title_block(self, width: int, height: int) -> str:
        """Renders standard engineering Title Block in bottom-right corner."""
        tb_w = 420
        tb_h = 135
        tb_x = width - tb_w - 30
        tb_y = height - tb_h - 30

        return f"""
        <g id="title-block" class="cad-layer">
            <!-- Title block background & grid -->
            <rect x="{tb_x}" y="{tb_y}" width="{tb_w}" height="{tb_h}" fill="#1c2541" stroke="#48cae4" stroke-width="1.5" />
            <line x1="{tb_x}" y1="{tb_y + 35}" x2="{tb_x + tb_w}" y2="{tb_y + 35}" stroke="#48cae4" stroke-width="1" />
            <line x1="{tb_x}" y1="{tb_y + 70}" x2="{tb_x + tb_w}" y2="{tb_y + 70}" stroke="#48cae4" stroke-width="1" />
            <line x1="{tb_x}" y1="{tb_y + 102}" x2="{tb_x + tb_w}" y2="{tb_y + 102}" stroke="#48cae4" stroke-width="1" />

            <!-- Vertical column dividers -->
            <line x1="{tb_x + 190}" y1="{tb_y + 35}" x2="{tb_x + 190}" y2="{tb_y + tb_h}" stroke="#48cae4" stroke-width="1" />
            <line x1="{tb_x + 300}" y1="{tb_y + 70}" x2="{tb_x + 300}" y2="{tb_y + tb_h}" stroke="#48cae4" stroke-width="1" />

            <!-- Row 1: Company Header -->
            <text x="{tb_x + 15}" y="{tb_y + 24}" fill="#00f5d4" font-size="14" font-weight="bold" letter-spacing="1">MODERN CRANE CO.</text>
            <text x="{tb_x + tb_w - 15}" y="{tb_y + 23}" fill="#caf0f8" font-size="10" text-anchor="end">OVERHEAD EOT CRANE DIVISION</text>

            <!-- Row 2: Drawing Title & Type -->
            <text x="{tb_x + 15}" y="{tb_y + 49}" fill="#8d99ae" font-size="8">DRAWING TITLE / EQUIPMENT:</text>
            <text x="{tb_x + 15}" y="{tb_y + 63}" fill="#caf0f8" font-size="11" font-weight="bold">{self.inputs.name[:32]}</text>
            <text x="{tb_x + 205}" y="{tb_y + 49}" fill="#8d99ae" font-size="8">CLIENT / LOCATION:</text>
            <text x="{tb_x + 205}" y="{tb_y + 63}" fill="#ffd166" font-size="11" font-weight="bold">{self.inputs.customer or 'General Project'}</text>

            <!-- Row 3: Engineering specs -->
            <text x="{tb_x + 15}" y="{tb_y + 83}" fill="#8d99ae" font-size="8">ENGINEER / DESIGNER:</text>
            <text x="{tb_x + 15}" y="{tb_y + 96}" fill="#caf0f8" font-size="10" font-weight="bold">Syed Jawad Hussain Shah</text>
            <text x="{tb_x + 205}" y="{tb_y + 83}" fill="#8d99ae" font-size="8">TYPE:</text>
            <text x="{tb_x + 205}" y="{tb_y + 96}" fill="#caf0f8" font-size="10">{'Double Box' if self.inputs.crane_type == 'double_girder' else 'Single Girder'}</text>
            <text x="{tb_x + 315}" y="{tb_y + 83}" fill="#8d99ae" font-size="8">SCALE:</text>
            <text x="{tb_x + 315}" y="{tb_y + 96}" fill="#caf0f8" font-size="10">N.T.S. (Parametric)</text>

            <!-- Row 4: Drawing Status & Revision -->
            <text x="{tb_x + 15}" y="{tb_y + 115}" fill="#8d99ae" font-size="8">DWG NO:</text>
            <text x="{tb_x + 15}" y="{tb_y + 127}" fill="#00f5d4" font-size="10" font-weight="bold">MCC-GA-{int(self.inputs.span_mm//1000)}M-{int(self.inputs.capacity_ton)}T</text>
            <text x="{tb_x + 205}" y="{tb_y + 115}" fill="#8d99ae" font-size="8">STATUS:</text>
            <text x="{tb_x + 205}" y="{tb_y + 127}" fill="#ffbe0b" font-size="9" font-weight="bold">PRELIMINARY OFFER</text>
            <text x="{tb_x + 315}" y="{tb_y + 115}" fill="#8d99ae" font-size="8">REV:</text>
            <text x="{tb_x + 315}" y="{tb_y + 127}" fill="#caf0f8" font-size="10">01 (Parametric)</text>
        </g>
        """

    def _render_technical_table(self, x: float, y: float) -> str:
        """Renders the Technical Data summary box directly on the CAD sheet."""
        w = 260
        h = 240
        return f"""
        <g id="technical-data-table" class="cad-layer">
            <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="#1c2541" stroke="#3a506b" stroke-width="1.2" opacity="0.95" />
            <rect x="{x}" y="{y}" width="{w}" height="24" rx="3" fill="#0f4c5c" />
            <text x="{x + (w/2)}" y="{y + 16}" fill="#00f5d4" font-size="10" font-weight="bold" text-anchor="middle">TECHNICAL SPECIFICATIONS</text>

            <g font-size="9.5" fill="#caf0f8">
                <text x="{x + 12}" y="{y + 45}" fill="#8d99ae">Rated SWL Capacity:</text>
                <text x="{x + w - 12}" y="{y + 45}" font-weight="bold" fill="#ffd166" text-anchor="end">{self.inputs.capacity_ton:.1f} Ton</text>

                <text x="{x + 12}" y="{y + 68}" fill="#8d99ae">Rail Center Span (S):</text>
                <text x="{x + w - 12}" y="{y + 68}" font-weight="bold" text-anchor="end">{self.inputs.span_mm:,.0f} mm</text>

                <text x="{x + 12}" y="{y + 91}" fill="#8d99ae">Effective Lift Height (H):</text>
                <text x="{x + w - 12}" y="{y + 91}" font-weight="bold" text-anchor="end">{self.inputs.lifting_height_mm:,.0f} mm</text>

                <text x="{x + 12}" y="{y + 114}" fill="#8d99ae">Girder Profile Depth:</text>
                <text x="{x + w - 12}" y="{y + 114}" font-weight="bold" text-anchor="end">{self.calcs.girder_depth_mm:,.0f} mm</text>

                <text x="{x + 12}" y="{y + 137}" fill="#8d99ae">End Carriage Wheelbase:</text>
                <text x="{x + w - 12}" y="{y + 137}" font-weight="bold" text-anchor="end">{self.calcs.wheelbase_mm:,.0f} mm</text>

                <text x="{x + 12}" y="{y + 160}" fill="#8d99ae">Est. Crane Deadweight:</text>
                <text x="{x + w - 12}" y="{y + 160}" font-weight="bold" text-anchor="end">{self.calcs.total_crane_deadweight_kg:,.0f} kg*</text>

                <text x="{x + 12}" y="{y + 183}" fill="#8d99ae">Max Static Wheel Load:</text>
                <text x="{x + w - 12}" y="{y + 183}" font-weight="bold" fill="#ffbe0b" text-anchor="end">{self.calcs.max_static_wheel_load_kn:.2f} kN*</text>

                <text x="{x + 12}" y="{y + 206}" fill="#8d99ae">Design Classification:</text>
                <text x="{x + w - 12}" y="{y + 206}" font-weight="bold" text-anchor="end">CMAA 70 / FEM A5</text>

                <text x="{x + 12}" y="{y + 226}" fill="#6c757d" font-size="7.5">*Note: Weights and wheel loads are estimates</text>
            </g>
        </g>
        """
