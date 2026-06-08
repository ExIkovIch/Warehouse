from flask import Flask, render_template, request, redirect, url_for
from models import (
    Warehouse, CommonItem, PerishableItem, FragileItem, OversizeItem, Shelf,
    Order, SupplyRequest
)
from datetime import date, timedelta
import json

app = Flask(__name__, static_folder='static')
STATE_FILE = 'warehouse_state.json'

def load_state():
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return Warehouse.from_dict(data)
    except FileNotFoundError:
        return None

def save_state(warehouse):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(warehouse.to_dict(), f, ensure_ascii=False, indent=2)


loaded_wh = load_state()
if loaded_wh:
    wh = loaded_wh
else:
    wh = Warehouse("Центральный склад", balance=1000000)
    wh.add_shelf(Shelf("Стеллаж №1", "common", capacity=1000))
    wh.add_shelf(Shelf("Стеллаж №2", "common", capacity=1000))
    wh.add_shelf(Shelf("Стеллаж №3", "common", capacity=1000))
    wh.add_shelf(Shelf("Холодильник №1", "perishable", capacity=500))
    wh.add_shelf(Shelf("Холодильник №2", "perishable", capacity=500))
    wh.add_shelf(Shelf("Холодильник №3", "perishable", capacity=1000))
    wh.add_shelf(Shelf("Стеллаж для хрупких товаров №1", "fragile", capacity=500))
    wh.add_shelf(Shelf("Стеллаж для хрупких товаров №2", "fragile", capacity=500))
    wh.add_shelf(Shelf("Стеллаж для хрупких товаров №3", "fragile", capacity=500))
    wh.add_shelf(Shelf("Стеллаж для хрупких товаров №4", "fragile", capacity=500))
    wh.add_shelf(Shelf("Стеллаж для хрупких товаров №5", "fragile", capacity=500))
    wh.add_shelf(Shelf("Крупный стеллаж №1", "oversize", capacity=2500))
    wh.add_shelf(Shelf("Крупный стеллаж №2", "oversize", capacity=2500))
    wh.add_shelf(Shelf("Ангар", "oversize", capacity=50000))

    save_state(wh)


@app.route('/')
def home():
    return redirect(url_for('warehouse'))

@app.route('/supplier')
def supplier():
    supply_requests = wh.get_supply_requests()
    return render_template('supplier.html', supply_requests=supply_requests)

@app.route('/process_supply', methods=['POST'])
def process_supply():
    req_index = int(request.form['req_index'])
    action = request.form['action']
    supplier_company = request.form.get('supplier_company', '')
    wh.process_supply_request(req_index, action, supplier_company)
    save_state(wh)
    return redirect(url_for('supplier'))

@app.route('/warehouse')
def warehouse():
    shelves_data = []
    for shelf in wh.shelves:
        items_list = []
        for item, qty in shelf.get_items().items():
            items_list.append({
                'name': item.name,
                'qty': qty,
                'unit': item.unit,
                'storage_units': item.storage_units,
                'is_expired': item.is_expired() if hasattr(item, 'is_expired') else False,
                'expiration_date': str(item.expiration_date) if hasattr(item, 'expiration_date') and item.expiration_date else None
            })
        shelves_data.append({
            'name': shelf.name,
            'category': shelf.category,
            'capacity': shelf.capacity,
            'used_units': shelf.used_units,
            'items': items_list
        })
    shelves_json = json.dumps(shelves_data, ensure_ascii=False)

    orders = wh.get_orders()
    supply_requests = wh.get_supply_requests()

    total_buy_cost = 0.0
    total_sell_cost = 0.0
    total_units = 0

    for shelf in wh.shelves:
        for item, qty in shelf.get_items().items():
            total_buy_cost += item.buy_price * qty
            total_sell_cost += item.sell_price * qty
            total_units += qty

    unique_items = len(wh.total_items())
    if wh.shelves:
        ratios = []
        for s in wh.shelves:
            if s.capacity > 0:
                ratios.append(s.used_units / s.capacity)
            else:
                ratios.append(0.0)
        fill_percent = (sum(ratios) / len(ratios)) * 100
    else:
        fill_percent = 0.0

    orders_total = len(wh.orders)
    orders_done = sum(1 for o in wh.orders if o.status == 'выполнен')
    orders_canceled = sum(1 for o in wh.orders if o.status == 'отменён')
    orders_income = sum(o.total for o in wh.orders if o.status == 'выполнен')

    supplies_total = len(wh.supply_requests)
    supplies_done = sum(1 for r in wh.supply_requests if r.status == 'выполнен')
    supplies_canceled = sum(1 for r in wh.supply_requests if r.status == 'отменён')
    supplies_expense = sum(r.total for r in wh.supply_requests if r.status == 'выполнен')

    stats = {
        'balance': wh.balance,
        'total_buy_cost': total_buy_cost,
        'total_sell_cost': total_sell_cost,
        'expected_profit': total_sell_cost - total_buy_cost,
        'total_units': total_units,
        'unique_items': unique_items,
        'fill_percent': round(fill_percent, 1),
        'orders_total': orders_total,
        'orders_done': orders_done,
        'orders_canceled': orders_canceled,
        'orders_income': orders_income,
        'supplies_total': supplies_total,
        'supplies_done': supplies_done,
        'supplies_canceled': supplies_canceled,
        'supplies_expense': supplies_expense,
    }

    advance_message = request.args.get('msg', '')
    return render_template('warehouse.html', wh=wh, shelves_json=shelves_json,
                           orders=orders, supply_requests=supply_requests,
                           stats=stats, advance_message=advance_message)

