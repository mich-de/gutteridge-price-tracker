/**
 * Gutteridge Price Tracker - Premium Frontend Application
 */

const API_BASE = '';
let currentProductId = null;
let priceChart = null;
let allProducts = [];

// ============ Initialize ============

document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    loadStats();
    loadAlerts();
    initTheme();

    // Enter key to add product
    document.getElementById('productUrl').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            addProduct();
        }
    });
});

// ============ Theme Management ============

function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    showToast(`Tema ${newTheme === 'dark' ? 'scuro' : 'chiaro'} attivato`, 'success');
}

// ============ Toast Notifications ============

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;

    container.appendChild(toast);

    // Auto remove after 4 seconds
    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.4s ease reverse';
        setTimeout(() => toast.remove(), 400);
    }, 4000);
}

// ============ API Functions ============

async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        },
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return { success: false, error: error.message };
    }
}

// ============ Load Data ============

async function loadProducts() {
    const result = await apiCall('/api/products');

    if (result.success) {
        allProducts = result.products;
        renderProducts(allProducts);
        updateStatsDisplay(allProducts.length);
    }
}

async function loadStats() {
    const result = await apiCall('/api/stats');

    if (result.success) {
        document.getElementById('totalProducts').textContent = result.stats.total_products;
        document.getElementById('totalRecords').textContent = result.stats.total_price_records;
    }
}

function updateStatsDisplay(productCount) {
    document.getElementById('totalProducts').textContent = productCount;
}

// ============ Search & Sort ============

async function searchProducts() {
    const query = document.getElementById('searchInput').value.trim();

    if (!query) {
        renderProducts(allProducts);
        return;
    }

    const result = await apiCall(`/api/products/search?q=${encodeURIComponent(query)}`);

    if (result.success) {
        renderProducts(result.products);
    }
}

async function sortProducts() {
    const sortValue = document.getElementById('sortSelect').value;
    const [sortBy, order] = sortValue.split('-');

    const result = await apiCall(`/api/products/sort?by=${sortBy}&order=${order}`);

    if (result.success) {
        renderProducts(result.products);
    }
}

// ============ Render Products ============

function renderProducts(products) {
    const grid = document.getElementById('productsGrid');
    const emptyState = document.getElementById('emptyState');

    if (products.length === 0) {
        grid.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }

    grid.style.display = 'grid';
    emptyState.style.display = 'none';

    grid.innerHTML = products.map(product => createProductCard(product)).join('');
}

function createProductCard(product) {
    const imageUrl = product.image_url || '/static/placeholder.svg';
    const price = formatPrice(product.current_price);
    const originalPrice = product.original_price ? formatPrice(product.original_price) : null;
    const discount = calculateDiscount(product.current_price, product.original_price);
    const lastUpdated = formatDate(product.updated_at);

    return `
        <div class="product-card" onclick="openProductModal(${product.id})">
            <div class="product-card-image-wrapper">
                <img class="product-card-image" src="${imageUrl}" alt="${product.name}" 
                     onerror="this.src='/static/placeholder.svg'" />
                ${discount ? `<div class="product-card-badge">-${discount}%</div>` : ''}
            </div>
            <div class="product-card-body">
                <h3 class="product-card-name">${product.name || 'Prodotto senza nome'}</h3>
                <p class="product-card-category">📁 ${product.category || 'Nessuna categoria'}</p>
                <div class="product-card-price">
                    <span class="current-price">${price}</span>
                    ${originalPrice ? `<span class="original-price">${originalPrice}</span>` : ''}
                </div>
            </div>
            <div class="product-card-footer">
                <span class="last-updated">🕐 ${lastUpdated}</span>
                <div class="product-card-actions">
                    <button class="btn-card btn-card-refresh" onclick="event.stopPropagation(); refreshProductCard(${product.id})" title="Aggiorna prezzo">🔄</button>
                    <button class="btn-card btn-card-delete" onclick="event.stopPropagation(); deleteProductCard(${product.id})" title="Elimina">🗑️</button>
                </div>
            </div>
        </div>
    `;
}

// ============ Add Product ============

