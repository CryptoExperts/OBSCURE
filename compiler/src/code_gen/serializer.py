from enum import Enum
from typing import Final
from math import ceil, log2
from IR import Opcode, ImmOperand, RegOperand, LLI, LLIRProgram
from schwaemm import schwaemm128128_encrypt
from pysodium import crypto_box_seal
from .keys import shared_key, pubkey

class OperandCode(Enum):
    """
    I: ImmOperand
    R: RegOperand
    N: NulOperand

    An instruction has format: dst,src1,[src2],[src3]
    where src1,src2,src3 can be a immediate (ImmOperand) or a register (RegOperand)
    and src2,src3 can be null (NulOperand). dst is always a register (RegOperand).
    
    Below are all possible instructions.
    For example:
        RRN: src1=RegOperand, src2=RegOperand, src3=NulOperand
        
    """

    INN = 0
    IRN = 1
    IRR = 2
    IRI = 3
    IIN = 4
    IIR = 5
    III = 6
    RNN = 7
    RRN = 8
    RRI = 9
    RRR = 10
    RII = 11
    RIR = 12
    RIN = 13

    def __str__(self):
        return self.name

NUL_FLAG = '00'
REG_FLAG = '01'
IMM_FLAG = '10'


class ID:
    def __init__(self, instrID: int, outputID: int):
        self.instrID  : Final = instrID
        self.outputID : Final = outputID

    def __str__(self):
        return f"(InstrID, OutputID) = ({self.instrID}, {self.outputID})"


def create_opdict():
    """count = 16, each opcode is represented by 4 bits"""
    assert len(Opcode) <= 16
    opdict = {}
    for x in Opcode:
        b = bin(x.value)[2:]
        opdict[x.name] = '0'*(4-len(b)) + b
    return opdict

def create_operanddict():
    """count = 14, each code is represented by 4 bits"""
    operanddict = {}
    for x in OperandCode:
        b = bin(x.value)[2:]
        operanddict[x.name] = '0'*(4-len(b)) + b
    return operanddict

def create_memdict(count: int, bytelen: int):
    memdict = {}
    for i in range(count):
        memdict[i] = (i).to_bytes(bytelen, byteorder='big')
    return memdict

def uint_tobytes(n: int, bytelen: int):
    return (n).to_bytes(bytelen, byteorder='big')

