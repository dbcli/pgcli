__version__ = '0.18.0'

try:
    from psycopg2cffi import compat
except ImportError:
    pass
else:
    compat.register()
