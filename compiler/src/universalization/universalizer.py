from IR import MLMI, MemOperand, ImmOperand, MLS, HLI, Opcode
from DFG import DFG
from .rectangularize import rectangularize
from . import routing
import math
import random
import time

def universalize(dfg:DFG, config) -> DFG :

    assert config.l_in == config.l_out and \
        2**math.log2(config.l_in) == config.l_in

    #dfg.show_dfg(filename="universalize_0")

    start_rectangularize_time = time.time()
    layers = rectangularize(dfg, config)

    if config.stats:
        if config.depth == 0 or config.depth <= len(layers):
            print(f"  program depth: {len(layers)}")
        else:
            print(f"  program initial depth: {len(layers)}")
            print(f"  program final depth: {config.depth}")


    #dfg.show_dfg(filename="universalize_1")

    add_depth_padding(dfg, layers, config)

    #dfg.show_dfg(filename="universalize_2")

    add_input_masking_layer(dfg, layers, config)

    #dfg.show_dfg(filename="universalize_3")

    propagate_outputs_to_last_layer(dfg, layers, config)

    #dfg.show_dfg(filename="universalize_4")

    equalize_layers(dfg, layers, config)

    #dfg.show_dfg(filename="universalize_5")

    match_layers_inputs_outputs(dfg, layers,config)
    rectangularize_total_time = time.time() - start_rectangularize_time

    if config.stats:
        print(f"Rectangularization: {rectangularize_total_time:.2f}")
        print(f"  MLIR size: {len(dfg.nodes)} MLMIs")

    #dfg.show_dfg(filename="universalize_6")

    add_permutation(dfg, layers, config)

    #dfg.show_dfg(filename="universalize_7")

    dfg.check_dfg_integrity()


    return dfg

def add_depth_padding(dfg:DFG, layers, config):
    """Add layers so that the number of layers is at config.depth"""
    depth = len(layers)
    if config.depth != 0:
        if config.depth < depth:
            print(f"Flag '-depth {config.depth}' was used, but the program has a depth of {depth}. Ignoring the -depth flag and continuing.")
        else:
            depth = config.depth

    for _ in range(len(layers), depth):
        node = MLMI(MLS([]), [], [])
        dfg.nodes.add(node)
        layers.append([node])

def add_input_masking_layer(dfg:DFG, layers, config):
    """Add an initial layer to mask where inputs are going (because there
    will be a permutation layer in between this initial layer and the
    next layer)

    Note that at least one LLMI of this layer must have |config.l_out|
    outputs, so that all LLMI of the next layer can take fill all
    their inputs.

    """
    # Creating this initial layer
    initial_layer = []
    old_to_new_inputs = dict()
    old_inputs = set(dfg.prog.inputs)
    while len(old_inputs) != 0:
        node = MLMI(MLS([]), [], [])
        initial_layer.append(node)
        while len(node.inputs)  < config.l_in and \
              len(node.outputs) < config.l_out and \
              len(old_inputs) != 0:
            m = old_inputs.pop()
            new_input = MemOperand(dfg.memory_count)
            dfg.memory_count += 1

            node.inputs.append(m)
            node.outputs.append(new_input)
            node.seq.instrs.append(HLI(Opcode.MOV, new_input, m))

            dfg.backward_edges[new_input] = node
            old_to_new_inputs[m] = new_input

    node = initial_layer[0]
    while len(node.outputs) != config.l_out:
        out = MemOperand(dfg.memory_count)
        dfg.memory_count += 1
        node.outputs.append(out)
        node.seq.instrs.append(HLI(Opcode.MOV, out, ImmOperand(0)))
        dfg.backward_edges[out] = node

    # Adding forward edges from this initial layer to the rest of the
    # graph, and updating the uses of the old inputs.
    dfg.prog_outputs = [ old_to_new_inputs.get(m, m) for m in dfg.prog_outputs ]
    for node in dfg.nodes:
        for m in node.inputs:
            if m in old_to_new_inputs:
                dfg.forward_edges[dfg.backward_edges[old_to_new_inputs[m]]].add(node)
        node.inputs = [ old_to_new_inputs.get(m, m) for m in node.inputs ]
        for instr in node.seq:
            instr.src1 = old_to_new_inputs.get(instr.src1, instr.src1)
            instr.src2 = old_to_new_inputs.get(instr.src2, instr.src2)
            instr.src3 = old_to_new_inputs.get(instr.src3, instr.src3)

    layers.insert(0, initial_layer)
    for node in initial_layer:
        dfg.nodes.add(node)



