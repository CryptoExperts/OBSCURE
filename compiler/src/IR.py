from abc    import ABC, abstractmethod
from enum   import Enum
from typing import Final

class Opcode(Enum):
    NOP = 0
    MOV = 1
    XOR = 2
    OR  = 3
    AND = 4
    LSL = 5
    LSR = 6
    LT  = 7
    ADD = 8
    SUB = 9
    MUL = 10
    EQ = 11

    DIV = 13
    MOD = 14
    CMOV = 15

    def __str__(self):
        return self.name

class Operand(ABC):
    pass

class MemOperand(Operand):
    def __init__(self, m:int):
        self.m : Final = m

    def __str__(self):
        return "m[" + str(self.m) + "]"

    def __eq__(self, other):
        if isinstance(other, MemOperand):
            return self.m == other.m
        return False

    def __hash__(self):
        return self.m

class RegOperand(Operand):
    def __init__(self, r:int):
        self.r : Final = r

    def __str__(self):
        return "r[" + str(self.r) + "]"

    def __eq__(self, other):
        if isinstance(other, RegOperand):
            return self.r == other.r
        return False

    def __hash__(self):
        return self.r


class ImmOperand(Operand):
    def __init__(self, imm:int):
        self.imm : Final = imm

    def __str__(self):
        return str(self.imm)

    def __eq__(self, other):
        if isinstance(other, ImmOperand):
            return self.imm == other.imm
        return False

    def __hash__(self):
        return self.imm



class HLI:
    """High level instruction

    At this point, the destination is a memory adress, and the source
    operands are either memory adresses or immediates. In particular,
    there are no registers yet.

    """
    def __init__(self, opcode:Opcode, dst:MemOperand=None, src1:Operand=None,
                 src2:Operand=None, src3:Operand=None):
        assert(not(src3 is not None and src2 is None))
        self.opcode : Final = opcode
        self.dst    : Final = dst
        self.src1   : Final = src1
        self.src2   : Final = src2
        self.src3   : Final = src3

    def mem_inputs(self):
        for m in [self.src1, self.src2, self.src3]:
            if isinstance(m, MemOperand):
                yield m

    def __eq__(self, other):
        if isinstance(other, HLI):
            return self.opcode == other.opcode and \
                self.dst == other.dst and \
                self.src1 == other.src1 and \
                self.src2 == other.src2 and \
                self.src3 == other.src3
        return False

    def __hash__(self):
        return self.opcode.__hash__() ^ self.dst.__hash__() ^ \
            (self.src1.__hash__() << 8) ^ (self.src2.__hash__() << 16) ^ \
            (self.src3.__hash__() << 24)

    def __str__(self):
        if self.opcode == Opcode.NOP:
            return "NOP"
        src2_str = ", " + str(self.src2) if self.src2 else ""
        src3_str = ", " + str(self.src3) if self.src3 else ""
        return str(self.opcode) + " " + str(self.dst) + ", " + \
            str(self.src1) + src2_str + src3_str

class MLS:
    """Mid-level Sequence"""
    def __init__(self, instrs):
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
    def __init__(self, seq:MLS, inputs, outputs):
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

    def __str__(self):
        inputs  = ", ".join([ str(i) for i in self.inputs  ])
        outputs = ", ".join([ str(i) for i in self.outputs ])
        seq     = str(self.seq)
        return f"{{\n  inputs: {inputs}\n  outputs: {outputs}\n  MLS:\n{seq}\n}}"


class LLI:
    """Low level instruction

    LLIs (Low-level instructions) should be part of a LLS (low-level
    sequence) inside an LLMI (low-level multi-instruction). As such,
    LLI manipulate the registers rather than the global memory (the
    source operands are thus either registers or immediate).

    """
    def __init__(self, opcode:Opcode, dst:RegOperand=None, src1:Operand=None,
                 src2:Operand=None, src3:Operand=None):
        assert(not(src3 is not None and src2 is None))
        self.opcode : Final = opcode
        self.dst    : Final = dst
        self.src1   : Final = src1
        self.src2   : Final = src2
        self.src3   : Final = src3

    def is_nop(self):
        return self.opcode == Opcode.NOP

    def __eq__(self, other):
        if isinstance(other, LLI):
            return self.opcode == other.opcode and \
                self.dst == other.dst and \
                self.src1 == other.src1 and \
                self.src2 == other.src2 and \
                self.src3 == other.src3
        return False

    def __hash__(self):
        return self.opcode.__hash__() ^ self.dst.__hash__() ^ \
            (self.src1.__hash__() << 8) ^ (self.src2.__hash__() << 16) ^ \
            (self.src3.__hash__() << 24)

    def __str__(self):
        if self.is_nop():
            return str(self.opcode)
        else:
            src2_str = ", " + str(self.src2) if self.src2 else ""
            src3_str = ", " + str(self.src3) if self.src3 else ""
            return str(self.opcode) + " " + str(self.dst) + ", " + \
                str(self.src1) + src2_str + src3_str


