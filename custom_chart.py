import itertools
from collections import OrderedDict

from nltk import Tree, TYPE, unify
from nltk.parse.chart import EdgeI, LeafEdge


class Chart():

    def __init__(self, tokens):
        """
        Construct a new chart. The chart is initialized with the
        leaf edges corresponding to the terminal leaves.
        """
        # Record the sentence token and the sentence length.
        self._tokens = tuple(tokens)
        self._num_leaves = len(self._tokens)

        # A list of edges contained in this chart.
        self._edges = []

        # The set of child pointer lists associated with each edge.
        self._edge_to_cpls = {}

        # Indexes mapping attribute values to lists of edges
        # (used by select()).
        self._indexes = {}

    def num_leaves(self):
        return self._num_leaves

    def leaf(self, index):
        return self._tokens[index]

    def leaves(self):
        return self._tokens

    def edges(self):
        return self._edges[:]

    def iteredges(self):
        return iter(self._edges)

    # Iterating over the chart yields its edges.
    __iter__ = iteredges

    def num_edges(self):
        return len(self._edge_to_cpls)

    def select(self, **restrictions):
        """
        Return an iterator over the edges in this chart.  Any
        new edges that are added to the chart before the iterator
        is exahusted will also be generated.  ``restrictions``
        can be used to restrict the set of edges that will be
        generated.
        """
        # If there are no restrictions, then return all edges.
        if restrictions == {}:
            return iter(self._edges)

        # Find the index corresponding to the given restrictions.
        restr_keys = sorted(restrictions.keys())
        restr_keys = tuple(restr_keys)

        # If it doesn't exist, then create it.
        if restr_keys not in self._indexes:
            self._add_index(restr_keys)

        vals = tuple(restrictions[key] for key in restr_keys)
        return iter(self._indexes[restr_keys].get(vals, []))

    def _add_index(self, restr_keys):
        """
        A helper function for ``select``, which creates a new index for
        a given set of attributes (aka restriction keys).
        """
        # Make sure it's a valid index.
        for key in restr_keys:
            if not hasattr(EdgeI, key):
                raise ValueError("Bad restriction: %s" % key)

        # Create the index.
        index = self._indexes[restr_keys] = {}

        # Add all existing edges to the index.
        for edge in self._edges:
            vals = tuple(getattr(edge, key)() for key in restr_keys)
            index.setdefault(vals, []).append(edge)

    def _register_with_indexes(self, edge):
        """
        A helper function for ``insert``, which registers the new
        edge with all existing indexes.
        """
        for (restr_keys, index) in self._indexes.items():
            vals = tuple(getattr(edge, key)() for key in restr_keys)
            index.setdefault(vals, []).append(edge)

    # ////////////////////////////////////////////////////////////
    # Edge Insertion
    # ////////////////////////////////////////////////////////////

    def insert_with_backpointer(self, new_edge, previous_edge, child_edge):
        """
        Add a new edge to the chart, using a pointer to the previous edge.
        """
        cpls = self.child_pointer_lists(previous_edge)
        new_cpls = [cpl + (child_edge,) for cpl in cpls]
        return self.insert(new_edge, *new_cpls)

    def insert(self, edge, *child_pointer_lists):
        """
        Add a new edge to the chart, and return True if this operation
        modified the chart.  In particular, return true iff the chart
        did not already contain ``edge``, or if it did not already associate
        ``child_pointer_lists`` with ``edge``.
        """
        # Is it a new edge?
        if edge not in self._edge_to_cpls:
            # Add it to the list of edges.
            self._append_edge(edge)
            # Register with indexes.
            self._register_with_indexes(edge)

        # Get the set of child pointer lists for this edge.
        cpls = self._edge_to_cpls.setdefault(edge, OrderedDict())
        chart_was_modified = False
        for child_pointer_list in child_pointer_lists:
            child_pointer_list = tuple(child_pointer_list)
            if child_pointer_list not in cpls:
                # It's a new CPL; register it, and return true.
                cpls[child_pointer_list] = True
                chart_was_modified = True
        return chart_was_modified

    def _append_edge(self, edge):
        self._edges.append(edge)

    # ////////////////////////////////////////////////////////////
    # Tree extraction & child pointer lists
    # ////////////////////////////////////////////////////////////

    def parses(self, root, tree_class=Tree):
        """
        Return an iterator of the complete tree structures that span
        the entire chart, and whose root node is ``root``.
        """
        for edge in self.select(start=0, end=self._num_leaves, lhs=root):
            yield from self.trees(edge, tree_class=tree_class, complete=True)

    def trees(self, edge, tree_class=Tree, complete=False):
        """
        Return an iterator of the tree structures that are associated
        with ``edge``.

        If ``edge`` is incomplete, then the unexpanded children will be
        encoded as childless subtrees, whose node value is the
        corresponding terminal or nonterminal.
        """
        return iter(self._trees(edge, complete, memo={}, tree_class=tree_class))

    def _trees(self, edge, complete, memo, tree_class):
        """
        A helper function for ``trees``.

        :param memo: A dictionary used to record the trees that we've
            generated for each edge, so that when we see an edge more
            than once, we can reuse the same trees.
        """
        # If we've seen this edge before, then reuse our old answer.
        if edge in memo:
            return memo[edge]

        # when we're reading trees off the chart, don't use incomplete edges
        if complete and edge.is_incomplete():
            return []

        # Leaf edges.
        if isinstance(edge, LeafEdge):
            leaf = self._tokens[edge.start()]
            memo[edge] = [leaf]
            return [leaf]

        # Until we're done computing the trees for edge, set
        # memo[edge] to be empty.  This has the effect of filtering
        # out any cyclic trees (i.e., trees that contain themselves as
        # descendants), because if we reach this edge via a cycle,
        # then it will appear that the edge doesn't generate any trees.
        memo[edge] = []
        trees = []
        lhs = edge.lhs().symbol()

        # Each child pointer list can be used to form trees.
        for cpl in self.child_pointer_lists(edge):
            # Get the set of child choices for each child pointer.
            # child_choices[i] is the set of choices for the tree's
            # ith child.
            child_choices = [self._trees(cp, complete, memo, tree_class) for cp in cpl]

            # For each combination of children, add a tree.
            for children in itertools.product(*child_choices):
                trees.append(tree_class(lhs, children))

        # If the edge is incomplete, then extend it with "partial trees":
        if edge.is_incomplete():
            unexpanded = [tree_class(elt, []) for elt in edge.rhs()[edge.dot():]]
            for tree in trees:
                tree.extend(unexpanded)

        # Update the memoization dictionary.
        memo[edge] = trees

        # Return the list of trees.
        return trees

    def child_pointer_lists(self, edge):
        """
        Return the set of child pointer lists for the given edge.
        Each child pointer list is a list of edges that have
        been used to form this edge.

        :rtype: list(list(EdgeI))
        """
        # Make a copy, in case they modify it.
        return self._edge_to_cpls.get(edge, {}).keys()

    # ////////////////////////////////////////////////////////////
    # Display
    # ////////////////////////////////////////////////////////////
    def pretty_format_edge(self, edge, width=None):
        """
        Return a pretty-printed string representation of a given edge
        in this chart.

        :rtype: str
        :param width: The number of characters allotted to each
            index in the sentence.
        """
        if width is None:
            width = 50 // (self.num_leaves() + 1)
        (start, end) = (edge.start(), edge.end())

        str = "|" + ("." + " " * (width - 1)) * start

        # Zero-width edges are "#" if complete, ">" if incomplete
        if start == end:
            if edge.is_complete():
                str += "#"
            else:
                str += ">"

        # Spanning complete edges are "[===]"; Other edges are
        # "[---]" if complete, "[--->" if incomplete
        elif edge.is_complete() and edge.span() == (0, self._num_leaves):
            str += "[" + ("=" * width) * (end - start - 1) + "=" * (width - 1) + "]"
        elif edge.is_complete():
            str += "[" + ("-" * width) * (end - start - 1) + "-" * (width - 1) + "]"
        else:
            str += "[" + ("-" * width) * (end - start - 1) + "-" * (width - 1) + ">"

        str += (" " * (width - 1) + ".") * (self._num_leaves - end)
        return str + "| %s" % edge

    def pretty_format_leaves(self, width=None):
        """
        Return a pretty-printed string representation of this
        chart's leaves.  This string can be used as a header
        for calls to ``pretty_format_edge``.
        """
        if width is None:
            width = 50 // (self.num_leaves() + 1)

        if self._tokens is not None and width > 1:
            header = "|."
            for tok in self._tokens:
                header += tok[: width - 1].center(width - 1) + "."
            header += "|"
        else:
            header = ""

        return header

    def pretty_format(self, width=None):
        """
        Return a pretty-printed string representation of this chart.
        """
        if width is None:
            width = 50 // (self.num_leaves() + 1)
        # sort edges: primary key=length, secondary key=start index.
        # (and filter out the token edges)
        edges = sorted((e.length(), e.start(), e) for e in self)
        edges = [e for (_, _, e) in edges]

        return (
                self.pretty_format_leaves(width)
                + "\n"
                + "\n".join(self.pretty_format_edge(edge, width) for edge in edges)
        )

    # ////////////////////////////////////////////////////////////
    # Display: Dot (AT&T Graphviz)
    # ////////////////////////////////////////////////////////////

    def dot_digraph(self):
        # Header
        s = "digraph nltk_chart {\n"
        # s += '  size="5,5";\n'
        s += "  rankdir=LR;\n"
        s += "  node [height=0.1,width=0.1];\n"
        s += '  node [style=filled, color="lightgray"];\n'

        # Set up the nodes
        for y in range(self.num_edges(), -1, -1):
            if y == 0:
                s += '  node [style=filled, color="black"];\n'
            for x in range(self.num_leaves() + 1):
                if y == 0 or (
                        x <= self._edges[y - 1].start() or x >= self._edges[y - 1].end()
                ):
                    s += '  %04d.%04d [label=""];\n' % (x, y)

        # Add a spacer
        s += "  x [style=invis]; x->0000.0000 [style=invis];\n"

        # Declare ranks.
        for x in range(self.num_leaves() + 1):
            s += "  {rank=same;"
            for y in range(self.num_edges() + 1):
                if y == 0 or (
                        x <= self._edges[y - 1].start() or x >= self._edges[y - 1].end()
                ):
                    s += " %04d.%04d" % (x, y)
            s += "}\n"

        # Add the leaves
        s += "  edge [style=invis, weight=100];\n"
        s += "  node [shape=plaintext]\n"
        s += "  0000.0000"
        for x in range(self.num_leaves()):
            s += "->%s->%04d.0000" % (self.leaf(x), x + 1)
        s += ";\n\n"

        # Add the edges
        s += "  edge [style=solid, weight=1];\n"
        for y, edge in enumerate(self):
            for x in range(edge.start()):
                s += '  %04d.%04d -> %04d.%04d [style="invis"];\n' % (
                    x,
                    y + 1,
                    x + 1,
                    y + 1,
                )
            s += '  %04d.%04d -> %04d.%04d [label="%s"];\n' % (
                edge.start(),
                y + 1,
                edge.end(),
                y + 1,
                edge,
            )
            for x in range(edge.end(), self.num_leaves()):
                s += '  %04d.%04d -> %04d.%04d [style="invis"];\n' % (
                    x,
                    y + 1,
                    x + 1,
                    y + 1,
                )
        s += "}\n"
        return s


