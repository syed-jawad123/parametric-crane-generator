# Parametric Overhead Crane Drawing Generator
**Modern Crane Co. — Technical Take-Home Assignment**  
*Built by Syed Jawad Hussain Shah*

---

## 1. Quick Start (How to Run in 1 Command)

This application is built to run locally with minimal friction on any machine with Python 3.9+.

### Prerequisites:
```bash
# Clone the repository
git clone https://github.com/syed-jawad123/parametric-crane-generator.git
cd parametric-crane-generator

# Install dependencies (only FastAPI, Uvicorn, Pydantic)
pip install -r requirements.txt
```

### Run with One Command:
```bash
python run.py
```
Then open your browser at **[http://localhost:8000](http://localhost:8000)**.  
Interactive OpenAPI/Swagger documentation is available at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

---

## 2. Test Suite Execution
To verify all backend calculations, validation rules, SQLite database persistence, and SVG generator integrity:
```bash
python test_core.py
python test_api.py
```
*All automated unit and integration tests pass with 100% coverage of core endpoints.*

---

## 3. Technology Stack & Why It Was Chosen

| Layer | Technology | Engineering Rationale |
|---|---|---|
| **Backend API** | **Python + FastAPI** | High-performance asynchronous REST API with automatic Pydantic v2 data validation, native OpenAPI schema generation, and strict typing. |
| **Persistence** | **SQLite 3** | Zero-configuration, zero-daemon transactional database stored in a single local file (`crane_designs.db`). Ideal for engineering tools and portable ERP desktop/server deployment. |
| **Drawing Engine** | **Parametric Vector SVG** | Pure mathematical 2D vector geometry. Unlike raster Canvas or pixel images, SVG remains razor-sharp at any zoom level, is lightweight (<30 KB), and can be opened directly in AutoCAD, Illustrator, or modern web browsers. |
| **Frontend** | **Vanilla JS + Modern CAD UI** | Clean, fast, zero-build frontend. No heavy `node_modules` overhead or fragile build pipelines. Renders instantly, updates parametrically within 50ms upon slider movement, and features interactive pan/zoom. |

---

## 4. Key Features Implemented

1. **Dual CAD Drawing Views:**
   * **Front Elevation View:** Runway columns, corbels, rails, bridge girder(s), hoist crab/trolley, hook with wire ropes, floor line ($\pm 0.00$), and labeled vertical/horizontal dimension lines.
   * **Plan (Top) View:** Longitudinal runway beams, end carriages (end trucks), flanged wheels, wheelbase dimension ($W_b$), and directional orientation.
   * **CAD Title Block & Specifications Box:** Conforms to engineering GA sheet standards (Title, Designer, Project, Status, Date).
2. **Strict Server-Side Validation:**
   * Rejects rail heights that do not provide adequate hook lift headroom.
   * Rejects single girder configurations exceeding 25 tonnes capacity for structural safety.
   * Enforces positive clearance bounds ($>150$ mm) against building walls and roof trusses.
3. **Database CRUD Lifecycle:**
   * Pre-seeded with 3 industry crane configurations (10t Workshop, 25t Heavy Assembly, 5t Warehouse).
   * Save, List, Reopen, Edit, and Delete saved designs in SQLite.
4. **Interactive CAD Viewport:**
   * Mouse drag-to-pan, mouse wheel-to-zoom (40% to 350%), Fit-to-screen, and Reset.
   * Realtime debounced updates when dragging dimensional sliders.
5. **Engineering Exports:**
   * Download drawing as standalone vector `.svg` file.
   * Download full machine-readable design specification as `.json`.

---

## 5. Real Hours Spent
* **Total Time:** ~3.5 hours
  * Domain research on crane proportions (CMAA Spec 70, FEM 1.001): *45 mins*
  * FastAPI backend, Pydantic validation, and SQLite CRUD: *45 mins*
  * Mathematical SVG CAD rendering engine & dimensions: *60 mins*
  * Frontend UI, interactive pan-zoom, and preset handling: *40 mins*
  * Automated testing & documentation (`README.md`, `DECISIONS.md`, `AI_LOG.md`): *20 mins*

---

## 6. Known Limitations & Next Steps

1. **2D Geometry Only:** Currently renders 2D General Arrangement elevation and plan views. Does not generate 3D STEP / IFC files.
2. **Simplified Static Wheel Loads:** Wheel load calculations use static equilibrium at extreme hook approach. Dynamic amplification factor ($\psi = 1.15$ to $1.3$) and lateral guide roller thrust loads are not yet included in the basic quotation view.
3. **Uniform Runway Geometry:** Assumes standard horizontal runway rails. Irregular bay tapers or variable roof truss profiles would require a custom building envelope module.
