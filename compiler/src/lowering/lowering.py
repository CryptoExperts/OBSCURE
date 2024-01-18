from IR import MLMI, LLMI, LLS, LLI, RegOperand, MemOperand, ImmOperand, LLIRProgram, Opcode
from .reg_alloc import LinearScanAllocator
import DFG

def MLMI_to_LLMI(mlmi:MLMI, max_register_count:int, max_output_count:int):
    """Converts an MLMI into an LLMI"""
    inputs = mlmi.inputs or [ MemOperand(0) ]
    registers = LinearScanAllocator().get_registers_mapping(
        mlmi.seq.instrs, inputs, mlmi.outputs, max_register_count,
        max_output_count)

    def convert_src(src):
        if src == None:
            return None
        if isinstance(src, MemOperand):
            return registers[src]
        if isinstance(src, ImmOperand):
            return src
        assert False

    # Note that we assume that the instructions inside the MLS are
    # correctly scheduled.
    instrs = []
    for instr in mlmi.seq:
        dst = registers[instr.dst]
        src1 = convert_src(instr.src1)
        src2 = convert_src(instr.src2)
        src3 = convert_src(instr.src3)
        instrs.append(LLI(instr.opcode, dst, src1, src2, src3))

    return LLMI(LLS(instrs), inputs, mlmi.outputs)


def extract_outputs(llir:LLIRProgram, config):
    """Extract outputs of the program into their own LLMI

    OUTDATED: this is now done in the universalitzation

    This will allow the code generator to mark those LLMI as "reveal".

    TODO: I think that doing this at the DFG level might make sense
    and enable some additional merges.

    """
    # Extracting the outputs that need to be put in their own LLMI
    generated_outputs = set()
    prog_outputs = set(llir.outputs)
    outputs_to_extract = set()
    for instr in llir.instrs:
        outputs_to_reveal = set()
        for o in instr.outputs:
            if o in prog_outputs:
                outputs_to_reveal.add(o)
            generated_outputs.add(o)
        if len(outputs_to_reveal) != len(instr.outputs):
            outputs_to_extract.update(outputs_to_reveal)
        else:
            # Checking if subsequent instructions use any of
            # |outputs_to_reveal| (if so, it's possible that this MI
            # as only program outputs as its outputs, but that they
            # actually need to be encrypted here)
            for other_instr in llir.instrs:
                if other_instr == instr:
                    continue
                found = False
                for o in outputs_to_reveal:
                    if o in other_instr.inputs:
                        outputs_to_extract.update(outputs_to_reveal)
                        found = True
                        break
                if found:
                    break

    # Extracting outputs that are direct inputs of the program (ie,
    # there was an input/output array where some items were not
    # updated). Since inputs are encrypted, those outputs will need to
    # be put in separated LLMIs with the reveal flag in order to be
    # decrypted.
    prog_inputs = set(llir.inputs)
    for o in prog_outputs:
        if o in llir.inputs:
            outputs_to_extract.add(o)

    # Grouping the outputs of |outputs_to_extract| into LLMIs
    first_output_idx_in_LLMI = config.r - config.l_out
    next_free_memory = llir.memory_count
    old_to_new_outputs = { m:m for m in llir.outputs }
    while len(outputs_to_extract) != 0:
        curr_instrs  = []
        curr_inputs  = []
        curr_outputs = []
        while len(outputs_to_extract) > 0 and \
              len(curr_instrs) < config.s and \
              len(curr_instrs) < config.l_in and \
              len(curr_instrs) < config.l_out:
            old_output = outputs_to_extract.pop()
            new_output = MemOperand(next_free_memory)
            next_free_memory += 1
            old_to_new_outputs[old_output] = new_output
            idx_in_instr = len(curr_instrs)
            curr_instrs.append(LLI(Opcode.MOV, RegOperand(first_output_idx_in_LLMI+idx_in_instr),
                                   RegOperand(idx_in_instr)))
            curr_inputs.append(old_output)
            curr_outputs.append(new_output)
        if curr_instrs != []:
            llir.instrs.append(LLMI(LLS(curr_instrs), curr_inputs, curr_outputs))

    llir.memory_count = next_free_memory
    llir.outputs = [ old_to_new_outputs[m] for m in llir.outputs ]


def lower(dfg, config) -> LLIRProgram:

    llir = dfg.to_LLIR(config)
    #extract_outputs(llir, config)

    return llir
