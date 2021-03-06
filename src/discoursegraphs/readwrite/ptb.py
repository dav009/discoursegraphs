#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module converts an Penn Treebank *.mrg file into a networkx-based
directed graph (``DiscourseDocumentGraph``).

TODO: add precedence edges if needed
"""

import os
import nltk # version 3.x is needed here (.labels() vs. .node)

import discoursegraphs as dg


class PTBDocumentGraph(dg.DiscourseDocumentGraph):
    """
    A directed graph with multiple edges (based on a networkx
    MultiDiGraph) that represents the syntax structure of a
    document.

    Attributes
    ----------
    name : str
        name, ID of the document or file name of the input file
    ns : str
        the namespace of the document (default: ptb)
    root : str
        name of the document root node ID
    tokens : list of str
        sorted list of all token node IDs contained in this document graph
    """
    def __init__(self, ptb_filepath, name=None, namespace='ptb',
                 tokenize=True, precedence=False, limit=None):
        """
        Creates an PTBDocumentGraph from a Penn Treebank *.mrg file and adds metadata
        to it.

        Parameters
        ----------
        ptb_filepath : str
            absolute or relative path to the Penn Treebank *.mrg file to be
            parsed.
        name : str or None
            the name or ID of the graph to be generated. If no name is
            given, the basename of the input file is used.
        namespace : str
            the namespace of the document (default: ptb)
        precedence : bool
            If True, add precedence relation edges
            (root precedes token1, which precedes token2 etc.)
        limit : int or None
            only parse the first n sentences of the input file into the
            document graph
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(PTBDocumentGraph, self).__init__()

        self.name = name if name else os.path.basename(ptb_filepath)
        self.ns = namespace
        self.root = 0
        self.add_node(self.root, layers={self.ns}, label=self.ns+':root_node')
        if 'discoursegraph:root_node' in self:
            self.remove_node('discoursegraph:root_node')
            
        self.sentences = []
        self.tokens = []

        self._node_id = 1

        ptb_path, ptb_filename = os.path.split(ptb_filepath)
        document = nltk.corpus.BracketParseCorpusReader(ptb_path, [ptb_filename])
        parsed_sents_iter = document.parsed_sents()
        
        if limit:
            for sentence in parsed_sents_iter[:limit]:
                self._add_sentence(sentence)
        else: # parse all sentences
            for sentence in parsed_sents_iter:
                self._add_sentence(sentence)

    def _add_sentence(self, sentence):
        """
        add a sentence from the input document to the document graph.

        Parameters
        ----------
        sentence : nltk.tree.Tree
            a sentence represented by a Tree instance
        """
        self.sentences.append(self._node_id)
        # add edge from document root to sentence root
        self.add_edge(self.root, self._node_id, edge_type=dg.EdgeTypes.spanning_relation)
        self._parse_sentencetree(sentence)
        self._node_id += 1 # iterate after last subtree has been processed
        
    def _parse_sentencetree(self, tree):
        def get_nodelabel(node):
            if isinstance(node, nltk.tree.Tree):
                return node.label()
            elif isinstance(node, unicode):
                return node.encode('utf-8')
            else:
                raise ValueError("Unexpected node type: {}, {}".format(type(node), node))

        root_node_id = self._node_id
        self.node[root_node_id]['label'] = get_nodelabel(tree)

        for subtree in tree:
            self._node_id += 1
            node_label = get_nodelabel(subtree)
            if isinstance(subtree, nltk.tree.Tree):
                node_attrs = {'label': node_label}
                edge_type = dg.EdgeTypes.dominance_relation
            else: # isinstance(subtree, unicode); subtree is a token
                node_attrs = {'label': node_label, self.ns+':token': node_label}
                edge_type = dg.EdgeTypes.spanning_relation
                self.tokens.append(self._node_id)

            self.add_node(self._node_id, attr_dict=node_attrs)
            self.add_edge(root_node_id, self._node_id, edge_type=edge_type)

            if isinstance(subtree, nltk.tree.Tree):
                self._parse_sentencetree(subtree)


# pseudo-function(s) to create a document graph from a Penn Treebank *.mrg file
read_mrg = read_ptb = PTBDocumentGraph



