# -*- coding: utf-8 -*-
import requests


class Spree(object):

    def __init__(self, url, api_key):
        self.url = url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers['X-Spree-Token'] = api_key

    @property
    def product(self):
        return Product(connection=self)

    @property
    def order(self):
        return Order(connection=self)

    @property
    def stock_item(self):
        return StockItem(connection=self)

    @property
    def variant(self):
        return Variant(connection=self)


class Pagination(object):
    def __init__(self, data, items_attribute, resource, filters=None):
        self.data = data
        self.items = data[items_attribute]
        self.current_index = -1
        self.resource = resource
        self.filters = filters

    @property
    def count(self):
        return int(self.data['count'])

    @property
    def page(self):
        return int(self.data['current_page'])

    @property
    def pages(self):
        return int(self.data['pages'])

    @property
    def has_next(self):
        return self.pages > self.page

    def next_page(self):
        if self.has_next:
            return self.resource.find(
                page=self.page + 1, filters=self.filters)

    def __iter__(self):
        return self

    def __getitem__(self, index):
        return self.items[index]

    def __setitem__(self, index, value):
        self.items[index] = value

    def next(self):
        if self.current_index < self.count-1:
            self.current_index += 1
            return self.items[self.current_index]
        else:
            raise StopIteration()


class Resource(object):
    """
    A base class for all Resources to extend
    """

    def __init__(self, connection, per_page=25):
        self.connection = connection
        self.per_page = per_page

    @property
    def url(self):
        return self.connection.url + self.path

    def load_payload(self, data):
        return data

    def find(self, page=1, filters=None):
        """
        Find all records that respect given filters

        :param filters: Dictionary whose key-value pairs are in
        for of: {
            'q[name_of_parameter_identifier]': 'some-value',
        }
        Reference: https://github.com/ernie/ransack/wiki/Basic-Searching
        :return: Paginated list of response
        """
        params = filters or {}
        params.update({
            'page': page,
            'per_page': self.per_page,
        })
        response = self.connection.session.get(self.url, params=params).json()
        return Pagination(
            response,
            self.item_attribute,
            resource=self,
            filters=filters,
        )

    def get(self, id):
        "Fetch a record with given id"
        path = self.url + '/%s' % id
        return self.connection.session.get(path).json()

    def create(self, data):
        "create a record with the given data"
        payload = self.load_payload(data)
        return self.connection.session.post(self.url, data=payload).json()

    def update(self, id, data):
        "update the record with given data"
        path = self.url + '/%d' % id
        payload = self.load_payload(data)
        return self.connection.session.put(path, data=payload).json()

    def delete(self, id):
        "delete a given record"
        path = self.url + '/%d' % id
        return self.connection.session.delete(path).json()


class Product(Resource):
    """
    A product Resource class
    """

    path = '/products'
    item_attribute = 'products'

    def load_payload(self, data):
        payload = {
                'product[name]': data['name']
            }
        if 'price' in data:
            payload['product[price]'] = data['price']
        if 'shipping_category_id' in data:
            payload['product[shipping_category_id]'] = \
                data['shipping_category_id']
        if 'sku' in data:
            payload['product[sku]'] = data['sku']
        if 'description' in data:
            payload['product[description]'] = data['description']
        if 'display_price' in data:
            payload['product[display_price]'] = data['display_price']
        if 'available_on' in data:
            payload['product[available_on]'] = data['available_on']
        if 'meta_description' in data:
            payload['product[meta_description]'] = data['meta_description']
        if 'meta_keywords' in data:
            payload['product[meta_keywords]'] = data['meta_keywords']
        if 'weight' in data:
            payload['product[weight]'] = data['weight']
        if 'height' in data:
            payload['product[height]'] = data['height']
        if 'width' in data:
            payload['product[width]'] = data['width']
        if 'depth' in data:
            payload['product[depth]'] = data['depth']
        if 'cost_price' in data:
            payload['product[cost_price]'] = data['cost_price']

        return super(Product, self).load_payload(payload)


class Order(Resource):
    """
    An order Resource class
    """

    path = '/orders'
    item_attribute = 'orders'


class StockItem(Resource):
    """
    A stock item Resource class
    """

    path = '/stock_locations' + '/%d'
    item_attribute = 'stock_items'

    def append_path(self, stk_loc_id):
        return self.path % stk_loc_id + '/stock_items'

    def load_payload(self, data):
        payload = {}
        if 'count_on_hand' in data:
            payload['stock_item[count_on_hand]'] = \
                data['count_on_hand']
        if 'force' in data:
            payload['stock_item[force]'] = data['force']
        return super(StockItem, self).load_payload(payload)

    def find(self, stk_loc_id, *args, **kwargs):
        self.path = self.append_path(stk_loc_id)
        return super(StockItem, self).find(*args, **kwargs)

    def get(self, stk_loc_id, id):
        self.path = self.append_path(stk_loc_id)
        return super(StockItem, self).get(id)

    def update(self, stk_loc_id, stk_id, data):
        self.path = self.append_path(stk_loc_id)
        return super(StockItem, self).update(stk_id, data)

    def delete(self, stk_loc_id, stk_id):
        self.path = self.append_path(stk_loc_id)
        return super(StockItem, self).delete(stk_id)


class Variant(Resource):
    """
    A variant item Resource class
    """

    path = '/variants'
    item_attribute = 'variants'

    def find(self, permalink):
        self.path = '/products' + '/' + permalink + self.path
        return super(Variant, self).find()
