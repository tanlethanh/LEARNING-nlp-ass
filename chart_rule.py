import re
from nltk.parse.chart import ChartRuleI, TreeEdge, LeafEdge

class AbstractChartRule(ChartRuleI):
    """
    An abstract base class for chart rules.  ``AbstractChartRule``
    provides:

    - A default implementation for ``apply``.
    - A default implementation for ``apply_everywhere``,
      (Currently, this implementation assumes that ``NUM_EDGES <= 3``.)
    - A default implementation for ``__str__``, which returns a
      name based on the rule's class name.
    """

    # Subclasses must define apply.
    def apply(self, chart, grammar, *edges):
        raise NotImplementedError()

    # Default: loop through the given number of edges, and call
    # self.apply() for each set of edges.
    def apply_everywhere(self, chart, grammar):
        if self.NUM_EDGES == 0:
            yield from self.apply(chart, grammar)

        elif self.NUM_EDGES == 1:
            for e1 in chart:
                yield from self.apply(chart, grammar, e1)

        elif self.NUM_EDGES == 2:
            for e1 in chart:
                for e2 in chart:
                    yield from self.apply(chart, grammar, e1, e2)

        elif self.NUM_EDGES == 3:
            for e1 in chart:
                for e2 in chart:
                    for e3 in chart:
                        yield from self.apply(chart, grammar, e1, e2, e3)

        else:
            raise AssertionError("NUM_EDGES>3 is not currently supported")

    # Default: return a name based on the class name.
    def __str__(self):
        # Add spaces between InitialCapsWords.
        return re.sub("([a-z])([A-Z])", r"\1 \2", self.__class__.__name__)
    
    
class LeafInitRule(AbstractChartRule):
    NUM_EDGES = 0

    def apply(self, chart, grammar):
        for index in range(chart.num_leaves()):
            new_edge = LeafEdge(chart.leaf(index), index)
            if chart.insert(new_edge, ()):
                yield new_edge
                
                
class EmptyPredictRule(AbstractChartRule):
    """
    A rule that inserts all empty productions as passive edges,
    in every position in the chart.
    """

    NUM_EDGES = 0

    def apply(self, chart, grammar):
        for prod in grammar.productions(empty=True):
            for index in range(chart.num_leaves() + 1):
                new_edge = TreeEdge.from_production(prod, index)
                if chart.insert(new_edge, ()):
                    yield new_edge
                    
    
class BottomUpPredictCombineRule(AbstractChartRule):
    r"""
    A rule licensing any edge corresponding to a production whose
    right-hand side begins with a complete edge's left-hand side.  In
    particular, this rule specifies that ``[A -> alpha \*]``
    licenses the edge ``[B -> A \* beta]`` for each grammar
    production ``B -> A beta``.

    :note: This is like ``BottomUpPredictRule``, but it also applies
        the ``FundamentalRule`` to the resulting edge.
    """

    NUM_EDGES = 1

    def apply(self, chart, grammar, edge):
        if edge.is_incomplete():
            return
        for prod in grammar.productions(rhs=edge.lhs()):
            new_edge = TreeEdge(edge.span(), prod.lhs(), prod.rhs(), 1)
            if chart.insert(new_edge, (edge,)):
                yield new_edge
                

class SingleEdgeFundamentalRule(AbstractChartRule):
    r"""
    A rule that joins a given edge with adjacent edges in the chart,
    to form combined edges.  In particular, this rule specifies that
    either of the edges:

    - ``[A -> alpha \* B beta][i:j]``
    - ``[B -> gamma \*][j:k]``

    licenses the edge:

    - ``[A -> alpha B * beta][i:j]``

    if the other edge is already in the chart.

    :note: This is basically ``FundamentalRule``, with one edge left
        unspecified.
    """

    NUM_EDGES = 1

    def apply(self, chart, grammar, edge):
        if edge.is_incomplete():
            yield from self._apply_incomplete(chart, grammar, edge)
        else:
            yield from self._apply_complete(chart, grammar, edge)

    def _apply_complete(self, chart, grammar, right_edge):
        for left_edge in chart.select(
            end=right_edge.start(), is_complete=False, nextsym=right_edge.lhs()
        ):
            new_edge = left_edge.move_dot_forward(right_edge.end())
            if chart.insert_with_backpointer(new_edge, left_edge, right_edge):
                yield new_edge

    def _apply_incomplete(self, chart, grammar, left_edge):
        for right_edge in chart.select(
            start=left_edge.end(), is_complete=True, lhs=left_edge.nextsym()
        ):
            new_edge = left_edge.move_dot_forward(right_edge.end())
            if chart.insert_with_backpointer(new_edge, left_edge, right_edge):
                yield new_edge