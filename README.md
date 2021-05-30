Module readcsv
================

# A module for reading csv files

The primary reason for this class is that:

- it will support CSV files which have an extra comma at the end of a line (as many do)
- it will allow the rows to be returned as dictionaries keyed by the column name
- the dictionary type can be set

The header line and current header is stored and can be retrieved.


## Example usage

Create the object and give it lines to process, get back a row generator:

    reader = CsvReader()
    rows = [ x for x in reader.ProcessLines(lines) ]

Create the object and read a file (get back a row generator):

    reader = CsvReader()
    rows = [ x for x in reader.Read("example.csv") ]


## Constructor

    CsvReader(sep=',',
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

## Constructor options

### Verbosity and output

***quiet***:
- disables some output messages

***msg***:
- if set, it should be a function or lambda which will process text output messages
- by default it will print messages to stderr.
- to make it silent, pass a lambda which does nothing, for exaample ```lambda *_args: None```

### Header row parsing

***has_header***:
-if True (the default) then the first row will be stored as column header names.
-if False, you can provide your own header via the 'header' constructor param.

***header***:
- used to pass an array of column names if the file will not contain its own header row

***expected_header***:
- if specified, then the header row expected will be validated against the one given.

***return_header_row***:
- if set to a true value, then the first value yielded when processing the data will be the header columns, and the calling code will need to detect that and handle it differently than a data row. Also in this case the relative row number will be incremented (ie the first data row number will be higher, as the header row is returned rather than being transparently swallowed).

### Dictification (return each row as a dictionary or object)

***dictify***:
- if True, the returned rows will be a dict of key/value pairs rather than a list.

***dict_type***:
- if True, then that class will be instantatiated rather than an AttrDict

### Handling of extra / unexpected columns and missing columns

If extra columns are found, the header line will not be modified, but the header will be updated with extra columns of the name format "column_x" where x is the 1-based column number, and the extra column format can be set in the constructor (defaults to "column_{}"). This behaviour can be customised through two parameters which work together:

If extra_columns_method contains 'store', then this data will be stored as an extra column and the value from missing_values will be used to fill any intervening extra values that were missing.

**extra_columns_method**:
- a colon-separated string of behaviour tokens for customising processing of extra column data
- each behaviour token is one of 'generate', 'append-last', 'as-list', 'store'
- if set, the extra_columns parameter will customise the behaviour
- for example 'append-last:as-list'

***extra_columns***:
- Used to generate a name for any extra column (depending on parameter extra_columns_method)
- If set to a string containing '{' it will be treated as a format string to format the column number.
- If set to a function it will be called with a single argument of the column number.
- If set to None, then any extra data will be retained in the last column that was seen in the header.
- If set to 'merge', then the extra columns will be left appended to the last column.
- If set to a string (not containing a '{') and 'dictify' is set, then all extra columns will be placed in a key with that name (given by extra_columns)


### Error handling

***raise_error***:
- if False, then an error message will be stored which can be retrieved with GetError()
- if True, then an exception will be thrown.

### Row numbering

***row_numbers***:
- if a string and dictify is set, then the row number will be stored in the dict by the key specified by that string.
  For example row_numbers='_row',dictify=True   will produce rows like {'_row':0,...}

***row_number_style***:
- if 'absolute' or 'relative' then the row number produced will either include, or ignore, any skipped lines

### Skipping lines

A number of lines at the start of the file can be skipped using ```skip_count```.

Empty lines can be skipped using ```skip_empty_lines```.

Lines matching a regular expression can be skipped using ```skip```.

When a line is skipped the absolute line number count will continue to increment, however the relative line number / row number will not increment.

***skip_count***:
- set to an int to skip that many lines at the start of the file

***skip_empty_lines***:
- skip any empty lines

***skip***:
- sets a regex. lines which match this regular expression will be skipped.

### Separators, comment and quote characters

***comment_char***:
- sets the character that will cause a line to be skipped as a comment (not data)
- Defaults to '#'

***sep***:
- sets the character that separates columns
- Defaults to ','

***quotechar***:
- sets the quote character that will allow the separator character to be embedded in a column value
- defaults to a double quote ( " )


## Example contructor parameter use cases

### Example input data:


    a,b,c       #header
    1,2,3,d,e   #data

---
Parameters:

    dictify = False
    extra_column_method = 'generate'
    extra_columns = 'column_{}'

produces:

    columns (a,b,c,column_4,column_5)
    row ['a','b','c','d','e']

---

Parameters:

    dictify = False
    extra_column_method = 'append-last'

produces:

    columns (a,b,c)
    row ['a','b','c,d,e']

---

Parameters:

    dictify = False
    extra_column_method = 'append-last:as-list'

produces:

    columns (a,b,c)
    row ['a','b',['c','d','e']]

---

Parameters:

    dictify = False
    extra_column_method = 'store'
    extra_columns = 'extra_data'

produces:

    columns (a,b,c,extra_data)
    row ['a','b','c','d,e']

---

Parameters:

    dictify = False
    extra_column_method = 'store:as-list'
    extra_columns = 'extra_data'

produces:

    columns (a,b,c,extra_data)
    row ['a','b','c',['d','e']]

---

Parameters:

    dictify = True
    extra_column_method = 'generate'
    extra_columns = 'column_{}'

produces:

    columns (a,b,c,column_4,column_5)
    row {'a':'a','b':'b','c':'c','column_4':'d','column_5': 'e'}

---

Parameters:

    dictify = True
    extra_column_method = 'append-last'

produces:

    columns (a,b,c)
    row {'a':'a','b':'b','c':'c,d,e'}

---

Parameters:

    dictify = True
    extra_column_method = 'append-last:as-list'


produces:

    columns (a,b,c)
    row {'a':'a','b':'b','c':['c','d','e']}


---


Parameters:

    dictify = True
    extra_column_method = 'store'
    extra_columns = 'extra_data'

produces:

    columns (a,b,c,column_4,column_5)
    row {'a':'a','b':'b','c':'c','extra_data':'d,e'}


---

Parameters:

    dictify = True
    extra_column_method = 'store:as-list'
    extra_columns = 'extra_data'

produces:

    columns (a,b,c,column_4,column_5)
    row {'a':'a','b':'b','c':'c','extra_data':['d','e']}


## Primary methods

###Use cases:

Read a file:

    reader = CsvReader()
    for row in reader.Read(path):
        do_something(row)

Read an array of line data:

    reader = CsvReader()
    for row in reader.ProcessLines(lines):
        do_something(row)

Read a multi-line chunk of text data:

    reader = CsvReader()
    for row in reader.ProcessData(multiline_text):
        do_something(row)



### csvreader.Read(path)

Begins processing a CSV file and returns a generator which will yield each row

### csvreader.ProcessLines(lines)

Begins processing a list of lines and returns a generator which will yield each row


### csvreader.ProcessData(text)

Begins processing a chunk of text data, splits it into lines and returns a generator which will yield each row



