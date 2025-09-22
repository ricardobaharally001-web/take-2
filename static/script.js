// static/script.js

// Add to cart buttons (works on products list and detail)
document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".add-to-cart-btn");
  if (!btn) return;
  e.preventDefault();
  const productId = parseInt(btn.dataset.productId, 10);
  let qty = 1;
  if (btn.dataset.qtyEl) {
    const el = document.querySelector(btn.dataset.qtyEl);
    if (el && el.value) qty = Math.max(1, parseInt(el.value, 10));
  }
  const res = await fetch("/api/cart/add", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ product_id: productId, qty })
  });
  const data = await res.json();
  if (data.ok) {
    // Update any known cart count badges
    const badge1 = document.getElementById("nav-cart-count");
    const badgeMobile = document.getElementById("cart-count-mobile");
    const badgeDesktop = document.getElementById("cart-count-desktop");
    if (badge1) badge1.textContent = data.cart_count;
    [badgeMobile, badgeDesktop].forEach(el => {
      if (!el) return;
      el.textContent = data.cart_count;
      if (data.cart_count > 0) {
        el.classList.remove('d-none');
        el.style.display = 'flex';
      } else {
        el.classList.add('d-none');
      }
    });
    toast("Added to cart");
  } else {
    alert(data.error || "Unable to add to cart.");
  }
});

// Cart page: update qty & remove
document.addEventListener("change", async (e) => {
  const qtyInput = e.target.closest(".cart-qty");
  if (!qtyInput) return;
  const row = qtyInput.closest("tr");
  const pid = parseInt(row.dataset.productId, 10);
  const qty = Math.max(1, parseInt(qtyInput.value, 10));
  const res = await fetch("/api/cart/update", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ product_id: pid, qty })
  });
  const data = await res.json();
  if (data.ok) {
    // refresh totals visually (simple way: reload)
    window.location.reload();
  }
});

document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".remove-item");
  if (!btn) return;
  const row = btn.closest("tr");
  const pid = parseInt(row.dataset.productId, 10);
  const res = await fetch("/api/cart/remove", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ product_id: pid })
  });
  const data = await res.json();
  if (data.ok) {
    window.location.reload();
  }
});

// Simple toast helper
function toast(msg) {
  try {
    const t = document.createElement("div");
    t.className = "position-fixed bottom-0 start-50 translate-middle-x mb-4 p-3 bg-dark text-white rounded shadow";
    t.style.zIndex = 1080;
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 1800);
  } catch {}
}

// Checkout: PayPal Smart Buttons
document.addEventListener("DOMContentLoaded", () => {
  // Apply saved theme for dark mode
  try {
    const saved = localStorage.getItem('store-theme');
    const theme = (saved === 'dark') ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', theme);
    if (document.body) document.body.setAttribute('data-theme', theme);
  } catch {}

  // Dark mode toggle
  const toggle = document.getElementById('dark-toggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      if (document.body) document.body.setAttribute('data-theme', next);
      try { localStorage.setItem('store-theme', next); } catch {}
    });
  }

  const paypalContainer = document.getElementById("paypal-button-container");
  const form = document.getElementById("checkout-form");
  if (paypalContainer && window.paypal && form) {
    const totalUSD = window.__PAYPAL_TOTAL_USD__ || 1.00;

    paypal.Buttons({
      createOrder: function (data, actions) {
        // DEMO ONLY: create order for displayed USD amount
        return actions.order.create({
          purchase_units: [{ amount: { value: totalUSD.toFixed(2) } }]
        });
      },
      onApprove: async function (data, actions) {
        try {
          await actions.order.capture(); // simulate capture
          const payload = {
            name: form.elements["name"].value,
            email: form.elements["email"].value,
            phone: form.elements["phone"].value,
            address: form.elements["address"].value,
            paypal_order_id: data.orderID
          };
          const res = await fetch("/api/order/paypal", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
          });
          const out = await res.json();
          if (out.ok) {
            alert("Payment successful. Order #" + out.order_id + " placed!");
            window.location.href = "/";
          } else {
            alert(out.error || "Could not place order.");
          }
        } catch (err) {
          console.error(err);
          alert("Payment failed or canceled.");
        }
      }
    }).render("#paypal-button-container");
  }

  // Checkout: MMG "I paid" button
  const mmgBtn = document.getElementById("mmg-paid-btn");
  if (mmgBtn && form) {
    mmgBtn.addEventListener("click", async () => {
      const payload = {
        name: form.elements["name"].value,
        email: form.elements["email"].value,
        phone: form.elements["phone"].value,
        address: form.elements["address"].value
      };
      if (!payload.name || !payload.email || !payload.phone || !payload.address) {
        alert("Please fill out your name, email, phone, and address.");
        return;
      }
      const res = await fetch("/api/order/mmg", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
      });
      const out = await res.json();
      if (out.ok) {
        alert("Order placed as PENDING via MMG. Order #" + out.order_id + ". The store will verify your payment.");
        window.location.href = "/";
      } else {
        alert(out.error || "Could not place order.");
      }
    });
  }
});
