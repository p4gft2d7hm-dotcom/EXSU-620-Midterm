"""Exercise the actual SQLite helper function definitions without web packages.

AST extraction excludes FastAPI/uvicorn setup and all network/serial operations.
This tests storage and summary logic, not the HTTP server or notification path.
"""
import ast
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import contextlib
import time


def main():
    source = ast.parse(Path(__file__).with_name('server.py').read_text())
    names = {'db', 'init_db', 'store', 'shift_start', 'shift_summary'}
    selected = ast.Module(body=[node for node in source.body
                               if isinstance(node, ast.FunctionDef) and node.name in names],
                          type_ignores=[])
    # An in-memory database keeps the helper test self-contained and read-only
    # with respect to the user's filesystem. Network and db-path setup excluded.
    with contextlib.closing(sqlite3.connect(':memory:')) as connection:
        connection.row_factory = sqlite3.Row
        pushed = []
        env = dict(sqlite3=sqlite3, datetime=datetime, timedelta=timedelta,
                   time=time, DB_PATH=':memory:',
                   SHIFT_STARTS=[7,15,23], latest={'t':0,'data':None},
                   push=pushed.append)
        exec(compile(selected, 'server.py:SQLite helpers', 'exec'), env)
        env['db'] = lambda: connection
        env['init_db']()
        env['store']({'pos':'supine', 'state':'critical', 'ev':[
            ('configuration','{"bench_mode":true}'),
            ('interval_expired','elapsed_s=7200.000'), ('critical',''),
            ('turn','lateral'), ('interval_expired','elapsed_s=7200.000')]})
        summary = env['shift_summary']()
        assert summary['audited_expiries'] == 2, summary
        assert summary['late_intervals'] == 1, summary
        assert pushed == ['critical'], pushed  # audit does not repeat notification
        with env['db']() as con:
            assert con.execute('SELECT COUNT(*) FROM events').fetchone()[0] == 5
            assert con.execute('SELECT COUNT(*) FROM samples').fetchone()[0] == 1
        print('PASS SQLite persistence: two audit expiries, one critical entry; no audit push')
        print('Legacy compliance formula is unchanged; HTTP/serial/network are not tested.')


if __name__ == '__main__':
    main()
