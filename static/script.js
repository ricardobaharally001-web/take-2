// Dark mode toggle
function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    updateThemeIcon(theme);
}

function updateThemeIcon(theme) {
    const icon = document.querySelector('#darkToggle i');
    if (icon) {
        icon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon-stars';
    }
}

// Initialize theme and cart helpers
function initPage() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);

    const darkBtn = document.getElementById('darkToggle');
    if (darkBtn && !darkBtn.dataset.bound) {
        darkBtn.dataset.bound = '1';
        darkBtn.addEventListener('click', function (e) {
            e.preventDefault();
            const current = document.documentElement.getAttribute('data-theme') || 'light';
            setTheme(current === 'light' ? 'dark' : 'light');
        });
    }

    updateCartCount();
    renderCart();

    const checkoutBtn = document.getElementById('checkoutBtn');
    if (checkoutBtn && !checkoutBtn.dataset.bound) {
        checkoutBtn.dataset.bound = '1';
        checkoutBtn.addEventListener('click', async () => {
            const cart = getCart();
            if (!cart.length) return;
            
            // Check if WhatsApp integration is enabled
            try {
                const whatsappResp = await fetch('/api/whatsapp-settings');
                const whatsappData = await whatsappResp.json();
                
                if (whatsappData.whatsapp_enabled) {
                    // Show customer name popup
                    const customerName = await showCustomerNameModal();
                    if (!customerName) return; // User cancelled
                    
                    await processCheckout(cart, customerName);
                } else {
                    await processCheckout(cart);
                }
            } catch (e) {
                console.error('Error checking WhatsApp settings:', e);
                await processCheckout(cart);
            }
        });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPage);
} else {
    initPage();
}

// Cart functionality
function getCart() {
    try {
        return JSON.parse(localStorage.getItem('cart') || '[]');
    } catch(e) {
        return [];
    }
}

function saveCart(cart) {
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartCount();
}

function updateCartCount() {
    const cart = getCart();
    const count = cart.reduce((acc, item) => acc + item.qty, 0);
    const el = document.getElementById('cartCount');
    if (el) {
        el.textContent = count;
        if (count > 0) {
            el.style.display = 'inline-block';
            el.classList.remove('cart-badge');
            // trigger reflow for animation restart
            void el.offsetWidth;
            el.classList.add('cart-badge');
        } else {
            el.style.display = 'none';
        }
    }
}

async function addToCart(pid) {
    // Check stock availability first
    try {
        const response = await fetch(`/api/check-stock/${pid}`);
        const stockData = await response.json();
        
        if (!stockData.available) {
            showToast('This product is out of stock', 'error');
            return;
        }
        
        // Check if we already have this item in cart and if adding one more would exceed stock
        const cart = getCart();
        const existing = cart.find(item => item.id === pid);
        const currentCartQty = existing ? existing.qty : 0;
        
        if (currentCartQty >= stockData.quantity) {
            showToast(`Cannot add more items. Only ${stockData.quantity} available in stock`, 'warning');
            return;
        }
        
    } catch (error) {
        console.error('Stock check failed:', error);
        showToast('Unable to check stock availability', 'error');
        return;
    }
    
    // Get product data from the page or fetch it
    const productCard = document.querySelector(`[onclick="addToCart('${pid}')"]`).closest('.product-card, .row');
    
    if (productCard) {
        const name = productCard.querySelector('h1, h5, h6')?.textContent || 'Product';
        const priceElement = productCard.querySelector('.price, .price-large');
        
        // Check if product has a price
        if (!priceElement) {
            showToast('This product requires contact for pricing', 'info');
            return;
        }
        
        const priceText = priceElement.textContent || '$0';
        // Strip currency symbols and thousand separators for robust parsing
        const price = parseFloat(priceText.replace(/[^0-9.]/g, ''));
        
        // Don't add to cart if price is invalid or not positive
        if (isNaN(price) || price <= 0) {
            showToast('This product requires contact for pricing', 'info');
            return;
        }
        
        const image = productCard.querySelector('img')?.src || '/static/img/placeholder.png';
        
        const cart = getCart();
        const existing = cart.find(item => item.id === pid);
        
        if (existing) {
            existing.qty += 1;
        } else {
            cart.push({
                id: pid,
                name: name,
                price: price,
                image: image,
                qty: 1
            });
        }
        
        saveCart(cart);
        
        // Show toast notification
        showToast('Successfully added to cart!', 'success');

        // If we're on the cart page, re-render
        renderCart();
    }
}

