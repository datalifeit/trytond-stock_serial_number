#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.

from trytond.pool import Pool
from .stock import *


def register():
    Pool.register(
        Move,
        SplitMoveStart,
        module='stock_serial_number', type_='model')
    Pool.register(
        SplitMove,
        module='stock_serial_number', type_='wizard')
