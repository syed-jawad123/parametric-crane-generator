/**
 * Modern Crane Co. - Parametric Overhead Crane Generator
 * Interactive State Management, SVG Pan-Zoom, Realtime CAD Calculation Engine
 */

// Application State
const state = {
  currentDesignId: null,
  viewMode: 'both',
  zoom: 1.0,
  panX: 0,
  panY: 0,
  isPanning: false,
  startX: 0,
  startY: 0,
  debounceTimer: null,
  latestCalculations: null,
  isDirty: false
};

// DOM Elements Cache
const elements = {
  // Inputs
  name: document.getElementById('input-name'),
  customer: document.getElementById('input-customer'),
  cardSingleGirder: document.getElementById('card-single-girder'),
  cardDoubleGirder: document.getElementById('card-double-girder'),
  rangeCapacity: document.getElementById('range-capacity'),
  numCapacity: document.getElementById('num-capacity'),
  valCapacity: document.getElementById('val-capacity'),
  rangeSpan: document.getElementById('range-span'),
  numSpan: document.getElementById('num-span'),
  valSpan: document.getElementById('val-span'),
  rangeLiftingHeight: document.getElementById('range-lifting-height'),
  numLiftingHeight: document.getElementById('num-lifting-height'),
  valLiftingHeight: document.getElementById('val-lifting-height'),
  rangeRailHeight: document.getElementById('range-rail-height'),
  numRailHeight: document.getElementById('num-rail-height'),
  valRailHeight: document.getElementById('val-rail-height'),
  rangeClearanceLeft: document.getElementById('range-clearance-left'),
  numClearanceLeft: document.getElementById('num-clearance-left'),
  valClearanceLeft: document.getElementById('val-clearance-left'),
  rangeClearanceRight: document.getElementById('range-clearance-right'),
  numClearanceRight: document.getElementById('num-clearance-right'),
  valClearanceRight: document.getElementById('val-clearance-right'),
  presetSelector: document.getElementById('preset-selector'),

  // Metrics
  metricGirderDepth: document.getElementById('metric-girder-depth'),
  metricWheelbase: document.getElementById('metric-wheelbase'),
  metricDeadweight: document.getElementById('metric-deadweight'),
  metricWheelLoad: document.getElementById('metric-wheel-load'),

  // CAD Canvas & Controls
  svgArea: document.getElementById('svg-render-area'),
  panZoomContainer: document.getElementById('svg-pan-zoom-container'),
  svgContent: document.getElementById('svg-content'),
  zoomLabel: document.getElementById('zoom-percentage'),
  btnZoomIn: document.getElementById('btn-zoom-in'),
  btnZoomOut: document.getElementById('btn-zoom-out'),
  btnZoomReset: document.getElementById('btn-zoom-reset'),
  btnZoomFit: document.getElementById('btn-zoom-fit'),
  viewTabs: document.querySelectorAll('.view-tab'),

  // Actions
  btnSaveDesign: document.getElementById('btn-save-design'),
  saveBtnText: document.getElementById('save-btn-text'),
  btnNewDesign: document.getElementById('btn-new-design'),
  btnOpenSaved: document.getElementById('btn-open-saved'),
  btnExportJson: document.getElementById('btn-export-json'),
  btnExportSvg: document.getElementById('btn-export-svg'),
  savedCountBadge: document.getElementById('saved-count-badge'),

  // Modal
  modalSaved: document.getElementById('modal-saved-designs'),
  btnCloseModal: document.getElementById('btn-close-modal'),
  savedDesignsList: document.getElementById('saved-designs-list'),

  // Notification Banner
  notificationBanner: document.getElementById('notification-banner'),
  notificationText: document.getElementById('notification-text'),
  notificationIcon: document.getElementById('notification-icon'),
};

// ----------------------------------------------------------------------------
// 1. Initialization
// ----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  setupPanZoom();
  refreshSavedCount();
  triggerCalculation(); // Initial CAD generation
});

