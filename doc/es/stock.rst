#:inside:stock/stock:section:split_moves#

Si introducimos un número en el campo |start_lot| se crearan un lote para cada
uno de las divisiones comenzando a partir del número introducido. Además,
podemos utilizar el campo |end_lot| para límitar el último lote que se va
a crear.

En el campo |lots| podemos especificar lotes ya existentes en el sistema y
utilizar esos lotes para las divisiones.

.. |lots| field:: stock.move.split.start/lots
.. |start_lot| field:: stock.move.split.start/start_lot
.. |end_lot| field:: stock.move.split.start/end_lot
