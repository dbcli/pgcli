from pgcli.packages.expanded import expanded_table

def test_expanded_table_renders():
    input = [("hello", 123),("world", 456)]

    expected = """-[ RECORD 0 ]-------------------------
name | hello
age  | 123
-[ RECORD 1 ]-------------------------
name | world
age  | 456
"""
    assert expected == expanded_table(input, ["name", "age"])
