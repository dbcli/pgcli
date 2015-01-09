def pad(field, total, char=u" "):
    return field + (char * (total - len(field)))

def get_separator(num, header_len, data_len):
    total_len = header_len + data_len + 1

    sep = u"-[ RECORD {0} ]".format(unicode(num))
    if len(sep) < header_len:
        sep = pad(sep, header_len - 1, u"-") + u"+"

    if len(sep) < total_len:
        sep = pad(sep, total_len, u"-")

    return sep + u"\n"

def expanded_table(rows, headers):
    header_len = max([len(x) for x in headers])
    max_row_len = 0
    results = []

    padded_headers = [pad(x, header_len) + u" |" for x in headers]
    header_len += 2

    for row in rows:
        row_len = max([len(str(x)) for x in row])
        row_result = ""
        if row_len > max_row_len:
            max_row_len = row_len

        for item in zip(padded_headers, row):
            row_result += item[0] + u" " + unicode(item[1]) + u"\n"

        results.append(row_result)

    output = ""
    for i, result in enumerate(results):
        output += get_separator(i, header_len, max_row_len)
        output += result

    return output

