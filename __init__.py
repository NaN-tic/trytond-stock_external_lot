# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .stock import *


def register():
    Pool.register(
        Lot,
        Move,
        Period,
        PeriodCacheLotParty,
        module='stock_external_lot', type_='model')
