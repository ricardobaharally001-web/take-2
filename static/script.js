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
            checkoutBtn.disabled = true;
            const originalText = checkoutBtn.innerHTML;
            checkoutBtn.innerHTML = '<span class="loading-spinner me-2"></span>Processing...';
            try {
                const resp = await axios.post('/api/cart/checkout', { cart });
                if (resp.data && resp.data.ok) {
                    showToast(resp.data.message || 'Order placed!', 'success');
                    clearCart();
                } else {
                    const errorMsg = resp.data?.message || 'Checkout failed';
                    if (resp.data?.errors) {
                        showToast(`${errorMsg}: ${resp.data.errors.join(', ')}`, 'error');
                    } else {
                        showToast(errorMsg, 'error');
                    }
                }
            } catch (e) {
                if (e.response && e.response.data) {
                    const errorMsg = e.response.data.message || 'Checkout error';
                    if (e.response.data.errors) {
                        showToast(`${errorMsg}: ${e.response.data.errors.join(', ')}`, 'error');
                    } else {
                        showToast(errorMsg, 'error');
                    }
                } else {
                    showToast('Checkout error', 'error');
                }
            } finally {
                checkoutBtn.disabled = getCart().length === 0;
                checkoutBtn.innerHTML = originalText;
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
