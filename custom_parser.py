from nltk.parse.chart import ParserI, Tree, LeafInitRule
from nltk.parse.featurechart import FeatureEmptyPredictRule, FeatureBottomUpPredictCombineRule, \
    FeatureSingleEdgeFundamentalRule

from custom_chart import FeatureChart


class Parser(ParserI):
    """
    This is a custom parser for Features-based context grammar
    Parsed algorithm: Bottom up left corner
    Parsed structure: FeatureChart
    """

    def __init__(self, grammar, trace=None):
        self._grammar = grammar
        self._strategy = [
            LeafInitRule(),
            FeatureEmptyPredictRule(),
            FeatureBottomUpPredictCombineRule(),
            FeatureSingleEdgeFundamentalRule(),
        ]
        self._chart_class = FeatureChart

        # For trace
        self._trace = trace
        self._trace_chart_width = 50

        self._axioms = []
        self._inference_rules = []
        for rule in self._strategy:
            if rule.NUM_EDGES == 0:
                self._axioms.append(rule)
            elif rule.NUM_EDGES == 1:
                self._inference_rules.append(rule)
            else:
                self._use_agenda = False

    def grammar(self):
        return self._grammar

    def _trace_new_edges(self, chart, rule, new_edges, trace, edge_width):
        if not trace:
            return
        print_rule_header = trace > 1
        for edge in new_edges:
            if print_rule_header:
                print("%s:" % rule)
                print_rule_header = False
            print(chart.pretty_format_edge(edge, edge_width))

    def chart_parse(self, tokens, trace=None):
        """
        Return the final parse ``Chart`` from which all possible
        parse trees can be extracted.

        :param tokens: The sentence to be parsed
        :type tokens: list(str)
        :rtype: Chart
        """
        if trace is None:
            trace = self._trace
        trace_new_edges = self._trace_new_edges

        tokens = list(tokens)
        self._grammar.check_coverage(tokens)
        chart = self._chart_class(tokens)
        grammar = self._grammar

        # Width, for printing trace edges.
        trace_edge_width = self._trace_chart_width // (chart.num_leaves() + 1)
        if trace:
            print(chart.pretty_format_leaves(trace_edge_width))

        edges_added = True
        while edges_added:
            edges_added = False
            for rule in self._strategy:
                new_edges = list(rule.apply_everywhere(chart, grammar))
                edges_added = len(new_edges)
                trace_new_edges(chart, rule, new_edges, trace, trace_edge_width)

        # Return the final chart.
        return chart

    def parse(self, tokens, tree_class=Tree):
        chart = self.chart_parse(tokens)
        return iter(chart.parses(self._grammar.start(), tree_class=tree_class))
