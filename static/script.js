// static/script.js - Professional E-commerce Store JavaScript

// Initialize app on DOM load
document.addEventListener("DOMContentLoaded", function() {
  initializeTheme();
  initializeNavigation();
  initializeCart();
  initializeCheckout();
});

// Theme Management
function initializeTheme() {
  try {
    const saved = localStorage.getItem('store-theme');
    const theme = saved === 'dark' ? 'dark' : 'light';
    applyTheme(theme);
    
    const toggle = document.getElementById('dark-toggle');
    if (toggle) {
      updateThemeIcon(theme);
      toggle.addEventListener('click', toggleTheme);
    }
  } catch (e) {
    console.warn('Theme initialization failed:', e);
  }
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  if (document.body) {
    document.body.setAttribute('data-theme', theme);
  }
}

function updateThemeIcon(theme) {
  const toggle = document.getElementById('dark-toggle');
  if (toggle) {
    const icon = toggle.querySelector('i');
    if (icon) {
      icon.className = theme === 'dark' ? 'bi bi-sun-fill me-2' : 'bi bi-moon-fill me-2';
    }
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  const next = current === 'dark' ? 'light' : 'dark';
  
  applyTheme(next);
  updateThemeIcon(next);
  
  try {
    localStorage.setItem('store-theme', next);
  } catch (e) {
    console.warn('Failed to save theme preference:', e);
  }
}

// Navigation Enhancement
function initializeNavigation() {
  // Mobile menu auto-close on outside click
  const navbarCollapse = document.getElementById('navbarNav');
  const navbarToggler = document.querySelector('.navbar-toggler');
  
  if (navbarCollapse && navbarToggler) {
    document.addEventListener('click', function(e) {
      if (!navbarCollapse.contains(e.target) && !navbarToggler.contains(e.target)) {
        const bsCollapse = new bootstrap.Collapse(navbarCollapse, { toggle: false });
        bsCollapse.hide();
      }
    });
  }
  
  // Smooth scrolling for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

// Cart Functionality
function initializeCart() {
  // Add to cart buttons
  document.addEventListener("click", handleAddToCart);
  
  // Cart page quantity updates
  document.addEventListener("change", handleCartQuantityChange);
  
  // Remove item buttons
  document.addEventListener("click", handleRemoveFromCart);
}

async function handleAddToCart(e) {
  const btn = e.target.closest(".add-to-cart-btn");
  if (!btn) return;
  
  e.preventDefault();
  btn.disabled = true;
  
  try {
    const productId = parseInt(btn.dataset.productId, 10);
    let qty = 1;
    
    // Check if there's a quantity input specified
    if (btn.dataset.qtyEl) {
      const qtyEl = document.querySelector(btn.dataset.qtyEl);
      if (qtyEl && qtyEl.value) {
        qty = Math.max(1, parseInt(qtyEl.value, 10));
      }
    }
    
    const response = await fetch("/api/cart/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: productId, qty })
    });
    
    const data = await response.json();
    
    if (data.ok) {
      updateCartBadges(data.cart_count);
      showToast("Added to cart successfully!", "success");
      
      // Add visual feedback
      btn.innerHTML = '<i class="bi bi-check2"></i>';
      setTimeout(() => {
        btn.innerHTML = '<i class="bi bi-cart-plus"></i>';
      }, 1000);
    } else {
      showToast(data.error || "Unable to add to cart", "error");
    }
  } catch (error) {
    console.error('Add to cart error:', error);
    showToast("Something went wrong. Please try again.", "error");
  }
}

async function handleRemoveFromCart(e) {
  const btn = e.target.closest(".remove-item");
  if (!btn) return;
  
  e.preventDefault();
  
  if (!confirm("Remove this item from your cart?")) {
    return;
  }
  
  const row = btn.closest("tr");
  if (!row) return;
  
  const productId = parseInt(row.dataset.productId, 10);
  
  try {
    const response = await fetch("/api/cart/remove", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: productId })
    });
    
    const data = await response.json();
    
    if (data.ok) {
      updateCartBadges(data.cart_count);
      showToast("Item removed from cart", "success");
      window.location.reload();
    } else {
      showToast("Failed to remove item", "error");
    }
  } catch (error) {
    console.error('Remove item error:', error);
    showToast("Something went wrong. Please try again.", "error");
  }
}

function updateCartBadges(count) {
  const badges = [
    document.getElementById("cart-count-mobile"),
    document.getElementById("cart-count-desktop")
  ];
  
  badges.forEach(badge => {
    if (!badge) return;
    
    badge.textContent = count;
    
    if (count > 0) {
      badge.classList.remove('d-none');
      badge.style.display = 'flex';
    } else {
      badge.classList.add('d-none');
    }
  });
}

