// Dark mode toggle using localStorage
function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
}
(function(){
  const saved = localStorage.getItem('theme');
  if (saved) setTheme(saved);
  const darkBtn = document.getElementById('darkToggle');
  const darkBtnMobile = document.getElementById('darkToggleMobile');
  if (darkBtn) darkBtn.addEventListener('click', ()=>{
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    setTheme(current === 'light' ? 'dark' : 'light');
  });
  if (darkBtnMobile) darkBtnMobile.addEventListener('click', ()=>{
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    setTheme(current === 'light' ? 'dark' : 'light');
  });

  // Mobile offcanvas
  const menuButton = document.getElementById('menuButton');
  if (menuButton) {
    const offcanvasEl = document.getElementById('mobileMenu');
    if (offcanvasEl) {
      const oc = new bootstrap.Offcanvas(offcanvasEl);
      menuButton.addEventListener('click', ()=> oc.toggle());
    }
  }
})();

// Cart utilities (localStorage)
function getCart() {
  try { return JSON.parse(localStorage.getItem('cart') || '[]'); } catch(_) { return []; }
}
function saveCart(cart) {
  localStorage.setItem('cart', JSON.stringify(cart));
  updateCartCount();
}
function updateCartCount() {
  const cart = getCart();
  const count = cart.reduce((acc, item)=> acc + item.qty, 0);
  const el = document.getElementById('cartCount');
  if (el) el.textContent = count;
}
function addToCart(pid) {
  // lightweight: load products quickly from embedded dataset via fetch
  fetch('/static/products.json')
    .then(r=>r.json())
    .then(all=>{
      const p = all.find(x=>x.id===pid);
      if (!p) return alert('Product not found');
      const cart = getCart();
      const found = cart.find(x=>x.id===pid);
      if (found) found.qty += 1;
      else cart.push({id: p.id, name: p.name, price: p.price, image: p.image, qty: 1});
      saveCart(cart);
      alert('Added to cart');
    });
}
document.addEventListener('DOMContentLoaded', updateCartCount);

// Render cart page
function renderCart() {
  const container = document.getElementById('cartContainer');
  if (!container) return;
  const cart = getCart();
  if (cart.length === 0) {
    container.innerHTML = '<div class="alert alert-info text-center">Your cart is empty.</div>';
    return;
  }
  let html = '<div class="list-group">';
  let total = 0;
  cart.forEach((item, idx)=>{
    total += item.price * item.qty;
    html += `
      <div class="list-group-item d-flex gap-3 align-items-center">
        <img src="${item.image}" style="width:64px;height:64px;object-fit:cover;border-radius:8px;">
        <div class="flex-grow-1">
          <div class="d-flex justify-content-between">
            <strong>${item.name}</strong>
            <span>$${item.price.toFixed(2)}</span>
          </div>
          <div class="d-flex align-items-center gap-2 mt-1">
            <button class="btn btn-sm btn-outline-secondary" onclick="decQty(${idx})">-</button>
            <span>${item.qty}</span>
            <button class="btn btn-sm btn-outline-secondary" onclick="incQty(${idx})">+</button>
            <button class="btn btn-sm btn-danger ms-auto" onclick="removeItem(${idx})">Remove</button>
          </div>
        </div>
      </div>`;
  });
  html += `</div>
  <div class="text-end mt-3"><strong>Total: $${total.toFixed(2)}</strong></div>`;
  container.innerHTML = html;

  const btn = document.getElementById('checkoutBtn');
  if (btn) {
    btn.onclick = async ()=>{
      try {
        const res = await axios.post('/api/cart/checkout', {cart});
        alert(res.data.message || 'Order placed');
        localStorage.removeItem('cart');
        updateCartCount();
        renderCart();
      } catch (e) {
        alert('Checkout failed');
      }
    };
  }
}
function incQty(i){ const cart=getCart(); cart[i].qty++; saveCart(cart); renderCart(); }
function decQty(i){ const cart=getCart(); cart[i].qty=Math.max(1, cart[i].qty-1); saveCart(cart); renderCart(); }
function removeItem(i){ const cart=getCart(); cart.splice(i,1); saveCart(cart); renderCart(); }
document.addEventListener('DOMContentLoaded', renderCart);
