from datetime import date, timedelta

class BaseItem:
    def __init__(self, name: str, buy_price: float, sell_price: float,
                 quantity: int, unit: str, storage_units: int):
        if not unit:
            raise ValueError("Единица измерения обязательна")
        if storage_units < 1:
            raise ValueError("Количество занимаемых мест должно быть >= 1")
        self.name = name
        self.buy_price = buy_price
        self.sell_price = sell_price
        self._quantity = None
        self.quantity = quantity
        self.unit = unit
        self.storage_units = storage_units

    @property
    def quantity(self):
        return self._quantity
    @quantity.setter
    def quantity(self, value):
        if value < 0:
            raise ValueError('Количество не может быть отрицательным!')
        self._quantity = value

    def to_dict(self):
        data = {
            'type': 'common',
            'name': self.name,
            'buy_price': self.buy_price,
            'sell_price': self.sell_price,
            'quantity': self.quantity,
            'unit': self.unit,
            'storage_units': self.storage_units
        }
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data['name'],
            buy_price=data['buy_price'],
            sell_price=data['sell_price'],
            quantity=data['quantity'],
            unit=data['unit'],
            storage_units=data['storage_units']
        )

    def __str__(self):
        return f'{self.name}: {self.quantity} {self.unit}'

    def __eq__(self, other):
        if not isinstance(other, BaseItem):
            return False
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)


class CommonItem(BaseItem):
    def __init__(self, name: str, buy_price: float, sell_price: float,
                 quantity: int, unit: str, storage_units: int):
        super().__init__(name, buy_price, sell_price, quantity, unit, storage_units)

    def to_dict(self):
        data = super().to_dict()
        data['type'] = 'common'
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data['name'],
            buy_price=data['buy_price'],
            sell_price=data['sell_price'],
            quantity=data['quantity'],
            unit=data['unit'],
            storage_units=data['storage_units']
        )

    def storage_category(self):
        return "common"


class PerishableItem(BaseItem):
    def __init__(self, name: str, buy_price: float, sell_price: float,
                 quantity: int, unit: str, storage_units: int, expiration_date: date):
        super().__init__(name, buy_price, sell_price, quantity, unit, storage_units)
        self.expiration_date = expiration_date

    def to_dict(self):
        data = super().to_dict()
        data['type'] = 'perishable'
        data['expiration_date'] = str(self.expiration_date)
        return data

    @classmethod
    def from_dict(cls, data):
        exp_date = date.fromisoformat(data['expiration_date'])
        return cls(
            name=data['name'],
            buy_price=data['buy_price'],
            sell_price=data['sell_price'],
            quantity=data['quantity'],
            unit=data['unit'],
            storage_units=data['storage_units'],
            expiration_date=exp_date
        )

    def storage_category(self):
        return "perishable"

    def is_expired(self, current_date=None):
        if current_date is None:
            current_date = date.today()
        return current_date > self.expiration_date

    def days_until_expiry(self, current_date=None):
        if current_date is None:
            current_date = date.today()
        return (self.expiration_date - current_date).days

    def __str__(self):
        base = super().__str__()
        status = "Просрочен" if self.is_expired() else "Годен"
        return f"{base} | Срок: {self.expiration_date} ({status})"

    def __eq__(self, other):
        if not isinstance(other, PerishableItem):
            return False
        return self.name == other.name and self.expiration_date == other.expiration_date

    def __hash__(self):
        return hash((self.name, self.expiration_date))


class FragileItem(BaseItem):
    def __init__(self, name: str, buy_price: float, sell_price: float,
                 quantity: int, unit: str, storage_units: int):
        super().__init__(name, buy_price, sell_price, quantity, unit, int(storage_units*2))

    def to_dict(self):
        data = super().to_dict()
        data['type'] = 'fragile'
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data['name'],
            buy_price=data['buy_price'],
            sell_price=data['sell_price'],
            quantity=data['quantity'],
            unit=data['unit'],
            storage_units=data['storage_units'] / 2
        )

    def storage_category(self):
        return "fragile"

    def __str__(self):
        return f"{super().__str__()} [fragile]"