def propagate_outputs_to_last_layer(dfg:DFG, layers, config):

    """Propagate outputs to the last layer

    In the original DFG (and even after rectangularization), some
    outputs can be defined before the last layer. This is a problem
    for security: all outputs need to be defined on the last
    layer.

    """

    def add_input_output_to_node(m:MemOperand, node:MLMI) -> MemOperand:
        """Adds |m| as input to |node|, and make |node| return a copy of |m|"""
        new_output = MemOperand(dfg.memory_count)
        dfg.memory_count += 1

        node.inputs.append(m)
        node.outputs.append(new_output)
        node.seq.instrs.append(HLI(Opcode.MOV, new_output, m))

        def_m_node = dfg.backward_edges[m]
        dfg.forward_edges[def_m_node].add(node)
        dfg.backward_edges[new_output] = node

        return new_output


    to_take_as_inputs = set() # Outputs that were defined in the previous
    for layer_idx, layer in enumerate(layers):
        layer = layers[layer_idx]
        new_outputs = dict()
        while len(to_take_as_inputs) != 0:
            m = to_take_as_inputs.pop()
            node = None
            for mlmi in layer:
                if len(mlmi.inputs)  < config.l_in and \
                   len(mlmi.outputs) < config.l_out and \
                   len(mlmi.seq.instrs)  < config.s:
                    # TODO: do we need to check register pressure?
                    node = mlmi
                    break
            if node == None:
                # Need to create a new node in the next layer
                node = MLMI(MLS([]), [], [])
                dfg.nodes.add(node)
                layers[layer_idx].append(node)

            new_output = add_input_output_to_node(m, node)
            new_outputs[m] = new_output

        # Updating program outputs
        dfg.prog_outputs = [ new_outputs.get(m, m) for m in dfg.prog_outputs ]

        # Collecting outputs of this layer
        prog_outputs_set = set(dfg.prog_outputs)
        to_take_as_inputs = set()
        for mlmi in layer:
            to_take_as_inputs.update([ m for m in mlmi.outputs if m in prog_outputs_set ])

    # Adding a final layer to reveal the outputs
    final_layer = []
    new_outputs = dict()
    while len(to_take_as_inputs) != 0:
        curr_mlmi = MLMI(MLS([]), [], [])
        dfg.nodes.add(curr_mlmi)
        while len(curr_mlmi.inputs)  < config.l_in and \
              len(curr_mlmi.outputs) < config.l_out and \
              len(curr_mlmi.seq.instrs)  < config.s and \
              len(to_take_as_inputs) != 0:
            m = to_take_as_inputs.pop()
            new_output = add_input_output_to_node(m, curr_mlmi)
            new_outputs[m] = new_output
        final_layer.append(curr_mlmi)

    dfg.prog_outputs = [ new_outputs.get(m, m) for m in dfg.prog_outputs ]

    layers.append(final_layer)


def equalize_layers(dfg:DFG, layers, config):
    """Make all layers the same width"""
    # Find the width of the largest layer
    max_width = -1
    for layer in layers[1:-1]:
        max_width = max(max_width, len(layer))

    if config.width != 0:
        if config.width < max_width:
            print(f"Flag '-width {config.width}' was used, but the program has a width of {max_width}. Ignoring the -width flag and continuing.")
        else:
            max_width = config.width

    if config.stats:
        print(f"  program width: {max_width}")

    # Add dummy nodes to all layers whose width is less than |max_width|
    for layer in layers[1:-1]:
        for _ in range(len(layer), max_width):
            mlmi = MLMI(MLS([]), [], [])
            dfg.nodes.add(mlmi)
            layer.append(mlmi)


def match_layers_inputs_outputs(dfg:DFG, layers, config):
    """Make all MLMIs have the same number of inputs/outputs

    * Outputs: we add to an MLMI outputs some of its intermediate
      (internal) variables. If the MLMI doesn't have enough outputs,
      then we just return some 0s by padding the MLMI with:

          MOV __, 0

      Note that we prefer to return intermediate variables, since this
      does not increase the amount of instructions inside the MLMI. In
      practice though, I'm not sure if it really makes a difference...

    * Inputs: for inputs, we need to take some input of the previous
      layer. In practice, it doesn't matter which input we choose:
      with the permutation layers that will be added, all inputs are
      identical from the dataflow's standpoint.

    """

    prev_layer_outputs = list({ o for node in layers[0]
                                for o in node.outputs }) # outputs of the previous layer
    for layer_idx in range(1, len(layers)-1):
        layer = layers[layer_idx]

        # Add inputs
        for mlmi in layer:
            config.l_in > len(prev_layer_outputs)
            while len(mlmi.inputs) != config.l_in:
                new_input = random.choice(prev_layer_outputs)
                while new_input in mlmi.inputs:
                    new_input = random.choice(prev_layer_outputs)
                mlmi.inputs.append(new_input)
                def_node = dfg.backward_edges[new_input]
                dfg.forward_edges[def_node].add(mlmi)

        # Add outputs
        for mlmi in layer:
            if len(mlmi.outputs) != config.l_out:
                # Gathering intermediate variables that are not
                # returned.
                possible_returns = set()
                for hli in mlmi.seq:
                    if hli.dst not in mlmi.outputs:
                        possible_returns.add(hli.dst)
                # Actually adding new outputs
                while len(mlmi.outputs) != config.l_out:
                    if len(possible_returns) != 0:
                        # Adding an intermediate variable to the
                        # outputs.
                        new_output = possible_returns.pop()
                        mlmi.outputs.append(new_output)
                        dfg.backward_edges[new_output] = mlmi
                    else:
                        # Returning a 0
                        new_output = MemOperand(dfg.memory_count)
                        dfg.memory_count += 1
                        mlmi.seq.instrs.append(HLI(Opcode.MOV, new_output, ImmOperand(0)))
                        mlmi.outputs.append(new_output)
                        dfg.backward_edges[new_output] = mlmi


        prev_layer_outputs = list({ m for mlmi in layer for m in mlmi.outputs })