function showToast(message, type = 'info') {
    // Create toast container if not exists
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'app-toast mb-2';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'polite');
    toast.setAttribute('aria-atomic', 'true');
    const icon = type === 'success' ? 'check-circle text-success'
        : type === 'error' ? 'x-circle text-danger'
        : type === 'warning' ? 'exclamation-triangle text-warning'
        : 'info-circle text-primary';
    toast.innerHTML = `<div class="d-flex align-items-center gap-2">
        <i class="bi bi-${icon}"></i>
        <div>${message}</div>
    </div>`;

    container.appendChild(toast);

    // Auto-remove after 3 seconds
    setTimeout(() => {
        toast.remove();
        if (container.childElementCount === 0) {
            container.remove();
        }
    }, 3000);
}

// Render cart page contents if present
function renderCart() {
    const container = document.getElementById('cartContainer');
    const summary = document.getElementById('cartSummary');
    if (!container && !summary) return; // Not on cart page

    const cart = getCart();

    if (container) {
        if (cart.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info text-center">
                    <i class="bi bi-info-circle me-2"></i>Your cart is empty.
                </div>`;
        } else {
            container.innerHTML = cart.map(item => `
                <div class="cart-item d-flex align-items-center gap-3">
                    <img src="${item.image}" alt="${item.name}" style="width: 80px; height: 80px; object-fit: cover;" class="rounded border">
                    <div class="flex-grow-1">
                        <div class="fw-semibold">${item.name}</div>
                        <div class="text-muted">$${item.price.toFixed(2)}</div>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        <button class="btn btn-outline-secondary btn-sm" onclick="changeQty('${item.id}', -1)">
                            <i class="bi bi-dash"></i>
                        </button>
                        <span class="px-2">${item.qty}</span>
                        <button class="btn btn-outline-secondary btn-sm" onclick="changeQty('${item.id}', 1)">
                            <i class="bi bi-plus"></i>
                        </button>
                    </div>
                    <div class="text-end" style="width: 100px;">
                        $${(item.qty * item.price).toFixed(2)}
                    </div>
                    <button class="btn btn-outline-danger btn-sm" title="Remove" onclick="removeFromCart('${item.id}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            `).join('');
        }
    }

    if (summary) {
        const subtotal = cart.reduce((acc, i) => acc + i.price * i.qty, 0);
        const shipping = cart.length > 0 ? 5.0 : 0.0;
        const total = subtotal + shipping;
        summary.innerHTML = `
            <div class="d-flex justify-content-between"><span>Subtotal</span><span>$${subtotal.toFixed(2)}</span></div>
            <div class="d-flex justify-content-between text-muted"><span>Shipping</span><span>$${shipping.toFixed(2)}</span></div>
            <hr>
            <div class="d-flex justify-content-between fw-bold"><span>Total</span><span>$${total.toFixed(2)}</span></div>
        `;
    }
}

// Change quantity of an item in the cart
async function changeQty(pid, delta) {
    const cart = getCart();
    const item = cart.find(i => i.id === pid);
    if (!item) return;
    
    const newQty = Math.max(1, (item.qty || 1) + delta);
    
    // If increasing quantity, check stock availability
    if (delta > 0) {
        try {
            const response = await fetch(`/api/check-stock/${pid}`);
            const stockData = await response.json();
            
            if (newQty > stockData.quantity) {
                showToast(`Cannot add more items. Only ${stockData.quantity} available in stock`, 'warning');
                return;
            }
        } catch (error) {
            console.error('Stock check failed:', error);
            showToast('Unable to check stock availability', 'error');
            return;
        }
    }
    
    item.qty = newQty;
    saveCart(cart);
    renderCart();
}

