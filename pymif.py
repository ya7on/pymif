# -*- coding: utf-8 -*-
"""
Python script for .mif .mid files parsing
"""

"""
    EXAMPLE
---
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
"""

class Mif:
    """
    Getting data from the .mif file

    Parameters
    ----------
    file_mif : <String>
        Mif file text

    Methods
    ----------
    .getVersion(); \n
    .getColumns(); \n
    .getDescription(); \n
    .getCoordSys(); \n
    .getDelimiter(); \n
    .getLineStarted(); \n
    .getGeometry(); \n
    """
    def __init__(self, file_mif):
        self.file_mif = file_mif
        self.lines = file_mif.split('\n')
        for l in xrange(len(self.lines)):
            if l >= len(self.lines):
                break
            line = self.lines[l]
            if not line:
                del self.lines[l]
    
    def getVersion(self):
        """
        Returns file version

        For example:
        ----
        <Integer>: 300
        """
        info = self.getLineStarted('VERSION')
        if not info:
            return None
        return int(info[0]['attrs'])
    
    def getColumns(self):
        """
        Returns COLUMNS field list

        For example:
        ----
        <list>: [..., { "name": %name%, "type" %type% }, ...]
        """
        columns = []
        info = self.getLineStarted("COLUMNS")
        if not info:
            return []
        info = info[0]
        start = info['line_num'] + 1
        finish = start + int(info['attrs'])
        for i in range(start, finish):
            line = self.lines[i]
            if line[0] in ['\t', ' ']:
                line = line[1:]
            line = line.replace('\t', '').split(' ')
            if line[0] in ['\t', ' ', '']:
                line = line[1:]
            col_name = line[0]
            col_type = ''.join(line[1:])

            columns.append({"name": col_name, "type": col_type})
        return columns
    
    def getDescription(self):
        """
        Returns DESCRIPTION field list

        For example:
        ----
        <list>: [..., { "name": %name%, "description" %description% }, ...]
        """
        columns = []
        info = self.getLineStarted("DESCRIPTION")
        if not info:
            return []
        info = info[0]
        start = info['line_num'] + 1
        finish = start + int(info['attrs'])
        for i in range(start, finish):
            line = self.lines[i]
            if line[0] != '\t':
                raise ValueError("Строка в поле description должна начинаться с табуляции")
            line = line.replace("\t", "").split(' ')
            col_name = line[0]
            col_description = ''.join(line[1:])

            if col_description[0] == '"' or col_description[0] == "'":
                col_description = col_description[1:-1]

            columns.append({"name": col_name, "description": col_description})
        return columns

    def getCoordSys(self):
        """
        Returns string coord. system

        For example:
        ---
        <string>: "Earth Projection 8, 104, 'm', 115.03333333333, 0, 1, 7250000, -5411057.63"
        """
        info = self.getLineStarted("CoordSys")
        if not info:
            return None
        return info[0]['attrs']

    def getDelimiter(self):
        """
        Returns current delimiter if it exists else returns standart delimiter "\\t"
        
        For example:
        ---
        <String>: "\\t"
        """
        info = self.getLineStarted("DELIMITER")
        if not info:
            return "\t"
        delimiter = info[0]['attrs']
        if delimiter[0] == delimiter[-1] and delimiter[0] in ['\'', '\"']:
            delimiter = delimiter[1:-1]
        return delimiter
    
    def getLineStarted(self, string):
        """
        Returns all lines that starts with incoming argument
        Parameters
        ---
        string: <String>
            for example: "VERISON" or "COLUMNS"
        
        Returns
        ---
        <List>: [ ..., { 
            "line_num": <Integer> %LineNumber%, 
            "attrs": <String> %LineAttributes%, 
            "line_text": <String> %CurrentLineString%
            }, ... ]
        """
        string = str(string)
        l = len(string)
        return_lines = []
        for i in xrange(len(self.lines)):
            line = self.lines[i]
            if line[:l].lower() == string.lower():
                attrs = line[l:]
                if attrs and attrs[0] == ' ':
                    attrs = attrs[1:]
                return_lines.append({"line_num": int(i), "attrs": attrs, "line_text": self.lines[i]})
        return return_lines
    
    def getGeometry(self):
        """
        Returns geometry's list

        Returns
        ---
        <List>: [ ..., {
            "geom": <List> %PointList%,
            "type": <String> %GeometryType%
            }, ... ]
        """
        info = self.getLineStarted("DATA")
        if not info:
            return None
        
        info = info[0]
        l = info['line_num'] + 1
        m = len(self.lines)

        geom_objects = []
        types = ("point", "line", "pline", "region", "arc", "text", "rect", "roundrect", "ellipse", "multipoint", "collection", "none")
        
        # Собираются все линии, с которых начинается геометрия
        for line_num in range(l, m):
            line = self.lines[line_num]
            if line.lower().startswith(types):
                geom_objects.append(line_num)
        
        geom = []
        for l in geom_objects:
            line = self.lines[l].lower().split(' ')
            parsers = {
                "point": self.__parsePoint,
                "line": self.__parseLine,
                "pline": self.__parsePline,
                "region": self.__parseRegion,
                "arc": self.__parseArc,
                "text": self.__parseText,
                "rect": self.__parseRect,
                "roundrect": self.__parseRoundrect,
                "ellipse": self.__parseEllipse,
                "multipoint": self.__parseMultipoint,
                "collection": self.__parseCollection,
                "none": self.__parseNone,
            }
            try:
                func = parsers[line[0]](l)
            except:
                raise ValueError("Uknown data format %s at line %s" % (line[0], l))
            geom.append(func)
        return geom
    
    def __parsePoint(self, line):
        """Parse point"""
        line_str = self.lines[line].lower().replace('\t', '').split(' ')
        geometry = line_str[1:]
        return { "type": "point", "geom": geometry }
    def __parseLine(self, line):
        """Parse line"""
        line_str = self.lines[line].lower().replace('\t', '').split(' ')
        geometry = [line_str[1:3], line_str[3:5]]
        return { "type": "line", "geom": geometry }
    def __parsePline(self, line):
        """Parse poly line"""
        line_str = self.lines[line].lower().replace('\t', '').split(' ')
        geom_len = 2
        geometry = [[]]
        if len(line_str) > 1 and line_str[1]:
            geom_len = int(line_str[1])
        line += 1
        for l in range(line, line + geom_len):
            point = self.lines[l].replace('\t', '').split(' ')
            geometry[0].append(point)
        return { "type": "pline", "geom": geometry }
    def __parseRegion(self, line):
        """Parse region"""
        line_str = self.lines[line].lower().replace('\t', '').split(' ')
        reg_count = int(line_str[1])
        reg_len = None
        geometry = []
        for _ in xrange(reg_count):
            for l in range(line, len(self.lines)):
                try:
                    reg_len = int(self.lines[l])
                except:
                    pass
                else:
                    line = l + 1
                    break
            if not reg_len:
                return None
            geometry.append([])
            for l in range(line, line + reg_len):
                point = self.lines[l].replace('\t', '').split(' ')
                geometry[-1].append(point)
        return { "type": "region", "geom": geometry, "reg_count": reg_count }
    def __parseArc(self, line): # TODO
        pass; return { "type": "arc", "geom": None }
    def __parseText(self, line): # TODO
        pass; return { "type": "text", "geom": None }
    def __parseRect(self, line): # TODO
        pass; return { "type": "rect", "geom": None }
    def __parseRoundrect(self, line): # TODO
        pass; return { "type": "roundrect", "geom": None }
    def __parseEllipse(self, line): # TODO
        pass; return { "type": "ellipse", "geom": None }
    def __parseMultipoint(self, line):
        """Parse multipoint"""
        line_str = self.lines[line].lower().replace('\t', '').split(' ')
        point_count = int(line_str[1])
        line += 1
        geometry = []
        for i in range(line, line + point_count):
            point = self.lines[i].replace('\t', '').split(' ')
            geometry.append(point)
        return { "type": "multipoint", "geom": geometry }
    def __parseCollection(self, line): # TODO
        """Parse geometry collection"""
        line_str = self.lines[line].lower().replace('\t', '').split(' ')
        collection_arr = []
        collection_len = int(line_str[1])
        line += 1
        types = ("point", "line", "pline", "region", "arc", "text", "rect", "roundrect", "ellipse", "multipoint", "collection")
        for l in range(line, len(self.lines)):
            line_str = self.lines[l].lower().replace('\t', '')
            if line_str.startswith(types):
                collection_arr.append(l)
            if len(collection_arr) >= collection_len:
                break
        parsers = {
            "point": self.__parsePoint,
            "line": self.__parseLine,
            "pline": self.__parsePline,
            "region": self.__parseRegion,
            "arc": self.__parseArc,
            "text": self.__parseText,
            "rect": self.__parseRect,
            "roundrect": self.__parseRoundrect,
            "ellipse": self.__parseEllipse,
            "multipoint": self.__parseMultipoint,
            "collection": self.__parseCollection,
            "none": self.__parseNone,
        }
        geom_return = []
        for obj in collection_arr:
            geom_type = self.lines[obj].lower().replace('\t', '').split(' ')[0]
            try:
                func = parsers[geom_type]
            except:
                raise ValueError("Uknown data format %s at line %s" % (line[0], l))
            geom_return.append(func(obj))
        return { "type": "collection", "geom": geom_return }
    def __parseNone(self, line): # TODO
        """returns None"""
        return { "type": "None", "geom": None }
        


