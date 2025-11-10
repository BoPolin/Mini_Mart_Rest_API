from flask import jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from datetime import timedelta, datetime
from app import app,db
from models import Invoice, Product, InvoiceDetail, Category, User


@app.route('/reports/sales/daily', methods=['GET'])
@jwt_required()
def daily_sales_report():
    today = datetime.utcnow().date()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())

    invoices = Invoice.query.filter(
        Invoice.date_time.between(start, end),
        Invoice.status == 'completed'
    ).all()

    total_sales = sum(inv.total_amount for inv in invoices)

    return jsonify({
        'period': 'daily',
        'date': today.strftime('%Y-%m-%d'),
        'total_sales': total_sales,
        'total_invoices': len(invoices),
        'invoices': [{
            'id': inv.id,
            'total_amount': inv.total_amount,
            'time': inv.date_time.strftime('%I:%M %p')
        } for inv in invoices]
    })


@app.route('/reports/sales/weekly', methods=['GET'])
@jwt_required()
def weekly_sales_report():
    today = datetime.utcnow().date()
    start_week = today - timedelta(days=today.weekday())
    start = datetime.combine(start_week, datetime.min.time())
    end = datetime.utcnow()

    invoices = Invoice.query.filter(
        Invoice.date_time.between(start, end),
        Invoice.status == 'completed'
    ).all()

    total_sales = sum(inv.total_amount for inv in invoices)

    return jsonify({
        'period': 'weekly',
        'start_date': start_week.strftime('%Y-%m-%d'),
        'end_date': today.strftime('%Y-%m-%d'),
        'total_sales': total_sales,
        'total_invoices': len(invoices)
    })


@app.route('/reports/sales/monthly', methods=['GET'])
@jwt_required()
def monthly_sales_report():
    today = datetime.utcnow()
    start = datetime(today.year, today.month, 1)

    invoices = Invoice.query.filter(
        Invoice.date_time >= start,
        Invoice.status == 'completed'
    ).all()

    total_sales = sum(inv.total_amount for inv in invoices)

    return jsonify({
        'period': 'monthly',
        'month': today.strftime('%B %Y'),
        'total_sales': total_sales,
        'total_invoices': len(invoices)
    })


@app.route('/reports/sales/by-product', methods=['GET'])
@jwt_required()
def sales_by_product():
    results = db.session.query(
        Product.id,
        Product.name,
        func.sum(InvoiceDetail.qty).label('total_qty'),
        func.sum(InvoiceDetail.total).label('total_sales')
    ).join(InvoiceDetail).join(Invoice).filter(
        Invoice.status == 'completed'
    ).group_by(Product.id, Product.name).all()

    return jsonify([{
        'product_id': r[0],
        'product_name': r[1],
        'total_qty_sold': int(r[2]),
        'total_sales': float(r[3])
    } for r in results])


@app.route('/reports/sales/by-category', methods=['GET'])
@jwt_required()
def sales_by_category():
    results = db.session.query(
        Category.id,
        Category.name,
        func.sum(InvoiceDetail.total).label('total_sales')
    ).select_from(Category)\
     .join(Product, Product.category_id == Category.id)\
     .join(InvoiceDetail, InvoiceDetail.product_id == Product.id)\
     .join(Invoice, Invoice.id == InvoiceDetail.invoice_id)\
     .filter(Invoice.status == 'completed')\
     .group_by(Category.id, Category.name).all()

    return jsonify([{
        'category_id': r[0],
        'category_name': r[1],
        'total_sales': float(r[2])
    } for r in results])


@app.route('/reports/sales/by-user', methods=['GET'])
@jwt_required()
def sales_by_user():
    results = db.session.query(
        User.id,
        User.username,
        func.count(Invoice.id).label('total_invoices'),
        func.sum(Invoice.total_amount).label('total_sales')
    ).join(Invoice).filter(
        Invoice.status == 'completed'
    ).group_by(User.id, User.username).all()

    return jsonify([{
        'user_id': r[0],
        'username': r[1],
        'total_invoices': int(r[2]),
        'total_sales': float(r[3])
    } for r in results])