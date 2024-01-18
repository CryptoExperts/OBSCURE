from pycparser import c_parser, c_ast, c_generator
from .alphaconvert import AlphaConverter
from .normalize import Normalizer
import IR
from utils import debug_print_AST, debug_print_IR
from .AST_to_IR import AST_to_IR


def file_to_IR(filestream, config):
    ast = file_to_AST(filestream)
    debug_print_AST(config.verbose >= 5, "Initial AST", ast)

    # Alpha-conversion (to avoid name conflicts later on)
    AlphaConverter().visit(ast)
    debug_print_AST(config.verbose >= 10, "Alpha-converted AST:", ast)

    # Normalize AST (remove high-level constructs)
    (ast, returns) = Normalizer().normalize(ast)
    debug_print_AST(config.verbose >= 10, "Normalized AST:", ast)

    # Conversion to non-SSA IR
    ir = AST_to_IR().convert(ast, returns)
    debug_print_IR(config.verbose >= 10, "Initial IR:", ir)

    # Conversion to SSA IR
    ir = to_SSA(ir)
    debug_print_IR(config.verbose >= 10, "Initial SSA IR:", ir)

    # Copy propagation
    ir = propagate_copy(ir)
    debug_print_IR(config.verbose >= 10, "Initial SSA IR after CP:", ir)

    # Remove dead code
    ir = remove_dead_code(ir)
    debug_print_IR(config.verbose >= 5, "Final initial IR:", ir)


    return ir


def file_to_AST(filestream):
    """Returns a pycparser AST from a file stream"""
    c_source = filestream.read()
    parser = c_parser.CParser()
    return parser.parse(c_source)


def to_SSA(ir):
    """Converts a non-SSA HLIRProgram into an SSA HLIRProgram"""

    new_instrs = [] # The instructions of the new SSA program
    env = dict() # Mapping from old adresses to new adresses
    written = set() # The set of memory adresses that have already been written

    # Set |written| to the inputs (ie, we cannot override the inputs)
    # TODO: do we want to change that for arrays?
    for inp in ir.inputs:
        written.add(inp.m)

    # Get the adress of the first unused memory cell (note that all
    # cells afterwards are unused as well, by construction)
    first_avail_mem = 0
    for instr in ir.instrs:
        first_avail_mem = max(first_avail_mem, instr.dst.m+1)

    # A simple helper to update source operands (in particular, if a
    # source operand is a MemOperand and this memory adress has been
    # written to multiple times, the the SSA transformation has
    # changed this address)
    def update_src(src:IR.Operand):
        if src is None:
            return src
        if isinstance(src, IR.ImmOperand):
            return src
        else:
            # Else, src has to be MemOperand
            if src.m in env:
                return IR.MemOperand(env[src.m])
            else:
                return src

    # The main loop: iterate over each instruction, update its source
    # operands, and, if the destination has already been written to,
    # assign the result to a new destination
    for instr in ir.instrs:
        src1 = update_src(instr.src1)
        src2 = update_src(instr.src2)
        src3 = update_src(instr.src3)

        dst_addr = instr.dst.m
        if dst_addr in written:
            # |dst_addr| has already been written to -> we replace it
            # by a fresh memory cell
            env[dst_addr] = first_avail_mem
            dst_addr = first_avail_mem
            first_avail_mem += 1
        dst = IR.MemOperand(dst_addr)
        written.add(dst_addr)

        # if instr.dst in ir.outputs:
        #     # Updating output
        #     ir.outputs[ir.outputs.index(instr.dst)] = dst


        new_instrs.append(IR.HLI(instr.opcode, dst, src1, src2, src3))

    # In the current state of the compiler, ir.outputs is written to
    # only once, and should thus not be changed by copy-propagation,
    # which means that this step is not really necessary. Anyways, it
    # doesn't hurt, so...
    outputs = [ IR.MemOperand(env[addr.m]) if addr.m in env else addr
                for addr in ir.outputs ]

    return IR.HLIRProgram(new_instrs, ir.inputs, outputs, first_avail_mem)


