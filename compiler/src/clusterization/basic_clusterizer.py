"""Basic clusterizer

This clusterizer groups instructions that have a single output with
their output node. Once no such transformation can be applied (ie, all
instructions that have a single output have been merge), random
instructions are merged with their parent, provided that this doesn't
increase the number of inputs/outputs to encrypt. Then, siblings are
merged together when possible.

Note that this clusterizer takes into account the internal constraints
of multi instructions (number of inputs, outputs, and intermediate
registers).

For instance, consider this dataflow graph:

    i1     i2       i3       i4
     \     /        |        |
      \   /         |        |
        +          /         |
          \       /          |
           \     /           |
            \   /           /
              *            /
              | \         /
              |  \       /
              |   \     /
              |    \   /
              |      &
              |      |
              |      |
              |      |
              o1     o2

Here, "+" only has a single output, so it would be merged with "*",
producing this DFG:

    i1     i2       i3       i4
     \     |        /        |
      \    |       /         |
       \   |      /          |
        \  |     /           |
         \  \   /           /
          \  \ /           /
             +            /
             *           /
             |  \       /
             |   \     /
             |    \   /
             |      &
             |      |
             |      |
             |      |
             o1     o2

If the token has enough temporary registers, then the "&" would be
added to the "+*" multi-instruction: doing this does not incrase the
number of inputs/outputs to encrypt (it reduces it actually).

"""

from collections import defaultdict
from lowering.reg_alloc import LinearScanAllocator
from DFG import DFG
from IR import Opcode, MemOperand, RegOperand, HLI, MLS, MLMI, LLI, LLS, LLMI, HLIRProgram, MLIRProgram, LLIRProgram

def initial_convertion_to_mlir(hlir:HLIRProgram) -> MLIRProgram :
    """Creates one MLMI per instruction.

    This way, clusterization operations are only merges of MLMI, and
    we don't have to deal with a graph whose nodes could be either HLI
    or MLMI.

    """
    return MLIRProgram([MLMI.FromHLI(hli) for hli in hlir.instrs],
                       hlir.inputs, hlir.outputs, hlir.memory_count)


def merge_1_output_nodes(dfg, config):
    merged_seq = None
    def should_merge_with_next(node:MLMI):
        """Checks if |node| should be merged with the following node"""
        # Checking that |node| has a single output
        if dfg.output_count(node) != 1:
            return False
        next_node = next(iter(dfg.next_nodes(node)))
        merged_inputs = dfg.compute_merged_inputs(node, next_node)
        # Checking input count
        if len(merged_inputs) > config.l_in:
            return False
        # Checking instruction count
        if len(node.seq.instrs) + len(next_node.seq.instrs) > config.s:
            return False
        # Checking register pressure
        merged_instrs = dfg.compute_merged_instrs(node, next_node, merged_inputs)
        if not LinearScanAllocator().needs_leq_k_registers(
                merged_instrs.instrs,
                merged_inputs,
                dfg.compute_merged_outputs(node, next_node),
                config.r, config.l_out):
            return False

        nonlocal merged_seq
        merged_seq = merged_instrs
        return True

    if config.simple_clusterizer:
        to_visit = dfg.nodes.copy()
        while len(to_visit) != 0:
            candidate = to_visit.pop()
            if not should_merge_with_next(candidate):
                continue

            assert merged_seq != None
            new_node = dfg.merge_nodes(candidate,
                                    next(iter(dfg.next_nodes(candidate))),
                                    merged_seq)
            merged_seq = None

            # Re-adding the successors and predecessors of the new node in
            # the set to visit.
            for node in dfg.next_nodes(new_node):
                to_visit.add(node)
            for node in dfg.prev_nodes(new_node):
                to_visit.add(node)
            to_visit.add(new_node)
    
    else:
        while True:
            # Searching for a node to merge
            candidate = None
            for node in dfg.nodes:
                if should_merge_with_next(node):
                    candidate = node
                    break

            if candidate != None:
                assert merged_seq != None
                dfg.merge_nodes(candidate, next(iter(dfg.next_nodes(candidate))),
                                merged_seq)
                merged_seq = None
            else:
                break


