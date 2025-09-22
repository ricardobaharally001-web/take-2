// Professional E-commerce JavaScript with Dark Mode and Cart Management

// Dark Mode Management
(function() {
  const html = document.documentElement;
  const key = 'store-theme';
  
  function applyTheme() {
    const isDark = localStorage.getItem(key) === 'dark';
    const theme = isDark ? 'dark' : 'light';
    html.setAttribute('data-theme', theme);
    if (document.body) {
      document.body.setAttribute('data-theme', theme);
    } else {
      document.addEventListener('DOMContentLoaded', () => {
        document.body && document.body.setAttribute('data-theme', theme);
      });
    }
    
    const toggleBtns = document.querySelectorAll('.theme-toggle, #dark-toggle');
    toggleBtns.forEach(btn => {
      if (btn) {
        const icon = btn.querySelector('i');
        if (icon) {
          icon.className = isDark ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
        } else {
          btn.innerHTML = `<i class="bi bi-${isDark ? 'sun' : 'moon'}-fill"></i>`;
        }
        btn.title = isDark ? 'Switch to light mode' : 'Switch to dark mode';
        btn.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
      }
    });
  }
  
  function toggleTheme() {
    const currentTheme = localStorage.getItem(key);
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    localStorage.setItem(key, newTheme);
    applyTheme();
    
    // Add feedback animation
    const toggleBtns = document.querySelectorAll('.theme-toggle, #dark-toggle');
    toggleBtns.forEach(btn => {
      btn.style.transform = 'scale(0.9)';
      setTimeout(() => {
        btn.style.transform = 'scale(1)';
      }, 150);
    });
  }
  
  // Apply theme immediately to prevent flash
  applyTheme();
  
  // Set up toggle functionality
  document.addEventListener('DOMContentLoaded', () => {
    applyTheme();
    
    const toggleBtns = document.querySelectorAll('.theme-toggle, #dark-toggle');
    toggleBtns.forEach(btn => {
      if (btn) {
        btn.removeEventListener('click', toggleTheme);
        btn.addEventListener('click', toggleTheme);
      }
    });
  });
  
  // Global click handler for dynamically added buttons
  document.addEventListener('click', (e) => {
    if (e.target.closest('.theme-toggle') || e.target.closest('#dark-toggle')) {
      e.preventDefault();
      toggleTheme();
    }
  });
})();

// Professional Cart Management
class CartManager {
  constructor() {
    this.init();
  }
  
  init() {
    document.addEventListener('click', (e) => {
      const addBtn = e.target.closest('.add-to-cart-btn');
      if (addBtn) {
        e.preventDefault();
        const productId = parseInt(addBtn.dataset.productId);
        const qty = parseInt(addBtn.dataset.qty) || 1;
        this.addToCart(productId, qty, addBtn);
      }
      
      const removeBtn = e.target.closest('.remove-item');
      if (removeBtn) {
        e.preventDefault();
        const productId = parseInt(removeBtn.dataset.id);
        this.removeFromCart(productId, removeBtn);
      }
    });
    
    document.addEventListener('input', (e) => {
      const qtyInput = e.target.closest('.qty-input');
      if (qtyInput) {
        clearTimeout(this.qtyTimeout);
        this.qtyTimeout = setTimeout(() => {
          const productId = parseInt(qtyInput.dataset.id);
          const qty = Math.max(1, parseInt(qtyInput.value) || 1);
          this.updateCartQuantity(productId, qty);
        }, 500);
      }
    });
  }
  
