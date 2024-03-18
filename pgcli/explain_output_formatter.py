from pgcli.pyev import Visualizer
import json


"""Explain response output adapter"""


class ExplainOutputFormatter:
    def __init__(self, max_width):
        self.max_width = max_width

    def format_output(self, cur, headers, **output_kwargs):
        # explain query results should always contain 1 row each
        [(data,)] = list(cur)
        explain_list = json.loads(data)
        visualizer = Visualizer(self.max_width)
        for explain in explain_list:
            visualizer.load(explain)
            yield visualizer.get_list()
