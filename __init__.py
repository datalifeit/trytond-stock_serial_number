# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

from trytond.pool import Pool
from . import stock


def register():
    Pool.register(
        stock.Template,
        stock.Move,
        stock.SplitMoveStart,
        module='stock_serial_number', type_='model')
    Pool.register(
        stock.SplitMove,
        module='stock_serial_number', type_='wizard')
