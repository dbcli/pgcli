# coding=UTF-8
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

def test_unicode_expanded_table():
    input = [(u'ö', 123)]

    expected = u"""-[ RECORD 0 ]-------------------------
name | ö
age  | 123
"""
    assert expected == expanded_table(input, ["name", "age"])
