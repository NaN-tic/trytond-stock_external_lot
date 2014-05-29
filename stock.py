#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta

__all__ = ['Move', 'Lot']
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
        for move in moves:
            move.check_lot_party()

    def check_lot_party(self):
        if self.lot and self.lot.party != self.party_used:
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
    def write(cls, moves, values):
        pool = Pool()
        Lot = pool.get('stock.lot')
        party = values.get('party_used', values.get('party'))
        if values.get('lot') and not party:
            lot = Lot(values.get('lot'))
            if lot.party:
                values['party_used'] = lot.party.id
        super(Move, cls).write(moves, values)
