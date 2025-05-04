import pytest
from unittest.mock import patch

from pgcli.packages.llm import (
    USAGE,
    FinishIteration,
    handle_llm,
    is_llm_command,
    sql_using_llm,
)


@pytest.fixture
def executor():
    # Dummy executor for handle_llm
    return None


@patch("pgcli.packages.llm.llm")
def test_llm_command_without_args(mock_llm, executor):
    r"""
    Invoking \llm without any arguments should print the usage and raise FinishIteration.
    """
    test_text = r"\\llm"
    with pytest.raises(FinishIteration) as exc_info:
        handle_llm(test_text, executor)
    assert exc_info.value.args[0] == [(None, None, None, USAGE)]


@patch("pgcli.packages.llm.llm")
@patch("pgcli.packages.llm.run_external_cmd")
def test_llm_command_with_c_flag(mock_run_cmd, mock_llm, executor):
    # Suppose the LLM returns some text without fenced SQL
    mock_run_cmd.return_value = (0, "Hello, no SQL today.")
    test_text = r"\\llm -c 'Something?'"
    with pytest.raises(FinishIteration) as exc_info:
        handle_llm(test_text, executor)
    # Expect raw output when no SQL fence found
    assert exc_info.value.args[0] == [(None, None, None, "Hello, no SQL today.")]


@patch("pgcli.packages.llm.llm")
@patch("pgcli.packages.llm.run_external_cmd")
def test_llm_command_with_c_flag_and_fenced_sql(mock_run_cmd, mock_llm, executor):
    # Return text containing a fenced SQL block
    sql_text = "SELECT * FROM users;"
    fenced = f"Here you go:\n```sql\n{sql_text}\n```"
    mock_run_cmd.return_value = (0, fenced)
    test_text = r"\\llm -c 'Rewrite SQL'"
    result, sql, duration = handle_llm(test_text, executor)
    # Without verbose, result is empty, sql extracted
    assert sql == sql_text
    assert result == ""
    assert isinstance(duration, float)


@patch("pgcli.packages.llm.llm")
@patch("pgcli.packages.llm.run_external_cmd")
def test_llm_command_known_subcommand(mock_run_cmd, mock_llm, executor):
    # 'models' is a known subcommand
    test_text = r"\\llm models"
    with pytest.raises(FinishIteration) as exc_info:
        handle_llm(test_text, executor)
    mock_run_cmd.assert_called_once_with("llm", "models", restart_cli=False)
    assert exc_info.value.args[0] is None


@patch("pgcli.packages.llm.llm")
@patch("pgcli.packages.llm.run_external_cmd")
def test_llm_command_with_help_flag(mock_run_cmd, mock_llm, executor):
    test_text = r"\\llm --help"
    with pytest.raises(FinishIteration) as exc_info:
        handle_llm(test_text, executor)
    mock_run_cmd.assert_called_once_with("llm", "--help", restart_cli=False)
    assert exc_info.value.args[0] is None


@patch("pgcli.packages.llm.llm")
@patch("pgcli.packages.llm.run_external_cmd")
def test_llm_command_with_install_flag(mock_run_cmd, mock_llm, executor):
    test_text = r"\\llm install openai"
    with pytest.raises(FinishIteration) as exc_info:
        handle_llm(test_text, executor)
    mock_run_cmd.assert_called_once_with("llm", "install", "openai", restart_cli=True)
    assert exc_info.value.args[0] is None


@patch("pgcli.packages.llm.llm")
@patch("pgcli.packages.llm.ensure_pgcli_template")
@patch("pgcli.packages.llm.sql_using_llm")
def test_llm_command_with_prompt(mock_sql_using_llm, mock_ensure_template, mock_llm, executor):
    r"""
    \llm prompt 'question' should use template and call sql_using_llm
    """
    mock_sql_using_llm.return_value = ("CTX", "SELECT 1;")
    test_text = r"\\llm prompt 'Test?'"
    context, sql, duration = handle_llm(test_text, executor)
    mock_ensure_template.assert_called_once()
    mock_sql_using_llm.assert_called()
    assert context == ""
    assert sql == "SELECT 1;"
    assert isinstance(duration, float)


