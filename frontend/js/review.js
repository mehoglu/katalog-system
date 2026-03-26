/**
 * Review UI - Product Data Review and Correction
 * Phase 6: Data Review & Correction
 */

// Configuration
const API_BASE_URL = 'http://localhost:8000';
let currentUploadId = null;
let allProducts = [];
let filteredProducts = [];

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    // Get upload_id from localStorage or URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    currentUploadId = urlParams.get('upload_id') || localStorage.getItem('upload_id');
    
    if (!currentUploadId) {
        showError('Keine Upload-ID gefunden. Bitte laden Sie zuerst Daten hoch.');
        return;
    }
    
    document.getElementById('upload-id-display').textContent = `Upload: ${currentUploadId}`;
    
    // Setup event listeners
    document.getElementById('filter-input').addEventListener('input', handleFilter);
    document.getElementById('refresh-btn').addEventListener('click', loadProducts);
    document.getElementById('catalog-btn').addEventListener('click', handleGenerateCatalog);
    
    // Load products
    loadProducts();
});

/**
 * Load all products from API
 */
async function loadProducts() {
    try {
        showLoading(true);
        hideError();
        
        const response = await fetch(`${API_BASE_URL}/api/review/${currentUploadId}`);
        
        if (!response.ok) {
            if (response.status === 404) {
                throw new Error('Produktdaten nicht gefunden. Bitte führen Sie zuerst den Merge-Prozess aus.');
            }
            throw new Error(`API Fehler: ${response.status}`);
        }
        
        const data = await response.json();
        allProducts = data.products;
        filteredProducts = [...allProducts];
        
        updateProductCount(filteredProducts.length, allProducts.length);
        renderTable(filteredProducts);
        
    } catch (error) {
        showError(`Fehler beim Laden: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

/**
 * Render table rows
 */
function renderTable(products) {
    const tbody = document.getElementById('review-table-body');
    tbody.innerHTML = '';
    
    if (products.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" style="text-align: center;">Keine Produkte gefunden</td></tr>';
        return;
    }
    
    products.forEach(product => {
        const row = createProductRow(product);
        tbody.appendChild(row);
    });
}

/**
 * Create single product row
 */
function createProductRow(product) {
    const row = document.createElement('tr');
    row.dataset.artikelnummer = product.artikelnummer;
    
    const data = product.data;
    const sources = product.sources;
    
    // Artikel-Nr (read-only)
    row.appendChild(createCell(data.artikelnummer || '', false));
    
    // Bezeichnung 1 (editable)
    row.appendChild(createEditableCell(
        data.bezeichnung1 || '',
        'bezeichnung1',
        product.artikelnummer,
        sources.bezeichnung1
    ));
    
    // Bezeichnung 1 Enhanced (read-only, styled differently)
    const bez1Enhanced = data.bezeichnung1_enhanced || '';
    const cellEnhanced = createCell(bez1Enhanced, false);
    if (bez1Enhanced) {
        cellEnhanced.classList.add('enhanced-field');
    }
    row.appendChild(cellEnhanced);
    
    // Bezeichnung 2 (editable)
    row.appendChild(createEditableCell(
        data.bezeichnung2 || '',
        'bezeichnung2',
        product.artikelnummer,
        sources.bezeichnung2
    ));
    
    // Preis (editable)
    row.appendChild(createEditableCell(
        data.preis || '',
        'preis',
        product.artikelnummer,
        sources.preis
    ));
    
    // Dimensions (editable)
    row.appendChild(createEditableCell(
        data.breite_cm || '',
        'breite_cm',
        product.artikelnummer,
        sources.breite_cm
    ));
    
    row.appendChild(createEditableCell(
        data.hoehe_cm || '',
        'hoehe_cm',
        product.artikelnummer,
        sources.hoehe_cm
    ));
    
    row.appendChild(createEditableCell(
        data.tiefe_cm || '',
        'tiefe_cm',
        product.artikelnummer,
        sources.tiefe_cm
    ));
    
    row.appendChild(createEditableCell(
        data.gewicht_kg || '',
        'gewicht_kg',
        product.artikelnummer,
        sources.gewicht_kg
    ));
    
    // Images (read-only, show thumbnails or count)
    const imagesCell = document.createElement('td');
    imagesCell.className = 'images-cell';
    if (data.bild_paths && data.bild_paths.length > 0) {
        imagesCell.textContent = `${data.bild_paths.length} 📷`;
        imagesCell.title = data.bild_paths.join(', ');
    } else {
        imagesCell.textContent = 'Keine';
        imagesCell.classList.add('no-images');
    }
    row.appendChild(imagesCell);
    
    // Sources (display badges)
    const sourcesCell = document.createElement('td');
    sourcesCell.className = 'sources-cell';
    sourcesCell.appendChild(createSourcesSummary(sources));
    row.appendChild(sourcesCell);
    
    return row;
}

/**
 * Create read-only cell
 */
function createCell(value, isEditable) {
    const cell = document.createElement('td');
    cell.textContent = value;
    if (!isEditable) {
        cell.classList.add('read-only');
    }
    return cell;
}

/**
 * Create editable cell with contenteditable
 */
function createEditableCell(value, fieldName, artikelnummer, source) {
    const cell = document.createElement('td');
    cell.textContent = value;
    cell.contentEditable = 'true';
    cell.dataset.fieldName = fieldName;
    cell.dataset.artikelnummer = artikelnummer;
    cell.dataset.originalValue = value;
    cell.dataset.source = source || 'unknown';
    
    // Add source badge
    const badge = createSourceBadge(source);
    cell.appendChild(badge);
    
    // Event listeners for editing
    cell.addEventListener('focus', handleCellFocus);
    cell.addEventListener('blur', handleCellBlur);
    cell.addEventListener('keydown', handleCellKeydown);
    
    return cell;
}

/**
 * Create source badge element
 */
function createSourceBadge(source) {
    const badge = document.createElement('span');
    badge.className = 'source-badge';
    
    const sourceMap = {
        'edi_export': { label: 'EDI', class: 'source-edi' },
        'preisliste': { label: 'Preis', class: 'source-preis' },
        'llm_enhancement': { label: 'LLM', class: 'source-llm' },
        'image_linking': { label: '📷', class: 'source-image' },
        'manual_edit': { label: '✏️', class: 'source-manual' }
    };
    
    const sourceInfo = sourceMap[source] || { label: '?', class: 'source-unknown' };
    badge.textContent = sourceInfo.label;
    badge.className = `source-badge ${sourceInfo.class}`;
    badge.title = `Quelle: ${source}`;
    
    return badge;
}

/**
 * Create sources summary for sources column
 */
function createSourcesSummary(sources) {
    const container = document.createElement('div');
    container.className = 'sources-summary';
    
    const sourceCounts = {};
    Object.values(sources).forEach(source => {
        if (source) {
            sourceCounts[source] = (sourceCounts[source] || 0) + 1;
        }
    });
    
    Object.entries(sourceCounts).forEach(([source, count]) => {
        const badge = createSourceBadge(source);
        badge.textContent += ` (${count})`;
        container.appendChild(badge);
    });
    
    return container;
}

/**
 * Handle cell focus (editing starts)
 */
function handleCellFocus(event) {
    const cell = event.target;
    cell.dataset.inEdit = 'true';
    
    // Hide source badge while editing
    const badge = cell.querySelector('.source-badge');
    if (badge) {
        badge.style.display = 'none';
    }
}

/**
 * Handle cell blur (save if changed)
 */
async function handleCellBlur(event) {
    const cell = event.target;
    delete cell.dataset.inEdit;
    
    // Show source badge again
    const badge = cell.querySelector('.source-badge');
    if (badge) {
        badge.style.display = '';
    }
    
    const newValue = cell.textContent.trim();
    const originalValue = cell.dataset.originalValue;
    
    if (newValue === originalValue) {
        return; // No change
    }
    
    // Value changed - save to backend
    await saveFieldChange(
        cell.dataset.artikelnummer,
        cell.dataset.fieldName,
        newValue,
        cell
    );
}

/**
 * Handle keydown in cell (Enter to save and blur, Escape to cancel)
 */
function handleCellKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        event.target.blur();
    } else if (event.key === 'Escape') {
        event.preventDefault();
        // Restore original value
        event.target.textContent = event.target.dataset.originalValue;
        event.target.blur();
    }
}

/**
 * Save field change to backend
 */
async function saveFieldChange(artikelnummer, fieldName, fieldValue, cell) {
    // Show loading indicator
    cell.classList.add('saving');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/review/${currentUploadId}/product`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                artikelnummer,
                field_name: fieldName,
                field_value: fieldValue
            })
        });
        
        if (!response.ok) {
            throw new Error(`Fehler beim Speichern: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Update successful
        cell.dataset.originalValue = fieldValue;
        cell.classList.remove('saving');
        cell.classList.add('save-success');
        
        // Update source badge to "manual_edit"
        const oldBadge = cell.querySelector('.source-badge');
        if (oldBadge) {
            oldBadge.remove();
        }
        const newBadge = createSourceBadge('manual_edit');
        cell.appendChild(newBadge);
        
        // Remove success animation after 1s
        setTimeout(() => {
            cell.classList.remove('save-success');
        }, 1000);
        
    } catch (error) {
        // Save failed
        cell.classList.remove('saving');
        cell.classList.add('save-error');
        alert(`Speichern fehlgeschlagen: ${error.message}`);
        
        // Restore original value
        cell.textContent = cell.dataset.originalValue;
        const badge = createSourceBadge(cell.dataset.source);
        cell.appendChild(badge);
        
        // Remove error animation after 2s
        setTimeout(() => {
            cell.classList.remove('save-error');
        }, 2000);
    }
}

/**
 * Handle filter input
 */
function handleFilter(event) {
    const filterText = event.target.value.toLowerCase();
    
    if (filterText === '') {
       filteredProducts = [...allProducts];
    } else {
        filteredProducts = allProducts.filter(product => {
            const searchText = JSON.stringify(product.data).toLowerCase();
            return searchText.includes(filterText);
        });
    }
    
    updateProductCount(filteredProducts.length, allProducts.length);
    renderTable(filteredProducts);
}

/**
 * Handle catalog generation button
 */
function handleGenerateCatalog() {
    alert('Katalog-Generierung wird in Phase 7 implementiert.');
}

/**
 * Update product count display
 */
function updateProductCount(filtered, total) {
    const countEl = document.getElementById('product-count');
    if (filtered === total) {
        countEl.textContent = `${total} Produkte`;
    } else {
        countEl.textContent = `${filtered} von ${total} Produkten`;
    }
}

/**
 * Show/hide loading indicator
 */
function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
    document.querySelector('.table-container').style.display = show ? 'none' : 'block';
}

/**
 * Show error message
 */
function showError(message) {
    const errorEl = document.getElementById('error-message');
    errorEl.textContent = message;
    errorEl.style.display = 'block';
}

/**
 * Hide error message
 */
function hideError() {
    document.getElementById('error-message').style.display = 'none';
}
