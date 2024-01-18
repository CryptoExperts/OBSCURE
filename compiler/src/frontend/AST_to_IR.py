"""Lowers the AST to the IR

    At this point, the AST has been normalized, and can thus be seen
    simply as an SLP (ie, it contains only assignments). As a result,
    this class just walks the AST down to those assignments, which can
    be trivially converted into HLIs.

    By convention, the last function of the program in the "main" (it
    doesn't have to be called "main" though) --> the inputs/outputs of
    the program are the inputs/outputs of the main.

    """
from pycparser import c_parser, c_ast, c_generator
import IR

class AST_to_IR(c_ast.NodeVisitor):


    def convert(self, ast, returns):
        self.returns = returns # Array/Pointers parameters to return
        self.env = dict()  # Memory location of variables
        self.next_mem = 0  # Next memory cell available
        self.instrs = []   # Converted instructions (HLIs)
        self.outputs = []  # Outputs of this program
        self.visit(ast)
        return IR.HLIRProgram(self.instrs, self.inputs, self.outputs, self.next_mem)

    def visit_FuncDef(self, fun):
        old_env = dict(self.env)

        input_count = 0
        for param in fun.decl.type.args:
            self.env[param.name] = self.next_mem
            if param.name in self.returns:
                self.outputs.append(IR.MemOperand(self.next_mem))
            self.next_mem += 1
            input_count += 1
        self.generic_visit(fun.body)

        self.inputs = [ IR.MemOperand(i) for i in range(input_count) ]

        self.env = old_env

    def visit_Return(self, stmt):
        dst = self.next_mem
        self.env["__ret"] = dst
        self.next_mem += 1

        self.outputs.insert(0, IR.MemOperand(dst))

        self.visit_Assignment(c_ast.Assignment("=", c_ast.ID("__ret"), stmt.expr))

    def visit_Decl(self, decl):
        # Allocating memory
        dst = self.next_mem
        self.env[decl.name] = dst
        self.next_mem += 1

        if decl.init:
            self.visit_Assignment(c_ast.Assignment("=", c_ast.ID(decl.name), decl.init))

    def visit_UnaryOp(self, node):
        # Should only be ++p, p++, --p, p--
        assert (node.op == "p--" or node.op == "--" or
                node.op == "p++" or node.op == "++")
        op = "+" if "++" in node.op else "-"
        asgn = c_ast.Assignment(op, node.expr,
                                c_ast.BinaryOp(op, node.expr,
                                               c_ast.Constant('int', '1')))
        self.visit(asgn)

    def visit_Assignment(self, asgn):
        if isinstance(asgn.rvalue, c_ast.BinaryOp):
            self.do_asgn(asgn.lvalue, asgn.rvalue.op,
                         asgn.rvalue.left, asgn.rvalue.right)
        elif isinstance(asgn.rvalue, c_ast.TernaryOp):
            self.do_asgn(asgn.lvalue, "?:",
                         asgn.rvalue.cond, asgn.rvalue.iftrue,
                         asgn.rvalue.iffalse)
        else:
            # Has to be copy, right?
            self.do_asgn(asgn.lvalue, "=", asgn.rvalue)

    def do_asgn(self, dst_c, op_c, src1_c, src2_c = None, src3_c = None):

        dst  = self.convert_operand(dst_c)
        op   = self.convert_operator(op_c)
        src1 = self.convert_operand(src1_c)
        src2 = self.convert_operand(src2_c) if src2_c else None
        src3 = self.convert_operand(src3_c) if src3_c else None

        self.instrs.append(IR.HLI(op, dst, src1, src2, src3))


    def convert_operand(self, operand):
        if isinstance(operand, c_ast.ID):
            return IR.MemOperand(self.env[operand.name])
        if isinstance(operand, c_ast.Constant):
            return IR.ImmOperand(int(operand.value))


    def convert_operator(self, op):
        if op == "=":
            return IR.Opcode.MOV
        if op == "^":
            return IR.Opcode.XOR
        if op == "|":
            return IR.Opcode.OR
        if op == "&":
            return IR.Opcode.AND
        if op == "<<":
            return IR.Opcode.LSL
        if op == ">>":
            return IR.Opcode.LSR
        if op == "+":
            return IR.Opcode.ADD
        if op == "-":
            return IR.Opcode.SUB
        if op == "*":
            return IR.Opcode.MUL
        if op == "/":
            return IR.Opcode.DIV
        if op == "%":
            return IR.Opcode.MOD
        if op == "?:":
            return IR.Opcode.CMOV
        if op == "<":
            return IR.Opcode.LT
        if op == "==":
            return IR.Opcode.EQ
        # TODO: handle ASR, ADDC, SUBC
