# DECISIONS.md

Written by: Syed Jawad Hussain Shah  
Role: Software Developer Candidate, Modern Crane Co.

---

### 1. Who is the user, and what do they need?
The user is likely an application engineer, technical sales engineer, or proposal manager at Modern Crane Co. (or a customer exploring options). 

When a factory needs an overhead crane, the customer gives basic numbers: capacity (like 10 tons), building bay width (like 20 meters), and how high they need to lift. The engineer needs to quickly plug these numbers in, see whether the crane fits the building clearances, verify key dimensions (like girder depth and wheelbase), and get a clean, dimensioned 2D General Arrangement (GA) drawing to attach to a quotation. They also need to save these configurations into a database so they can reopen, revise, or duplicate them when the customer requests adjustments.

---

### 2. What did you assume (crane type, inputs, units, ranges), and why?
* **Units:** All dimensions are in millimeters (mm), capacity is in metric tons (t), and wheel loads are in kilonewtons (kN). This is standard for international crane manufacturing and matches the reference drawing.
* **Crane Types:** I focused on the two most common types:
  * *Single Girder:* For lighter duty and loads up to 20t-25t. Hoist is underslung beneath the bottom flange.
  * *Double Girder Box:* For heavy industrial duty (up to 50t) where the hoist trolley rides on top of two box beams.
* **Ranges & Constraints:**
  * Span: 6,000 mm to 35,000 mm (covers standard workshop bays).
  * Capacity: 1.0 t to 50.0 t.
  * Lift Height: 3,000 mm to 24,000 mm.
  * Rail Height: I added a validation rule enforcing `rail_height >= lifting_height + 400mm` because the hoist machinery and hook block need physical headroom above the hook's highest reach.
  * Single girder capacity limit: If a user selects single girder for >25t, the system rejects it and advises double girder to avoid excessive lateral sway and deflection.

---

### 3. Where did each formula or rule come from, and how sure are you?
* **Girder Depth ($H_g$):**  
  * *Formula:* $H_g \approx \text{Span} / 19$ for single girder, and $\text{Span} / 17 + 18 \times \text{Capacity}^{0.65}$ for double girder.
  * *Source:* Sourced from standard crane structural rules of thumb (CMAA Specification 70 and FEM 1.001) to keep vertical live load deflection within the safe $L/800$ limit.
  * *Confidence:* High confidence for preliminary sizing and drawings. However, for actual fabrication, plate thickness and stiffener spacing must be calculated against exact bending moments and fatigue load cycles.
* **End Carriage Wheelbase ($W_b$):**  
  * *Formula:* $W_b \approx \text{Span} / 6.5$, clamped between 2,200 mm and 4,800 mm.
  * *Source:* CMAA Spec 70 and DIN 15018 mandate $W_b / \text{Span} \ge 1/7$ to prevent skewing and rail flange binding ("crabbing") as the crane travels down the runway.
  * *Confidence:* Very high. This is an industry-wide geometric rule.
* **Static Wheel Loads ($P_{\text{wheel}}$):**  
  * *Formula:* Derived using basic statics (lever arm moment equilibrium). The critical condition is assumed when the hoist trolley is carrying 100% rated capacity at the extreme left hook approach ($C_{\text{left}}$). Load on near truck is divided equally between 2 wheels.
  * *Confidence:* Confident in the static physics, but I explicitly flagged it as an **estimate** because real production design requires dynamic impact factors ($\psi \approx 1.15 - 1.25$) and runway alignment tolerances.

---

### 4. What did you leave out on purpose?
* **Full 3D CAD modeling (STEP/IGES files):** For quick quotation and preliminary engineering, 2D General Arrangement drawings are what sales and workshop teams actually use. 3D modeling would have overcomplicated the 4-hour scope without adding value to the primary problem.
* **Complex roof profiles:** I assumed rectangular building envelopes and flat roof clearances rather than angled truss gables or pitched roofs.
* **Electrical motor/gearbox selection:** I represented the motor and cable festoons visually, but did not implement motor torque and kW calculations since that depends on customer-specified traveling speeds (e.g. 20 m/min vs 40 m/min).

---

### 5. What three questions would you ask our engineers?
1. **Wheel & Rail Catalogs:** What standard wheel diameters (e.g., 250mm, 315mm, 400mm) and rail profiles (CR73, CR100, or square bar) does Modern Crane Co. keep in stock so we can automatically select standard wheel blocks based on calculated wheel loads?
2. **ERP Integration:** How should this tool connect to your existing bill of materials (BOM) system—does your team prefer generating a component list (steel tonnage, hoist model, end truck part numbers) directly into an ERP database?
3. **Drawing Formats:** Do your clients and fabrication shops prefer receiving drawings strictly as DXF/AutoCAD files, or is an interactive browser link with printable PDF/SVG sufficient for sales sign-offs?

---

### 6. What would you do with another week?
1. **AutoCAD / DXF Export:** Use the Python `ezdxf` library to allow users to export native `.dxf` CAD files that engineers can open directly in AutoCAD or SolidWorks.
2. **Factory Envelope & Interference Clashes:** Allow users to input warehouse column spacing and roof slope, showing automatic visual warning highlights if the crane hook or girder infringes on building obstructions.
3. **Rough Cost Estimation Module:** Add a pricing calculator that multiplies estimated steel deadweight by raw material rates and adds standard hoist costs, providing an instant quotation sheet alongside the technical drawing.
