# coding=utf-8
import re
import os
import json
import logging
import unittest
# import StringIO
import io as StringIO
# import ConfigParser
import configparser as ConfigParser

VERSION_REGEX = re.compile(r"(\d+)?\.(\d+)?\.?(\*|\d+)")
BUFFER_SIZE = 8192


class UniversalParser:
    def __init__(self, file_path, logger=None):
        self.parser_factory = None
        self.name = None
        self.version = None
        self.file = open(file_path, "r")
        self._logger = logger if logger else logging.getLogger(__name__)
        for parser in [CuraParser(), Slic3rParser(), Simplify3DParser()]:
            if parser.detect(self.file):
                self.parser_factory = parser
                self.name = parser.name
                self.version = parser.version
            # /if parser.detect(self.file)
        # /for parser in [CuraParser(), Slic3rParser(), Simplify3DParser()]
    # /def __init__(self, file_path, logger=None)

    def parse(self):
        if self.parser_factory:
            parameters = self.parser_factory.parse(self.file)
            parameters.update({"slicer_name": self.name})
            parameters.update({"slicer_version": self.version})
        else:
            parameters = {}
            self._logger.info("Can't parse additional parameters from %s" % self.file.name)
        # /if self.parser_factory
        return parameters
    # /def parse(self)
# /class UniversalPlayer


class BaseParser:
    def parse(self, gcode_file):
        parameters = {}
        parameters.update(self.parse_header(gcode_file))
        parameters.update(self.parse_bottom(gcode_file))
        gcode_file.close()
        return parameters
    # /parse(self, gcode_file)
# /class BaseParser


class CuraParser(BaseParser):
    def __init__(self):
        self.name = "cura"
        self.version = None
    # /def __init__(self)

    def detect(self, gcode_file):
        detected = False
        # on the third line (not always)
        # ;Generated with Cura_SteamEngine 2.3.1
        for _ in range(10):
            line = gcode_file.readline()
            if re.search(r"Cura_SteamEngine", line):
                version = VERSION_REGEX.search(line)
                if version:
                    detected = True
                    self.version = version.group(0)
                # /if version
            # /if re.search(r"Cura_SteamEngine", line)
        # /for _ in range(10)
        gcode_file.seek(0)
        return detected
    # /def detect(self, gcode_file)

    def parse_header(self, gcode_file):
        parameters = {}
        for i in range(15):
            line = gcode_file.readline()
            if line.startswith(";"):
                line = line.replace(";", "")
                if line.startswith("TIME") or line.startswith("LAYER_COUNT"):
                    splitted = line.split(":", 1)
                    parameters.update({splitted[0]: splitted[1].strip()})
                # /if line.startswith("TIME") or line.startswith("LAYER_COUNT")
            # /if line.startswith(";")
        # /for i in range(15)
        gcode_file.seek(0)
        return parameters
    # /def parse_header(self, gcode_file)

    def parse_bottom(self, gcode_file):
        parameters = {}
        settings_reversed = []
        settings = []
        for line in reverse_readline(gcode_file):
            if line.startswith(";SETTING_3"):
                line = line.replace(";SETTING_3", "")
                settings_reversed.append(line)
            else:
                break
            # /if line.startswith(";SETTING_3")
        # /for line in reverse_readline(gcode_file)

        [settings.append(x.strip()) for x in reversed(settings_reversed)]
        settings = "".join(settings)
        settings = json.loads(settings)
        # Cura >= 3.1 prints also a section extruder_quality
        settings = settings["global_quality"].replace("\\\\n", "\n")
        config = ConfigParser.RawConfigParser(allow_no_value=True)
        try:
            config.readfp(StringIO.StringIO(settings))
        except ConfigParser.MissingSectionHeaderError:
            # TODO add a log message
            return {}
        # /try
        try:
            for section in ["values", "metadata"]:
                for option in config.options(section):
                    parameters.update({option: config.get(section, option)})
                # /for option in config.options(section)
            # /for section in ["values", "metadata"]
        except ConfigParser.NoSectionError:
            pass
        except ConfigParser.NoOptionError:
            pass
        # /try
        return parameters
    # /def parse_bottom(self, gcode_file)
