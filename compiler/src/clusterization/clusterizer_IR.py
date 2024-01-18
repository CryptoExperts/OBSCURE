"""Mid-level intermediate representation used by clusterizers

During clusterization, it's easier to have an intermediate
representation to build multi-instructions without taking registers
into account. We thus introduce here MLS (mid-level sequences) and
MLMI (mid-level multi instructions), which are similar to LLS and
LLMI, except that instruction still use memory adresses rather than
registers.

"""
from IR import ImmOperand, MemOperand, RegOperand, HLI, LLI, LLS, LLMI
from .reg_alloc import LinearScanAllocator

class MLS:
    """Mid-level Sequence"""
    def __init__(self, instrs:list[HLI]):
        self.instrs = instrs

    def __str__(self):
        return "\n".join([ "    " + str(i) for i in self.instrs ])

    def __iter__(self):
        for instr in self.instrs:
            yield instr

    def get_defs(self):
        """Returns variables defined by this MLS"""
        defs = set()
        for instr in self.instrs:
            defs.add(instr.dst)
        return defs

    def get_used(self):
        """Returns registers used but not defs by this MLS"""
        defs = self.get_defs()
        used = set()
        for instr in self.instrs:
            for src in [instr.src1, instr.src2, instr.src3]:
                if isinstance(src, MemOperand):
                    used.add(src)
        return used - defs


class MLMI:
    """Mid-level Multi instruction"""
    def __init__(self, seq:MLS,
                 inputs:list[MemOperand],
                 outputs:list[MemOperand]):
        self.seq     = seq
        self.inputs  = inputs
        self.outputs = outputs

    @staticmethod
    def FromHLI(hli:HLI):
        """Creates an MLMI from an HLI"""
        inputs =  [ src for src in [hli.src1, hli.src2, hli.src3]
                    if isinstance(src,MemOperand) ]
        outputs = [ hli.dst ]
        return MLMI(MLS([hli]), inputs, outputs)

    def get_defs(self):
        """Returns variables defined by this MLMI"""
        return self.seq.get_defs()

    def get_used(self):
        """Returns registers used but not defs by this MLMI"""
        return self.seq.get_used()

    def to_LLMI(self, max_register_count:int, max_output_count:int):
        """Converts this MLMI into an LLMI"""
        inputs = self.inputs or [ MemOperand(0) ]
        registers = LinearScanAllocator().get_registers_mapping(
            self.seq.instrs, inputs, self.outputs, max_register_count,
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
        for instr in self.seq:
            dst = registers[instr.dst]
            src1 = convert_src(instr.src1)
            src2 = convert_src(instr.src2)
            src3 = convert_src(instr.src3)
            instrs.append(LLI(instr.opcode, dst, src1, src2, src3))

        return LLMI(LLS(instrs), inputs, self.outputs)


    def __str__(self):
        inputs  = ", ".join([ str(i) for i in self.inputs  ])
        outputs = ", ".join([ str(i) for i in self.outputs ])
        seq     = str(self.seq)
        return f"{{\n  inputs: {inputs}\n  outputs: {outputs}\n  MLS:\n{seq}\n}}"

class MLIRProgram:
    """Mid-level Program"""

    def __init__(self, instrs:list[MLMI], inputs:list[MemOperand],
                 outputs:list[MemOperand], memory_count: int):
        self.instrs = instrs
        self.inputs  = inputs
        self.outputs = outputs
        self.memory_count = memory_count

    def __str__(self):
        inputs  = ", ".join([ str(i) for i in self.inputs  ])
        outputs = ", ".join([ str(i) for i in self.outputs ])
        body    = "\n".join([ "  " + str(i) for i in self.instrs ])
        return f"Inputs: {inputs}\nOutputs: {outputs}\nBody:\n{body}\n"