class LLS:
    """Low level sequence"""
    def __init__(self, instrs):
        self.instrs = instrs

    def __str__(self):
        return "\n".join([ "    " + str(i) for i in self.instrs ])

    def __eq__(self, other):
        if isinstance(other, LLS):
            return self.instrs == other.instrs
        return False

    def __hash__(self):
        hash = 0
        for i in self.instrs:
            hash ^= i.__hash__()
        return hash

    def __iter__(self):
        for instr in self.instrs:
            yield instr

class LLMI:
    """Low-level multi-instruction

    At the low-level IR, a program is a list of low-level
    multi-instructions (LLMI). Each LLMI has its own registers. The
    execution of an LLMI is as follows:

      1. Fetch the |inputs| from the global memory, and pass them as
      argument to the token. Inside the token:

         3. Decrypt the inputs and store them in the internal registers

         4. Execute the LLS (|seq|) of the LLMI

         5. Encrypt and return the last |len(outputs)| registers

      6. Store the outputs of the token into the registers at adresses
        |outputs| in the global memory.

    Attributes/Parameters:
    ------------
      * instrs: the single-instructions of this multi-instruction.
      * inputs: the inputs of this multi-instructions. Those are register
                indices in the main memory.
      * outputs: where to store the outputs of this multi-instructions. Those
                are also indices in the main memory.

    """

    def __init__(self, seq:LLS, inputs, outputs):
        self.seq     = seq
        self.inputs  = inputs
        self.outputs = outputs

    def __eq__(self, other):
        if isinstance(other, LLMI):
            return self.seq == other.seq and \
                self.inputs == other.inputs and \
                self.outputs == other.outputs
        return False

    def __hash__(self):
        hash = self.seq.__hash__()
        for i in self.inputs:
            hash ^= i.__hash__()
        for o in self.outputs:
            hash ^= o.__hash__()
        return hash

    def __str__(self):
        inputs  = ", ".join([ str(i) for i in self.inputs  ])
        outputs = ", ".join([ str(i) for i in self.outputs ])
        seq     = str(self.seq)
        return f"{{\n  inputs: {inputs}\n  outputs: {outputs}\n  LLS:\n{seq}\n}}"


class HLIRProgram:
    """High-level intermediate representation

    A program at that level is simply a list of HLI. Global memory is
    in SSA at that point.

    """

    def __init__(self, instrs, inputs, outputs, memory_count: int):
        self.instrs = instrs
        self.inputs  = inputs
        self.outputs = outputs
        self.memory_count = memory_count

    def __str__(self):
        inputs  = ", ".join([ str(i) for i in self.inputs  ])
        outputs = ", ".join([ str(i) for i in self.outputs ])
        body    = "\n".join([ "  " + str(i) for i in self.instrs ])
        return f"Inputs: {inputs}\nOutputs: {outputs}\nBody:\n{body}\n"

class MLIRProgram:
    """Mid-level Program

    A program at that level is a list of mid-level multi
    instructions. Register allocation has not yet been performed.

    """

    def __init__(self, instrs, inputs, outputs, memory_count: int):
        self.instrs = instrs
        self.inputs  = inputs
        self.outputs = outputs
        self.memory_count = memory_count

    def __str__(self):
        inputs  = ", ".join([ str(i) for i in self.inputs  ])
        outputs = ", ".join([ str(i) for i in self.outputs ])
        body    = "\n".join([ "  " + str(i) for i in self.instrs ])
        return f"Inputs: {inputs}\nOutputs: {outputs}\nBody:\n{body}\n"


class LLIRProgram:
    """Low-level intermediate representation

    A program at that level is a list of low-level
    multi-instructions. The memory does not have to be in SSA. (in all
    likelyhood, it is initially, but some later pass should remove the
    SSA to optimize memory usage)

    """

    def __init__(self, instrs, inputs, outputs, memory_count:int):
        self.instrs  = instrs
        self.inputs  = inputs
        self.outputs = outputs
        self.memory_count = memory_count

    def __str__(self):
        inputs  = ", ".join([ str(i) for i in self.inputs  ])
        outputs = ", ".join([ str(i) for i in self.outputs ])
        body    = "\n".join([ str(i) for i in self.instrs ])
        return f"Inputs: {inputs}\nOutputs: {outputs}\nBody:\n{body}\n"
