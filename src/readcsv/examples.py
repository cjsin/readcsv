import sys
import os
import textwrap
import tempfile

from readcsv.csvreader import CsvReader

EXAMPLE_DATA=textwrap.dedent("""\
    a,b,c,d
    abra,11,cadabra,13,
    hello,12,world,14,
    """)

def msg(*args):
    print(" ".join(str(x) for x in args), file=sys.stderr)

def dump_row(row):
    msg("Row:", row)

def dump_rows(rows):
    for r in rows:
        dump_row(r)

def example_1():
    """Read an array of line data"""
    lines = EXAMPLE_DATA.splitlines()
    reader = CsvReader()
    rows = [ r for r in reader.ProcessLines(lines)]
    dump_rows(rows)

def example_2():
    """Read a multi-line chunk of text data"""
    reader = CsvReader()
    rows = [ r for r in reader.ProcessData(EXAMPLE_DATA)]
    for row in rows:
        dump_row(row)

def example_3():
    """Read a csv file"""
    fd, path = tempfile.mkstemp(".csv")
    with open(fd, "w") as f:
        print(EXAMPLE_DATA, file=f)

    reader = CsvReader()
    for row in reader.Read(path):
        dump_row(row)
    os.unlink(path)

def run_examples():
    example_1()
    example_2()
    example_3()

if __name__ == "__main__":
    run_examples()