class OversizeItem(BaseItem):
    def __init__(self, name: str, buy_price: float, sell_price: float,
                 quantity: int, unit: str, storage_units: int):
        super().__init__(name, buy_price, sell_price, quantity, unit, storage_units)

    def to_dict(self):
        data = super().to_dict()
        data['type'] = 'oversize'
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data['name'],
            buy_price=data['buy_price'],
            sell_price=data['sell_price'],
            quantity=data['quantity'],
            unit=data['unit'],
            storage_units=data['storage_units']
        )

    def storage_category(self):
        return "oversize"

    def __str__(self):
        return f"{super().__str__()} | Габариты: {self.storage_units} усл. мест [oversize]"


class Order:
    def __init__(self, company, item_name, unit, quantity, price_per_unit, status="новый"):
        self.company = company
        self.item_name = item_name
        self.unit = unit
        self.quantity = quantity
        self.price_per_unit = float(price_per_unit)
        self.total = self.quantity * self.price_per_unit
        self.status = status
        self.created_at = date.today().isoformat()

    def to_dict(self):
        return {
            'company': self.company,
            'item_name': self.item_name,
            'unit': self.unit,
            'quantity': self.quantity,
            'price_per_unit': self.price_per_unit,
            'total': self.total,
            'status': self.status,
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data):
        order = cls(
            company=data['company'],
            item_name=data['item_name'],
            unit=data['unit'],
            quantity=data['quantity'],
            price_per_unit=data['price_per_unit'],
            status=data.get('status', 'новый')
        )
        order.total = data.get('total', order.quantity * order.price_per_unit)
        order.created_at = data.get('created_at', date.today().isoformat())
        return order


class SupplyRequest:
    def __init__(self, item_name, unit, quantity, buy_price_per_unit, item_type,
                 storage_units=1, expiration_date=None, status="новый"):
        self.item_name = item_name
        self.unit = unit
        self.quantity = quantity
        self.buy_price_per_unit = float(buy_price_per_unit)
        self.total = self.quantity * self.buy_price_per_unit
        self.item_type = item_type
        self.storage_units = storage_units
        self.expiration_date = expiration_date
        self.status = status
        self.created_at = date.today().isoformat()
        self.supplier_company = ""

    def to_dict(self):
        return {
            'item_name': self.item_name,
            'unit': self.unit,
            'quantity': self.quantity,
            'buy_price_per_unit': self.buy_price_per_unit,
            'total': self.total,
            'item_type': self.item_type,
            'storage_units': self.storage_units,
            'expiration_date': str(self.expiration_date) if self.expiration_date else None,
            'status': self.status,
            'created_at': self.created_at,
            'supplier_company': self.supplier_company
        }

    @classmethod
    def from_dict(cls, data):
        exp = data.get('expiration_date')
        if exp:
            exp = date.fromisoformat(exp)
        req = cls(
            item_name=data['item_name'],
            unit=data['unit'],
            quantity=data['quantity'],
            buy_price_per_unit=data['buy_price_per_unit'],
            item_type=data.get('item_type', 'common'),
            storage_units=data.get('storage_units', 1),
            expiration_date=exp,
            status=data.get('status', 'новый')
        )
        req.total = data.get('total', req.quantity * req.buy_price_per_unit)
        req.created_at = data.get('created_at', date.today().isoformat())
        req.supplier_company = data.get('supplier_company', '')
        return req


