from contextlib import closing

fname = "pandas-df.py"
fname = "python-context-closing.py"
with closing( open( fname ) ) as f :
    print( f.read() )