def propagate_copy(ir:IR.HLIRProgram):
    """Performs copy propagation on an SSA HLIRProgram"""

    new_instrs = [] # The instructions of the new program
    env = dict()    # The mapping of copies

    # A simpler helper to apply the copy propagation on an operand
    def update_src(src:IR.Operand):
        # TODO: this is the same helper as the "update_src" in
        # "to_SSA". Would be nice to merge both.
        if src is None:
            return src
        if isinstance(src, IR.ImmOperand):
            return src
        else:
            # Else, src has to be MemOperand
            if src.m in env:
                return env[src.m]
            else:
                return src

    outputs = set(ir.outputs)
    n = len(ir.instrs)
    for (i, instr) in enumerate(ir.instrs):
        src1 = update_src(instr.src1)
        src2 = update_src(instr.src2)
        src3 = update_src(instr.src3)
        dst  = instr.dst

        if instr.opcode == IR.Opcode.MOV and i != n-1:
            env[dst.m] = src1
            if dst not in outputs:
                continue
            # If |dst| is an output, we could have skipped the
            # "env[dst.m] = src1". However, outputs of the program are
            # not encrypted, and thus cannot be used in computations
            # with unencrypted programs. Thus, it's a bit more
            # convenient to do the copy propagation for outputs, but
            # still generate the MOV. For instance:
            #
            #     o1 = i
            #     v  = o1 ^ k
            #     o2 = v
            #
            # Will be transformed to:
            #
            #     o1 = i
            #     v  = i ^ k
            #     o2 = v
            #
            # Rather than:
            #
            #     o1 = i
            #     v  = o1 ^ k
            #     o2 = v
            #
            # Note that doing a pass of backwards copy-propagation
            # could be useful (as shown by this example). TODO.

        new_instrs.append(IR.HLI(instr.opcode, dst, src1, src2, src3))

    return IR.HLIRProgram(new_instrs, ir.inputs, ir.outputs, ir.memory_count)


def fix_outputs(ir:IR.HLIRProgram):
    """Copy outputs that are read so that outputs are never read

    WARNING: OBSOLETE. This function is now obsolete: this
    transformation is done directly inside the clusterizer/universalizer.

    The token does not encrypt outputs, but encrypts all internal
    data. In order to avoid having to compute on both encrypted and
    clear data, we impose that outputs are never read. If an output is
    read in the program, then this function will make a copy: the
    original output is no longer an output and can be read, while the
    copy is the new output and can never be read.

    """

    outputs = set(ir.outputs) # Set of outputs that should not be read
    new_outputs = dict() # Mapping from old outputs to new
    first_avail_mem = ir.memory_count

    added_instrs = []
    for instr in ir.instrs:
        src1 = instr.src1
        src2 = instr.src2
        src3 = instr.src3

        for src in [src1, src2, src3]:
            if src in outputs:
                new_out = IR.MemOperand(first_avail_mem)
                first_avail_mem += 1
                added_instrs.append(IR.HLI(IR.Opcode.MOV, new_out, src))
                outputs.remove(src) # So that we do re-copy this output
                new_outputs[src] = new_out

    updated_outputs = [ new_outputs.get(out, out) for out in ir.outputs ]
    ir.memory_count = first_avail_mem

    return IR.HLIRProgram(ir.instrs + added_instrs, ir.inputs,
                          updated_outputs, first_avail_mem)

def remove_dead_code(ir:IR.HLIRProgram) -> IR.HLIRProgram:
    """Removes instructions whose results is not used

    Some dead come may come from the initial program, and some other
    dead code can be introduced by our compiler when unrolling
    loop. Indeed, to unroll a loop such as:

        for (i = 0; i < 42; i++) {
            arr[i] = f(x)
        }

    We convert this to:

         i = 0;
         arr[0] = f(x)
         i = 1;
         arr[1] = f(x)
         ...

    As you can see, the "i = _" instructions are actually dead code
    (because we do constant propagation in the NodeCopyVisitorWithEnv,
    and thus generate "arr[0]", "arr[1]" etc, instead of "arr[i]".

    """
    new_instrs = []
    outputs = set(ir.outputs)

    read = set()
    for hli in reversed(ir.instrs):
        if hli.dst not in read and hli.dst not in outputs:
            # The output of this HLI is never read nor returned. We
            # remove it (by not adding it to |new_instrs|).
            pass
        else:
            new_instrs.append(hli)
            # Marking the inputs as read
            for m in hli.mem_inputs():
                read.add(m)

    return IR.HLIRProgram(list(reversed(new_instrs)), ir.inputs, ir.outputs,
                          ir.memory_count)