def bin_tobytes(bitstr: str):
    bitlen = len(bitstr)
    assert bitlen % 8 == 0
    n = int(bitstr, 2)
    return (n).to_bytes(bitlen//8, byteorder='big')

def serialize_metadata(config):
    meta_bytecode = bytes()

    # version (32)
    meta_bytecode += uint_tobytes(config.version, 4)
    # word_size (32)
    meta_bytecode += uint_tobytes(config.word_size, 4)
    # LLMI_max_input_count (l_in) (32)
    meta_bytecode += uint_tobytes(config.l_in, 4)
    # LLMI_max_output_count (l_out) (32)
    meta_bytecode += uint_tobytes(config.l_out, 4)
    # register_count (r) (32)
    meta_bytecode += uint_tobytes(config.r, 4)
    # LLS_max_length (s) (32)
    meta_bytecode += uint_tobytes(config.s, 4)

    return meta_bytecode

def serialize_lls(lls, regdict: dict, opdict: dict, operanddict: dict, config):
    lls_bytecode = bytes()

    for lli in lls:
        if lli.is_nop():
            lli_code = opdict[Opcode.NOP.value] + NUL_FLAG + NUL_FLAG
            lls_bytecode += lli_code
            continue

        # opcode (4)
        op_code = opdict[lli.opcode.name]
        flag = ''

        # dst (lb_r)
        dst_code = regdict[lli.dst.r]

        # src1 (lb_r or word_size)
        src1_code = bytes()
        if isinstance(lli.src1, RegOperand):
            flag += 'R'
            src1_code += regdict[lli.src1.r]
        elif isinstance(lli.src1, ImmOperand):
            flag += 'I'
            src1_code += uint_tobytes(lli.src1.imm, config.word_size // 8)
        else:
            raise ValueError('Invalid Operand.')

        # src2 (0 or lb_r or word_size)
        src2_code = bytes()
        if lli.src2 is None:
            flag += 'N'
            # src2_code is skipped
        elif isinstance(lli.src2, RegOperand):
            flag += 'R'
            src2_code += regdict[lli.src2.r]
        elif isinstance(lli.src2, ImmOperand):
            flag += 'I'
            src2_code += uint_tobytes(lli.src2.imm, config.word_size // 8)
        else:
            raise ValueError('Invalid Operand.')

        # src3 (0 or lb_r or word_size)
        src3_code = bytes()
        if lli.src3 is None:
            flag += 'N'
        elif isinstance(lli.src3, RegOperand):
            flag += 'R'
            src3_code += regdict[lli.src3.r]
        elif isinstance(lli.src3, ImmOperand):
            flag += 'I'
            src3_code += uint_tobytes(lli.src3.imm, config.word_size // 8)
        else:
            raise ValueError('Invalid Operand.')

        flag_code = operanddict[flag]
        opfl_code = bin_tobytes(op_code + flag_code)
        lli_code = opfl_code + dst_code + src1_code + src2_code + src3_code
        lls_bytecode += lli_code

    return lls_bytecode

def serialize(ir:LLIRProgram, config):
    outputs = set(ir.outputs)
    l_out = config.l_out

    bytecode = bytes()
    # bytelen
    lb_o = ((ceil(log2(l_out)) + 7) & (-8)) // 8             # for 1 outputID
    lb_m = ((ceil(log2(ir.memory_count)) + 7) & (-8)) // 8   # for 1 memory cell
    lb_r = ((ceil(log2(config.r)) + 7) & (-8)) // 8          # for 1 register

    # metadata (6*32)
    bytecode += serialize_metadata(config)

    # memory_count (32)
    bytecode += uint_tobytes(ir.memory_count, 4)
    memdict = create_memdict(ir.memory_count, lb_m)

    # program header (512)
    ct_sk = crypto_box_seal(shared_key, pubkey)
    bytecode += ct_sk

    # input_count (lb_m)
    bytecode += uint_tobytes(len(ir.inputs), lb_m)

    # inputs (lb_m * input_count)
    id_dict = dict() # dict of (InstrID, OutputID)
    for (idx, inp) in enumerate(ir.inputs):
        bytecode += memdict[inp.m]
        instrID  = idx//l_out + 1
        outputID = idx % l_out
        id_dict[inp.m] = ID(instrID, outputID)

    # output_count (lb_m)
    bytecode += uint_tobytes(len(ir.outputs), lb_m)

    # outputs (lb_m * output_count)
    for out in ir.outputs:
        bytecode += memdict[out.m]

    # LLMI_count (32)
    bytecode += uint_tobytes(len(ir.instrs), 4)

    # Flush header to output
    config.outfile.write(bytecode)

    # LLMI
    opdict = create_opdict()
    operanddict = create_operanddict()
    regdict = create_memdict(config.r, lb_r)
    for (i, llmi) in enumerate(ir.instrs):
        instrID = (i+1) + (len(ir.inputs)//l_out + 1)

        # input_count (lb_m)
        input_count_bstr = uint_tobytes(len(llmi.inputs), lb_m)

        # inputs (lb_m * input_count)
        inputIDs     = [] # list of (instrID, outputID)
        inputs_bstr  = bytes()
        for inp in llmi.inputs:
            inputs_bstr += memdict[inp.m]
            inputIDs.append(id_dict[inp.m])

        # output_count (lb_m)
        output_count_bstr = uint_tobytes(len(llmi.outputs), lb_m)

        # outputs (lb_m * output_count)
        outputs_bstr = bytes()
        for (outputID, out) in enumerate(llmi.outputs):
            outputs_bstr  += memdict[out.m]
            id_dict[out.m] = ID(instrID, outputID)

        # InstrID (32)
        instrID_bstr = uint_tobytes(instrID, 4)

        # RevealFlag (8)
        reveal_flag = 1 if [ True for out in llmi.outputs
                             if out in outputs ] != [] else 0
        rflag_bitstr = bin(reveal_flag)[2:]
        rflag_bitstr = (8-len(rflag_bitstr))*'0' + rflag_bitstr
        rflag_bstr = bin_tobytes(rflag_bitstr)

        # inputIDs ((lb_o + 32)*input_count)
        inputIDs_bstr = bytes()
        for id in inputIDs:
            inputIDs_bstr += uint_tobytes(id.instrID, 4)
            inputIDs_bstr += uint_tobytes(id.outputID, lb_o)

        # LLS
        lls_code_bstr = serialize_lls(llmi.seq.instrs, \
                                      regdict, \
                                      opdict, \
                                      operanddict, \
                                      config)
        msg   = lls_code_bstr
        ad    = (instrID_bstr + rflag_bstr + \
                    input_count_bstr + inputIDs_bstr + output_count_bstr)
        nonce = uint_tobytes(instrID, 32)
        lls_code_bstr  = schwaemm128128_encrypt(msg, ad, nonce, shared_key)

        # LLS_bytelen (32)
        lls_bytelen_bstr = uint_tobytes(len(lls_code_bstr), 4)

        llmi_code = input_count_bstr  + inputs_bstr       \
                  + output_count_bstr + outputs_bstr      \
                  + instrID_bstr                          \
                  + rflag_bstr                            \
                  + inputIDs_bstr                         \
                  + lls_bytelen_bstr  + lls_code_bstr

        config.outfile.write(llmi_code)
