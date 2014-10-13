# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from collections import defaultdict

from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool, PoolMeta

__all__ = ['Move', 'Lot', 'Period', 'PeriodCacheLotParty', 'Inventory']
__metaclass__ = PoolMeta


class Lot:
    __name__ = 'stock.lot'
    party = fields.Many2One('party.party', 'Party', readonly=True)


class Move:
    __name__ = 'stock.move'

    @classmethod
    def __setup__(cls):
        super(Move, cls).__setup__()
        cls._error_messages.update({
                'diferent_lot_party': ('You can not use a lot "%s" from a '
                    'diferent party "%s" than the move "%s".'),
                })

    @classmethod
    def set_party_used(cls, moves, name, value):
        pool = Pool()
        Lot = pool.get('stock.lot')

        lots = []
        for move in moves:
            if move.lot and not move.lot.party:
                lots.append(move.lot)
                continue
        if lots:
            Lot.write(lots, {'party': value})
        super(Move, cls).set_party_used(moves, name, value)

    @classmethod
    def validate(cls, moves):
        super(Move, cls).validate(moves)
        for move in moves:
            move.check_lot_party()

    def check_lot_party(self):
        if (self.lot and self.lot.party and self.party_used and
                self.lot.party != self.party_used):
            self.raise_user_error('diferent_lot_party', (self.lot.rec_name,
                    self.lot.party.rec_name, self.party_used.rec_name))

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Lot = pool.get('stock.lot')
        for move_vals in vlist:
            party = move_vals.get('party_used', move_vals.get('party'))
            if move_vals.get('lot') and not party:
                lot = Lot(move_vals.get('lot'))
                if lot.party:
                    move_vals['party_used'] = lot.party.id
        return super(Move, cls).create(vlist)

    @classmethod
    def write(cls, *args):
        pool = Pool()
        Lot = pool.get('stock.lot')
        actions = iter(args)
        args = []
        for moves, values in zip(actions, actions):
            party = values.get('party_used', values.get('party'))
            if 'lot' in values and not party:
                if values['lot']:
                    lot = Lot(values.get('lot'))
                    if lot.party:
                        values['party_used'] = lot.party.id
                else:
                    values['party'] = None
            args.extend((moves, values))
        super(Move, cls).write(*args)


class Period:
    __name__ = 'stock.period'
    lot_party_caches = fields.One2Many('stock.period.cache.lot_party',
        'period', 'Party/Lot Caches', readonly=True)

    @classmethod
    def groupings(cls):
        return super(Period, cls).groupings() + [('product', 'lot', 'party')]

    @classmethod
    def get_cache(cls, grouping):
        pool = Pool()
        Cache = super(Period, cls).get_cache(grouping)
        if grouping == ('product', 'lot', 'party'):
            return pool.get('stock.period.cache.lot_party')
        return Cache


class PeriodCacheLotParty(ModelSQL, ModelView):
    '''
    Stock Period Cache per Lot and Party

    It is used to store cached computation of stock quantities per lot and
    party.
    '''
    __name__ = 'stock.period.cache.lot_party'
    period = fields.Many2One('stock.period', 'Period', required=True,
        readonly=True, select=True, ondelete='CASCADE')
    location = fields.Many2One('stock.location', 'Location', required=True,
        readonly=True, select=True, ondelete='CASCADE')
    product = fields.Many2One('product.product', 'Product', required=True,
        readonly=True, ondelete='CASCADE')
    lot = fields.Many2One('stock.lot', 'Lot', readonly=True,
        ondelete='CASCADE')
    party = fields.Many2One('party.party', 'Party', readonly=True,
        ondelete='CASCADE')
    internal_quantity = fields.Float('Internal Quantity', readonly=True)


class Inventory:
    __name__ = 'stock.inventory'

    @classmethod
    def grouping(cls):
        grouping = super(Inventory, cls).grouping()
        return grouping + ('lot', )
