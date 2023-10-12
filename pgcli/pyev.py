import textwrap
import re
from click import style as color

DESCRIPTIONS = {
    "Append": "Used in a UNION to merge multiple record sets by appending them together.",
    "Limit": "Returns a specified number of rows from a record set.",
    "Sort": "Sorts a record set based on the specified sort key.",
    "Nested Loop": "Merges two record sets by looping through every record in the first set and trying to find a match in the second set. All matching records are returned.",
    "Merge Join": "Merges two record sets by first sorting them on a join key.",
    "Hash": "Generates a hash table from the records in the input recordset. Hash is used by Hash Join.",
    "Hash Join": "Joins to record sets by hashing one of them (using a Hash Scan).",
    "Aggregate": "Groups records together based on a GROUP BY or aggregate function (e.g. sum()).",
    "Hashaggregate": "Groups records together based on a GROUP BY or aggregate function (e.g. sum()). Hash Aggregate uses a hash to first organize the records by a key.",
    "Sequence Scan": "Finds relevant records by sequentially scanning the input record set. When reading from a table, Seq Scans (unlike Index Scans) perform a single read operation (only the table is read).",
    "Seq Scan": "Finds relevant records by sequentially scanning the input record set. When reading from a table, Seq Scans (unlike Index Scans) perform a single read operation (only the table is read).",
    "Index Scan": "Finds relevant records based on an Index. Index Scans perform 2 read operations: one to read the index and another to read the actual value from the table.",
    "Index Only Scan": "Finds relevant records based on an Index. Index Only Scans perform a single read operation from the index and do not read from the corresponding table.",
    "Bitmap Heap Scan": "Searches through the pages returned by the Bitmap Index Scan for relevant rows.",
    "Bitmap Index Scan": "Uses a Bitmap Index (index which uses 1 bit per page) to find all relevant pages. Results of this node are fed to the Bitmap Heap Scan.",
    "CTEScan": "Performs a sequential scan of Common Table Expression (CTE) query results. Note that results of a CTE are materialized (calculated and temporarily stored).",
    "ProjectSet": "ProjectSet appears when the SELECT or ORDER BY clause of the query.  They basically just execute the set-returning function(s) for each tuple until none of the functions return any more records.",
    "Result": "Returns result",
}