class Shelf:
    def __init__(self, name: str, category: str, capacity: int):
        self.name = name
        self.category = category
        self.capacity = capacity
        self._used_units = 0
        self._items = {}

    @property
    def used_units(self):
        return self._used_units

    @property
    def free_units(self):
        return self.capacity - self._used_units

    def can_store(self, item: 'BaseItem', quantity: int = 1):
        if item.storage_category() != self.category:
            return False
        required = item.storage_units * quantity
        return self.free_units >= required

    def add_item(self, item: 'BaseItem', quantity: int = 1):
        if not self.can_store(item, quantity):
            raise ValueError(f"Невозможно разместить '{item.name}' на полке '{self.name}'")
        self._items[item] = self._items.get(item, 0) + quantity
        self._used_units += item.storage_units * quantity

    def remove_item(self, item: 'BaseItem', quantity: int = 1):
        if self._items.get(item, 0) < quantity:
            raise ValueError(f"На полке '{self.name}' недостаточно товара '{item.name}'")
        self._items[item] -= quantity
        if self._items[item] == 0:
            del self._items[item]
        self._used_units -= item.storage_units * quantity

    def get_items(self):
        return dict(self._items)

    def to_dict(self):
        items = {}
        for item, quantity in self._items.items():
            if isinstance(item, PerishableItem):
                key = f"{item.name}|{item.expiration_date.isoformat()}"
            else:
                key = item.name
            items[key] = {
                'item': item.to_dict(),
                'quantity': quantity
            }
        return {
            'name': self.name,
            'category': self.category,
            'capacity': self.capacity,
            'items': items
        }

    @classmethod
    def from_dict(cls, data, warehouse=None):
        shelf = cls(
            name=data['name'],
            category=data['category'],
            capacity=data['capacity']
        )
        for key, entry in data.get('items', {}).items():
            item_data = entry['item']
            quantity = entry['quantity']
            item_type = item_data['type']
            if item_type == 'common':
                item = CommonItem.from_dict(item_data)
            elif item_type == 'perishable':
                item = PerishableItem.from_dict(item_data)
                if '|' in key:
                    _, date_str = key.split('|', 1)
                    item.expiration_date = date.fromisoformat(date_str)
            elif item_type == 'fragile':
                item = FragileItem.from_dict(item_data)
            elif item_type == 'oversize':
                item = OversizeItem.from_dict(item_data)
            else:
                raise ValueError(f"Неизвестный тип товара: {item_type}")
            shelf._items[item] = shelf._items.get(item, 0) + quantity
            shelf._used_units += item.storage_units * quantity
        return shelf

    def __str__(self):
        return (f"Полка '{self.name}' [{self.category}]"
                f"{self._used_units}/{self.capacity} усл. мест"
                f"({len(self._items)} поз.)")

