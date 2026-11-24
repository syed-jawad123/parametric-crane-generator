# AI_LOG.md

Engineering Transparency Log  
Project: Parametric Overhead Crane Drawing Generator  
Candidate: Syed Jawad Hussain Shah  

---

## 1. AI Tools Used & Purpose
* **Tool:** Antigravity / Gemini 2.0 (Google DeepMind AI Coding Assistant)
* **What it was used for:**
  * Rapidly generating boilerplate code for the FastAPI backend and SQLite database operations.
  * Formulating SVG mathematical coordinate transformations (mapping physical millimeter values to SVG coordinate space).
  * Structuring CSS rules for the dark industrial CAD blueprint theme.
  * Writing automated unit and integration tests (`test_core.py` and `test_api.py`).

---

## 2. Key Prompts Used (3 to 5 Prompts)

### Prompt 1 (Engineering Formulas):
> *"Formulate standard mechanical engineering proportions for an overhead (EOT) crane bridge girder depth, wheelbase, and wheel loads based on CMAA Spec 70 and FEM 1.001 standards. Format as a clean Python calculation function."*

### Prompt 2 (Parametric SVG CAD Drawing):
> *"Write a Python class that generates a complete 2D engineering General Arrangement (GA) drawing in SVG format. It should include Front Elevation View, Plan (Top) View, dimension lines with leader extensions and arrowheads, and an engineering Title Block in the bottom-right corner."*

### Prompt 3 (FastAPI & SQLite CRUD):
> *"Create a clean FastAPI application with Pydantic v2 schemas and SQLite persistence using python's built-in sqlite3. Implement endpoints to calculate crane geometry, save designs, list saved designs, and update/delete designs with clear error validation."*

### Prompt 4 (Interactive Pan & Zoom):
> *"Write a lightweight vanilla JavaScript pan and zoom engine for an inline SVG drawing container that supports mouse wheel zooming and click-and-drag panning without requiring any external libraries like D3 or jQuery."*

---

## 3. One Time the AI Was Wrong & How I Caught It

### The Issue:
When generating the initial vertical coordinate math for the Front Elevation View, the AI made two mistakes:
1. It anchored the **Lifting Height** dimension line from the bottom flange of the bridge girder downward toward the hook, treating it as hook suspension drop.
2. In the FastAPI route definitions, it used `Query("both", regex="...")`, which triggered `FastAPIDeprecationWarning: regex has been deprecated, please use pattern instead`.

### How I Caught It:
* Looking closely at the **Reference Drawing (Page 4 of the assignment)**, in industrial overhead crane engineering, **Lifting Height ($H$)** is strictly measured from the **finished factory floor ($\pm 0.00$)** up to the hook saddle in its highest position—NOT from the bridge girder downward!
* Because of the AI's inverted coordinate assumption, when a user entered a larger lifting height, the hook visually moved *closer* to the floor instead of higher up, and for tall lifting heights the hook clipped through the floor datum line.

### How I Fixed It:
* I restructured the vertical coordinate frame in `svg_generator.py`:
  * I defined `floor_y` as the primary ground datum line.
  * Top of rail elevation was anchored relative to `floor_y`: `rail_y = floor_y - (rail_height_mm * scale_factor)`.
  * Hook position was properly bounded: `hook_y = floor_y - (lifting_height_mm * scale_factor)`.
  * Added validation in Pydantic: `rail_height_mm >= lifting_height_mm + 400mm` so a user can never physically enter a rail that is lower than the required hook lift height.
* Replaced `regex` with `pattern` in `app/api.py`, resulting in 100% clean test passes with zero deprecation warnings.