class Visualizer:
    def __init__(self, terminal_width=100, color=True):
        self.color = color
        self.terminal_width = terminal_width
        self.string_lines = []

    def load(self, explain_dict):
        self.plan = explain_dict.pop("Plan")
        self.explain = explain_dict
        self.process_all()
        self.generate_lines()

    def process_all(self):
        self.plan = self.process_plan(self.plan)
        self.plan = self.calculate_outlier_nodes(self.plan)

    #
    def process_plan(self, plan):
        plan = self.calculate_planner_estimate(plan)
        plan = self.calculate_actuals(plan)
        self.calculate_maximums(plan)
        #
        for index in range(len(plan.get("Plans", []))):
            _plan = plan["Plans"][index]
            plan["Plans"][index] = self.process_plan(_plan)
        return plan

    def prefix_format(self, v):
        if self.color:
            return color(v, fg="bright_black")
        return v

    def tag_format(self, v):
        if self.color:
            return color(v, fg="white", bg="red")
        return v

    def muted_format(self, v):
        if self.color:
            return color(v, fg="bright_black")
        return v

    def bold_format(self, v):
        if self.color:
            return color(v, fg="white")
        return v

    def good_format(self, v):
        if self.color:
            return color(v, fg="green")
        return v

    def warning_format(self, v):
        if self.color:
            return color(v, fg="yellow")
        return v

    def critical_format(self, v):
        if self.color:
            return color(v, fg="red")
        return v

    def output_format(self, v):
        if self.color:
            return color(v, fg="cyan")
        return v

    def calculate_planner_estimate(self, plan):
        plan["Planner Row Estimate Factor"] = 0
        plan["Planner Row Estimate Direction"] = "Under"

        if plan["Plan Rows"] == plan["Actual Rows"]:
            return plan

        if plan["Plan Rows"] != 0:
            plan["Planner Row Estimate Factor"] = (
                plan["Actual Rows"] / plan["Plan Rows"]
            )

        if plan["Planner Row Estimate Factor"] < 10:
            plan["Planner Row Estimate Factor"] = 0
            plan["Planner Row Estimate Direction"] = "Over"
            if plan["Actual Rows"] != 0:
                plan["Planner Row Estimate Factor"] = (
                    plan["Plan Rows"] / plan["Actual Rows"]
                )
        return plan

    #
    def calculate_actuals(self, plan):
        plan["Actual Duration"] = plan["Actual Total Time"]
        plan["Actual Cost"] = plan["Total Cost"]

        for child in plan.get("Plans", []):
            if child["Node Type"] != "CTEScan":
                plan["Actual Duration"] = (
                    plan["Actual Duration"] - child["Actual Total Time"]
                )
                plan["Actual Cost"] = plan["Actual Cost"] - child["Total Cost"]

        if plan["Actual Cost"] < 0:
            plan["Actual Cost"] = 0

        plan["Actual Duration"] = plan["Actual Duration"] * plan["Actual Loops"]
        return plan

    def calculate_outlier_nodes(self, plan):
        plan["Costliest"] = plan["Actual Cost"] == self.explain["Max Cost"]
        plan["Largest"] = plan["Actual Rows"] == self.explain["Max Rows"]
        plan["Slowest"] = plan["Actual Duration"] == self.explain["Max Duration"]

        for index in range(len(plan.get("Plans", []))):
            _plan = plan["Plans"][index]
            plan["Plans"][index] = self.calculate_outlier_nodes(_plan)
        return plan

    def calculate_maximums(self, plan):
        if not self.explain.get("Max Rows"):
            self.explain["Max Rows"] = plan["Actual Rows"]
        elif self.explain.get("Max Rows") < plan["Actual Rows"]:
            self.explain["Max Rows"] = plan["Actual Rows"]

        if not self.explain.get("Max Cost"):
            self.explain["Max Cost"] = plan["Actual Cost"]
        elif self.explain.get("Max Cost") < plan["Actual Cost"]:
            self.explain["Max Cost"] = plan["Actual Cost"]

        if not self.explain.get("Max Duration"):
            self.explain["Max Duration"] = plan["Actual Duration"]
        elif self.explain.get("Max Duration") < plan["Actual Duration"]:
            self.explain["Max Duration"] = plan["Actual Duration"]

        if not self.explain.get("Total Cost"):
            self.explain["Total Cost"] = plan["Actual Cost"]
        elif self.explain.get("Total Cost") < plan["Actual Cost"]:
            self.explain["Total Cost"] = plan["Actual Cost"]

    #
    def duration_to_string(self, value):
        if value < 1:
            return self.good_format("<1 ms")
        elif value < 100:
            return self.good_format("%.2f ms" % value)
        elif value < 1000:
            return self.warning_format("%.2f ms" % value)
        elif value < 60000:
            return self.critical_format(
                "%.2f s" % (value / 1000.0),
            )
        else:
            return self.critical_format(
                "%.2f m" % (value / 60000.0),
            )

    # }
    #
    def format_details(self, plan):
        details = []

        if plan.get("Scan Direction"):
            details.append(plan["Scan Direction"])

        if plan.get("Strategy"):
            details.append(plan["Strategy"])

        if len(details) > 0:
            return self.muted_format(" [%s]" % ", ".join(details))

        return ""

    def format_tags(self, plan):
        tags = []

        if plan["Slowest"]:
            tags.append(self.tag_format("slowest"))
        if plan["Costliest"]:
            tags.append(self.tag_format("costliest"))
        if plan["Largest"]:
            tags.append(self.tag_format("largest"))
        if plan.get("Planner Row Estimate Factor", 0) >= 100:
            tags.append(self.tag_format("bad estimate"))

        return " ".join(tags)

    def get_terminator(self, index, plan):
        if index == 0:
            if len(plan.get("Plans", [])) == 0:
                return "⌡► "
            else:
                return "├►  "
        else:
            if len(plan.get("Plans", [])) == 0:
                return "   "
            else:
                return "│  "

    def wrap_string(self, line, width):
        if width == 0:
            return [line]
        return textwrap.wrap(line, width)

    def intcomma(self, value):
        sep = ","
        if not isinstance(value, str):
            value = int(value)

        orig = str(value)

        new = re.sub(r"^(-?\d+)(\d{3})", rf"\g<1>{sep}\g<2>", orig)
        if orig == new:
            return new
        else:
            return self.intcomma(new)

    def output_fn(self, current_prefix, string):
        return "%s%s" % (self.prefix_format(current_prefix), string)

    def create_lines(self, plan, prefix, depth, width, last_child):
        current_prefix = prefix
        self.string_lines.append(
            self.output_fn(current_prefix, self.prefix_format("│"))
        )

        joint = "├"
        if last_child:
            joint = "└"
        #
        self.string_lines.append(
            self.output_fn(
                current_prefix,
                "%s %s%s %s"
                % (
                    self.prefix_format(joint + "─⌠"),
                    self.bold_format(plan["Node Type"]),
                    self.format_details(plan),
                    self.format_tags(plan),
                ),
            )
        )
        #
        if last_child:
            prefix += "  "
        else:
            prefix += "│ "

        current_prefix = prefix + "│ "

        cols = width - len(current_prefix)

        for line in self.wrap_string(
            DESCRIPTIONS.get(plan["Node Type"], "Not found : %s" % plan["Node Type"]),
            cols,
        ):
            self.string_lines.append(
                self.output_fn(current_prefix, "%s" % self.muted_format(line))
            )
        #
        if plan.get("Actual Duration"):
            self.string_lines.append(
                self.output_fn(
                    current_prefix,
                    "○ %s %s (%.0f%%)"
                    % (
                        "Duration:",
                        self.duration_to_string(plan["Actual Duration"]),
                        (plan["Actual Duration"] / self.explain["Execution Time"])
                        * 100,
                    ),
                )
            )

        self.string_lines.append(
            self.output_fn(
                current_prefix,
                "○ %s %s (%.0f%%)"
                % (
                    "Cost:",
                    self.intcomma(plan["Actual Cost"]),
                    (plan["Actual Cost"] / self.explain["Total Cost"]) * 100,
                ),
            )
        )

        self.string_lines.append(
            self.output_fn(
                current_prefix,
                "○ %s %s" % ("Rows:", self.intcomma(plan["Actual Rows"])),
            )
        )

        current_prefix = current_prefix + "  "

        if plan.get("Join Type"):
            self.string_lines.append(
                self.output_fn(
                    current_prefix,
                    "%s %s" % (plan["Join Type"], self.muted_format("join")),
                )
            )

        if plan.get("Relation Name"):
            self.string_lines.append(
                self.output_fn(
                    current_prefix,
                    "%s %s.%s"
                    % (
                        self.muted_format("on"),
                        plan.get("Schema", "unknown"),
                        plan["Relation Name"],
                    ),
                )
            )

        if plan.get("Index Name"):
            self.string_lines.append(
                self.output_fn(
                    current_prefix,
                    "%s %s" % (self.muted_format("using"), plan["Index Name"]),
                )
            )

        if plan.get("Index Condition"):
            self.string_lines.append(
                self.output_fn(
                    current_prefix,
                    "%s %s" % (self.muted_format("condition"), plan["Index Condition"]),
                )
            )

        if plan.get("Filter"):
            self.string_lines.append(
                self.output_fn(
                    current_prefix,
                    "%s %s %s"
                    % (
                        self.muted_format("filter"),
                        plan["Filter"],
                        self.muted_format(
                            "[-%s rows]" % self.intcomma(plan["Rows Removed by Filter"])
                        ),
                    ),
                )
            )

        if plan.get("Hash Condition"):
            self.string_lines.append(
                self.output_fn(
                    current_prefix,
                    "%s %s" % (self.muted_format("on"), plan["Hash Condition"]),
                )
            )

        if plan.get("CTE Name"):
            self.string_lines.append(
                self.output_fn(current_prefix, "CTE %s" % plan["CTE Name"])
            )

        if plan.get("Planner Row Estimate Factor") != 0:
            self.string_lines.append(
                self.output_fn(
                    current_prefix,
                    "%s %sestimated %s %.2fx"
                    % (
                        self.muted_format("rows"),
                        plan["Planner Row Estimate Direction"],
                        self.muted_format("by"),
                        plan["Planner Row Estimate Factor"],
                    ),
                )
            )

        current_prefix = prefix

        if len(plan.get("Output", [])) > 0:
            for index, line in enumerate(
                self.wrap_string(" + ".join(plan["Output"]), cols)
            ):
                self.string_lines.append(
                    self.output_fn(
                        current_prefix,
                        self.prefix_format(self.get_terminator(index, plan))
                        + self.output_format(line),
                    )
                )

        for index, nested_plan in enumerate(plan.get("Plans", [])):
            self.create_lines(
                nested_plan, prefix, depth + 1, width, index == len(plan["Plans"]) - 1
            )

    def generate_lines(self):
        self.string_lines = [
            "○ Total Cost: %s" % self.intcomma(self.explain["Total Cost"]),
            "○ Planning Time: %s"
            % self.duration_to_string(self.explain["Planning Time"]),
            "○ Execution Time: %s"
            % self.duration_to_string(self.explain["Execution Time"]),
            self.prefix_format("┬"),
        ]
        self.create_lines(
            self.plan,
            "",
            0,
            self.terminal_width,
            len(self.plan.get("Plans", [])) == 1,
        )

    def get_list(self):
        return "\n".join(self.string_lines)

    def print(self):
        for lin in self.string_lines:
            print(lin)