// ----------------------------------------------------------------------------
// 2. Event Listeners Setup
// ----------------------------------------------------------------------------
function setupEventListeners() {
  // Synchronized Sliders and Number Inputs
  bindSyncInput(elements.rangeCapacity, elements.numCapacity, (v) => {
    elements.valCapacity.textContent = `${parseFloat(v).toFixed(1)} t`;
    autoCheckGirderRecommendation();
    triggerCalculation();
  });

  bindSyncInput(elements.rangeSpan, elements.numSpan, (v) => {
    const mm = parseFloat(v);
    elements.valSpan.textContent = `${mm.toLocaleString()} mm (${(mm / 1000).toFixed(2)} m)`;
    triggerCalculation();
  });

  bindSyncInput(elements.rangeLiftingHeight, elements.numLiftingHeight, (v) => {
    const mm = parseFloat(v);
    elements.valLiftingHeight.textContent = `${mm.toLocaleString()} mm (${(mm / 1000).toFixed(2)} m)`;
    // Auto-adjust rail height if needed
    if (parseFloat(elements.numRailHeight.value) < mm + 500) {
      const newRail = mm + 1000;
      elements.rangeRailHeight.value = newRail;
      elements.numRailHeight.value = newRail;
      elements.valRailHeight.textContent = `${newRail.toLocaleString()} mm`;
    }
    triggerCalculation();
  });

  bindSyncInput(elements.rangeRailHeight, elements.numRailHeight, (v) => {
    elements.valRailHeight.textContent = `${parseFloat(v).toLocaleString()} mm`;
    triggerCalculation();
  });

  bindSyncInput(elements.rangeClearanceLeft, elements.numClearanceLeft, (v) => {
    elements.valClearanceLeft.textContent = `${parseFloat(v).toLocaleString()} mm`;
    triggerCalculation();
  });

  bindSyncInput(elements.rangeClearanceRight, elements.numClearanceRight, (v) => {
    elements.valClearanceRight.textContent = `${parseFloat(v).toLocaleString()} mm`;
    triggerCalculation();
  });

  // Crane Type Radio Cards
  elements.cardSingleGirder.addEventListener('click', () => setCraneType('single_girder'));
  elements.cardDoubleGirder.addEventListener('click', () => setCraneType('double_girder'));

  // Design metadata changes
  elements.name.addEventListener('input', () => { state.isDirty = true; });
  elements.customer.addEventListener('input', () => { state.isDirty = true; });

  // View Mode Tabs
  elements.viewTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      elements.viewTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      state.viewMode = tab.dataset.view;
      triggerCalculation();
    });
  });

  // Quick Preset Selection
  elements.presetSelector.addEventListener('change', (e) => {
    applyPreset(e.target.value);
  });

  // Save / Action Buttons
  elements.btnSaveDesign.addEventListener('click', handleSaveDesign);
  elements.btnNewDesign.addEventListener('click', handleNewDesign);
  elements.btnOpenSaved.addEventListener('click', openSavedModal);
  elements.btnCloseModal.addEventListener('click', () => elements.modalSaved.classList.remove('open'));
  elements.modalSaved.addEventListener('click', (e) => {
    if (e.target === elements.modalSaved) elements.modalSaved.classList.remove('open');
  });

  // Export Buttons
  elements.btnExportJson.addEventListener('click', handleExportJson);
  elements.btnExportSvg.addEventListener('click', handleExportSvg);
}

function bindSyncInput(rangeEl, numEl, onChange) {
  rangeEl.addEventListener('input', () => {
    numEl.value = rangeEl.value;
    onChange(rangeEl.value);
  });
  numEl.addEventListener('input', () => {
    rangeEl.value = numEl.value;
    onChange(numEl.value);
  });
}

function setCraneType(type) {
  if (type === 'single_girder') {
    elements.cardSingleGirder.classList.add('active');
    elements.cardDoubleGirder.classList.remove('active');
  } else {
    elements.cardDoubleGirder.classList.add('active');
    elements.cardSingleGirder.classList.remove('active');
  }
  triggerCalculation();
}

function getSelectedCraneType() {
  return elements.cardDoubleGirder.classList.contains('active') ? 'double_girder' : 'single_girder';
}

function autoCheckGirderRecommendation() {
  const cap = parseFloat(elements.numCapacity.value);
  if (cap > 25.0 && getSelectedCraneType() === 'single_girder') {
    showNotification('Capacities above 25t require a Double Girder structure for safety. Auto-switching to Double Girder.', 'error');
    setCraneType('double_girder');
  }
}

// ----------------------------------------------------------------------------
// 3. API Calculation & Realtime Live Preview
// ----------------------------------------------------------------------------
function getPayload() {
  return {
    name: elements.name.value.trim() || 'Custom EOT Crane',
    customer: elements.customer.value.trim() || 'Internal Engineering',
    crane_type: getSelectedCraneType(),
    capacity_ton: parseFloat(elements.numCapacity.value),
    span_mm: parseFloat(elements.numSpan.value),
    lifting_height_mm: parseFloat(elements.numLiftingHeight.value),
    rail_height_mm: parseFloat(elements.numRailHeight.value),
    building_clearance_left_mm: parseFloat(elements.numClearanceLeft.value),
    building_clearance_right_mm: parseFloat(elements.numClearanceRight.value),
    roof_clearance_mm: 300.0,
    notes: 'Parametrically generated General Arrangement drawing.'
  };
}

