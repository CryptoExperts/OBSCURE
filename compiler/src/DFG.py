"""Dataflow Graph intermediate representation

"""
import IR
from collections import defaultdict
from graphviz import Digraph
from IR import MLIRProgram, MLMI, MLS
import lowering.lowering as lowering
import sys


class DFG:
    """Data Flow Graph (DFG)

    The internal datastructures of the DFG are the following:

     - nodes: a set of all the MLMI of the DFG

     - backward_edges: a map from MemOperand to MLMI, mapping each
       MemOperand to the MLMI that defines it.

     - forward_edges: a map from MLMI to list of MLMI, mapping each
       MLMI to the MLMIs that use its outputs.

     - prog_inputs: the inputs of the program

     - prog: the original mlir program

    """
    def __init__(self, mlir:MLIRProgram, show_dfg=False):
        self.build_graph(mlir, show_dfg)

    def build_graph(self, mlir:MLIRProgram, show_dfg=False):
        """Builds the dataflow graph of the program"""

        # Storing which instruction defines each variables
        backward_edges = { dst : instr for instr in mlir.instrs
                           for dst in instr.get_defs() }

        # Get all variables used by the program
        used_vars = { var for instr in mlir.instrs
                      for var in instr.get_used() }
        # Get inputs
        inputs = set(mlir.inputs)

        # Computing edges
        forward_edges = defaultdict(lambda: set())
        for instr in mlir.instrs:
            for src in instr.get_used():
                if src not in inputs:
                    forward_edges[backward_edges[src]].add(instr)

        self.prog = mlir
        self.prog_inputs = inputs
        self.prog_outputs = mlir.outputs
        self.memory_count = mlir.memory_count
        self.backward_edges = backward_edges
        self.nodes = { v for v in backward_edges.values() }
        self.forward_edges = forward_edges

        if show_dfg:
            # DEBUG ONLY: Plotting the graph
            self.show_dfg()

    def output_count(self, node:MLMI):
        return len(self.forward_edges[node])

    def next_nodes(self, node:MLMI):
        return self.forward_edges[node]

    def prev_nodes(self, node:MLMI):
        prevs = set()
        for m in node.inputs:
            if m in self.backward_edges:
                prevs.add(self.backward_edges[m])
        return prevs

    def check_domination_for_merge(self, n1, n2):
        """Check if n1 and n2 could be merged, based on their domination
        relation.

        That is, we cannot merge two nodes n1 and n2 if some nodes are
        dominated by n1 but dominate n2 (or vise-versa): this would
        create a cycle in the DFG.

        The way to check this is to a traversal of the DFG from n1
        (ignoring its direct successor n2 at the start) and see if we
        end up on n2. (and vise-versa)

        """
        for nstart, nend in [ (n1,n2), (n2,n1) ]:
            to_visit = { n for n in self.next_nodes(nstart) if n != nend }
            visited = set()
            while len(to_visit) != 0:
                n = to_visit.pop()
                if n in visited:
                    continue
                if n == nend:
                    return False
                visited.add(n)
                for next_node in self.next_nodes(n):
                    to_visit.add(next_node)

        return True


    def compute_merged_instrs(self, n1:MLMI, n2:MLMI, merged_inputs):
        # When merging two nodes, we need to make sure that variables
        # are computed before being used inside the resulting MI. For
        # instance, if we merge:
        #
        #     x = a + b
        #
        # and
        #
        #     y = x + 4
        #
        # We need to make sure that the result is:
        #
        #    x = a + b
        #    y = x + 4
        #
        # Rather than:
        #
        #    y = x + 4
        #    x = a + b
        #
        # When merging two MI where one is a direct predecessor of the
        # other, this is fairly trivial to do. However, in the general
        # case, it's probably a little bit less trivial, so, to avoid
        # any unforseen complication, we do a simple scheduling here,
        # iterating though all instructions and making sure that we
        # schedule them only once their operands have been computed.
        #
        # Note: this function is non-deterministic. This means that it
        # could return a sequence that reg_alloc can allocate
        # registers for, but then be called on the same inputs and
        # return a sequence for which reg_alloc cannot allocate
        # registers. Thus, it's best to call it only once for some
        # given inputs. If you wanted to make this function
        # deterministic, then change |to_schedule| into a list
        # (instead of a set), but be aware that this will negatively
        # impact performance.
        to_schedule = set(n1.seq.instrs + n2.seq.instrs)
        defined = set(merged_inputs)
        instrs = []
        while len(to_schedule) != 0:
            to_remove = set()
            for instr in to_schedule:
                if (isinstance(instr.src1, IR.MemOperand) and instr.src1 not in defined) or \
                   (isinstance(instr.src2, IR.MemOperand) and instr.src2 not in defined) or \
                   (isinstance(instr.src3, IR.MemOperand) and instr.src3 not in defined):
                    # Instruction uses a source not defined yet
                    continue
                to_remove.add(instr)
                defined.add(instr.dst)
                instrs.append(instr)
            to_schedule = to_schedule - to_remove

        return MLS(instrs)

    def compute_merged_inputs(self, n1:MLMI, n2:MLMI):
        return list(set(n1.inputs).union(set(n2.inputs)) -
                    set(n1.outputs).union(set(n2.outputs)))

    def compute_merged_outputs(self, n1:MLMI, n2:MLMI):
        outputs = set()

        n1_outputs = set(n1.outputs)
        n1_inputs  = set(n1.inputs)
        n2_outputs = set(n2.outputs)
        n2_inputs  = set(n2.inputs)

        prog_outputs = set(self.prog_outputs)

        for first_node, second_node in [ (n1, n2), (n2, n1) ]:
            f_outputs = set(first_node.outputs)
            s_inputs  = set(second_node.inputs)
            for o in f_outputs:
                if o in s_inputs:
                    # This output will be used as an input in the MI. If
                    # it's not used in any other MI, then it's not an
                    # output but rather a local register.
                    output_use_count = 0
                    for n in self.next_nodes(first_node):
                        if o in n.inputs:
                            output_use_count += 1
                    assert output_use_count >= 1 # after all, it's in s_inputs
                    if o in prog_outputs:
                        output_use_count += 1
                    if output_use_count > 1:
                        # This output is not a local register but rather a
                        # real output.
                        outputs.add(o)
                else:
                    # This output is not in the inputs of the next node,
                    # which means that it's a real output
                    outputs.add(o)

        return list(outputs)

    def merge_nodes(self, n1:MLMI, n2:MLMI, merged_mls=None):
        """Merges |n1| and |n2|, and updates internal structures so that the
        DFG is still coherent.

        Warning: this function does no do any verification that the
        nodes can actually be safely merged. You should do this
        beforehand (by calling check_domination_for_merge for instance).

        """

        inputs  = self.compute_merged_inputs(n1, n2)
        outputs = self.compute_merged_outputs(n1, n2)
        if merged_mls is None:
            seq     = self.compute_merged_instrs(n1, n2, inputs)
        else:
            seq = merged_mls

        new_MLMI = MLMI(seq, inputs, outputs)

        # Updating internal
        self.nodes.remove(n1)
        self.nodes.remove(n2)
        self.nodes.add(new_MLMI)

        defined_in_new_MLMI = new_MLMI.get_defs()
        used_in_new_LLMI    = new_MLMI.get_used()

        # Removing out-dated forward_edges (needs to be done before
        # updating backward edges)
        for src in used_in_new_LLMI:
            if src not in self.prog_inputs:
                self.forward_edges[self.backward_edges[src]].discard(n1)
                self.forward_edges[self.backward_edges[src]].discard(n2)

        forward_edges_for_new = set()
        for use_mlmi in self.forward_edges[n1]:
            if use_mlmi != n2:
                forward_edges_for_new.add(use_mlmi)
        for use_mlmi in self.forward_edges[n2]:
            if use_mlmi != n1:
                forward_edges_for_new.add(use_mlmi)
        self.forward_edges[new_MLMI] = forward_edges_for_new

        # Updating backward edges
        for var in defined_in_new_MLMI:
            self.backward_edges[var] = new_MLMI

        # Updating new forward edges
        del self.forward_edges[n1]
        del self.forward_edges[n2]

        for src in used_in_new_LLMI:
            if src not in self.prog_inputs:
                self.forward_edges[self.backward_edges[src]].add(new_MLMI)

        return new_MLMI


    def to_LLIR(self, config):
        llir_instrs = []  # The final LLMIs
        mem_ready = set() # The MemOperand that have already been defined
        for m in self.prog_inputs:
            mem_ready.add(m)

        def schedule_node(node):
            llir_instrs.append(lowering.MLMI_to_LLMI(node, config.r, config.l_out))
            for m in node.outputs:
                mem_ready.add(m)

        def node_is_ready(node) -> bool :
            for m in node.inputs:
                if m not in mem_ready:
                    return False
            return True

        todo = { n for n in self.nodes if node_is_ready(n) }
        done = set()
        while len(todo) != 0:
            node = todo.pop()
            if node_is_ready(node):
                schedule_node(node)
                todo.update(self.forward_edges[node])
                done.add(node)

        # Checking that all nodes were scheduled.
        for node in self.nodes:
            if node not in done:
                print("Not scheduled: ", node)
                raise RuntimeError()

        return IR.LLIRProgram(llir_instrs, self.prog.inputs, self.prog_outputs,
                              self.memory_count)


    def check_dfg_integrity(self):
        """Check that the edges of the graph are consistent"""
        for node in self.nodes:
            for m in node.inputs:
                # Checking incoming forward edges
                if m in self.prog_inputs:
                    continue
                if m not in self.backward_edges:
                    print(f"Missing backward edges for memory {m}")
                    sys.exit("Invalid DFG")
                else:
                    def_node = self.backward_edges[m]
                    if node not in self.forward_edges[def_node]:
                        print(f"Missing forward edge from def to use of {m}")
                        print("def: ", def_node)
                        print("use: ", node)
                        sys.exit("Invalid DFG")

                # Checking out-going forward edges
                outputs = set(node.outputs)
                for next_node in self.forward_edges[node]:
                    if len(outputs & set(next_node.inputs)) == 0:
                        print(f"Erroneous forward edge.")
                        sys.exit("Invalid DFG")

    def show_dfg(self, filename="out.gv"):
        self.check_dfg_integrity()
        dot = Digraph(filename=filename)
        for node in self.nodes:
            dot.node(str(id(node)), str(node))
        for def_instr, use_instr_list in self.forward_edges.items():
            for use_instr in use_instr_list:
                dot.edge(str(id(def_instr)), str(id(use_instr)))

        dot.render(view=True)