def merge_score(dfg, config, n1, n2):
    """Returns a score for the resulting node representing how much of an
     improvement this merge would be.

     The score is simply the number of inputs/outputs that are
     removed. The score is -1 if the merge would produce an
     invalid node

    """
    # Note that the checks are ordered from the cheapest to the most
    # expensive: checking instruction could is very fast, computing
    # merged inputs is fairly fast as well, computing merged outputs
    # is a bit more expensive, computing register pressure is again
    # more expensive, and computing check_domination_for_merge is very
    # expensive. This way, this function will otfen early-return
    # without computing the more expensive parts.

    # Checking instruction count
    if len(n1.seq.instrs) + len(n2.seq.instrs) > config.s:
        return (-1, None)
    merged_inputs  = dfg.compute_merged_inputs(n1, n2)
    # Checking input count
    if len(merged_inputs) > config.l_in:
        return (-1, None)
    merged_outputs = dfg.compute_merged_outputs(n1, n2)
    # Checking output count
    if len(merged_outputs) > config.l_out:
        return (-1, None)
    # Checking register pressure
    merged_instrs = dfg.compute_merged_instrs(n1, n2, merged_inputs)
    if not LinearScanAllocator().needs_leq_k_registers(
            merged_instrs.instrs,
            merged_inputs, merged_outputs,
            config.r, config.l_out):
        return (-1, None)
    # Checking that no nodes are dominated by n1 but dominate n2
    # (or vise-versa).
    if not dfg.check_domination_for_merge(n1, n2):
        return (-1, None)

    score = len(n1.inputs) + len(n2.inputs) - len(merged_inputs) + \
        len(n1.outputs) + len(n2.outputs) - len(merged_outputs)
    return (score, merged_instrs)

def merge_parents_childs(dfg, config):
    """Merges parents with their childs when possible"""
    if config.simple_clusterizer:
        to_visit = dfg.nodes.copy()
        while len(to_visit) != 0:
            n1 = to_visit.pop()
            best_node, best_score = None, -1
            for n2 in dfg.next_nodes(n1):
                (n2_score, merged_instrs) = merge_score(dfg, config, n1, n2)
                if n2_score > best_score:
                    best_node  = n2
                    best_score = n2_score
                    best_mls   = merged_instrs
            if best_score == -1:
                continue

            new_node = dfg.merge_nodes(n1, best_node, best_mls)

            # Re-adding the successors and predecessors of the new node in
            # the set to visit.
            if not config.fast:
                for node in dfg.next_nodes(new_node):
                    to_visit.add(node)
                for node in dfg.prev_nodes(new_node):
                    to_visit.add(node)
                to_visit.add(new_node)
    else:
        to_skip = set()
        while True:
            c1, c2, mls = None, None, None
            for n1 in dfg.nodes:
                if config.fast and n1 in to_skip:
                    continue
                best_node, best_score = None, -1
                for n2 in dfg.next_nodes(n1):
                    (n2_score, merged_instrs) = merge_score(dfg, config, n1, n2)
                    if n2_score > best_score:
                        best_node  = n2
                        best_score = n2_score
                        best_mls   = merged_instrs
                if best_score != -1:
                    c1 = n1
                    c2 = best_node
                    mls = best_mls
                    break
                elif config.fast:
                    to_skip.add(n1)

            if c1 != None:
                assert c2 != None
                assert mls != None
                dfg.merge_nodes(c1, c2, mls)
            else:
                # No possible merges were found
                break


def merge_siblings(dfg, config):
    """Merges siblings when possible"""

    to_skip = set()
    merged = True
    while merged:
        merged = False
        for parent in dfg.nodes:
            if config.fast and parent in to_skip:
                continue
            childs = list(dfg.next_nodes(parent))
            c1, c2, best_score, best_mls = None, None, -1, None
            for i1 in range(len(childs)):
                n1 = childs[i1]
                for i2 in range(i1+1, len(childs)):
                    n2 = childs[i2]
                    (score, merged_instrs) = merge_score(dfg, config, n1, n2)
                    if score > best_score:
                        best_score = score
                        c1 = n1
                        c2 = n2
                        best_mls = merged_instrs
            if best_score > 0:
                assert c1 != None and c2 != None and best_mls != None
                dfg.merge_nodes(c1, c2, best_mls)
                merged = True
                break
            elif config.fast:
                to_skip.add(parent)


def clusterize(hlir:HLIRProgram, config, print_stats=False) -> LLIRProgram :
    mlir = initial_convertion_to_mlir(hlir)

    dfg = DFG(mlir, False)

    if print_stats:
        inout_count  = 0
        instrs_count = len(dfg.nodes)
        for node in dfg.nodes:
            inout_count  += len(node.inputs) + len(node.outputs)
        print(f"Before clusterization: {inout_count} inputs/outputs, {instrs_count} instructions.")

    #dfg.show_dfg(filename="before_clusterize")

    # Step 1: merge 1-output instructions with their output
    merge_1_output_nodes(dfg, config)

    #dfg.show_dfg()

    # Step 2: merge parents with their childs when possible
    merge_parents_childs(dfg, config)

    # Step 3: merge nodes that share a direct parent
    merge_siblings(dfg, config)

    #dfg.show_dfg()

    #dfg.show_dfg(filename="after_clusterize")


    if print_stats:
        inout_count  = 0
        instrs_count = len(dfg.nodes)
        for node in dfg.nodes:
            inout_count  += len(node.inputs) + len(node.outputs)
        print(f"After clusterization: {inout_count} inputs/outputs, {instrs_count} instructions.")

    return dfg