# /class CuraParser(BaseParser)


class Slic3rParser(BaseParser):
    def __init__(self):
        self.name = "slic3r"
        self.version = None
        self.is_parameter = re.compile(r"^[\w _]+={1}")
    # /def __init__(self)

    def detect(self, gcode_file):
        detected = False
        # on the first line
        # ; generated by Slic3r 1.2.9 on 2017-01-30 at 21:53:46
        line = gcode_file.readline()
        gcode_file.seek(0)
        if re.search(r"Slic3r", line):
            self.version = VERSION_REGEX.search(line).group(0)
            detected = True
        # /if re.search(r"Slic3r", line)
        return detected
    # /def detect(self, gcode_file)

    def parse_header(self, gcode_file):
        parameters = {}
        for line in gcode_file:
            if line.startswith(";"):
                line = line.split(";")[1].strip()
                if self.is_parameter.match(line):
                    splitted = line.split("=")
                    param = splitted[0].strip()
                    value = splitted[1].strip()
                    parameters.update({param: value})
            elif line == "\n":
                continue
            else:
                break
            # /if line.startswith(";")
        # /for line in gcode_file
        gcode_file.seek(0)
        return parameters
    # /def parse_header(self, gcode_file)

    def parse_bottom(self, gcode_file):
        parameters = {}
        for line in reverse_readline(gcode_file):
            if line.startswith(";"):
                line = line.split(";")[1].strip()
                if self.is_parameter.match(line):
                    splitted = line.split("=")
                    param = splitted[0].strip()
                    value = splitted[1].strip()
                    parameters.update({param: value})
            elif line == "\n":
                continue
            else:
                break
            # /if line.startswith(";")
        # /for line in reverse_readline(gcode_file)
        return parameters
    # /def parse_bottom(self, gcode_file)
# /class Slic3rParser(BaseParser)


class Simplify3DParser(BaseParser):
    def __init__(self):
        self.name = "simplify3d"
        self.version = None
        # checks if string starts with a word followed by a comma
        self.is_parameter = re.compile(r"^\w+,{1}")
        self.is_bparameter = re.compile(r"^[\w ]+:{1}")
    # /def __init__(self)

    def detect(self, gcode_file):
        detected = False
        # on the first line
        # ; G-Code generated by Simplify3D(R) Version 3.1.0
        line = gcode_file.readline()
        gcode_file.seek(0)
        if re.search(r"Simplify3D\(R\)", line):
            self.version = VERSION_REGEX.search(line).group(0)
            detected = True
        # /if re.search(r"Simplify3D\(R\)", line)
        return detected
    # /def detect(self, gcode_file)

    def parse_header(self, gcode_file):
        parameters = {}
        for line in gcode_file:
            if line.startswith(";"):
                # extract a string between semicolons ; =>target string<= ;
                line = line.split(";")[1].strip()
                if self.is_parameter.match(line):
                    comma_split = line.split(",")
                    param = comma_split[0]
                    value = ",".join(comma_split[1:])
                    try:
                        parameters.update({param: value})
                    except ValueError:
                        pass
                    # /try
                # /if self.is_parameter.match(line)
            # comment section is ended
            else:
                break
            # /if line.startswith(";")
        # /for line in gcode_file
        gcode_file.seek(0)
        return parameters
    # /def parse_header(self, gcode_file)

    def parse_bottom(self, gcode_file):
        # Filament length is a duplicate
        # ; Build Summary
        # ;   Build time: 3 hours 30 minutes
        # ;   Filament length: 54599.6 mm (54.60 m)
        # ;   Plastic volume: 131327.49 mm^3 (131.33 cc)
        # ;   Plastic weight: 164.16 g (0.36 lb)
        # ;   Material cost: 20.52
        parameters = {}
        for line in reverse_readline(gcode_file):
            if line.startswith(";"):
                line = line.split(";")[1].strip()
                if self.is_bparameter.match(line):
                    splitted = line.split(":")
                    param = splitted[0]
                    value = splitted[1].strip()
                    parameters.update({param: value})
                # /if self.is_bparameter.match(line)
            else:
                break
            # /if line.startswith(";")
        # /for line in reverse_readline(gcode_file)
        # Rename "Filament length"
        return parameters
    # /def parse_bottom(self, gcode_file)