def add_permutation(dfg:DFG, layers, config):
    for i in range(len(layers)-1):
        before_layer = layers[i]
        after_layer  = layers[i+1]

        inputs  = [ m for mlmi in before_layer for m in mlmi.outputs ]
        outputs = [ m for mlmi in after_layer  for m in mlmi.inputs  ]

        # Removing old foward edges: the permutation network will make
        # them obsolete.
        for mlmi in before_layer:
            dfg.forward_edges[mlmi] = set()

        perm_layer_min_size = max(len(inputs), len(outputs))
        if int(math.log2(perm_layer_min_size)) == math.log2(perm_layer_min_size):
            perm_layer_size = perm_layer_min_size
        else:
            perm_layer_size = 2**(1+int(math.log2(perm_layer_min_size)))

        inputs_pos = { m:i for i,m in enumerate(inputs) }
        inputs_pos_rev = { i:m for i,m in enumerate(inputs) }
        perm_outputs = [ inputs_pos[m] for m in outputs ]
        perm_outputs += [ 0 ] * (perm_layer_size - len(perm_outputs))

        # Padding inputs so that it's the same length as outputs
        inputs += [ImmOperand(0)] * (perm_layer_size - len(inputs))

        le = math.log2(config.l_in)
        bf = routing.BDBFuncMI(perm_outputs, le=le)
        perm = routing.optimize(bf.canonical())

        def apply_secret_perm(inputs, off, p, inputs_checker):
            new_inputs = list(inputs)
            new_inputs_checker = list(inputs_checker)
            node = MLMI(MLS([]), [], [])
            dfg.nodes.add(node)
            node.inputs = [ m for m in inputs[off:off+len(p)] if isinstance(m,MemOperand)]
            for i,idx in enumerate(p):
                out = MemOperand(dfg.memory_count)
                dfg.memory_count += 1
                prev = inputs[off+idx]
                node.seq.instrs.append(HLI(Opcode.MOV, out, inputs[off+idx]))
                node.outputs.append(out)

                new_inputs[off+i] = out
                new_inputs_checker[off+i] = inputs_checker[off+idx]

                dfg.backward_edges[out] = node

            for m in node.inputs:
                if m in dfg.backward_edges:
                    dfg.forward_edges[dfg.backward_edges[m]].add(node)

            for i in range(len(inputs)):
                inputs[i] = new_inputs[i]
                inputs_checker[i] = new_inputs_checker[i]

        # inputs_checker is used to check that the permutation is
        # correct: it's an array of integers of which we apply the
        # permutation alongside the real |inputs|, and at the end we
        # check if |inputs_checker| is indeed |perm_outputs|.
        inputs_checker = [ i for i,_ in enumerate(inputs) ]

        # Converting the permutation into nodes in the DFG
        for row in perm:
            if isinstance(row, routing.PublicShuffle):
                inputs = [ inputs[i] for i in row ]
                inputs_checker = [ inputs_checker[i] for i in row ]

            elif isinstance(row, routing.SecretShuffles):
                for off, p in row.items():
                    apply_secret_perm(inputs, off, p, inputs_checker)

            else:
                assert False

        if perm_outputs != inputs_checker:
            print("Error in the permutation.")
            print("Target: ", perm_outputs)
            print("Got: ", inputs_checker)
            raise RuntimeError()

        # Updating the inputs of the next layer
        off = 0
        for mlmi in after_layer:
            old_to_new = dict()
            # Updating inputs and DFG edges
            for i,old_m in enumerate(mlmi.inputs):
                new_m = inputs[off+i]
                dfg.forward_edges[dfg.backward_edges[new_m]].add(mlmi)
                old_to_new[old_m] = new_m
                mlmi.inputs[i]    = new_m
            # Updating body of the MLMI
            for instr in mlmi.seq.instrs:
                instr.src1 = old_to_new.get(instr.src1, instr.src1)
                instr.src2 = old_to_new.get(instr.src2, instr.src2)
                instr.src3 = old_to_new.get(instr.src3, instr.src3)

            off += len(mlmi.inputs)