class Warehouse:
    def __init__(self, name: str, balance: float = 1000000):
        self.name = name
        self.shelves = []
        self.orders = []
        self.supply_requests = []
        self.current_date = date.today()
        self.balance = balance

    def add_shelf(self, shelf: Shelf):
        self.shelves.append(shelf)

    def store_item(self, item: 'BaseItem', quantity: int = 1):
        suitable_shelves = [s for s in self.shelves if s.can_store(item, 1)]
        if not suitable_shelves:
            return False

        suitable_shelves.sort(key=lambda s: s.free_units, reverse=True)
        total_possible = 0
        for shelf in suitable_shelves:
            total_possible += shelf.free_units // item.storage_units
            if total_possible >= quantity:
                break

        if total_possible < quantity:
            return False

        remaining = quantity
        for shelf in suitable_shelves:
            if remaining <= 0:
                break
            max_by_units = shelf.free_units // item.storage_units
            take = min(remaining, max_by_units)
            if take > 0:
                shelf.add_item(item, take)
                remaining -= take

        return True

    def remove_item(self, item: 'BaseItem', quantity: int = 1):
        needed = quantity
        if isinstance(item, PerishableItem):
            target_item = self._find_best_perishable(item.name)
            if not target_item:
                return False
            total_available = sum(
                shelf.get_items().get(target_item, 0)
                for shelf in self.shelves
            )
            if total_available < needed:
                return False
            for shelf in self.shelves:
                if shelf.get_items().get(target_item, 0) > 0:
                    take = min(needed, shelf.get_items()[target_item])
                    shelf.remove_item(target_item, take)
                    needed -= take
                    if needed == 0:
                        return True
            return False
        else:
            total_available = sum(
                shelf.get_items().get(item, 0)
                for shelf in self.shelves
            )
            if total_available < needed:
                return False
            for shelf in self.shelves:
                if item in shelf.get_items():
                    available_on_shelf = shelf.get_items()[item]
                    if available_on_shelf <= 0:
                        continue
                    take = min(needed, available_on_shelf)
                    shelf.remove_item(item, take)
                    needed -= take
                    if needed == 0:
                        return True
            return False

    def total_items(self):
        totals = {}
        for shelf in self.shelves:
            for item, quantity in shelf.get_items().items():
                totals[item] = totals.get(item, 0) + quantity
        return totals

    def to_dict(self):
        return {
            'name': self.name,
            'current_date': str(self.current_date),
            'balance': self.balance,
            'shelves': [shelf.to_dict() for shelf in self.shelves],
            'orders': [order.to_dict() for order in self.orders],
            'supply_requests': [req.to_dict() for req in self.supply_requests]
        }

    @classmethod
    def from_dict(cls, data):
        wh = cls(
            name=data['name'],
            balance=data.get('balance', 1000000)
        )
        wh.current_date = date.fromisoformat(data.get('current_date', str(date.today())))
        for shelf_data in data.get('shelves', []):
            shelf = Shelf.from_dict(shelf_data)
            wh.add_shelf(shelf)
        for order_data in data.get('orders', []):
            wh.orders.append(Order.from_dict(order_data))
        for req_data in data.get('supply_requests', []):
            wh.supply_requests.append(SupplyRequest.from_dict(req_data))
        return wh

    def add_order(self, order: Order):
        self.orders.append(order)

    def get_orders(self):
        return self.orders

    def process_order(self, order_index, action):
        if order_index < 0 or order_index >= len(self.orders):
            return False
        order = self.orders[order_index]
        if action == 'выполнить':
            if order.status == 'отменён':
                return False
            if order.status == 'выполнен':
                return False
            target_item = None
            for item, quantity in self.total_items().items():
                if item.name == order.item_name:
                    target_item = item
                    break
            if not target_item:
                return False
            if self.remove_item(target_item, order.quantity):
                order.status = 'выполнен'
                self.balance += order.total
                return True
            else:
                return False
        elif action == 'отменить':
            if order.status == 'выполнен':
                return False
            order.status = 'отменён'
            return True
        else:
            return False

    def add_supply_request(self, request):
        self.supply_requests.append(request)

    def get_supply_requests(self):
        return self.supply_requests

    def process_supply_request(self, request_index, action, supplier_company=None):
        if request_index < 0 or request_index >= len(self.supply_requests):
            return False, "Заявка не найдена"
        req = self.supply_requests[request_index]

        if action == 'выполнить':
            if req.status == 'отменён':
                return False
            if req.status == 'выполнен':
                return False
            if not supplier_company:
                return False
            req.supplier_company = supplier_company

            if self.balance < req.total:
                return False

            sell_price = req.buy_price_per_unit * 1.5
            storage = req.storage_units
            exp_date = req.expiration_date

            if req.item_type == 'common':
                new_item = CommonItem(
                    req.item_name, req.buy_price_per_unit, sell_price,
                    req.quantity, req.unit, storage_units=storage
                )
            elif req.item_type == 'perishable':
                if not exp_date:
                    exp_date = self.current_date + timedelta(days=7)
                new_item = PerishableItem(
                    req.item_name, req.buy_price_per_unit, sell_price,
                    req.quantity, req.unit, storage_units=storage,
                    expiration_date=exp_date
                )
            elif req.item_type == 'fragile':
                new_item = FragileItem(
                    req.item_name, req.buy_price_per_unit, sell_price,
                    req.quantity, req.unit, storage_units=storage
                )
            elif req.item_type == 'oversize':
                new_item = OversizeItem(
                    req.item_name, req.buy_price_per_unit, sell_price,
                    req.quantity, req.unit, storage_units=storage
                )

            if self.store_item(new_item, req.quantity):
                self.balance -= req.total
                req.status = 'выполнен'
                return True
            else:
                return False

        elif action == 'отменить':
            if req.status == 'выполнен':
                return False
            req.status = 'отменён'
            return True

        else:
            return False

    def _find_best_perishable(self, item_name):
        best = None
        best_date = None
        for shelf in self.shelves:
            for item, qty in shelf.get_items().items():
                if isinstance(item, PerishableItem) and item.name == item_name and qty > 0:
                    if best is None or item.expiration_date < best_date:
                        best = item
                        best_date = item.expiration_date
        return best

    def advance_day(self, current_date=None):
        if current_date is None:
            current_date = self.current_date
        spoiled = {}
        for shelf in self.shelves:
            to_remove = []
            for item, qty in shelf.get_items().items():
                if isinstance(item, PerishableItem) and item.is_expired(current_date):
                    to_remove.append((item, qty))
            for item, qty in to_remove:
                shelf._items.pop(item, None)
                shelf._used_units -= item.storage_units * qty
                spoiled[item.name] = (item.expiration_date, qty)
        return spoiled

    def buy_shelf(self, name, category, capacity):
        cost = capacity * 25
        if cost <= 0:
            return False
        if self.balance < cost:
            return False
        new_shelf = Shelf(name, category, capacity)
        self.add_shelf(new_shelf)
        self.balance -= cost
        return True

    def __str__(self):
        header = f"Склад '{self.name}' — полок: {len(self.shelves)}"
        shelf_lines = "\n".join(str(s) for s in self.shelves)
        return f"{header}\n{shelf_lines}"