function triggerCalculation() {
  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(performCalculation, 40);
}

async function performCalculation() {
  const payload = getPayload();

  try {
    const response = await fetch(`/api/calculate?view=${state.viewMode}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errData = await response.json();
      let errorMsg = 'Validation Error';
      if (errData.detail) {
        if (Array.isArray(errData.detail)) {
          errorMsg = errData.detail.map(d => `${d.loc.slice(-1)}: ${d.msg}`).join(', ');
        } else {
          errorMsg = errData.detail;
        }
      }
      showNotification(errorMsg, 'error');
      return;
    }

    const data = await response.json();
    hideNotification();

    // Render returned vector SVG CAD
    elements.svgContent.innerHTML = data.svg;
    state.latestCalculations = data.calculations;

    // Update floating engineering metrics bar
    elements.metricGirderDepth.textContent = `${Math.round(data.calculations.girder_depth_mm)} mm`;
    elements.metricWheelbase.textContent = `${Math.round(data.calculations.wheelbase_mm)} mm`;
    elements.metricDeadweight.textContent = `${Math.round(data.calculations.total_crane_deadweight_kg).toLocaleString()} kg`;
    elements.metricWheelLoad.textContent = `${data.calculations.max_static_wheel_load_kn.toFixed(2)} kN`;

  } catch (err) {
    console.error('Calculation error:', err);
    showNotification('Network connection error connecting to backend API.', 'error');
  }
}

// ----------------------------------------------------------------------------
// 4. Database CRUD Operations (SQLite)
// ----------------------------------------------------------------------------
async function handleSaveDesign() {
  const payload = getPayload();
  elements.btnSaveDesign.disabled = true;
  elements.saveBtnText.textContent = 'Saving...';

  try {
    let url = '/api/designs';
    let method = 'POST';

    if (state.currentDesignId) {
      url = `/api/designs/${state.currentDesignId}`;
      method = 'PUT';
    }

    const res = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to save design');
    }

    const result = await res.json();
    state.currentDesignId = result.id;
    state.isDirty = false;
    elements.saveBtnText.textContent = 'Update Saved Design';

    showNotification(`✓ Successfully saved design "${payload.name}" to database!`, 'success');
    refreshSavedCount();
  } catch (err) {
    showNotification(err.message, 'error');
    elements.saveBtnText.textContent = state.currentDesignId ? 'Update Saved Design' : 'Save Design to Database';
  } finally {
    elements.btnSaveDesign.disabled = false;
  }
}

async function refreshSavedCount() {
  try {
    const res = await fetch('/api/designs');
    if (res.ok) {
      const list = await res.json();
      elements.savedCountBadge.textContent = list.length;
    }
  } catch (e) {
    console.warn('Could not fetch saved count:', e);
  }
}

async function openSavedModal() {
  elements.modalSaved.classList.add('open');
  elements.savedDesignsList.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 20px;">Fetching from SQLite...</div>';

  try {
    const res = await fetch('/api/designs');
    if (!res.ok) throw new Error('Could not load designs');
    const designs = await res.json();

    if (designs.length === 0) {
      elements.savedDesignsList.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 20px;">No saved designs in database.</div>';
      return;
    }

    elements.savedDesignsList.innerHTML = designs.map(d => `
      <div class="saved-design-item">
        <div>
          <div class="design-item-name">${escapeHtml(d.name)}</div>
          <div class="design-item-meta">
            ${d.capacity_ton}t SWL • Span: ${(d.span_mm / 1000).toFixed(1)}m • Lift: ${(d.lifting_height_mm / 1000).toFixed(1)}m • Type: ${d.crane_type.replace('_', ' ')}
            ${d.customer ? ' • Client: ' + escapeHtml(d.customer) : ''}
          </div>
        </div>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-primary btn-sm" onclick="loadDesignById(${d.id})">Reopen</button>
          <a class="btn btn-secondary btn-sm" href="/api/designs/${d.id}/export/svg" download title="Download SVG">SVG</a>
          <button class="btn btn-secondary btn-sm" style="color: var(--accent-red);" onclick="deleteDesignById(${d.id})">✕</button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    elements.savedDesignsList.innerHTML = `<div style="color: var(--accent-red); padding: 20px;">Error: ${err.message}</div>`;
  }
}

window.loadDesignById = async function(id) {
  try {
    const res = await fetch(`/api/designs/${id}`);
    if (!res.ok) throw new Error('Design not found');
    const data = await res.json();

    const inp = data.input;
    elements.name.value = inp.name;
    elements.customer.value = inp.customer || '';
    setCraneType(inp.crane_type);

    elements.rangeCapacity.value = inp.capacity_ton;
    elements.numCapacity.value = inp.capacity_ton;
    elements.valCapacity.textContent = `${inp.capacity_ton.toFixed(1)} t`;

    elements.rangeSpan.value = inp.span_mm;
    elements.numSpan.value = inp.span_mm;
    elements.valSpan.textContent = `${inp.span_mm.toLocaleString()} mm (${(inp.span_mm / 1000).toFixed(2)} m)`;

    elements.rangeLiftingHeight.value = inp.lifting_height_mm;
    elements.numLiftingHeight.value = inp.lifting_height_mm;
    elements.valLiftingHeight.textContent = `${inp.lifting_height_mm.toLocaleString()} mm (${(inp.lifting_height_mm / 1000).toFixed(2)} m)`;

    elements.rangeRailHeight.value = inp.rail_height_mm;
    elements.numRailHeight.value = inp.rail_height_mm;
    elements.valRailHeight.textContent = `${inp.rail_height_mm.toLocaleString()} mm`;

    elements.rangeClearanceLeft.value = inp.building_clearance_left_mm;
    elements.numClearanceLeft.value = inp.building_clearance_left_mm;
    elements.valClearanceLeft.textContent = `${inp.building_clearance_left_mm.toLocaleString()} mm`;

    elements.rangeClearanceRight.value = inp.building_clearance_right_mm;
    elements.numClearanceRight.value = inp.building_clearance_right_mm;
    elements.valClearanceRight.textContent = `${inp.building_clearance_right_mm.toLocaleString()} mm`;

    state.currentDesignId = data.id;
    state.isDirty = false;
    elements.saveBtnText.textContent = 'Update Saved Design';

    elements.modalSaved.classList.remove('open');
    showNotification(`Loaded design #${data.id}: "${inp.name}"`, 'success');
    triggerCalculation();
  } catch (err) {
    showNotification(`Failed to load design: ${err.message}`, 'error');
  }
};

window.deleteDesignById = async function(id) {
  if (!confirm(`Are you sure you want to delete design #${id}?`)) return;

  try {
    const res = await fetch(`/api/designs/${id}`, { method: 'DELETE' });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Could not delete design');
    }
    showNotification(`Design #${id} deleted.`, 'success');
    if (state.currentDesignId === id) {
      handleNewDesign();
    }
    openSavedModal();
    refreshSavedCount();
  } catch (err) {
    showNotification(err.message, 'error');
  }
};

