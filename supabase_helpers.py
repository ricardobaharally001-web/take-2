{% extends "base_store.html" %}
{% block content %}
<nav aria-label="breadcrumb">
    <ol class="breadcrumb">
        <li class="breadcrumb-item"><a href="{{ url_for('index') }}">Home</a></li>
        <li class="breadcrumb-item"><a href="{{ url_for('store.products') }}">Products</a></li>
        <li class="breadcrumb-item active">{{ product.name }}</li>
    </ol>
</nav>

<div class="row">
    <div class="col-md-6">
        <img src="{{ product.image }}" 
             alt="{{ product.name }}" 
             class="img-fluid rounded"
             onerror="this.onerror=null; this.src='https://via.placeholder.com/400x400?text=No+Image';">
    </div>
    <div class="col-md-6">
        <h1>{{ product.name }}</h1>
        {% if product.price is defined %}
            <p class="price-large">${{ '%.2f'|format(product.price|float) }}</p>
            {% set quantity = product.quantity if product.quantity is defined else 0 %}
            {% if quantity > 0 %}
                <p class="stock-indicator in-stock">
                    <i class="bi bi-check-circle"></i> In Stock ({{ quantity }} available)
                </p>
            {% else %}
                <p class="stock-indicator out-of-stock">
                    <i class="bi bi-x-circle"></i> Out of Stock
                </p>
            {% endif %}
        {% else %}
            <p class="text-muted lead">Contact for pricing</p>
        {% endif %}
        <p class="lead">{{ product.description }}</p>
        
        <div class="d-grid gap-2 d-md-block">
            {% if product.price is defined %}
                {% set quantity = product.quantity if product.quantity is defined else 0 %}
                {% if quantity > 0 %}
                    <button class="btn btn-primary btn-lg" onclick="addToCart('{{ product.id }}')">
                        <i class="bi bi-cart-plus me-2"></i>Add to Cart
                    </button>
                {% else %}
                    <button class="btn btn-secondary btn-lg" disabled>
                        <i class="bi bi-x-circle me-2"></i>Out of Stock
                    </button>
                {% endif %}
            {% else %}
                <button class="btn btn-secondary btn-lg" disabled>
                    <i class="bi bi-info-circle me-2"></i>Contact for Purchase
                </button>
            {% endif %}
            <a href="{{ url_for('store.products') }}" class="btn btn-outline-secondary btn-lg">
                <i class="bi bi-arrow-left me-2"></i>Continue Shopping
            </a>
        </div>
    </div>
</div>
{% endblock %}