  async addToCart(productId, qty = 1, button = null) {
    try {
      if (button) {
        button.disabled = true;
        this.setButtonLoading(button, 'Adding...');
      }
      
      const response = await fetch('/api/cart/add', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_id: productId,
          qty: qty
        })
      });
      
      const data = await response.json();
      
      if (data.ok) {
        this.updateCartCount(data.cart_count);
        this.showToast('Added to cart!', 'success');
        this.pulseCartButton();
      } else {
        this.showToast(data.error || 'Failed to add to cart', 'error');
      }
    } catch (error) {
      console.error('Cart error:', error);
      this.showToast('Network error. Please try again.', 'error');
    } finally {
      if (button) {
        button.disabled = false;
        this.resetButtonText(button, 'Add to Cart');
      }
    }
  }
  
  async removeFromCart(productId, button = null) {
    try {
      if (button) {
        button.disabled = true;
        this.setButtonLoading(button, 'Removing...');
      }
      
      const response = await fetch('/api/cart/remove', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_id: productId
        })
      });
      
      const data = await response.json();
      
      if (data.ok) {
        this.updateCartCount(data.cart_count);
        if (window.location.pathname === '/cart') {
          window.location.reload();
        } else {
          this.showToast('Item removed from cart', 'success');
        }
      } else {
        this.showToast(data.error || 'Failed to remove item', 'error');
      }
    } catch (error) {
      console.error('Cart error:', error);
      this.showToast('Network error. Please try again.', 'error');
    } finally {
      if (button) {
        button.disabled = false;
        this.resetButtonText(button, 'Remove');
      }
    }
  }
  
  async updateCartQuantity(productId, qty) {
    try {
      const response = await fetch('/api/cart/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_id: productId,
          qty: qty
        })
      });
      
      const data = await response.json();
      
      if (data.ok) {
        this.updateCartCount(data.cart_count);
        const subtotalEl = document.getElementById('subtotal');
        if (subtotalEl && data.subtotal !== undefined) {
          subtotalEl.textContent = `GYD $${data.subtotal.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        }
      } else {
        this.showToast(data.error || 'Failed to update quantity', 'error');
      }
    } catch (error) {
      console.error('Cart error:', error);
      this.showToast('Network error. Please try again.', 'error');
    }
  }
  
  updateCartCount(count) {
    const cartCountEl = document.getElementById('cart-count');
    if (cartCountEl) {
      cartCountEl.textContent = count;
      cartCountEl.style.display = count > 0 ? 'flex' : 'none';
      if (count > 0) {
        cartCountEl.classList.add('cart-badge');
        setTimeout(() => cartCountEl.classList.remove('cart-badge'), 300);
      }
    }
  }
  
  pulseCartButton() {
    const cartButtons = document.querySelectorAll('[href*="cart"]');
    cartButtons.forEach(btn => {
      btn.style.transform = 'scale(1.05)';
      setTimeout(() => {
        btn.style.transform = 'scale(1)';
      }, 200);
    });
  }
  
  setButtonLoading(button, text) {
    const spinner = '<span class="loading-spinner me-2"></span>';
    button.innerHTML = `${spinner}${text}`;
  }
  
  autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
  }
  
  initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
  }
  
  initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
      return new bootstrap.Popover(popoverTriggerEl);
    });
  }
  
  resetButtonText(button, text) {
    button.innerHTML = text;
  }
  
  showToast(message, type = 'info') {
    const toastContainer = this.getOrCreateToastContainer();
    const toastId = 'toast-' + Date.now();
    const iconClass = type === 'success' ? 'bi-check-circle-fill text-success' :
                     type === 'error' ? 'bi-exclamation-triangle-fill text-danger' :
                     'bi-info-circle-fill text-primary';
    const toastHtml = `
      <div class="toast" id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="3000">
        <div class="toast-header">
          <i class="bi ${iconClass} me-2"></i>
          <strong class="me-auto">Store</strong>
          <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
          ${message}
        </div>
      </div>
    `;
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    toastElement.addEventListener('hidden.bs.toast', () => {
      toastElement.remove();
    });
  }
  
  getOrCreateToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    return container;
  }
}

// Professional Navbar Enhancement
class NavbarEnhancer {
  constructor() {
    this.init();
  }
  
  init() {
    const navbarNav = document.getElementById('navbarNav') || document.getElementById('adminNav');
    if (navbarNav) {
      const navLinks = navbarNav.querySelectorAll('.nav-link');
      navLinks.forEach(link => {
        link.addEventListener('click', () => {
          const navbarToggler = document.querySelector('.navbar-toggler');
          const bsCollapse = bootstrap.Collapse.getInstance(navbarNav);
          if (navbarToggler && !navbarToggler.classList.contains('collapsed')) {
            if (bsCollapse) {
              bsCollapse.hide();
            }
          }
        });
      });
    }
  }
}

// Professional Product Detail Enhancement
class ProductDetailEnhancer {
  constructor() {
    this.init();
  }
  
  init() {
    const qtyInput = document.getElementById('quantity');
    const qtyDecrease = document.getElementById('qty-decrease');
    const qtyIncrease = document.getElementById('qty-increase');
    const addToCartBtn = document.querySelector('.add-to-cart-btn');
    
    if (qtyInput && qtyDecrease && qtyIncrease) {
      qtyDecrease.addEventListener('click', () => {
        const current = parseInt(qtyInput.value);
        if (current > 1) {
          qtyInput.value = current - 1;
          this.updateAddToCartButton();
        }
      });
      
      qtyIncrease.addEventListener('click', () => {
        const current = parseInt(qtyInput.value);
        const max = parseInt(qtyInput.getAttribute('max'));
        if (current < max) {
          qtyInput.value = current + 1;
          this.updateAddToCartButton();
        }
      });
      
      qtyInput.addEventListener('input', () => {
        const current = parseInt(qtyInput.value);
        const max = parseInt(qtyInput.getAttribute('max'));
        const min = parseInt(qtyInput.getAttribute('min'));
        
        qtyDecrease.disabled = current <= min;
        qtyIncrease.disabled = current >= max;
        this.updateAddToCartButton();
      });
      
      qtyInput.dispatchEvent(new Event('input'));
    }
    
    this.initializeProductImageZoom();
    this.initializeProductTabs();
  }
  
  updateAddToCartButton() {
    const qtyInput = document.getElementById('quantity');
    const addToCartBtn = document.querySelector('.add-to-cart-btn');
    if (addToCartBtn && qtyInput) {
      const qty = parseInt(qtyInput.value);
      addToCartBtn.dataset.qty = qty;
    }
  }
  
  initializeProductImageZoom() {
    const productImage = document.querySelector('.product-main-image');
    if (productImage) {
      productImage.addEventListener('mouseenter', () => {
        productImage.style.transform = 'scale(1.05)';
        productImage.style.transition = 'transform 0.3s ease';
      });
      
      productImage.addEventListener('mouseleave', () => {
        productImage.style.transform = 'scale(1)';
      });
    }
  }
  
  initializeProductTabs() {
    document.querySelectorAll('#productTabs button').forEach(tab => {
      tab.addEventListener('shown.bs.tab', () => {
        const card = document.querySelector('.card');
        if (card) {
          card.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
          });
        }
      });
    });
  }
}

// Professional Cart Enhancement
class CartPageEnhancer {
  constructor() {
    this.init();
  }
  
  init() {
    document.addEventListener('click', (e) => {
      if (e.target.closest('.qty-increase')) {
        const btn = e.target.closest('.qty-increase');
        const input = btn.parentElement.querySelector('.qty-input');
        const max = parseInt(input.getAttribute('max'));
        const current = parseInt(input.value);
        if (current < max) {
          input.value = current + 1;
          input.dispatchEvent(new Event('input'));
        }
      }
      
      if (e.target.closest('.qty-decrease')) {
        const btn = e.target.closest('.qty-decrease');
        const input = btn.parentElement.querySelector('.qty-input');
        const current = parseInt(input.value);
        if (current > 1) {
          input.value = current - 1;
          input.dispatchEvent(new Event('input'));
        }
      }
    });
    
    document.addEventListener('input', (e) => {
      if (e.target.classList.contains('qty-input')) {
        const input = e.target;
        const increaseBtn = input.parentElement.querySelector('.qty-increase');
        const max = parseInt(input.getAttribute('max'));
        const current = parseInt(input.value);
        
        if (increaseBtn) {
          increaseBtn.disabled = current >= max;
        }
      }
    });
    
    document.addEventListener('click', (e) => {
      if (e.target.closest('.remove-item')) {
        const btn = e.target.closest('.remove-item');
        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i>';
      }
    });
  }
}

// Professional Admin Enhancement
class AdminEnhancer {
  constructor() {
    this.init();
  }
  
  init() {
    this.initializeDeleteConfirmations();
    this.initializeFormValidation();
    this.initializeCategoryManagement();
    this.initializeProductManagement();
  }
  
  initializeDeleteConfirmations() {
    document.addEventListener('click', (e) => {
      const deleteBtn = e.target.closest('[onclick*="confirm"]');
      if (deleteBtn) {
        const form = deleteBtn.closest('form');
        if (form) {
          form.addEventListener('submit', () => {
            deleteBtn.disabled = true;
            deleteBtn.innerHTML = '<span class="loading-spinner me-2"></span>Deleting...';
          });
        }
      }
    });
  }
  
  initializeFormValidation() {
    document.addEventListener('submit', (e) => {
      if (e.target.matches('form[enctype="multipart/form-data"]')) {
        const btn = e.target.querySelector('button[type="submit"]');
        if (btn) {
          btn.disabled = true;
          const isEdit = btn.textContent.includes('Update');
          btn.innerHTML = `<span class="loading-spinner me-2"></span>${isEdit ? 'Updating...' : 'Creating...'}`;
        }
      }
    });
  }
  
  initializeCategoryManagement() {
    const deleteButtons = document.querySelectorAll('.delete-category-btn');
    const deleteModal = document.getElementById('deleteCategoryModal');
    
    if (deleteModal) {
      const modal = new bootstrap.Modal(deleteModal);
      const deleteForm = document.getElementById('deleteForm');
      const deleteWarning = document.getElementById('deleteWarning');
      const deleteConfirm = document.getElementById('deleteConfirm');
      const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
      const categoryNameSpan = document.getElementById('categoryName');
      const productCountSpan = document.getElementById('productCount');
      
      deleteButtons.forEach(button => {
        button.addEventListener('click', (e) => {
          e.preventDefault();
          
          const categoryId = button.dataset.categoryId;
          const categoryName = button.dataset.categoryName;
          const productCount = parseInt(button.dataset.productCount);
          
          categoryNameSpan.textContent = categoryName;
          productCountSpan.textContent = productCount;
          
          if (productCount > 0) {
            deleteWarning.classList.remove('d-none');
            deleteConfirm.style.display = 'none';
            confirmDeleteBtn.style.display = 'none';
          } else {
            deleteWarning.classList.add('d-none');
            deleteConfirm.style.display = 'block';
            confirmDeleteBtn.style.display = 'inline-block';
            deleteForm.action = `/admin/categories/${categoryId}/delete`;
          }
          
          modal.show();
        });
      });
    }
  }
  
  initializeProductManagement() {
    const stockInput = document.querySelector('input[name="stock_quantity"]');
    if (stockInput) {
      stockInput.addEventListener('input', () => {
        const value = parseInt(stockInput.value);
        const warning = document.getElementById('stockWarning');
        
        if (warning) warning.remove();
        
        if (value <= 5 && value > 0) {
          const warningDiv = document.createElement('div');
          warningDiv.id = 'stockWarning';
          warningDiv.className = 'form-text text-warning';
          warningDiv.innerHTML = '⚠️ Low stock warning: Consider restocking soon';
          stockInput.parentNode.appendChild(warningDiv);
        } else if (value === 0) {
          const warningDiv = document.createElement('div');
          warningDiv.id = 'stockWarning';
          warningDiv.className = 'form-text text-danger';
          warningDiv.innerHTML = '❌ Out of stock: Product will not be visible to customers';
          stockInput.parentNode.appendChild(warningDiv);
        }
      });
    }
    
    const urlParams = new URLSearchParams(window.location.search);
    const categoryParam = urlParams.get('category');
    if (categoryParam) {
      const categorySelect = document.querySelector('select[name="category_id"]');
      if (categorySelect) {
        categorySelect.value = categoryParam;
      }
    }
  }
}

// Initialize Everything
document.addEventListener('DOMContentLoaded', () => {
  new CartManager();
  new CheckoutManager();
  new FormEnhancer();
  new NavbarEnhancer();
  new ProductDetailEnhancer();
  new CartPageEnhancer();
  new AdminEnhancer();
  
  // Add fade-in animation to main content
  const main = document.querySelector('main');
  if (main) {
    main.style.opacity = '0';
    main.style.transform = 'translateY(20px)';
    main.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    
    setTimeout(() => {
      main.style.opacity = '1';
      main.style.transform = 'translateY(0)';
    }, 100);
  }
  
  // Initialize Bootstrap components
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
  
  const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
  popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });
});

// Legacy support for existing onclick handlers
window.addToCart = async function(productId, qty = 1) {
  const cartManager = new CartManager();
  await cartManager.addToCart(productId, qty);
};

// Enhanced error handling
window.addEventListener('error', (event) => {
  console.error('Global error:', event.error);
  
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'assertive');
  toast.setAttribute('aria-atomic', 'true');
  toast.setAttribute('data-bs-delay', '5000');
  
  toast.innerHTML = `
    <div class="toast-header">
      <i class="bi bi-exclamation-triangle-fill text-warning me-2"></i>
      <strong class="me-auto">Error</strong>
      <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
    <div class="toast-body">
      Something went wrong. Please refresh the page and try again.
    </div>
  `;
  
  const container = document.getElementById('toast-container') || document.body;
  container.appendChild(toast);
  
  const bsToast = new bootstrap.Toast(toast);
  bsToast.show();
  
  toast.addEventListener('hidden.bs.toast', () => {
    toast.remove();
  });
});

// Professional Checkout Manager
class CheckoutManager {
  constructor() {
    this.init();
  }
  
  init() {
    const paypalBtn = document.getElementById('pay-paypal');
    const cashBtn = document.getElementById('pay-cash');
    const form = document.getElementById('checkout-form');
    
    if (paypalBtn && form) {
      paypalBtn.addEventListener('click', () => this.processOrder('paypal'));
    }
    
    if (cashBtn && form) {
      cashBtn.addEventListener('click', () => this.processOrder('cash'));
    }
    
    this.setupFormValidation();
  }
  
  setupFormValidation() {
    const form = document.getElementById('checkout-form');
    if (!form) return;
    
    const inputs = form.querySelectorAll('input[required]');
    inputs.forEach(input => {
      input.addEventListener('blur', this.validateField);
      input.addEventListener('input', this.clearValidation);
    });
  }
  
  validateField(event) {
    const field = event.target;
    if (field.checkValidity()) {
      field.classList.remove('is-invalid');
      field.classList.add('is-valid');
    } else {
      field.classList.remove('is-valid');
      field.classList.add('is-invalid');
    }
  }
  
  clearValidation(event) {
    const field = event.target;
    field.classList.remove('is-valid', 'is-invalid');
  }
  
  getFormData() {
    const form = document.getElementById('checkout-form');
    if (!form) return null;
    
    const formData = new FormData(form);
    return {
      name: formData.get('name')?.trim() || '',
      email: formData.get('email')?.trim() || '',
      phone: formData.get('phone')?.trim() || '',
      address: formData.get('address')?.trim() || ''
    };
  }
  
  validateForm(data) {
    const errors = [];
    
    if (!data.name) errors.push('Name is required');
    if (!data.email) errors.push('Email is required');
    if (!data.phone) errors.push('Phone is required');
    if (!data.address) errors.push('Address is required');
    
    if (data.email && !this.isValidEmail(data.email)) {
      errors.push('Please enter a valid email address');
    }
    
    return errors;
  }
  
  isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }
  
  async processOrder(paymentMethod) {
    const formData = this.getFormData();
    if (!formData) return;
    
    const errors = this.validateForm(formData);
    if (errors.length > 0) {
      this.showValidationErrors(errors);
      return;
    }
    
    const endpoint = paymentMethod === 'paypal' ? '/api/order/paypal' : '/api/order/cash';
    const btn = document.getElementById(`pay-${paymentMethod}`);
    
    try {
      if (btn) {
        btn.disabled = true;
        this.setButtonLoading(btn, 'Processing...');
      }
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      
      if (data.ok) {
        this.showSuccessModal(data.order_id, data.wa_url);
      } else {
        this.showErrorAlert(data.error || `Failed to process ${paymentMethod} order`);
      }
    } catch (error) {
      console.error('Order error:', error);
      this.showErrorAlert('Network error. Please try again.');
    } finally {
      if (btn) {
        btn.disabled = false;
        this.resetButtonText(btn, paymentMethod === 'paypal' ? 'Pay with PayPal' : 'Pay with Cash');
      }
    }
  }
  
  setButtonLoading(button, text) {
    const spinner = '<span class="loading-spinner me-2"></span>';
    button.innerHTML = `${spinner}${text}`;
  }
  
  resetButtonText(button, text) {
    button.innerHTML = text;
  }
  
  showValidationErrors(errors) {
    const alertHtml = `
      <div class="alert alert-danger alert-dismissible fade show" role="alert">
        <i class="bi bi-exclamation-triangle-fill me-2"></i>
        <strong>Please fix the following errors:</strong>
        <ul class="mb-0 mt-2">
          ${errors.map(error => `<li>${error}</li>`).join('')}
        </ul>
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
      </div>
    `;
    
    const form = document.getElementById('checkout-form');
    const existingAlert = form.parentElement.querySelector('.alert');
    if (existingAlert) {
      existingAlert.remove();
    }
    
    form.insertAdjacentHTML('beforebegin', alertHtml);
  }
  
  showErrorAlert(message) {
    const alertHtml = `
      <div class="alert alert-danger alert-dismissible fade show" role="alert">
        <i class="bi bi-exclamation-triangle-fill me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
      </div>
    `;
    
    const form = document.getElementById('checkout-form');
    const existingAlert = form.parentElement.querySelector('.alert');
    if (existingAlert) {
      existingAlert.remove();
    }
    
    form.insertAdjacentHTML('beforebegin', alertHtml);
  }
  
  showSuccessModal(orderId, waUrl) {
    const modalHtml = `
      <div class="modal fade" id="successModal" tabindex="-1" aria-labelledby="successModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header bg-success text-white">
              <h5 class="modal-title" id="successModalLabel">
                <i class="bi bi-check-circle-fill me-2"></i>
                Order Placed Successfully!
              </h5>
            </div>
            <div class="modal-body text-center">
              <div class="mb-3">
                <i class="bi bi-bag-check text-success" style="font-size: 3rem;"></i>
              </div>
              <h6>Order #${orderId}</h6>
              <p class="text-muted">Your order has been placed successfully. You will be redirected shortly.</p>
              ${waUrl ? '<p><small class="text-muted">A WhatsApp message will open for order confirmation.</small></p>' : ''}
            </div>
            <div class="modal-footer justify-content-center">
              <button type="button" class="btn btn-success" onclick="window.location.href='/'">
                <i class="bi bi-house me-2"></i>
                Continue Shopping
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
    
    const existingModal = document.getElementById('successModal');
    if (existingModal) {
      existingModal.remove();
    }
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    const modal = new bootstrap.Modal(document.getElementById('successModal'));
    modal.show();
    
    if (waUrl) {
      setTimeout(() => {
        window.open(waUrl, '_blank');
      }, 1000);
    }
    
    setTimeout(() => {
      window.location.href = '/';
    }, 3000);
  }
}

// Professional Form Enhancement
class FormEnhancer {
  constructor() {
    this.init();
  }
  
  init() {
    document.addEventListener('submit', (e) => {
      const form = e.target.closest('form');
      if (form && !form.classList.contains('no-loading')) {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.dataset.originalText = submitBtn.textContent;
          this.setButtonLoading(submitBtn, 'Saving...');
        }
      }
    });
    
    document.addEventListener('input', (e) => {
      if (e.target.tagName === 'TEXTAREA') {
        this.autoResizeTextarea(e.target);
      }
    });
    
    this.initializeTooltips();
    this.initializePopovers();
  }
  
  setButtonLoading(button, text) {
    const spinner = '<span class="loading-spinner me-2"></span>';
    button.innerHTML = `${spinner}${text}`;
  }
  
  resetButtonText(button, text) {
    button.innerHTML = text;
  }
  
  autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
  }
  
  initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
  }
  
  initializePopovers() {
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
  }
}