async function addProduct() {
    const urlInput = document.getElementById('productUrl');
    const url = urlInput.value.trim();
    const messageDiv = document.getElementById('addMessage');
    const addBtn = document.getElementById('addProductBtn');

    if (!url) {
        showMessage(messageDiv, 'Inserisci un URL valido', 'error');
        showToast('Inserisci un URL valido', 'error');
        return;
    }

    if (!url.includes('gutteridge.com')) {
        showMessage(messageDiv, 'L\'URL deve essere di gutteridge.com', 'error');
        showToast('L\'URL deve essere di gutteridge.com', 'error');
        return;
    }

    // Show loading state
    addBtn.disabled = true;
    addBtn.innerHTML = '<span class="spinner"></span> Aggiungendo...';

    const result = await apiCall('/api/products', 'POST', { url });

    // Reset button
    addBtn.disabled = false;
    addBtn.innerHTML = 'Aggiungi';

    if (result.success) {
        showMessage(messageDiv, result.message || 'Prodotto aggiunto con successo!', 'success');
        showToast('Prodotto aggiunto con successo!', 'success');
        urlInput.value = '';
        loadProducts();
        loadStats();
    } else {
        showMessage(messageDiv, result.error || 'Errore durante l\'aggiunta del prodotto', 'error');
        showToast(result.error || 'Errore durante l\'aggiunta del prodotto', 'error');
    }
}

// ============ Product Modal ============

async function openProductModal(productId) {
    currentProductId = productId;
    const modal = document.getElementById('productModal');

    // Show modal
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';

    // Load product details
    const result = await apiCall(`/api/products/${productId}/history`);

    if (result.success) {
        renderProductModal(result.product, result.history, result.stats);
        loadProductImages(productId);
    }
}

function renderProductModal(product, history, stats) {
    // Basic info
    document.getElementById('modalName').textContent = product.name;
    document.getElementById('modalCategory').textContent = product.category || '';
    document.getElementById('modalLink').href = product.url;

    // Image
    const modalImage = document.getElementById('modalImage');
    modalImage.src = product.image_url || '/static/placeholder.svg';
    modalImage.onerror = function () {
        this.src = '/static/placeholder.svg';
    };

    // Prices
    document.getElementById('modalCurrentPrice').textContent = formatPrice(product.current_price);

    const originalPriceContainer = document.getElementById('originalPriceContainer');
    const discountBadge = document.getElementById('discountBadge');

    if (product.original_price && product.original_price > product.current_price) {
        document.getElementById('modalOriginalPrice').textContent = formatPrice(product.original_price);
        originalPriceContainer.style.display = 'flex';

        const discount = calculateDiscount(product.current_price, product.original_price);
        document.getElementById('discountPercent').textContent = `-${discount}%`;
        discountBadge.style.display = 'block';
    } else {
        originalPriceContainer.style.display = 'none';
        discountBadge.style.display = 'none';
    }

    // Stats
    document.getElementById('minPrice').textContent = stats.min_price ? formatPrice(stats.min_price) : '-';
    document.getElementById('maxPrice').textContent = stats.max_price ? formatPrice(stats.max_price) : '-';
    document.getElementById('avgPrice').textContent = stats.avg_price ? formatPrice(stats.avg_price) : '-';

    // Render chart
    renderPriceChart(history);
}

async function loadProductImages(productId) {
    const result = await apiCall(`/api/products/${productId}/images`);
    const gallery = document.getElementById('productGallery');

    if (result.success && result.images.length > 0) {
        gallery.innerHTML = result.images.map((img, index) => `
            <img src="${img}" alt="Product image ${index + 1}" 
                 onclick="changeMainImage('${img}')"
                 class="${index === 0 ? 'active' : ''}" />
        `).join('');
    } else {
        gallery.innerHTML = '';
    }
}

function changeMainImage(src) {
    document.getElementById('modalImage').src = src;

    // Update active state in gallery
    const galleryImages = document.querySelectorAll('.product-gallery img');
    galleryImages.forEach(img => {
        img.classList.toggle('active', img.src === src);
    });
}

function closeModal() {
    const modal = document.getElementById('productModal');
    modal.classList.remove('active');
    document.body.style.overflow = '';
    currentProductId = null;

    // Destroy chart
    if (priceChart) {
        priceChart.destroy();
        priceChart = null;
    }
}