// Remove item entirely from the cart
function removeFromCart(pid) {
    let cart = getCart();
    cart = cart.filter(i => i.id !== pid);
    saveCart(cart);
    renderCart();
}

// Clear the entire cart
function clearCart() {
    localStorage.removeItem('cart');
    updateCartCount();
    renderCart();
}

// Show customer name modal for WhatsApp checkout
function showCustomerNameModal() {
    return new Promise((resolve) => {
        // Create modal HTML
        const modalHtml = `
            <div class="modal fade" id="customerNameModal" tabindex="-1" aria-labelledby="customerNameModalLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="customerNameModalLabel">
                                <i class="bi bi-whatsapp text-success me-2"></i>WhatsApp Checkout
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <p>Your order will be sent via WhatsApp. Please enter your full name:</p>
                            <div class="mb-3">
                                <label for="customerNameInput" class="form-label">Full Name</label>
                                <input type="text" class="form-control" id="customerNameInput" placeholder="Enter your full name" required>
                                <div class="form-text">This name will be included in your order details.</div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-success" id="proceedWhatsAppBtn">
                                <i class="bi bi-whatsapp me-1"></i>Proceed to WhatsApp
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        const existingModal = document.getElementById('customerNameModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const modal = document.getElementById('customerNameModal');
        const nameInput = document.getElementById('customerNameInput');
        const proceedBtn = document.getElementById('proceedWhatsAppBtn');
        
        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Focus on input
        modal.addEventListener('shown.bs.modal', () => {
            nameInput.focus();
        });
        
        // Handle proceed button
        proceedBtn.addEventListener('click', () => {
            const name = nameInput.value.trim();
            if (!name) {
                nameInput.classList.add('is-invalid');
                return;
            }
            bsModal.hide();
            resolve(name);
        });
        
        // Handle enter key
        nameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                proceedBtn.click();
            }
        });
        
        // Handle input validation
        nameInput.addEventListener('input', () => {
            nameInput.classList.remove('is-invalid');
        });
        
        // Handle modal close
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
            if (!nameInput.value.trim()) {
                resolve(null); // User cancelled
            }
        });
    });
}

// Process checkout with optional customer name
async function processCheckout(cart, customerName = null) {
    const checkoutBtn = document.getElementById('checkoutBtn');
    if (!checkoutBtn) return;
    
    checkoutBtn.disabled = true;
    const originalText = checkoutBtn.innerHTML;
    checkoutBtn.innerHTML = '<span class="loading-spinner me-2"></span>Processing...';
    
    try {
        const payload = { cart };
        if (customerName) {
            payload.customer_name = customerName;
        }
        
        const resp = await fetch('/api/cart/checkout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });
        
        const data = await resp.json();
        
        if (data && data.ok) {
            if (data.use_whatsapp && data.whatsapp_url) {
                // Redirect to WhatsApp
                showToast(data.message || 'Redirecting to WhatsApp...', 'success');
                clearCart();
                
                // Small delay to show the toast, then redirect
                setTimeout(() => {
                    window.open(data.whatsapp_url, '_blank');
                }, 1000);
            } else {
                showToast(data.message || 'Order placed!', 'success');
                clearCart();
            }
        } else {
            const errorMsg = data?.message || 'Checkout failed';
            if (data?.errors) {
                showToast(`${errorMsg}: ${data.errors.join(', ')}`, 'error');
            } else {
                showToast(errorMsg, 'error');
            }
        }
    } catch (e) {
        console.error('Checkout error:', e);
        showToast('Checkout error. Please try again.', 'error');
    } finally {
        checkoutBtn.disabled = getCart().length === 0;
        checkoutBtn.innerHTML = originalText;
    }
}