class FeatureChart(Chart):
    """
    A Chart for feature grammars.
    :see: ``Chart`` for more information.
    """

    def select(self, **restrictions):
        """
        Returns an iterator over the edges in this chart.
        See ``Chart.select`` for more information about the
        ``restrictions`` on the edges.
        """
        # If there are no restrictions, then return all edges.
        if restrictions == {}:
            return iter(self._edges)

        # Find the index corresponding to the given restrictions.
        restr_keys = sorted(restrictions.keys())
        restr_keys = tuple(restr_keys)

        # If it doesn't exist, then create it.
        if restr_keys not in self._indexes:
            self._add_index(restr_keys)

        vals = tuple(
            self._get_type_if_possible(restrictions[key]) for key in restr_keys
        )
        return iter(self._indexes[restr_keys].get(vals, []))

    def _add_index(self, restr_keys):
        """
        A helper function for ``select``, which creates a new index for
        a given set of attributes (aka restriction keys).
        """
        # Make sure it's a valid index.
        for key in restr_keys:
            if not hasattr(EdgeI, key):
                raise ValueError("Bad restriction: %s" % key)

        # Create the index.
        index = self._indexes[restr_keys] = {}

        # Add all existing edges to the index.
        for edge in self._edges:
            vals = tuple(
                self._get_type_if_possible(getattr(edge, key)()) for key in restr_keys
            )
            index.setdefault(vals, []).append(edge)

    def _register_with_indexes(self, edge):
        """
        A helper function for ``insert``, which registers the new
        edge with all existing indexes.
        """
        for (restr_keys, index) in self._indexes.items():
            vals = tuple(
                self._get_type_if_possible(getattr(edge, key)()) for key in restr_keys
            )
            index.setdefault(vals, []).append(edge)

    def _get_type_if_possible(self, item):
        """
        Helper function which returns the ``TYPE`` feature of the ``item``,
        if it exists, otherwise it returns the ``item`` itself
        """
        if isinstance(item, dict) and TYPE in item:
            return item[TYPE]
        else:
            return item

    def parses(self, start, tree_class=Tree):
        for edge in self.select(start=0, end=self._num_leaves):
            from nltk.parse.featurechart import FeatureTreeEdge
            if (
                    (isinstance(edge, FeatureTreeEdge))
                    and (edge.lhs()[TYPE] == start[TYPE])
                    and (unify(edge.lhs(), start, rename_vars=True))
            ):
                yield from self.trees(edge, complete=True, tree_class=tree_class)

