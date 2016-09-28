# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import re
from itertools import izip
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction

__all__ = ['Template', 'Move', 'SplitMoveStart', 'SplitMove']

NUMBER_REGEXP = re.compile("(\d+)")


class Template:
    __name__ = 'product.template'
    __metaclass__ = PoolMeta

    serial_number = fields.Boolean('Serial Number',
        states={
            'invisible': ~Eval('type').in_(['goods', 'assets']),
            },
        depends=['type'], help='If marked it won\'t be allowed to move this '
        'product in quantities diferent than 1.')

    @classmethod
    def __setup__(cls):
        super(Template, cls).__setup__()
        cls._error_messages.update({
                'change_serial_number': ('You cannot change the serial number '
                    'for a product which is associated to stock moves.'),
                })
        cls._modify_no_move.append(
            ('serial_number', 'change_serial_number'),
            )


class Move:
    __name__ = 'stock.move'
    __metaclass__ = PoolMeta

    @classmethod
    def __setup__(cls):
        super(Move, cls).__setup__()
        cls._error_messages.update({
            'no_numbers': ('No numbers found in string "%s".'),
            'serial_number': ('Move "%(move)s" can not be done as its product '
                    '"%(product)s" is marked as serial number and its quantity'
                    ' is different than 1.'),
            })

    @classmethod
    def do(cls, moves):
        for move in moves:
            # in case that remove inventory move, the outgoing move is 0.0
            if move.quantity == 0.0:
                continue
            if move.product.serial_number and move.quantity != 1.0:
                cls.raise_user_error('serial_number', {
                        'move': move.rec_name,
                        'product': move.product.rec_name,
                        })
        super(Move, cls).do(moves)

    def get_lot_range(self, start_lot, end_lot):
        " Return a lot range from start_lot to end_lot"
        def search_number(string):
            r = NUMBER_REGEXP.search(string)
            groups = r.groups()
            if not groups:
                self.raise_user_error('no_numbers', string)
            value, = groups
            return int(value)
        start = search_number(start_lot)
        prefix = ''
        index = start_lot.find(str(start))
        if index > 0:
            prefix = start_lot[:index]
        return [prefix + str(n) for n in range(start,
                search_number(end_lot) + 1)]

    def split_by_lot(self, quantity, uom, count=None, lots=None,
            start_lot=None, end_lot=None):
        """ Split moves by lots:
            * If lots is especified creates a move of quantity foreach lot
            * If start_lot and end_lot are specified create all the lots
              in range between start_lot and end_lot and uses the resulting
              lots as lots parameter
        """
        pool = Pool()
        Lot = pool.get('stock.lot')
        if not lots and start_lot and end_lot:
            to_create = []
            lots = []
            for number in self.get_lot_range(start_lot, end_lot):
                current_lots = Lot.search([
                        ('product', '=', self.product),
                        ('number', '=', number),
                        ], limit=1)
                if current_lots:
                    lots.append(current_lots[0])
                    continue
                to_create.append({
                        'product': self.product,
                        'number': number,
                        })
            if to_create:
                lots += Lot.create(to_create)
        count = count or len(lots)
        moves = self.split(quantity, uom, count)
        #Last move must be without lot
        if count < self.quantity / quantity:
            lots.append(None)
        for lot, move in izip(lots, moves):
            move.lot = lot
            move.save()
        return moves


class SplitMoveStart:
    __name__ = 'stock.move.split.start'
    __metaclass__ = PoolMeta

    product = fields.Many2One('product.product', 'Product', readonly=True)
    lots = fields.Many2Many('stock.lot', None, None, 'Lot', domain=[
            ('product', '=', Eval('product')),
            ], depends=['product'])
    start_lot = fields.Char('Start Lot')
    end_lot = fields.Char('End Lot')


class SplitMove:
    __name__ = 'stock.move.split'
    __metaclass__ = PoolMeta

    def default_start(self, fields):
        pool = Pool()
        Move = pool.get('stock.move')
        move = Move(Transaction().context['active_id'])
        default = super(SplitMove, self).default_start(fields)
        default['quantity'] = 1
        default['product'] = move.product.id
        return default

    def transition_split(self):
        pool = Pool()
        Move = pool.get('stock.move')
        move = Move(Transaction().context['active_id'])
        lots = None
        if hasattr(self.start, 'lots'):
            lots = self.start.lots
        move.split_by_lot(self.start.quantity, self.start.uom,
            count=self.start.count, lots=lots,
            start_lot=self.start.start_lot,
            end_lot=self.start.end_lot)
        return 'end'