// Checkout Functionality
function initializeCheckout() {
  initializePayPal();
  initializeMMG();
}

function initializePayPal() {
  const paypalContainer = document.getElementById("paypal-button-container");
  const form = document.getElementById("checkout-form");
  
  if (paypalContainer && window.paypal && form) {
    const totalUSD = window.__PAYPAL_TOTAL_USD__ || 1.00;

    paypal.Buttons({
      style: {
        layout: 'vertical',
        color: 'blue',
        shape: 'rect',
        label: 'paypal'
      },
      
      createOrder: function(data, actions) {
        return actions.order.create({
          purchase_units: [{
            amount: {
              value: totalUSD.toFixed(2)
            }
          }]
        });
      },
      
      onApprove: async function(data, actions) {
        try {
          showLoadingState("Processing payment...");
          
          await actions.order.capture();
          
          const formData = new FormData(form);
          const payload = {
            name: formData.get("name"),
            email: formData.get("email"),
            phone: formData.get("phone"),
            address: formData.get("address"),
            paypal_order_id: data.orderID
          };
          
          if (!payload.name || !payload.email || !payload.phone || !payload.address) {
            throw new Error("Please fill out all required fields");
          }
          
          const response = await fetch("/api/order/paypal", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          });
          
          const result = await response.json();
          
          if (result.ok) {
            showSuccessMessage(`Payment successful! Order #${result.order_id} has been placed.`);
            setTimeout(() => {
              window.location.href = "/";
            }, 3000);
          } else {
            throw new Error(result.error || "Could not place order");
          }
        } catch (error) {
          console.error('PayPal payment error:', error);
          showToast(error.message || "Payment failed. Please try again.", "error");
        } finally {
          hideLoadingState();
        }
      },
      
      onError: function(err) {
        console.error('PayPal error:', err);
        showToast("Payment error occurred. Please try again.", "error");
      },
      
      onCancel: function(data) {
        showToast("Payment was cancelled.", "warning");
      }
    }).render("#paypal-button-container");
  }
}

function initializeMMG() {
  const mmgBtn = document.getElementById("mmg-paid-btn");
  const form = document.getElementById("checkout-form");
  
  if (mmgBtn && form) {
    mmgBtn.addEventListener("click", handleMMGPayment);
  }
}

async function handleMMGPayment() {
  const form = document.getElementById("checkout-form");
  if (!form) return;
  
  const formData = new FormData(form);
  const payload = {
    name: formData.get("name"),
    email: formData.get("email"),
    phone: formData.get("phone"),
    address: formData.get("address")
  };
  
  // Validate required fields
  const requiredFields = ['name', 'email', 'phone', 'address'];
  const missingFields = requiredFields.filter(field => !payload[field]?.trim());
  
  if (missingFields.length > 0) {
    showToast(`Please fill out: ${missingFields.join(', ')}`, "error");
    return;
  }
  
  // Validate email format
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(payload.email)) {
    showToast("Please enter a valid email address", "error");
    return;
  }
  
  try {
    showLoadingState("Processing MMG order...");
    
    const response = await fetch("/api/order/mmg", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    const result = await response.json();
    
    if (result.ok) {
      // Close the modal
      const modal = bootstrap.Modal.getInstance(document.getElementById('mmgModal'));
      if (modal) modal.hide();
      
      showSuccessMessage(
        `Order placed successfully! Order #${result.order_id} is pending payment verification. You will be contacted once payment is confirmed.`
      );
      
      setTimeout(() => {
        window.location.href = "/";
      }, 5000);
    } else {
      throw new Error(result.error || "Could not place order");
    }
  } catch (error) {
    console.error('MMG payment error:', error);
    showToast(error.message || "Failed to place order. Please try again.", "error");
  } finally {
    hideLoadingState();
  }
}

// UI Helper Functions
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  const bgClass = type === "success" ? "bg-success" : 
                  type === "error" ? "bg-danger" : 
                  type === "warning" ? "bg-warning" : "bg-info";
  
  toast.className = `position-fixed bottom-0 end-0 m-3 p-3 ${bgClass} text-white rounded shadow-lg`;
  toast.style.zIndex = "1080";
  toast.style.minWidth = "300px";
  toast.style.animation = "slideInUp 0.3s ease";
  
  const icon = type === "success" ? "check-circle-fill" : 
               type === "error" ? "exclamation-triangle-fill" : 
               type === "warning" ? "exclamation-circle-fill" : "info-circle-fill";
  
  toast.innerHTML = `
    <div class="d-flex align-items-center">
      <i class="bi bi-${icon} me-2"></i>
      <span class="flex-grow-1">${message}</span>
      <button type="button" class="btn-close btn-close-white ms-2" onclick="this.parentElement.parentElement.remove()"></button>
    </div>
  `;
  
  document.body.appendChild(toast);
  
  // Auto remove after 5 seconds
  setTimeout(() => {
    if (toast.parentNode) {
      toast.style.animation = "slideOutDown 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }
  }, 5000);
}