@patch("pgcli.packages.llm.llm")
@patch("pgcli.packages.llm.ensure_pgcli_template")
@patch("pgcli.packages.llm.sql_using_llm")
def test_llm_command_question_with_context(mock_sql_using_llm, mock_ensure_template, mock_llm, executor):
    r"""
    \llm 'question' treats as prompt and returns SQL
    """
    mock_sql_using_llm.return_value = ("CTX2", "SELECT 2;")
    test_text = r"\\llm 'Top 10?'"
    context, sql, duration = handle_llm(test_text, executor)
    mock_ensure_template.assert_called_once()
    mock_sql_using_llm.assert_called()
    assert context == ""
    assert sql == "SELECT 2;"
    assert isinstance(duration, float)


@patch("pgcli.packages.llm.llm")
@patch("pgcli.packages.llm.ensure_pgcli_template")
@patch("pgcli.packages.llm.sql_using_llm")
def test_llm_command_question_verbose(mock_sql_using_llm, mock_ensure_template, mock_llm, executor):
    r"""
    \llm+ returns verbose context and SQL
    """
    mock_sql_using_llm.return_value = ("VERBOSE_CTX", "SELECT 42;")
    test_text = r"\\llm+ 'Verbose?'"
    context, sql, duration = handle_llm(test_text, executor)
    assert context == "VERBOSE_CTX"
    assert sql == "SELECT 42;"
    assert isinstance(duration, float)


def test_is_llm_command():
    # Valid llm command variants
    for cmd in ["\\llm 'x'", "\\ai 'x'", "\\llm+ 'x'", "\\ai+ 'x'"]:
        assert is_llm_command(cmd)
    # Invalid commands
    assert not is_llm_command("select * from table;")


@patch("pgcli.packages.llm.run_external_cmd")
def test_sql_using_llm_no_connection(mock_run_cmd):
    # Should error if no database cursor provided
    with pytest.raises(RuntimeError) as exc_info:
        sql_using_llm(None, question="test")
    assert "Connect to a database" in str(exc_info.value)


@patch("pgcli.packages.llm.PGExecute.table_columns")
@patch("pgcli.packages.llm.run_external_cmd")
def test_sql_using_llm_success(mock_run_cmd, mock_table_columns):
    # Setup table columns from PGExecute
    mock_table_columns.return_value = [
        ("public", "table1", "col1", "int", None, None),
        ("public", "table2", "colA", "varchar(20)", None, None),
    ]

    # Dummy cursor for metadata and sample data
    class DummyConn:
        def cursor(self):
            return self

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    class DummyCur:
        def __init__(self):
            self.connection = DummyConn()
            self._row = None
            self.description = None

        def execute(self, query):
            if "current_schema" in query:
                self._row = ("public",)
            elif query.strip().upper().startswith("SELECT * FROM"):
                self.description = [("col1", None), ("col2", None)]
                self._row = (1, "abc")

        def fetchone(self):
            return self._row

    dummy_cur = DummyCur()
    sql_text = "SELECT 1, 'abc';"
    fenced = f"Note\n```sql\n{sql_text}\n```"
    mock_run_cmd.return_value = (0, fenced)
    result, sql = sql_using_llm(dummy_cur, question="dummy", verbose=False)
    assert result == fenced
    assert sql == sql_text


@pytest.mark.parametrize("prefix", [r"\\llm", r".llm", r"\\ai", r".ai"])
def test_handle_llm_aliases_without_args(prefix, executor, monkeypatch):
    # Ensure llm is available to prevent import errors
    import pgcli.packages.llm as llm_module

    monkeypatch.setattr(llm_module, "llm", object())
    with pytest.raises(FinishIteration) as exc_info:
        handle_llm(prefix, executor)
    assert exc_info.value.args[0] == [(None, None, None, USAGE)]
