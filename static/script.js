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

// Initialize theme
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
    
    const darkBtn = document.getElementById('darkToggle');
    if (darkBtn) {
        darkBtn.addEventListener('click', function() {
            const current = document.documentElement.getAttribute('data-theme') || 'light';
            setTheme(current === 'light' ? 'dark' : 'light');
        });
    }
    
    updateCartCount();
    renderCart();
});

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
        } else {
            el.style.display = 'none';
        }
    }
}

function addToCart(pid) {
    // Get product data from the page or fetch it
    const productCard = document.querySelector(`[onclick="addToCart('${pid}')"]`).closest('.product-card, .row');
    
    if (productCard) {
        const name = productCard.querySelector('h1, h5, h6')?.textContent || 'Product';
        const priceText = productCard.querySelector('.price, .price-large')?.textContent || '$0';
        const price = parseFloat(priceText.replace('$', ''));
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
        showToast('Product added to cart!');
    }
}

function showToast(message) {
    // Create toast element