class Mid:
    # Функция инициализации класса
    # Принимает строку содержимого mid файла в file_mid
    def __init__(self, file_mid, file_mif):
        self.file_mid = file_mid
        self.lines = file_mid.split('\n')
        self.mif = file_mif
        if not isinstance(file_mif, Mif):
            raise ValueError("'file_mif' argument must be a Mif() instance")

    def data(self, soft = False):
        columns = self.mif.getDescription() if self.mif.getDescription() else self.mif.getColumns()
        key = 'description' if self.mif.getDescription() else 'name'
        delimiter = self.mif.getDelimiter()

        data = {"count": 0, "info": []}

        for line in self.lines:
            if not line:
                continue
            data['info'].append([])
            if line[-1] == '\t':
                line = line[:-1]
            els = line.split(delimiter)
            if len(els) != len(columns) and not soft:
                raise ValueError("columns length is not equal to mid file data.\ncall this function with 'soft=True' argument")
            for i in xrange(len(els)):
                attr_name = columns[ i % len(els) ]
                data['info'][-1].append( { "name": attr_name[key], "value": els[i] } )
        data['count'] = len(data['info'])
        return data

class CoordSys:
    """
    Перевод MapInfo системы координат в EPSG:

    Variables
    ---
    .epsg : Integer \n
    .name : String

    Parameters
    ---
    String : coordSys - Система координат из файла
    """
    def __init__(self, coordSys):
        self.__loadProjs()
        try:
            info = self.projs[coordSys]
        except:
            print coordSys
            raise ValueError("Uknown coordsys")
        else:
            self.epsg = info['epsg']
            self.name = info['name']
        
    def __loadProjs(self):
        self.projs = {
            "Earth Projection 1, 104": {"epsg": 4326, "name": "WGS84 / Long/Lat"},
            "Earth 1, 104": {"epsg": 4326, "name": "WGS84"},
            
            "Earth Projection 8, 104, \"m\", 97.03333333333, 0, 1, 1250000, -5411057.63": {"epsg": 911001, "name": "MSK-38 - zone 1"},
            "Earth Projection 8, 104, \"m\", 100.03333333333, 0, 1, 2250000, -5411057.63": {"epsg": 911002, "name": "MSK-38 - zone 2"},
            "Earth Projection 8, 104, \"m\", 103.03333333333, 0, 1, 3250000, -5411057.63": {"epsg": 911003, "name": "MSK-38 - zone 3"},
            "Earth Projection 8, 104, \"m\", 106.03333333333, 0, 1, 4250000, -5411057.63": {"epsg": 911004, "name": "MSK-38 - zone 4"},
            "Earth Projection 8, 104, \"m\", 109.03333333333, 0, 1, 5250000, -5411057.63": {"epsg": 911005, "name": "MSK-38 - zone 5"},
            "Earth Projection 8, 104, \"m\", 112.03333333333, 0, 1, 6250000, -5411057.63": {"epsg": 911006, "name": "MSK-38 - zone 6"},
            "Earth Projection 8, 104, \"m\", 115.03333333333, 0, 1, 7250000, -5411057.63": {"epsg": 911007, "name": "MSK-38 - zone 7"},
            "Earth Projection 8, 104, \"m\", 118.03333333333, 0, 1, 8250000, -5411057.63": {"epsg": 911008, "name": "MSK-38 - zone 8"},
        }