""" provides the CsvReader class """
# pylint: disable=missing-function-docstring
import sys
import re
import importlib

from pprint import pformat

class CsvReader:
    # pylint: disable=too-many-instance-attributes
    """
    CSV reader class that supports basic CSV files.
    The primary reason for this class is that it will support CSV files which have an extra comma
    at the end of a line (as many do).
    The header line and current header is stored and can be retrieved.

    header row parsing:
      If has_header is True (the default) then the first row will be stored as column header names.
      If has_header is False, you can provide your own header via the 'header' constructor param.
      If expected_header is specified, then the header row expected will be validated against the one given.

    dictification:
      If dictify is True, the returned rows will be a dict of key/value pairs rather than a list.
      If dict_type is True, then that class will be instantatiated rather than an AttrDict

    extra columns:
      If extra columns are found, the header line will not be modified, but the header will be updated
      with extra columns of the name format "column_x" where x is the 1-based column number,
      and the extra column format can be set in the constructor (defaults to "column_{}").
      If extra_columns is a string containing '{' it will be treated as a format string to format the column number.
      If extra_columns is a function it will be called with a single argument of the column number.
      If extra_columns is set to None, then any extra data will be retained in the last column that was
      seen in the header.
      If extra_columns is set to 'merge', then the extra columns will be left appended to the last column.
      If extra_columns is set to a string (not containing a '{') and 'dictify' is set, then all extra columns
      will be placed in a key with that name (given by extra_columns).

    error_handling:
      if raise_error is False, then an error message will be stored which can be retrieved with GetError()
      if raise_error is True, then an exception will be thrown.

    row numbers:
      if row numbers is a string and dictify is set, then the row number will be stored in the dict
      by the key specified by that string.
      For example row_numbers='_row',dictify=True   will produce rows like {'_row':0,...}
      if row_number_style is 'absolute' or 'relative' then the row number produced will either include, or ignore, any skipped lines
    """
    def __init__(self,
                 sep=',',
                 quotechar='"',
                 skip=None,
                 skip_count=0,
                 extra_columns_method="generate",
                 extra_columns="column_{}",
                 has_header=True,
                 header=None,
                 expected_header=None,
                 dictify=False,
                 dict_type=None,
                 skip_empty_lines=True,
                 comment_char='#',
                 return_header_row=True,
                 missing_values=None,
                 row_numbers=None,
                 row_number_style='absolute',
                 quiet=False,
                 raise_error=False,
                 msg=None
                ):
        # pylint: disable=too-many-arguments,too-many-locals,too-many-statements
        self.quotechar = quotechar
        self.sep = sep
        self.quiet = quiet
        if msg is None:
            msg = lambda *args: print(" ".join(str(a) for a in args), file=sys.stderr)
        self.msg = msg
        self.return_header_row = return_header_row
        self.has_header = has_header
        self.header_line = None
        self.expected_header = expected_header
        if not has_header:
            if header is not None:
                self.header = header
                self.columns = [] + header
            elif extra_columns is None:
                self.SetError("Because has_header is False, you must either provide a header, or a format/function for formatting extra_column names.")
            else:
                self.header = []
                self.columns = []
        elif header is not None:
            self.header = header
            self.columns = [] + header
        else:
            self.header = None
            self.columns = None

        #Example use cases:
        #   Example input data:
        #      a,b,c       #header
        #      1,2,3,d,e   #data
        #   dictify=False,extra_columns_method='generate',  extra_columns='column_{}'            produces columns (a,b,c,column_4,column_5) row ['a','b','c','d','e']
        #   dictify=False,extra_columns_method='append-last',                                    produces columns (a,b,c)                   row ['a','b','c,d,e']
        #   dictify=False,extra_columns_method='append-last:as-list'                             produces columns (a,b,c)                   row ['a','b',['c','d','e']]
        #   dictify=False,extra_columns_method='store',             extra_columns='extra_data'   produces columns (a,b,c,extra_data)        row ['a','b','c','d,e']
        #   dictify=False,extra_columns_method='store:as-list',     extra_columns='extra_data'   produces columns (a,b,c,extra_data)        row ['a','b','c',['d','e']]
        #   dictify=True, extra_columns_method='generate',          extra_columns='column_{}'    produces columns (a,b,c,column_4,column_5) row {'a':'a','b':'b','c':'c','column_4':'d','column_5': 'e'}
        #   dictify=True, extra_columns_method='append-last',                                    produces columns (a,b,c)                   row {'a':'a','b':'b','c':'c,d,e'}
        #   dictify=True, extra_columns_method='append-last:as-list',                            produces columns (a,b,c)                   row {'a':'a','b':'b','c':['c','d','e']}
        #   dictify=True, extra_columns_method='store',             extra_columns='extra_data'   produces columns (a,b,c,column_4,column_5) row {'a':'a','b':'b','c':'c','extra_data':'d,e'}
        #   dictify=True, extra_columns_method='store:as-list',     extra_columns='extra_data'   produces columns (a,b,c,column_4,column_5) row {'a':'a','b':'b','c':'c','extra_data':['d','e']}
        if extra_columns_method is None:
            extra_columns_method = []
        elif isinstance(extra_columns_method, str):
            extra_columns_method = extra_columns_method.split(':') if extra_columns_method else []

        self.extra_columns_method = extra_columns_method

        self.raise_error = raise_error

        if 'generate' in extra_columns_method and isinstance(extra_columns, str) and '{' in extra_columns:
            # Produce a format generator function from the generator string
            self.extra_columns = extra_columns.format
        else:
            self.extra_columns = extra_columns
        for item in self.extra_columns_method:
            if item not in [ 'ignore', 'generate', 'append-last', 'as-list', 'store' ]:
                self.SetError("Bad value {} for extra_columns_method".format(extra_columns_method))

        self.missing_values = missing_values

        self.rows = []
        self.row_number_style = row_number_style
        self.row_numbers = row_numbers
        self.absolute_row_number = -1
        self.relative_row_number = -1
        self.skip = skip
        self.skip_count = skip_count
        self.skip_empty_lines = skip_empty_lines

        self.comment_char = comment_char

        self.dictify = dictify

        if dictify and dict_type is None:
            # use importlib for geting the AttrDict type, so that it is a soft dependency only
            try:
                # pylint: disable=bare-except
                attrdict = importlib.import_module("attrdict")
                dict_type = attrdict.AttrDict
            except:
                self.msg("WARNING: AttrDict type is not available. Standard dict type used instead. You can customise this by setting dict_type in the constructor.")
                dict_type = dict

        self.dict_type = dict_type

        self.error = None

    def __str__(self):
        return "CSV file currently with {} rows and {} columns (header={})".format(len(self.rows), len(self.header), pformat(self.header))

    def SplitLine(self, line):
        # pylint: disable=missing-function-docstring,too-many-statements
        beg = 0
        quote_idx = line.find(self.quotechar)
        if quote_idx < 0:
            for x in line.split(self.sep):
                yield x
            return

        sz = len(line)
        beg = 0
        inquote = False
        sep = self.sep
        qc = self.quotechar
        keep = ""
        while True:
            next_sep = line.find(sep, beg)
            next_quote = line.find(qc, beg)
            #msg("{} of {} got next {}={}, next {}={}", beg, sz, sep, next_sep, qc, next_quote)
            if beg >= sz:
                yield keep
                return
            if inquote and next_sep == beg: # Comma within quoted section, accumulate it
                keep += sep
                beg += 1
                continue
            if next_sep == beg: # Comma starting next field. Return anything accumulated
                yield keep
                keep = ""
                beg +=1
                continue
            if inquote and next_quote == beg: # End quoted section, continue looking for sep
                keep += line[beg:next_quote]
                beg +=1
                inquote = False
                continue
            if next_quote == beg: # Begin quoted section, skip this single quote.
                inquote = True
                beg +=1
                continue
            if inquote and next_quote > beg: # Accumulate up to the next quote, if one found
                keep += line[beg:next_quote]
                beg = next_quote + 1 # skip this quote
                inquote = False
                continue
            if inquote and next_quote <= beg: # In quoted section,but no more quotes avail.
                keep += line[beg:] # Accumlate everything to end of line
                yield keep
                keep = ""
                return # Finish
            if 0 < next_sep < next_quote:  # From this point on, inquote==False
                keep += line[beg:next_sep]  # There is another quote, but next comma is closer than next quote
                beg = next_sep + 1
                yield keep
                keep = ""
                continue
            if  next_sep > 0 and next_sep > next_quote >= beg:
                # Accumulate up to the quote and begin quoted section.
                keep += line[beg:next_quote]
                beg = next_quote + 1
                inquote = True
                continue
            if next_sep > 0 and next_quote <=beg:
                keep += line[beg:next_sep]
                beg = next_sep + 1
                yield keep
                keep = ""
                continue
            if next_sep < 0 <= next_quote:
                keep += line[beg:next_quote]
                beg = next_quote + 1
                inquote = True
                continue
            if next_sep < 0 and next_quote < 0:
                # Neither separator or quote have been seen.
                # Grab to the end of the line, and finish.
                keep += line[beg]
                yield keep
                keep = ""
                return
            self.msg("This should never happen")
            return
        return


    def AddRow(self, row):
        self.rows.append(row)

    def Read(self, f):
        self.error = None
        err_generated = None
        try:
            # pylint: disable=bare-except
            with open(f, 'r') as fh:
                for line in fh.readlines():
                    try:
                        # pylint: disable=bare-except
                        row = self.ProcessLine(line)
                        if self.error:
                            err_generated = None
                            break
                        if row is not None:
                            yield row
                    except:
                        err_generated = "Failed processing line:" + line
                        break
        except:
            err_generated = "Failed reading file {}".format(f)

        if err_generated:
            self.SetError(err_generated)


    def ClearError(self):
        self.error = None

    def Error(self):
        return self.error

    def GetError(self):
        return self.error

    def GetHeader(self):
        """ Get the header (either as specified in constructor, or read from the file). See also GetColumns() for all columns seen so far. """
        return self.header

    def GetHeaderLine(self):
        return self.header_line

    def GetColumns(self):
        """ Return the columns seen from processing - which may include additions from what was seen in the header """
        return self.columns

    def ProcessLine(self, line):
        """
        Handle one line from the input source - processing any outstanding skip directives
        and storing the header line separately
        """

        self.absolute_row_number += 1

        if self.skip_count is not None and self.skip_count > 0:
            self.skip_count -= 1
            return None

        if self.skip is not None:
            if re.match(self.skip, line):
                return None

        line = line.rstrip()
        if not line:
            if self.skip_empty_lines:
                return None

        if self.header is None:
            return self.HandleHeader(line)
        return self.HandleData(line)

    def HandleData(self, line):
        self.relative_row_number += 1
        row = list(self.SplitLine(line))
        columns, row, extras = self.HandleExtraColumns(row)
        if extras is not None and not self.quiet:
            self.msg("WARNING: Unsupported extra column data method - extra data is being discarded")
        if self.dictify:
            row = self.Dictify(columns, row, extras)
        self.AddRow(row)
        return row

    def HandleHeader(self, line):
        self.header_line = line
        self.header = list(self.SplitLine(line))
        self.columns = [] + self.header
        expected = self.expected_header
        if expected is not None:
            if isinstance(expected, list):
                if len(expected) != len(self.header):
                    self.error = "Header line had unexpected number of columns"
                    return None
                for idx, cell in enumerate(expected):
                    if self.header[idx] != cell:
                        self.error = "Header column {}({}) did not match expected column name:{}".format(idx, self.header[idx], cell)
                        return None
            elif self.header_line != expected:
                self.error = "Header line did not match that expected"
                return None
        if self.return_header_row:
            self.relative_row_number += 1
            return self.header
        return None

    def SetError(self, errmsg):
        self.error = errmsg
        if not self.quiet:
            self.msg("ERROR:" + errmsg)
        if self.raise_error:
            raise ValueError(self.error)

    def HandleExtraColumns(self, row):
        header = self.header
        columns = self.columns
        orig_col_count = len(header)
        current_col_count = len(columns)
        row_len = len(row)

        if row_len <= orig_col_count:
            # Nothing to do
            return header, row, None

        #Example use cases:
        #   Example input data:
        #      a,b,c       #header
        #      1,2,3,d,e   #data
        #   dictify=False, extra_columns_method='generate',          extra_columns='column_{}'    produces columns (a,b,c,column_4,column_5) row ['a','b','c','d','e']
        #   dictify=False, extra_columns_method='append-last',                                    produces columns (a,b,c)                   row ['a','b','c,d,e']
        #   dictify=False, extra_columns_method='append-last:as-list'                             produces columns (a,b,c)                   row ['a','b',['c','d','e']]
        #   dictify=False, extra_columns_method='store',             extra_columns='extra_data'   produces columns (a,b,c,extra_data)        row ['a','b','c','d,e']
        #   dictify=False, extra_columns_method='store:as-list',     extra_columns='extra_data'   produces columns (a,b,c,extra_data)        row ['a','b','c',['d','e']]
        #   dictify=True,  extra_columns_method='generate',          extra_columns='column_{}'    produces columns (a,b,c,column_4,column_5) row {'a':'a','b':'b','c':'c','column_4':'d','column_5': 'e'}
        #   dictify=True,  extra_columns_method='append-last',                                    produces columns (a,b,c)                   row {'a':'a','b':'b','c':'c,d,e'}
        #   dictify=True,  extra_columns_method='append-last:as-list',                            produces columns (a,b,c)                   row {'a':'a','b':'b','c':['c','d','e']}
        #   dictify=True,  extra_columns_method='store',             extra_columns='extra_data'   produces columns (a,b,c,column_4,column_5) row {'a':'a','b':'b','c':'c','extra_data':'d,e'}
        #   dictify=True,  extra_columns_method='store:as-list',     extra_columns='extra_data'   produces columns (a,b,c,column_4,column_5) row {'a':'a','b':'b','c':'c','extra_data':['d','e']}

        method = self.extra_columns_method
        fmt = self.extra_columns

        if 'generate' in method:
            columns = self.columns
            if row_len > current_col_count:
                # Simply add new individual header columns with an appropriate generated name
                for idx in range(current_col_count + 1, row_len + 1):
                    columns.append(fmt(idx))
            # Now return the row as-is, with no extras (columns have been generated for the extras)
            return columns, row, None

        if 'append-last' in method:
            # The last value is replaced with either a merged string, or a list,
            # no extra columns are added (the extra data is in the last column)
            last_col = current_col_count - 1
            if 'as-list' in method:
                # Replace the last column with a list containing that column and any extra values
                extras = row[last_col:]
                del row[last_col:]
                row.append(extras)
            else:
                # Replace the last column with a string containing the merged extra values
                extras = row[last_col:]
                del row[last_col:]
                row.append(self.sep.join(extras))
            return columns, row, None

        last_col = current_col_count
        extras = row[last_col:]
        del row[last_col:]

        if 'store' in method:
            if 'as-list' not in method:
                # Replace the last column with a list containing that column and any extra values
                extras = self.sep.join(extras)

            idx = None
            # An extra named value is created, but not permanently added to the header
            if fmt not in columns:
                columns.append(fmt)
                row.append(extras)
                extras = None
            else:
                idx = columns.index(fmt)
                if idx < row_len:
                    # Adding to an exising column
                    existing = row[idx]
                    if 'as-list' in method:
                        extras = [existing] + extras
                    else:
                        extras = existing + self.sep + extras
                else:
                    while len(row) < idx - 1:
                        row.append(self.missing_values)
                row[idx] = extras
                extras = None

        if 'ignore' in method:
            # silently discard the data as requested
            extras = None

        return columns, row, extras

    def Dictify(self, columns, row, extras):
        """
        Turn a row into another indexable type based on the dict type specified in the constructor.
        So if the header was 'a,b,c'
        Then a data row '1,2,3' will produce an object like { 'a': 1, 'b': 2, 'c': 3 }
        """
        if extras is not None and not self.quiet:
            self.msg("WARNING: Unsupported extra column data method - extra data is being discarded")

        ret = self.dict_type()
        for idx, col in enumerate(columns):
            val = row[idx]
            ret[col] = val
        return ret

    def ProcessData(self, data):
        """
        Process a chunk of text data as if it was a file (split into lines and then process)
        """
        lines = data.replace('\r\n','\n').split('\n')
        for line in self.ProcessLines(lines):
            yield line

    def ProcessLines(self, lines):
        """
        Process a number of lines
        """
        for line in lines:
            ret = self.ProcessLine(line)
            if ret is not None:
                yield ret
