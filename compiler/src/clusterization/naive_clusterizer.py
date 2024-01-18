"""This naive clusterizer puts a single LLI per LLS

Despites its simplicity, this clusterizers respects the
constraints of the compiler's configuration (number of
inputs/outputs/registers/instructions). Number of inputs and
internal registers is trivial to meet (since we consider a single
instruction per LLS), but outputs and instructions require a tiny
bit of work:

  - by convention, outputs are supposed to be in the last l_out registers.

  - LLC must be padded with NOPs to be s instructions long

"""

import IR


def convert_src_input_mem_to_reg(src, input_reg_dict):
    """Returns the register to used for an operand

    Note that this function assumes that |src| is an operand of the
    first instruction of an sequence, and that it corresponds to an
    input of the LLMI (ie, it cannot need to be mapped to an internal
    register of the LLMI).

    """
    if src is None:
        return None

    if isinstance(src, IR.ImmOperand):
        return src

    if src.m in input_reg_dict['mapping']:
        # This special case will only be used if the 2 operands of an
        # LLMI the same. For instance,
        #
        #     XOR m[1], m[0], m[0]
        #
        # In that case, m[0] will be mapped to r[0], and we need this
        # if to make sure that we do not compile this to
        #
        #     XOR _, r[0], r[1]
        #
        return IR.RegOperand(input_reg_dict['mapping'][src.m])

    else:
        # This is the standard case: the memory operand has not been
        # encoutered yet, and is thus assumed to be in the next unused
        # register (the index of this register can be found in
        # input_reg_dict['next_input_reg'])
        input_reg_dict['mapping'][src.m] = input_reg_dict['next_input_reg']
        reg = IR.RegOperand(input_reg_dict['next_input_reg'])
        input_reg_dict['next_input_reg'] += 1
        return reg


def clusterize(hlir:IR.HLIRProgram, config) -> IR.LLIRProgram :
    clusterized_instrs = [] # The LLMIs

    l_out = config.l_out # Number of outputs
    r = config.r # Number of internal registers
    s = config.s # Number of instructions per LLS


    for instr in hlir.instrs:
        inputs  = [ x for x in [ instr.src1, instr.src2, instr.src3 ]
                    if x and isinstance(x, IR.MemOperand) ]
        outputs = [ instr.dst ]

        if len(inputs) == 0:
            # Adding a dummy input, just because the interpreter
            # requires all LLMI to have at least one input. Actually,
            # we might want to go further and make it so that all LLMI
            # have the same amount of inputs.
            inputs = [ IR.MemOperand(0) ]

        input_reg_dict = { 'next_input_reg': 0, # Next not-yet-used input
                           'mapping': dict() # Map from inputs to local registers
                          }

        dst  = IR.RegOperand(r-l_out)
        src1 = convert_src_input_mem_to_reg(instr.src1, input_reg_dict)
        src2 = convert_src_input_mem_to_reg(instr.src2, input_reg_dict)
        src3 = convert_src_input_mem_to_reg(instr.src3, input_reg_dict)

        ll_instr = IR.LLI(instr.opcode, dst, src1, src2, src3)
        lls = IR.LLS([ ll_instr ])
        # Uncomment the following line to do NOP padding
        # lls.instrs.extend([ IR.LLI(IR.Opcode.NOP) ] * (s - 1))
        clusterized_instrs.append(IR.LLMI(lls, inputs, outputs))

    return IR.LLIRProgram(clusterized_instrs, hlir.inputs, hlir.outputs, hlir.memory_count)
