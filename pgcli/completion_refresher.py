import threading
try:
    from collections import OrderedDict
except ImportError:
    from .packages.ordereddict import OrderedDict

from .pgcompleter import PGCompleter
from .pgexecute import PGExecute

class CompletionRefresher(object):

    refreshers = OrderedDict()

    def __init__(self):
        self._completer_thread = None
        self._restart_completion = threading.Event()

    def refresh(self, executor, special, callbacks):
        if self._completer_thread and self._completer_thread.is_alive():
            self._restart_completion.set()
            return [(None, None, None, 'Auto-completion refresh restarted.')]
        else:
            self._completer_thread = threading.Thread(target=self._bg_refresh,
                                                      args=(executor, special, callbacks),
                                                      name='completion_refresh')
            self._completer_thread.setDaemon(True)
            self._completer_thread.start()
            return [(None, None, None,
                     'Auto-completion refresh started in the background.')]

    def _bg_refresh(self, pgexecute, special, callbacks):
        completer = PGCompleter(smart_completion=True, pgspecial=special)

        # Create a new pgexecute method to popoulate the completions.
        e = pgexecute
        executor = PGExecute(e.dbname, e.user, e.password, e.host, e.port, e.dsn)

        if callable(callbacks):
            callbacks = [callbacks]

        while 1:
            for refresher in self.refreshers.values():
                refresher(completer, executor)
                if self._restart_completion.is_set():
                    self._restart_completion.clear()
                    break
            else:
                # Break out of while loop if the for loop finishes natually
                # without hitting the break statement.
                break

            # Start over the refresh from the beginning if the for loop hit the
            # break statement.
            continue

        for callback in callbacks:
            callback(completer)

def refresher(name, refreshers=CompletionRefresher.refreshers):
    """Decorator to populate the dictionary of refreshers with the current
    function.
    """
    def wrapper(wrapped):
        refreshers[name] = wrapped
        return wrapped
    return wrapper

@refresher('schemata')
def refresh_schemata(completer, executor):
    completer.set_search_path(executor.search_path())
    completer.extend_schemata(executor.schemata())

@refresher('tables')
def refresh_tables(completer, executor):
    completer.extend_relations(executor.tables(),
                                      kind='tables')
    completer.extend_columns(executor.table_columns(),
                                    kind='tables')

@refresher('views')
def refresh_views(completer, executor):
    completer.extend_relations(executor.views(), kind='views')
    completer.extend_columns(executor.view_columns(),
                                    kind='views')

@refresher('functions')
def refresh_functions(completer, executor):
    completer.extend_functions(executor.functions())

@refresher('types')
def refresh_types(completer, executor):
    completer.extend_datatypes(executor.datatypes())

@refresher('databases')
def refresh_databases(completer, executor):
    completer.extend_database_names(executor.databases())
