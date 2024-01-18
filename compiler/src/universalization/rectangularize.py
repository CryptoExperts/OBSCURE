from IR import MLMI, MemOperand, MLS, HLI, Opcode
from DFG import DFG

def segregate_layers(dfg:DFG, node_layers, layers, config):
    # This function routes edges that skip layer must to nodes in the
    # intermediate layer. For instance, if our DFG is:
    #
    #               N1
    #               |  \
    #               |   \
    #               |    \
    #               |    N2
    #               |    /
    #               |   /
    #               |  /
    #                N3
    #
    # Then, we have to convert it in either:
    #
    #               N1
    #               |  \
    #               |   \
    #               |    \
    #              N4    N2
    #               |    /
    #               |   /
    #               |  /
    #                N3
    #
    # Or
    #
    #               N1
    #               |
    #               |
    #               N2
    #               |
    #               |
    #               N3
    #
    # The latter is preferable, because it does not introduce an
    # additional LLMI. However, it can only be done if N2 still has
    # some room for an additional input+output+instr.
    #
    # To do so, we iterate from the last layer to the first once,
    # because the backward_edges in the DFG can be be used to map each
    # variable to the node that defines them (and we don't have a map
    # mapping define points to the use points (although we could
    # generate it from other structures that we have)).


    # Records alternative places where MemOperands are defined
    alternative_defs = dict()

    def has_alternative_def(m:MemOperand, layer:int):
        """Returns true if |altenative_defs| has an entry for |m| in layer |layer|"""
        if m in alternative_defs:
            if alternative_defs[m][layer] != None:
                return True
        return False

    def replace_input(node:MLMI, old_m:MemOperand, new_m:MemOperand):
        """Replace |old_m| by |new_m| in |node|"""
        node.inputs = [ m if m != old_m else new_m
                        for m in node.inputs ]
        for instr in node.seq:
            if instr.src1 == old_m:
                instr.src1 = new_m
            if instr.src2 == old_m:
                instr.src2 = new_m
            if instr.src3 == old_m:
                instr.src3 = new_m

    def make_alternative(old_m:MemOperand, node:MLMI, layer:int):
        """Creates a new MemOperand to replace |old_m|"""
        # Creating the new MemOperand
        new_m = MemOperand(dfg.memory_count)
        dfg.memory_count += 1
        if old_m not in alternative_defs:
            alternative_defs[old_m] = [ None for _ in range(len(layers)) ]
        alternative_defs[old_m][layer] = new_m

        # Updating |node| with this new MemOperand
        dfg.backward_edges[new_m] = node
        node.outputs.append(new_m)
        if old_m not in node.inputs:
            node.inputs.append(old_m)
            if old_m not in dfg.prog_inputs:
                old_m_def = dfg.backward_edges[old_m]
                dfg.forward_edges[old_m_def].add(node)
        # Making sure to add the next MOV at the begining of node's
        # seq, so that it doesn't needlessly keep the input alive
        # throughout the whole MLS.
        node.seq.instrs.insert(0, HLI(Opcode.MOV, new_m, old_m))

        return new_m

    def remove_forward_edge_if_needed(def_node:MLMI, dst_node:MLMI):
        """Removes the edge from |def_node| to |dst_node| if needed.

        "if needed" means "if the edge shouldn't be here now that
        we've removed one of the MemOperand that was the cause of this
        edge".

        """
        need_to_remove_edge = True
        for m in dst_node.inputs:
            if m in def_node.outputs:
                need_to_remove_edge = False
                break
        if need_to_remove_edge:
            dfg.forward_edges[def_node] = { n for n in dfg.forward_edges[def_node]
                                            if n != dst_node }


    def break_edge(def_node:MLMI, dst_node:MLMI, mid_layer:int, m:MemOperand):
        if has_alternative_def(m, mid_layer):
            # |m| is actually already in layer |mid_layer|.
            alt_m = alternative_defs[m][mid_layer]
            alt_m_def = dfg.backward_edges[alt_m]
            dfg.forward_edges[alt_m_def].add(dst_node)
            replace_input(dst_node, m, alt_m)
            if def_node != None:
                remove_forward_edge_if_needed(def_node, dst_node)
            return
        # Searching for a candidate node in layer |mid_layer| to use.
        candidate = None
        for node in layers[mid_layer]:
            if len(node.outputs) < config.l_out and len(node.seq.instrs) < config.s:
                if m in node.inputs:
                    # Found a node in layer |mid_layer| that already
                    # has |m| in its inputs. That's the best we can hope for
                    candidate = node
                    break
                elif len(node.inputs) < config.l_in:
                    # Found a node with enough space in its
                    # inputs/outputs to |m|. That's better than
                    # nothing, but not has good at the previous if, so
                    # we don't break yet.
                    candidate = node

        if candidate != None:
            node = candidate
        else:
            # Creating a new node in layer |mid_layer|
            node = MLMI(MLS([]), [], [])
            node_layers[node] = mid_layer
            layers[mid_layer].append(node)
            dfg.nodes.add(node)

        # Creating alternative |m|
        alt_m = make_alternative(m, node, mid_layer)
        # Updating |dst_node|
        dst_node.inputs = [ x if x != m else alt_m for x in dst_node.inputs ]
        for instr in dst_node.seq.instrs:
            if instr.src1 == m:
                instr.src1 = alt_m
            if instr.src2 == m:
                instr.src2 = alt_m
            if instr.src3 == m:
                instr.src3 = alt_m
        # Adding forward edge from |node| to |dst_node|
        dfg.forward_edges[node].add(dst_node)

        if def_node != None:
            # Removing the forward edge from |def_node| to |dst_node|
            remove_forward_edge_if_needed(def_node, dst_node)

            # Adding forward edge from |def_node| to |node|
            dfg.forward_edges[def_node].add(node)


    count = 0

    for i in range(len(layers)):
        curr_layer_idx = len(layers) - i - 1
        curr_layer = layers[curr_layer_idx]
        if curr_layer_idx == 0:
            # Nothing to do in the first layer
            continue
        for node in curr_layer:
            for m in node.inputs:
                # There will be an issue with inputs
                if m in dfg.prog_inputs:
                    def_point = None
                    def_layer_idx = -1
                else:
                    def_point = dfg.backward_edges[m]
                    def_layer_idx = node_layers[def_point]
                if def_layer_idx != curr_layer_idx-1:
                    break_edge(def_point, node, curr_layer_idx-1, m)


def layerize(dfg:DFG):
    node_layers = dict()
    defined = set(dfg.prog_inputs)
    to_visit = set(dfg.nodes)
    last_layer = 0
    while len(to_visit) != 0:
        to_remove = set()
        for node in to_visit:
            layer = 0
            for prev in dfg.prev_nodes(node):
                if prev not in node_layers:
                    layer = -1
                    break
                layer = max(layer, node_layers[prev]+1)

            if layer != -1:
                last_layer = max(last_layer, layer)
                node_layers[node] = layer
                to_remove.add(node)

        to_visit = to_visit - to_remove

    # Computing all the nodes in each layer
    layers = [ [] for _ in range(last_layer+1) ]
    for node, layer in node_layers.items():
        layers[layer].append(node)

    return (node_layers, layers)

def rectangularize(dfg:DFG, config):

    # Computing the layer of each node
    (node_layers, layers) = layerize(dfg)

    # Make sure that no edges of the DFG skip layers
    segregate_layers(dfg, node_layers, layers, config)

    #dfg.show_dfg()


    return layers
