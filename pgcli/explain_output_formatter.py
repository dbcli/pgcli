from pgcli.pyev import Visualizer
import json


"""Explain response output adapter"""


class ExplainOutputFormatter:
    def format_output(self, cur, headers, **output_kwargs):
        (data,) = cur.fetchone()
        explain_list = json.loads(data)
        visualizer = Visualizer(210)
        for explain in explain_list:
            visualizer.load(explain)
            yield visualizer.get_list()