@app.route('/buy_shelf', methods=['POST'])
def buy_shelf():
    name = request.form['shelf_name']
    category = request.form['shelf_category']
    capacity = int(request.form['shelf_capacity'])
    wh.buy_shelf(name, category, capacity)
    save_state(wh)
    return redirect(url_for('warehouse'))

@app.route('/customer', methods=['GET', 'POST'])
def customer():
    items_available = wh.total_items()
    items_list = []
    for item, qty in items_available.items():
        items_list.append({
            'name': item.name,
            'unit': item.unit,
            'sell_price': float(item.sell_price),
            'available': qty
        })

    if request.method == 'POST':
        company = request.form['company']
        item_name = request.form['item_name']
        quantity = int(request.form['quantity'])
        price_per_unit = float(request.form['price_per_unit'])
        if quantity <= 0 or price_per_unit <= 0:
            return "<h2>Ошибка: количество и цена должны быть положительными.</h2><a href='/customer'>Назад</a>"

        order = Order(
            company=company,
            item_name=item_name,
            unit=request.form['unit'],
            quantity=quantity,
            price_per_unit=price_per_unit
        )
        wh.add_order(order)
        save_state(wh)
        return redirect(url_for('warehouse'))

    return render_template('customer.html', items=items_list)

@app.route('/process_order', methods=['POST'])
def process_order():
    order_index = int(request.form['order_index'])
    action = request.form['action']
    wh.process_order(order_index, action)
    save_state(wh)
    return redirect(url_for('warehouse'))

@app.route('/submit_supply_request', methods=['POST'])
def submit_supply_request():
    item_name = request.form['item_name']
    unit = request.form['unit']
    quantity = int(request.form['quantity'])
    buy_price = float(request.form['buy_price'])
    item_type = request.form['item_type']
    storage_units = int(request.form.get('storage_units', 1))
    exp_date_str = request.form.get('expiration_date', '')
    expiration_date = None
    if item_type == 'perishable':
        if not exp_date_str:
            return "<h2>Ошибка: для скоропортящегося товара необходимо указать срок годности.</h2><a href='/warehouse'>Назад</a>"
        expiration_date = date.fromisoformat(exp_date_str)

    if quantity <= 0 or buy_price < 0 or storage_units < 1:
        return "<h2>Ошибка: неверные параметры.</h2><a href='/warehouse'>Назад</a>"

    req = SupplyRequest(
        item_name, unit, quantity, buy_price, item_type,
        storage_units=storage_units,
        expiration_date=expiration_date
    )
    wh.add_supply_request(req)
    save_state(wh)
    return redirect(url_for('warehouse'))

@app.route('/advance_day', methods=['POST'])
def advance_day():
    wh.current_date = wh.current_date + timedelta(days=1)
    spoiled = wh.advance_day(current_date=wh.current_date)
    save_state(wh)

    if spoiled:
        msgs = [f"{name} (срок {exp}): списано {qty} шт." for name, (exp, qty) in spoiled.items()]
        full_msg = "; ".join(msgs)
    else:
        full_msg = "Просроченных товаров нет."
    return redirect(url_for('warehouse') + f'?msg={full_msg}')

if __name__ == '__main__':
    app.run(debug=True)