from pgcli.packages.prioritization import PrevalenceCounter


def test_prevalence_counter():
    counter = PrevalenceCounter()
    sql = """SELECT * FROM foo WHERE bar GROUP BY baz;
             select * from foo;
             SELECT * FROM foo WHERE bar GROUP
             BY baz"""
    counter.update(sql)

    keywords = ["SELECT", "FROM", "GROUP BY"]
    expected = [3, 3, 2]
    kw_counts = [counter.keyword_count(x) for x in keywords]
    assert kw_counts == expected
    assert counter.keyword_count("NOSUCHKEYWORD") == 0

    names = ["foo", "bar", "baz"]
    name_counts = [counter.name_count(x) for x in names]
    assert name_counts == [3, 2, 2]
