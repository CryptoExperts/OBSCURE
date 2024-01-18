"""Register allocation and graph coloring"""

from IR import HLI, MemOperand, RegOperand, MLMI, MLS
from collections import defaultdict
from graphviz import Graph


# ----------------------------------------------------- #
#
#              Linear scan register allocation
#
# ----------------------------------------------------- #
class LinearScanAllocator:
    not_enough_register_msg = 'Not enough registers to perform register allocation'

    def compute_live_intervals(self, instrs, inputs, outputs):
        """Compute live intervals for all variables of |instrs|"""
        births = defaultdict(lambda:set())
        deaths = defaultdict(lambda:set())
        for m in inputs:
            births[-1].add(m)
        for m in outputs:
            deaths[len(instrs)+1].add(m)

        # Setting births
        for idx, instr in enumerate(instrs):
            births[idx].add(instr.dst)

        # Setting deaths
        last = len(instrs) - 1
        dead = set()
        for idx, instr in enumerate(reversed(instrs)):
            for m in instr.mem_inputs():
                if m not in dead:
                    deaths[last-idx].add(m)
                    dead.add(m)

        return births, deaths

    def get_registers_mapping(self, instrs, inputs,
                              outputs, k:int, max_output_count:int):
        """Assign a register for each MemOperand of |instrs|

        A mapping of MemOperand to RegOperand is thus returned.

        Under no circumstances shall more than |k| registers be used. If
        this happens, this function will throw an error.

        By conventions, inputs will be put in the first registers and
        outputs in the last registers.

        """
        mem_to_reg = dict()
        # Putting inputs in the first registers. Note that we make
        # sure that inputs are actually used: universalisation
        # introduces inputs that are not used.
        used = MLMI(MLS(instrs), inputs, outputs).get_used()
        for idx, m in enumerate(inputs):
            if m in used and m not in mem_to_reg:
                mem_to_reg[m] = RegOperand(idx)
        first_free_register = len(mem_to_reg.keys())

        # Putting outputs in the last registers
        first_output_idx = k - max_output_count
        for idx, m in enumerate(outputs):
            mem_to_reg[m] = RegOperand(first_output_idx+idx)
        last_free_register  = k - len(outputs) - 1

        (births, deaths) = self.compute_live_intervals(instrs, inputs, outputs)

        free_registers = set([RegOperand(r) for r in
                              range(first_free_register, first_output_idx)])

        # Perform linear allocation
        for i in range(len(instrs)):
            # Free registers
            for m in deaths[i]:
                r = mem_to_reg[m]
                free_registers.add(r)
            # Allocating new registers
            for m in births[i]:
                if m not in mem_to_reg:
                    if len(free_registers) == 0:
                        raise ValueError(self.not_enough_register_msg)
                    r = free_registers.pop()
                    mem_to_reg[m] = r

        return mem_to_reg


    def needs_leq_k_registers(self, instrs, inputs,
                              outputs, k:int, max_output_count:int):
        """Returns True if |instrs| requires less than |k| registers
        (and False otherwise)

        """
        try:
            self.get_registers_mapping(instrs, inputs, outputs, k, max_output_count)
            return True
        except ValueError as e:
            if str(e) == self.not_enough_register_msg:
                return False
            raise e


# ----------------------------------------------------- #
#
#              Graph-coloring approach (WIP)
#
# ----------------------------------------------------- #

# Builds the inference graph of |instrs|.
def build_inference_graph(instrs, inputs, outputs):
    # Computing defined point
    born = defaultdict(lambda: set())
    defined = dict()
    for (idx,instr) in enumerate(instrs):
        defined[instr.dst.m] = idx
        born[idx].add(instr.dst.m)
    # Adding inputs to |defined| (we consider that they are defined at instruction -1)
    for i in inputs:
        defined[i] = -1
        born[-1].add(i)

    # Computing last used
    last_used = dict()
    for (idx, instr) in enumerate(instrs):
        for src in [instr.src1, instr.src2, instr.src3]:
            if isinstance(src, MemOperand):
                last_used[src.m] = idx
    # Correction |last_used| for outputs
    for o in outputs:
        last_used[o] = len(instrs)
    # Creating index:died map
    died = defaultdict(lambda: set())
    for mem,idx in last_used.items():
        died[idx].add(mem)

    print("born: ", born)
    print("defined: ", defined)
    print("died: ", died)
    print("last_used: ", last_used)

    # Building inference graph
    inference_graph = defaultdict(lambda: set())
    alive = set() or born[-1]
    # Initialization
    for i in alive:
        for j in alive:
            if j != i:
                inference_graph[i].add(j)
                inference_graph[j].add(i)
    for i in range(len(instrs)+1):
        print(f'i = {i}. Alive: ', alive)
        alive = alive - died[i]
        print("  Died: ", died[i])
        for b1 in born[i]:
            for b2 in born[i]:
                if b1 != b2:
                    inference_graph[b1].add(b2)
                    inference_graph[b2].add(b1)
            for b2 in alive:
                inference_graph[b1].add(b2)
                inference_graph[b2].add(b1)
        alive = alive.union(born[i])

    print("Inference_graph:")
    print(inference_graph)

    # DEBUG ONLY: Plotting the inference graph
    if True:
        dot = Graph()
        shown_edges = set()
        for m in inference_graph:
            dot.node(str(m))
        for (m,l) in inference_graph.items():
            for d in l:
                str_edge = "-".join([str(x) for x in sorted([m,d])])
                if str_edge not in shown_edges:
                    dot.edge(str(m), str(d))
                    shown_edges.add(str_edge)

        #print(dot.source)

        dot.render(view=True)

def is_k_colorable(instrs, inputs, outputs, k:int):
    # Build inference graph
    inference_graph = build_inference_graph(instrs, inputs, outputs)

    # Check if all nodes have less than k neighbors
