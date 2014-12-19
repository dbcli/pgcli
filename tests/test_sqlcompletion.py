from pgcli.packages.sqlcompletion import suggest_type

class TestSqlCompletion:
    def test_lparen_suggest_cols(self):
        suggestion = suggest_type('SELECT MAX( FROM table_name', 'SELECT MAX(')
        assert (suggestion and suggestion[0] == 'columns')

    def test_select_suggest_cols_and_funcs(self):
        suggestion = suggest_type('SELECT ', 'SELECT ')
        assert (suggestion and suggestion[0] == 'columns-and-functions')

    def test_from_suggest_tables(self):
        suggestion = suggest_type('SELECT * FROM ', 'SELECT * FROM ')
        assert (suggestion and suggestion[0] == 'tables')

    def test_distinct_suggest_cols(self):
        suggestion = suggest_type('SELECT DISTINCT ', 'SELECT DISTINCT ')
        assert (suggestion and suggestion[0] == 'columns')
