#    EXAMPLE
```
>>> from pymif import Mif
>>> mif = Mif(mif_string)
>>> mif.getVersion()
300
>>> mif.getColumns()
[{'type': 'CHAR(256)', 'name': 'id'}, {'type': 'CHAR(1000)', 'name': 'help'}]
>>> mif.getLineStarted("DATA")
[{'line_text': 'Data', 'attrs': '', 'line_num': 12}]
>>> mif.getLineStarted("MULTIPOINT")
[{'line_text': 'MULTIPOINT 4', 'attrs': '4', 'line_num': 11}]

>>> mid_string = open('etetet.mid', 'r').read()
>>> from pymif import Mid
>>> mid = Mid(mid_string, mif)
>>> mid.data()
[...]

>>> from pymif import CoordSys
>>> cs = mif.getCoordSys()
>>> coordSys = CoordSys(cs)
>>> coordSys.epsg
4326
```