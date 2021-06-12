"""
tests for csvreader
"""
import unittest

# pylint: disable=wildcard-import,missing-function-docstring,unused-wildcard-import

from readcsv.csvreader import *


def reader(**kwargs):
    return CsvReader(dict_type=dict, **kwargs)

class TestCsvParsing(unittest.TestCase):
    """ Test class CsvReader """

    input_lines=[
        'a,b,c,d,e,f', #header
        '0,b,c,d,e,f', #0
        '"1",b,c,d,e,f', #1
        '"2,1",b,c,d,e,f', #2
        '"3,1,2",b,c,d,e,f', #3
        '"4","b,1",c,d,e,f', #4
        '"5","b,,,,2",c,d,e,f', #5
        '"6","b c d",c,"d 1 2",e,f', #6
        '"7","b c d",c,"d 1 2",e,"f"', #7
        '"8","b c d",c,"d 1 2",e,"f', #8
        '"9","b c d",c,"d 1 2",e,"f,', #9
        '10,"b c d",c,"d 1 2,e,f,', #10
        '11,"b c d"xyz"mor,e",c,"d 1 2,e,f,', #11
        '12,b c d"xyz"mor,"e",c,"d 1 2,e,f,', #12
        '13,b c d"x,yz"mor,"e",c,"d 1 2,e,f,', #13
        ]

    expected=[
        [ 'a',     'b',             'c', 'd',         'e',         'f'  ], #Header
        [ '0',     'b',             'c', 'd',         'e',         'f'  ], #0
        [ '1',     'b',             'c', 'd',         'e',         'f'  ], #1
        [ '2,1',   'b',             'c', 'd',         'e',         'f'  ], #2
        [ '3,1,2', 'b',             'c', 'd',         'e',         'f'  ], #3
        [ '4',     'b,1',           'c', 'd',         'e',         'f'  ], #4
        [ '5',     'b,,,,2',        'c', 'd',         'e',         'f'  ], #5
        [ '6',     'b c d',         'c', 'd 1 2',     'e',         'f'  ], #6
        [ '7',     'b c d',         'c', 'd 1 2',     'e',         'f'  ], #7
        [ '8',     'b c d',         'c', 'd 1 2',     'e',         'f'  ], #8
        [ '9',     'b c d',         'c', 'd 1 2',     'e',         'f,' ], #9
        [ '10',    'b c d',         'c', 'd 1 2,e,f,'                   ], #10
        [ '11',    'b c dxyzmor,e', 'c', 'd 1 2,e,f,'                   ], #11
        [ '12',    'b c dxyzmor',   'e', 'c',         'd 1 2,e,f,'      ], #12
        [ '13',    'b c dx,yzmor',  'e', 'c',         'd 1 2,e,f,'      ], #13
        ]


    def test_parsing(self):
        r = CsvReader()
        lines = TestCsvParsing.input_lines
        expected = TestCsvParsing.expected

        rows = list(r.ProcessLines(lines))

        # self.assertEqual(len(rows),len(expected))
        # for i in range(0,len(expected)):
        #     self.assertEqual(len(rows[i]), len(expected[i]))
        #     for j in range(0,len(rows[i])):
        #         self.assertEqual(rows[i][j], expected[i][j])
        self.assertEqual(rows, expected)


class TestExtraColumnHandling(unittest.TestCase):
    """ Test class CsvReader """

    def check_data(self, testdata):
        for t in testdata:
            r, lines, expected_columns, expected = t
            rows = list(r.ProcessLines(lines))
            self.assertEqual(expected_columns, r.GetColumns())
            self.assertEqual(expected, rows)

    def test_extra_columns(self):
        abc = [ "a", "b", "c" ]
        datarow = [ "a,b,c,d,e" ]
        in_data = [ "a,b,c" ] + datarow
        testdata = [
            [reader(),                                                                            in_data,   abc + [ 'column_4', 'column_5' ], [ abc, [ "a", "b", "c", "d", "e" ] ] ],
            [reader(extra_columns_method='append-last'),                                          in_data,   abc,                              [ abc, [ "a", "b", "c,d,e" ] ] ],
            [reader(extra_columns_method='append-last:as-list'),                                  in_data,   abc,                              [ abc, [ "a","b", [ "c", "d", "e" ] ] ] ],
            [reader(extra_columns_method='append-last', dictify=True),                            in_data,   abc,                              [ abc, { 'a':"a", 'b': "b", 'c': "c,d,e" } ] ],
            [reader(extra_columns_method='append-last:as-list', dictify=True),                    in_data,   abc,                              [ abc, { 'a':"a", 'b': "b", 'c': [ "c", "d", "e"] } ] ],
            [reader(extra_columns_method='store', extra_columns='extra'),                         in_data,   abc + [ "extra" ],                [ abc, [ "a", "b", "c", "d,e" ] ] ],
            [reader(extra_columns_method='store:as-list', extra_columns='extra', dictify=True),   in_data,   abc + [ "extra" ],                [ abc, { 'a': "a", 'b': "b", 'c': 'c', 'extra': [ "d", "e" ] } ] ],
            [reader(extra_columns_method='generate', extra_columns='col{}', dictify=True),        in_data,   abc + [ "col4", "col5" ],         [ abc, { 'a': "a", 'b': "b", 'c': 'c', 'col4': "d", 'col5': "e" } ] ],
        ]
        self.check_data(testdata)

    def test_no_header(self):
        abc = [ "a", "b", "c" ]
        datarow = [ "a,b,c,d,e" ]
        #in_data = [ "a,b,c" ] + datarow
        testdata = [
            [ reader(has_header=False, header=abc),                                                datarow, abc + [ 'column_4', 'column_5' ], [ [ "a", "b", "c", "d", "e" ] ] ],
        ]
        self.check_data(testdata)

    def test_header_validation(self):
        # pylint: disable=too-many-locals
        in_header      = [ "a,b,c" ]
        in_datarow     = [ "a,b,c,d,e" ]
        in_badheader   = [ "x,y,z" ]
        abc            = [ "a", "b", "c" ]
        datarow_only   = in_datarow
        both           = in_header + in_datarow
        with_badheader = in_badheader + in_datarow

        good_data = [
            [ reader(has_header=True, header=abc),                                                 both, abc + [ 'column_4', 'column_5' ], [ abc, [ "a","b","c","d","e" ] ] ],
            [ reader(has_header=False, header=abc),                                                datarow_only, abc + [ 'column_4', 'column_5' ], [ [ "a", "b", "c", "d", "e" ] ] ],
        ]
        bad_data = [
            [ reader(has_header=True, expected_header=abc),                                        with_badheader, abc + [ 'column_4', 'column_5' ], [ abc, [ "a", "b", "c", "d", "e" ] ] ],
        ]

        self.check_data(good_data)

        for t in bad_data:
            r, lines, _expected_columns, _expected = t
            _rows = list(r.ProcessLines(lines))
            self.assertIsNotNone(r.GetError())


if __name__ == '__main__':
    unittest.main()