# /class Simplify3DParser(BaseParser)


def reverse_readline(fh, buf_size=BUFFER_SIZE):
    """a generator that returns the lines of a file in reverse order
       It's a memory-efficient way to read file backwards.
       http://stackoverflow.com/questions/2301789/read-a-file-in-reverse-order-using-python
    """
    segment = None
    offset = 0
    fh.seek(0, os.SEEK_END)
    file_size = remaining_size = fh.tell()
    while remaining_size > 0:
        offset = min(file_size, offset + buf_size)
        fh.seek(file_size - offset)
        buffer = fh.read(min(remaining_size, buf_size))
        remaining_size -= buf_size
        lines = buffer.split('\n')
        # the first line of the buffer is probably not a complete line so
        # we'll save it and append it to the last line of the next buffer
        # we read
        if segment is not None:
            # if the previous chunk starts right from the beginning of line
            # do not concact the segment to the last line of new chunk
            # instead, yield the segment first
            if buffer[-1] is not '\n':
                lines[-1] += segment
            else:
                yield segment
            # /if buffer[-1] is not '\n'
        # /if segment is not None
        segment = lines[0]
        for index in range(len(lines) - 1, 0, -1):
            if len(lines[index]):
                yield lines[index]
            # /if len(lines[index])
        # /for index in range(len(lines) - 1, 0, -1)
    # /while remaining_size > 0
    # Don't yield None if the file was empty
    if segment is not None:
        yield segment
    # /if segment is not None
# /def reverse_readline(fh, buf_size=BUFFER_SIZE)


class TestUniversalParser(unittest.TestCase):
    def setUp(self):
        self.simplify3d_file = "parser_test/simplify3d_test.gcode"
        self.slic3r_file = "parser_test/slic3r_test.gcode"
        self.cura_file = "parser_test/cura_test.gcode"
    # /def setUp(self)

    def test_simplify3d_detection(self):
        uparser = UniversalParser(self.simplify3d_file)
        self.assertEqual(uparser.name, "simplify3d")
    # /def test_simplify3d_detection(self)

    def test_simplify3d_parse(self):
        uparser = UniversalParser(self.simplify3d_file)
        result = uparser.parse()
        self.assertEqual(len(result), 187)
        self.assertIn("Filament length", result)
        self.assertEqual(result["slicer_version"], "3.1.0")
    # /def test_simplify3d_parse(self)

    def test_slic3r_detection(self):
        uparser = UniversalParser(self.slic3r_file)
        self.assertEqual(uparser.name, "slic3r")
    # /def test_slic3r_detection(self)

    def test_slic3r_parse(self):
        uparser = UniversalParser(self.slic3r_file)
        result = uparser.parse()
        self.assertEqual(len(result), 137)
        self.assertIn("thin_walls", result)
        self.assertIn("support material extrusion width", result)
        self.assertEqual(result["slicer_version"], "1.2.9")
    # /def test_slic3r_parse(self)

    def test_cura_detection(self):
        uparser = UniversalParser(self.cura_file)
        self.assertEqual(uparser.name, "cura")
    # /def test_cura_detection(self)

    def test_cura_parse(self):
        uparser = UniversalParser(self.cura_file)
        result = uparser.parse()
        self.assertEqual(len(result), 12)
        self.assertIn("adhesion_type", result)
        self.assertEqual(result["slicer_version"], "2.3.1")
    # /def test_cura_parse(self)
# /class TestUniversalParser(unittest.TestCase)


if __name__ == "__main__":
    unittest.main()
# /if __name__ == "__main__"
