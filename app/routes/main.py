"""Main / dashboard routes."""
import json
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required

from app.models import db, Product, Category, StockMovement, Budget

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def dashboard():
    total_products = Product.query.filter_by(is_active=True).count()
    total_categories = Category.query.count()
    low_stock_products = Product.query.filter(
        Product.stock <= Product.min_stock,
        Product.is_active == True
    ).all()
    total_stock_value = db.session.query(
        db.func.sum(Product.stock * Product.cost)
    ).filter(Product.is_active == True).scalar() or 0

    recent_movements = StockMovement.query.order_by(
        StockMovement.created_at.desc()
    ).limit(8).all()
    recent_budgets = Budget.query.order_by(Budget.created_at.desc()).limit(5).all()

    categories = Category.query.all()
    cat_data = [
        {'name': c.name, 'stock': sum(p.stock for p in c.products if p.is_active), 'color': c.color}
        for c in categories
    ]

    return render_template('dashboard.html',
        total_products=total_products,
        total_categories=total_categories,
        low_stock_products=low_stock_products,
        total_stock_value=total_stock_value,
        recent_movements=recent_movements,
        recent_budgets=recent_budgets,
        cat_data=json.dumps(cat_data)
    )


@main_bp.route('/api/products/search')
@login_required
def api_search_products():
    q = request.args.get('q', '')
    exact = Product.query.filter(Product.sku == q, Product.is_active == True).first()
    if exact:
        products = [exact]
    else:
        products = Product.query.filter(
            Product.name.ilike(f'%{q}%'), Product.is_active == True
        ).limit(10).all()
    return jsonify([{
        'id': p.id, 'name': p.name, 'price': p.price,
        'stock': p.stock, 'unit': p.unit, 'sku': p.sku
    } for p in products])