function handleNewDesign() {
  state.currentDesignId = null;
  state.isDirty = false;
  elements.saveBtnText.textContent = 'Save Design to Database';
  elements.presetSelector.value = '';
  applyPreset('preset-10t');
  showNotification('Created new design template.', 'success');
}

// ----------------------------------------------------------------------------
// 5. Presets
// ----------------------------------------------------------------------------
function applyPreset(presetKey) {
  if (presetKey === 'preset-10t') {
    elements.name.value = 'Standard 10t Workshop EOT Crane';
    elements.customer.value = 'Main Fabrication Bay';
    setCraneType('single_girder');
    setParamValues(10.0, 20000, 7500, 8500, 300, 300);
  } else if (presetKey === 'preset-25t') {
    elements.name.value = 'Heavy 25t Manufacturing Double Girder';
    elements.customer.value = 'Turbine Assembly Hall';
    setCraneType('double_girder');
    setParamValues(25.0, 25000, 9000, 10500, 350, 350);
  } else if (presetKey === 'preset-5t') {
    elements.name.value = 'Compact 5t Warehouse Crane';
    elements.customer.value = 'Material Staging Yard';
    setCraneType('single_girder');
    setParamValues(5.0, 14000, 6000, 7000, 250, 250);
  }
  triggerCalculation();
}

function setParamValues(cap, span, liftH, railH, clL, clR) {
  elements.rangeCapacity.value = cap; elements.numCapacity.value = cap;
  elements.valCapacity.textContent = `${cap.toFixed(1)} t`;

  elements.rangeSpan.value = span; elements.numSpan.value = span;
  elements.valSpan.textContent = `${span.toLocaleString()} mm (${(span/1000).toFixed(2)} m)`;

  elements.rangeLiftingHeight.value = liftH; elements.numLiftingHeight.value = liftH;
  elements.valLiftingHeight.textContent = `${liftH.toLocaleString()} mm (${(liftH/1000).toFixed(2)} m)`;

  elements.rangeRailHeight.value = railH; elements.numRailHeight.value = railH;
  elements.valRailHeight.textContent = `${railH.toLocaleString()} mm`;

  elements.rangeClearanceLeft.value = clL; elements.numClearanceLeft.value = clL;
  elements.valClearanceLeft.textContent = `${clL.toLocaleString()} mm`;

  elements.rangeClearanceRight.value = clR; elements.numClearanceRight.value = clR;
  elements.valClearanceRight.textContent = `${clR.toLocaleString()} mm`;
}

