#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

'''
The 'brackets' module will convert document graphs into plain text files
with brackets encoding [[the begin]_{2} and and [end]_{3} of spans]_{1}.
Indices attached to the closing brackets can be used to signal relations
between the spans (e.g. coreference chains).
'''

import os
import itertools
from collections import defaultdict

import discoursegraphs as dg
from discoursegraphs.readwrite.mmax2 import spanstring2tokens


def gen_bracket_mappings(docgraph, layer=None):
    """
    extract all pointing chains (e.g. coreference chains) from a document
    graph (or just from the specified layer). return dictionaries describing
    which token signals the beginning of markables, the end of markables,
    as well as a mapping from a markable to the chain it belongs to.
    """
    pointing_chains = dg.get_pointing_chains(docgraph, layer=layer)
    markables = sorted(itertools.chain(*pointing_chains),
                       key=dg.util.natural_sort_key)

    markable2chain = {}
    for chain in pointing_chains:
        chain_id = chain[0] # first markable in a chain
        for markable in chain:
            markable2chain[markable] = chain_id

    opening = defaultdict(list)
    closing = defaultdict(list)
    for markable in markables:
        span_tokens = spanstring2tokens(
            docgraph, docgraph.node[markable][docgraph.ns+':span'])
        opening[span_tokens[0]].append(markable)
        closing[span_tokens[-1]].append(markable)
    return opening, closing, markable2chain


def gen_closing_string(closing_dict, markable2chain, token_id, stack):
    num_of_closing_brackets = len(closing_dict[token_id])
    closing_markable_ids = [stack.pop()
                            for i in range(num_of_closing_brackets)]
    return u''.join(u']_{{{}}}'.format(markable2chain[closing_id])
                                   for closing_id in closing_markable_ids)


def gen_bracketed_output(docgraph):
    '''

    TODO: the order of the opening brackets should be determined (e.g. if
    a token marks the beginning of two markables, we could check if the
    first markable subsumes the second markable or vice versa.)

    Example
    -------
    Die Diskussion , wie teuer [die neue [Wittstocker]_{markable_22}
    Stadthalle]_{markable_21} für Vereine und Veranstalter wird , hat
    einige Zeit in Anspruch genommen .
    Die Betriebskosten [für den schmucken Veranstaltungsort]_{markable_21}
    sind hoch . Jetzt wird es darum gehen , [die Halle]_{markable_21} so oft
    wie möglich zu füllen .
    Und [in der Region]_{markable_22} gibt es Konkurrenz .
    '''
    opening, closing, markable2chain = gen_bracket_mappings(docgraph)

    ret_str = u''
    stack = []
    for token_id in docgraph.tokens:
        token_str = docgraph.get_token(token_id)
        if token_id in opening:
            num_of_opening_brackets = len(opening[token_id])
            stack.extend(opening[token_id])
            opening_str = u'[' * num_of_opening_brackets

            if token_id in closing:
                # token is both the first and last element of 1+ markables
                closing_str = gen_closing_string(closing, markable2chain,
                                                 token_id, stack)
                ret_str += u'{0}{1}{2} '.format(opening_str, token_str,
                                                closing_str)
            else: # token is the first element of 1+ markables
                ret_str += u'{0}{1} '.format(opening_str, token_str)
        elif token_id in closing:
            closing_str = gen_closing_string(closing, markable2chain,
                                             token_id, stack)
            ret_str += u'{0}{1} '.format(token_str, closing_str)
        else:
            ret_str += u'{} '.format(token_str)
    return ret_str


def write_brackets(docgraph, output_file):
    """
    converts a document graph into a plain text file with brackets.
    """
    bracketed_str = gen_bracketed_output(docgraph)
    assert isinstance(output_file, (str, file))
    if isinstance(output_file, str):
        path_to_file = os.path.dirname(output_file)
        if not os.path.isdir(path_to_file):
            create_dir(path_to_file)
        with open(output_file, 'w') as outfile:
            outfile.write(bracketed_str)

    else:  # output_file is a file object
        output_file.write(bracketed_str)