function showLoadingState(message = "Loading...") {
  const overlay = document.createElement("div");
  overlay.id = "loading-overlay";
  overlay.className = "position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center";
  overlay.style.zIndex = "2000";
  overlay.style.backgroundColor = "rgba(0,0,0,0.7)";
  
  overlay.innerHTML = `
    <div class="card shadow-lg" style="min-width: 300px;">
      <div class="card-body text-center p-4">
        <div class="spinner-border text-primary mb-3" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <h5 class="card-title">${message}</h5>
        <p class="card-text text-muted">Please wait...</p>
      </div>
    </div>
  `;
  
  document.body.appendChild(overlay);
}

function hideLoadingState() {
  const overlay = document.getElementById("loading-overlay");
  if (overlay) {
    overlay.remove();
  }
}

function showSuccessMessage(message) {
  const overlay = document.createElement("div");
  overlay.className = "position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center";
  overlay.style.zIndex = "2000";
  overlay.style.backgroundColor = "rgba(0,0,0,0.8)";
  
  overlay.innerHTML = `
    <div class="card shadow-lg text-center" style="max-width: 500px;">
      <div class="card-body p-5">
        <div class="text-success mb-4">
          <i class="bi bi-check-circle-fill" style="font-size: 4rem;"></i>
        </div>
        <h3 class="card-title text-success mb-3">Success!</h3>
        <p class="card-text">${message}</p>
        <div class="mt-4">
          <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
          <small class="text-muted">Redirecting to home page...</small>
        </div>
      </div>
    </div>
  `;
  
  document.body.appendChild(overlay);
  
  // Auto remove after redirect
  setTimeout(() => {
    overlay.remove();
  }, 10000);
}

// Enhanced form validation
function validateForm(form) {
  const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
  let isValid = true;
  
  inputs.forEach(input => {
    if (!input.value.trim()) {
      input.classList.add('is-invalid');
      isValid = false;
    } else {
      input.classList.remove('is-invalid');
    }
    
    // Email validation
    if (input.type === 'email' && input.value) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(input.value)) {
        input.classList.add('is-invalid');
        isValid = false;
      }
    }
  });
  
  return isValid;
}

// Product image lazy loading
function initializeLazyLoading() {
  if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.classList.remove('lazy');
          imageObserver.unobserve(img);
        }
      });
    });

    document.querySelectorAll('img[data-src]').forEach(img => {
      imageObserver.observe(img);
    });
  }
}

// Search enhancement
function initializeSearch() {
  const searchInput = document.querySelector('input[name="q"]');
  if (searchInput) {
    let searchTimeout;
    searchInput.addEventListener('input', function() {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        // Could implement live search here
      }, 500);
    });
  }
}

// CSS Animation keyframes (added via JavaScript)
const style = document.createElement('style');
style.textContent = `
  @keyframes slideInUp {
    from {
      transform: translateY(100%);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOutDown {
    from {
      transform: translateY(0);
      opacity: 1;
    }
    to {
      transform: translateY(100%);
      opacity: 0;
    }
  }
  
  .lazy {
    opacity: 0;
    transition: opacity 0.3s;
  }
  
  .lazy.loaded {
    opacity: 1;
  }
`;
document.head.appendChild(style);

// Initialize additional features
document.addEventListener("DOMContentLoaded", function() {
  initializeLazyLoading();
  initializeSearch();
}); went wrong. Please try again.", "error");
  } finally {
    btn.disabled = false;
  }
}

async function handleCartQuantityChange(e) {
  const qtyInput = e.target.closest(".cart-qty");
  if (!qtyInput) return;
  
  const row = qtyInput.closest("tr");
  if (!row) return;
  
  const productId = parseInt(row.dataset.productId, 10);
  const qty = Math.max(1, parseInt(qtyInput.value, 10));
  
  try {
    const response = await fetch("/api/cart/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: productId, qty })
    });
    
    const data = await response.json();
    
    if (data.ok) {
      updateCartBadges(data.cart_count);
      // Reload page to update totals (simple approach)
      window.location.reload();
    } else {
      showToast("Failed to update cart", "error");
    }
  } catch (error) {
    console.error('Cart update error:', error);
    showToast("Something