// ----------------------------------------------------------------------------
// 6. Exports
// ----------------------------------------------------------------------------
function handleExportJson() {
  const payload = getPayload();
  const exportData = {
    metadata: {
      generated_by: 'Modern Crane Co. Parametric CAD System',
      designer: 'Syed Jawad Hussain Shah',
      timestamp: new Date().toISOString()
    },
    specifications: payload,
    engineering_calculations: state.latestCalculations
  };

  const jsonStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(exportData, null, 2));
  const dlAnchor = document.createElement('a');
  dlAnchor.setAttribute("href", jsonStr);
  dlAnchor.setAttribute("download", `ModernCrane_${payload.name.replace(/\s+/g, '_')}_Spec.json`);
  document.body.appendChild(dlAnchor);
  dlAnchor.click();
  dlAnchor.remove();
  showNotification('JSON specification downloaded.', 'success');
}

function handleExportSvg() {
  const svgEl = elements.svgContent.querySelector('svg');
  if (!svgEl) return;

  const svgXml = new XMLSerializer().serializeToString(svgEl);
  const blob = new Blob([svgXml], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const dlAnchor = document.createElement('a');
  dlAnchor.href = url;
  dlAnchor.download = `ModernCrane_GA_${elements.name.value.replace(/\s+/g, '_')}.svg`;
  document.body.appendChild(dlAnchor);
  dlAnchor.click();
  dlAnchor.remove();
  URL.revokeObjectURL(url);
  showNotification('CAD Vector SVG drawing downloaded.', 'success');
}

// ----------------------------------------------------------------------------
// 7. Interactive CAD Pan & Zoom Engine
// ----------------------------------------------------------------------------
function setupPanZoom() {
  const area = elements.svgArea;
  const container = elements.panZoomContainer;

  // Mouse wheel zoom
  area.addEventListener('wheel', (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
    const newZoom = Math.min(3.5, Math.max(0.4, state.zoom * zoomFactor));
    state.zoom = newZoom;
    updateTransform();
  }, { passive: false });

  // Pan (Click & Drag)
  area.addEventListener('mousedown', (e) => {
    // Left click only
    if (e.button !== 0) return;
    state.isPanning = true;
    state.startX = e.clientX - state.panX;
    state.startY = e.clientY - state.panY;
    area.classList.add('grabbing');
  });

  window.addEventListener('mousemove', (e) => {
    if (!state.isPanning) return;
    state.panX = e.clientX - state.startX;
    state.panY = e.clientY - state.startY;
    updateTransform();
  });

  window.addEventListener('mouseup', () => {
    state.isPanning = false;
    area.classList.remove('grabbing');
  });

  // Zoom Buttons
  elements.btnZoomIn.addEventListener('click', () => {
    state.zoom = Math.min(3.5, state.zoom * 1.2);
    updateTransform();
  });

  elements.btnZoomOut.addEventListener('click', () => {
    state.zoom = Math.max(0.4, state.zoom * 0.83);
    updateTransform();
  });

  elements.btnZoomReset.addEventListener('click', () => {
    state.zoom = 1.0;
    state.panX = 0;
    state.panY = 0;
    updateTransform();
  });

  elements.btnZoomFit.addEventListener('click', () => {
    state.zoom = 0.92;
    state.panX = 0;
    state.panY = 10;
    updateTransform();
  });
}

function updateTransform() {
  elements.panZoomContainer.style.transform = `translate(${state.panX}px, ${state.panY}px) scale(${state.zoom})`;
  elements.zoomLabel.textContent = `${Math.round(state.zoom * 100)}%`;
}

// ----------------------------------------------------------------------------
// 8. Notifications & Helpers
// ----------------------------------------------------------------------------
function showNotification(msg, type = 'error') {
  elements.notificationText.textContent = msg;
  elements.notificationIcon.textContent = type === 'error' ? '⚠️' : '✓';
  elements.notificationBanner.className = `notification-banner ${type}`;
  clearTimeout(showNotification.timer);
  showNotification.timer = setTimeout(hideNotification, 5000);
}

function hideNotification() {
  elements.notificationBanner.style.display = 'none';
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, function(m) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m];
  });
}
