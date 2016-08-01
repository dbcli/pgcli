from .tabulate import _text_type

def pad(field, total, char=u" "):
    return field + (char * (total - len(field)))

def expanded_table(rows, headers, missingval=""):
    header_len = max([len(x) for x in headers])
    max_row_len = 0
    results = []
    sep = u"-[ RECORD {0} ]-------------------------\n"

    padded_headers = [pad(x, header_len) + u" |" for x in headers]
    header_len += 2

    for row in rows:
        row_len = max([len(_text_type(x)) for x in row])
        row_result = []
        if row_len > max_row_len:
            max_row_len = row_len

        for header, value in zip(padded_headers, row):
            value = missingval if value is None else value
            row_result.append((u"%s" % header) + " " + (u"%s" % value).strip())

        results.append('\n'.join(row_result))

    output = []
    for i, result in enumerate(results):
        output.append(sep.format(i))
        output.append(result)
        output.append('\n')

    return ''.join(output)