// Close modal on outside click
document.getElementById('productModal').addEventListener('click', (e) => {
    if (e.target.id === 'productModal') {
        closeModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
        closeAlertModal();
    }
});

// ============ Price Chart ============

function renderPriceChart(history) {
    const ctx = document.getElementById('priceChart').getContext('2d');

    // Destroy existing chart
    if (priceChart) {
        priceChart.destroy();
    }

    // Prepare data (reverse to show chronological order)
    const sortedHistory = [...history].reverse();

    const labels = sortedHistory.map(h => new Date(h.recorded_at));
    const prices = sortedHistory.map(h => h.price);
    const originalPrices = sortedHistory.map(h => h.original_price);

    // Get theme colors
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)';
    const textColor = isDark ? '#c9d1d9' : '#495057';

    // Create chart
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Prezzo Attuale',
                    data: prices,
                    borderColor: '#c9a962',
                    backgroundColor: 'rgba(201, 169, 98, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#c9a962',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                },
                {
                    label: 'Prezzo Originale',
                    data: originalPrices,
                    borderColor: isDark ? '#8b949e' : '#adb5bd',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.4,
                    pointBackgroundColor: isDark ? '#8b949e' : '#adb5bd',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        color: textColor
                    }
                },
                tooltip: {
                    backgroundColor: isDark ? '#21262d' : '#fff',
                    titleColor: isDark ? '#f0f6fc' : '#1a1a2e',
                    bodyColor: isDark ? '#c9d1d9' : '#495057',
                    borderColor: isDark ? '#30363d' : '#e9ecef',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                    titleFont: { size: 14, weight: 600 },
                    bodyFont: { size: 13 },
                    callbacks: {
                        label: function (context) {
                            return `${context.dataset.label}: €${context.parsed.y.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        displayFormats: {
                            day: 'dd MMM',
                            hour: 'HH:mm'
                        }
                    },
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45,
                        color: textColor
                    }
                },
                y: {
                    beginAtZero: false,
                    grid: {
                        color: gridColor
                    },
                    ticks: {
                        color: textColor,
                        callback: function (value) {
                            return '€' + value.toFixed(2);
                        }
                    }
                }
            }
        }
    });
}

// ============ Product Actions ============

async function refreshProduct() {
    if (!currentProductId) return;

    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Aggiornamento...';

    const result = await apiCall(`/api/products/${currentProductId}/refresh`, 'POST');

    btn.disabled = false;
    btn.innerHTML = '🔄 Aggiorna';

    if (result.success) {
        showToast('Prezzo aggiornato con successo!', 'success');
        // Reload modal data
        const historyResult = await apiCall(`/api/products/${currentProductId}/history`);
        if (historyResult.success) {
            renderProductModal(historyResult.product, historyResult.history, historyResult.stats);
        }
        loadProducts();
    } else {
        showToast('Errore durante l\'aggiornamento', 'error');
    }
}

async function refreshProductCard(productId) {
    showToast('Aggiornamento in corso...', 'info');
    const result = await apiCall(`/api/products/${productId}/refresh`, 'POST');

    if (result.success) {
        showToast('Prezzo aggiornato!', 'success');
        loadProducts();
    } else {
        showToast('Errore durante l\'aggiornamento', 'error');
    }
}

async function deleteProduct() {
    if (!currentProductId) return;

    if (!confirm('Sei sicuro di voler eliminare questo prodotto?')) {
        return;
    }

    const result = await apiCall(`/api/products/${currentProductId}`, 'DELETE');

    if (result.success) {
        showToast('Prodotto eliminato', 'success');
        closeModal();
        loadProducts();
        loadStats();
    } else {
        showToast('Errore durante l\'eliminazione', 'error');
    }
}

async function deleteProductCard(productId) {
    event.stopPropagation();

    if (!confirm('Sei sicuro di voler eliminare questo prodotto?')) {
        return;
    }

    const result = await apiCall(`/api/products/${productId}`, 'DELETE');

    if (result.success) {
        showToast('Prodotto eliminato', 'success');
        loadProducts();
        loadStats();
    } else {
        showToast('Errore durante l\'eliminazione', 'error');
    }
}

async function refreshAllProducts() {
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Aggiornamento...';

    showToast('Aggiornamento di tutti i prodotti in corso...', 'info');

    const result = await apiCall('/api/products/refresh-all', 'POST');

    // Wait a bit then reload
    setTimeout(() => {
        btn.disabled = false;
        btn.innerHTML = '🔄 Aggiorna Tutti';
        loadProducts();
        loadStats();
        showToast('Aggiornamento completato!', 'success');
    }, 5000);
}

// ============ Export Functions ============

function exportProductCSV() {
    if (!currentProductId) return;
    showToast('Download CSV in corso...', 'info');
    window.open(`/api/products/${currentProductId}/export/csv`, '_blank');
}

function exportProductJSON() {
    if (!currentProductId) return;
    showToast('Download JSON in corso...', 'info');
    window.open(`/api/products/${currentProductId}/export/json`, '_blank');
}

function exportAllCSV() {
    showToast('Download CSV in corso...', 'info');
    window.open('/api/products/export/all/csv', '_blank');
}

// ============ Alert Functions ============

function showAlertModal() {
    const modal = document.getElementById('alertModal');
    modal.classList.add('active');
    loadAlerts();
}

function closeAlertModal() {
    const modal = document.getElementById('alertModal');
    modal.classList.remove('active');
    document.getElementById('alertTargetPrice').value = '';
    document.getElementById('alertMessage').className = 'message';
}

async function loadAlerts() {
    const result = await apiCall('/api/alerts');
    const alertsList = document.getElementById('alertsList');

    if (result.success && result.alerts.length > 0) {
        alertsList.innerHTML = result.alerts.map(alert => `
            <div class="alert-item">
                <img src="${alert.image_url || '/static/placeholder.svg'}" alt="${alert.product_name}" class="alert-image" />
                <div class="alert-info">
                    <span class="alert-name">${alert.product_name}</span>
                    <span class="alert-target">Target: €${alert.target_price.toFixed(2)}</span>
                    <span class="alert-current">Attuale: €${alert.current_price ? alert.current_price.toFixed(2) : '-'}</span>
                </div>
                <button class="btn-card btn-card-delete" onclick="deleteAlert(${alert.id})" title="Elimina alert">🗑️</button>
            </div>
        `).join('');
    } else {
        alertsList.innerHTML = '<p class="no-alerts">Nessun alert attivo. Imposta un alert per essere notificato quando il prezzo scende!</p>';
    }
}

async function createAlert() {
    if (!currentProductId) return;

    const targetPrice = parseFloat(document.getElementById('alertTargetPrice').value);
    const messageDiv = document.getElementById('alertMessage');

    if (!targetPrice || targetPrice <= 0) {
        showMessage(messageDiv, 'Inserisci un prezzo target valido', 'error');
        return;
    }

    const result = await apiCall('/api/alerts', 'POST', {
        product_id: currentProductId,
        target_price: targetPrice
    });

    if (result.success) {
        showMessage(messageDiv, 'Alert creato con successo!', 'success');
        showToast('Alert creato con successo!', 'success');
        document.getElementById('alertTargetPrice').value = '';
        loadAlerts();
    } else {
        showMessage(messageDiv, result.error || 'Errore durante la creazione dell\'alert', 'error');
        showToast(result.error || 'Errore durante la creazione dell\'alert', 'error');
    }
}

async function deleteAlert(alertId) {
    if (!confirm('Sei sicuro di voler eliminare questo alert?')) {
        return;
    }

    const result = await apiCall(`/api/alerts/${alertId}`, 'DELETE');

    if (result.success) {
        showToast('Alert eliminato', 'success');
        loadAlerts();
    } else {
        showToast('Errore durante l\'eliminazione', 'error');
    }
}

// ============ Utility Functions ============

function formatPrice(price) {
    if (!price) return '€ -';
    return `€ ${parseFloat(price).toFixed(2).replace('.', ',')}`;
}

function calculateDiscount(currentPrice, originalPrice) {
    if (!currentPrice || !originalPrice || originalPrice <= currentPrice) {
        return null;
    }
    return Math.round((1 - currentPrice / originalPrice) * 100);
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showMessage(element, message, type) {
    element.textContent = message;
    element.className = `message ${type}`;

    // Auto-hide after 5 seconds
    setTimeout(() => {
        element.className = 'message';
    }, 5000);
}
