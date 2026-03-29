/**
 * Review UI - Product Data Review and Correction
 * Phase 6: Data Review & Correction
 */

// Configuration
const API_BASE_URL = 'http://localhost:8000';
let currentUploadId = null;
let allProducts = [];
let filteredProducts = [];
// selectedArtikelnummern is defined in pdf-export.js and available via window.selectedArtikelnummern

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    // Get upload_id from localStorage or URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    currentUploadId = urlParams.get('upload_id') || localStorage.getItem('upload_id') || 'complete_run_001';
    
    console.log('Using upload_id:', currentUploadId);
    
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
    console.log('Loading products for upload_id:', currentUploadId);
    
    try {
        showLoading(true);
        hideError();
        
        const response = await fetch(`${API_BASE_URL}/api/review/${currentUploadId}`);
        
        console.log('API response status:', response.status);
        
        if (!response.ok) {
            if (response.status === 404) {
                throw new Error('Produktdaten nicht gefunden. Bitte führen Sie zuerst den Merge-Prozess aus.');
            }
            throw new Error(`API Fehler: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Received products:', data.products ? data.products.length : 0);
        
        allProducts = data.products;
        filteredProducts = [...allProducts];
        
        // Enable catalog generation button when products loaded
        document.getElementById('catalog-btn').disabled = false;
        
        updateProductCount(filteredProducts.length, allProducts.length);
        renderTable(filteredProducts);
        
        console.log('Products rendered successfully');
        
    } catch (error) {
        console.error('Error loading products:', error);
        showError(`Fehler beim Laden: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

/**
 * Render table rows
 */
function renderTable(products) {
    console.log('renderTable called with', products ? products.length : 0, 'products');
    
    const tbody = document.getElementById('review-table-body');
    tbody.innerHTML = '';
    
    if (products.length === 0) {
        console.log('No products to render');
        tbody.innerHTML = '<tr><td colspan="16" style="text-align: center;">Keine Produkte gefunden</td></tr>';
        return;
    }
    
    console.log('Creating rows...');
    products.forEach((product, index) => {
        if (index === 0) console.log('First product:', product.artikelnummer);
        const row = createProductRow(product);
        tbody.appendChild(row);
    });
    console.log('All rows appended to tbody');
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
    
    // Bezeichnung 2 Enhanced (read-only, styled differently)
    const bez2Enhanced = data.bezeichnung2_enhanced || '';
    const cellBez2Enhanced = createCell(bez2Enhanced, false);
    if (bez2Enhanced) {
        cellBez2Enhanced.classList.add('enhanced-field');
    }
    row.appendChild(cellBez2Enhanced);
    
    // Abnahmemenge (read-only, multi-line) - Format as "ab X"
    const abnahmeCell = document.createElement('td');
    abnahmeCell.className = 'staffel-cell';
    if (data.abnahmemenge && data.abnahmemenge.length > 0) {
        const lines = data.abnahmemenge.map(menge => `ab ${menge}`).join('<br>');
        abnahmeCell.innerHTML = lines;
    } else {
        abnahmeCell.textContent = '-';
    }
    row.appendChild(abnahmeCell);
    
    // Preis nach Menge (read-only, multi-line)
    const preisCell = document.createElement('td');
    preisCell.className = 'staffel-cell';
    if (data.preis_nach_menge && data.preis_nach_menge.length > 0) {
        const lines = data.preis_nach_menge.map(preis => preis.toFixed(3) + ' €').join('<br>');
        preisCell.innerHTML = lines;
    } else {
        preisCell.textContent = '-';
    }
    row.appendChild(preisCell);
    
    // Innenseitemaße (editable) - Order: Breite × Länge × Höhe
    row.appendChild(createEditableCell(
        data.breite_cm || '',
        'breite_cm',
        product.artikelnummer,
        sources.breite_cm
    ));
    
    row.appendChild(createEditableCell(
        data.tiefe_cm || '',
        'tiefe_cm',
        product.artikelnummer,
        sources.tiefe_cm
    ));
    
    row.appendChild(createEditableCell(
        data.hoehe_cm || '',
        'hoehe_cm',
        product.artikelnummer,
        sources.hoehe_cm
    ));
    
    // Außenseitemaße (placeholder - not yet in data)
    // TODO: Add breite_aussen_cm, tiefe_aussen_cm, hoehe_aussen_cm to merge process
    const aussenBreite = createCell(data.breite_aussen_cm || '', false);
    aussenBreite.classList.add('missing-data');
    aussenBreite.title = 'Außenmaße noch nicht im Merge-Prozess erfasst';
    row.appendChild(aussenBreite);
    
    const aussenTiefe = createCell(data.tiefe_aussen_cm || '', false);
    aussenTiefe.classList.add('missing-data');
    aussenTiefe.title = 'Außenmaße noch nicht im Merge-Prozess erfasst';
    row.appendChild(aussenTiefe);
    
    const aussenHoehe = createCell(data.hoehe_aussen_cm || '', false);
    aussenHoehe.classList.add('missing-data');
    aussenHoehe.title = 'Außenmaße noch nicht im Merge-Prozess erfasst';
    row.appendChild(aussenHoehe);
    
    row.appendChild(createEditableCell(
        data.gewicht_kg || '',
        'gewicht_kg',
        product.artikelnummer,
        sources.gewicht_kg
    ));
    
    // Images (read-only, show thumbnails with lightbox)
    const imagesCell = document.createElement('td');
    imagesCell.className = 'images-cell';
    if (data.bild_paths && data.bild_paths.length > 0) {
        const thumbnailContainer = document.createElement('div');
        thumbnailContainer.className = 'thumbnail-container';
        data.bild_paths.slice(0, 3).forEach((path, index) => {
            const img = document.createElement('img');
            // Path is relative to server root (server runs in project root)
            img.src = `/${path}`;
            img.className = 'thumbnail';
            img.alt = 'Produktbild';
            img.title = 'Klicken zum Vergrößern';
            img.onerror = function() {
                this.style.display = 'none';
                console.error('Failed to load image:', path);
            };
            // Add click handler to open lightbox
            img.onclick = () => openLightbox(data.bild_paths, index);
            thumbnailContainer.appendChild(img);
        });
        if (data.bild_paths.length > 3) {
            const more = document.createElement('span');
            more.className = 'more-images';
            more.textContent = `+${data.bild_paths.length - 3}`;
            more.title = 'Klicken um alle Bilder zu sehen';
            more.onclick = () => openLightbox(data.bild_paths, 3);
            thumbnailContainer.appendChild(more);
        }
        imagesCell.appendChild(thumbnailContainer);
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
async function handleGenerateCatalog() {
    const catalogBtn = document.getElementById('catalog-btn');
    const originalText = catalogBtn.textContent;
    
    // Disable button and show loading state
    catalogBtn.disabled = true;
    catalogBtn.textContent = '⏳ Generiere Katalog...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/catalog/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                upload_id: currentUploadId
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Katalog-Generierung fehlgeschlagen');
        }
        
        const result = await response.json();
        
        // Show success message
        catalogBtn.textContent = '✅ Katalog generiert!';
        catalogBtn.style.backgroundColor = '#10b981';
        
        // Show success alert with link
        const catalogPath = result.output_path.replace('uploads/', '../uploads/');
        const catalogUrl = `${window.location.origin}/${catalogPath}/index.html`;
        
        const message = `
✅ HTML-Katalog erfolgreich generiert!

📊 ${result.total_products} Produkte
📄 ${result.files_generated} Dateien erstellt

🔗 Katalog öffnen:
${catalogUrl}
        `.trim();
        
        alert(message);
        
        // Add "View Catalog" button
        if (!document.getElementById('view-catalog-btn')) {
            const viewBtn = document.createElement('button');
            viewBtn.id = 'view-catalog-btn';
            viewBtn.className = 'btn-primary';
            viewBtn.textContent = '👁️ Katalog ansehen';
            viewBtn.style.marginLeft = '10px';
            viewBtn.onclick = () => window.open(catalogUrl, '_blank');
            
            catalogBtn.parentElement.appendChild(viewBtn);
            
            // Add PDF export button (if function exists from pdf-export.js)
            if (typeof addPDFExportButton === 'function') {
                setTimeout(() => addPDFExportButton(), 100);
            }
        }
        
        // Reset button after 3 seconds
        setTimeout(() => {
            catalogBtn.textContent = originalText;
            catalogBtn.style.backgroundColor = '';
            catalogBtn.disabled = false;
        }, 3000);
        
    } catch (error) {
        console.error('Catalog generation error:', error);
        catalogBtn.textContent = '❌ Fehler';
        catalogBtn.style.backgroundColor = '#ef4444';
        
        alert(`Fehler bei der Katalog-Generierung:\n\n${error.message}`);
        
        // Reset button after 3 seconds
        setTimeout(() => {
            catalogBtn.textContent = originalText;
            catalogBtn.style.backgroundColor = '';
            catalogBtn.disabled = false;
        }, 3000);
    }
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

/**
 * Image Lightbox functionality
 */
let currentLightboxImages = [];
let currentLightboxIndex = 0;

function openLightbox(imagePaths, startIndex = 0) {
    currentLightboxImages = imagePaths;
    currentLightboxIndex = startIndex;
    
    // Create lightbox if it doesn't exist
    let lightbox = document.getElementById('image-lightbox');
    if (!lightbox) {
        lightbox = createLightboxElement();
        document.body.appendChild(lightbox);
    }
    
    showLightboxImage(currentLightboxIndex);
    lightbox.style.display = 'flex';
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
}

function createLightboxElement() {
    const lightbox = document.createElement('div');
    lightbox.id = 'image-lightbox';
    lightbox.className = 'lightbox';
    
    lightbox.innerHTML = `
        <div class="lightbox-content">
            <span class="lightbox-close">&times;</span>
            <img class="lightbox-image" src="" alt="Produktbild">
            <button class="lightbox-prev">&#10094;</button>
            <button class="lightbox-next">&#10095;</button>
            <div class="lightbox-counter"></div>
        </div>
    `;
    
    // Close on background click
    lightbox.onclick = (e) => {
        if (e.target === lightbox) {
            closeLightbox();
        }
    };
    
    // Close button
    lightbox.querySelector('.lightbox-close').onclick = closeLightbox;
    
    // Navigation buttons
    lightbox.querySelector('.lightbox-prev').onclick = (e) => {
        e.stopPropagation();
        navigateLightbox(-1);
    };
    
    lightbox.querySelector('.lightbox-next').onclick = (e) => {
        e.stopPropagation();
        navigateLightbox(1);
    };
    
    // Keyboard navigation
    document.addEventListener('keydown', handleLightboxKeyboard);
    
    return lightbox;
}

function showLightboxImage(index) {
    const lightbox = document.getElementById('image-lightbox');
    if (!lightbox || !currentLightboxImages.length) return;
    
    const img = lightbox.querySelector('.lightbox-image');
    const counter = lightbox.querySelector('.lightbox-counter');
    const prevBtn = lightbox.querySelector('.lightbox-prev');
    const nextBtn = lightbox.querySelector('.lightbox-next');
    
    // Path is relative to server root
    const path = currentLightboxImages[index];
    img.src = `/${path}`;
    
    // Update counter
    counter.textContent = `${index + 1} / ${currentLightboxImages.length}`;
    
    // Show/hide navigation buttons
    prevBtn.style.display = currentLightboxImages.length > 1 ? 'block' : 'none';
    nextBtn.style.display = currentLightboxImages.length > 1 ? 'block' : 'none';
}

function navigateLightbox(direction) {
    currentLightboxIndex += direction;
    
    // Wrap around
    if (currentLightboxIndex < 0) {
        currentLightboxIndex = currentLightboxImages.length - 1;
    } else if (currentLightboxIndex >= currentLightboxImages.length) {
        currentLightboxIndex = 0;
    }
    
    showLightboxImage(currentLightboxIndex);
}

function closeLightbox() {
    const lightbox = document.getElementById('image-lightbox');
    if (lightbox) {
        lightbox.style.display = 'none';
        document.body.style.overflow = ''; // Restore scrolling
    }
}

function handleLightboxKeyboard(e) {
    const lightbox = document.getElementById('image-lightbox');
    if (!lightbox || lightbox.style.display === 'none') return;
    
    switch(e.key) {
        case 'Escape':
            closeLightbox();
            break;
        case 'ArrowLeft':
            navigateLightbox(-1);
            break;
        case 'ArrowRight':
            navigateLightbox(1);
            break;
    }
}
