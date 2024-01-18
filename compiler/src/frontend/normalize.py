"""Normalization removes "high-level" constructs from the AST to obtain a C SLP

For now, we perform the following normalization passes:

  - Replacement of ~ (binary not) by "^ 0xffffffff"

  - Convertion of hexadecimal integers into decimal ones (eg, 0x0F
    becomes 15)

  - Removal of compound assignments (eg, +=, -=, etc)

  - Inlining

  - Unrolling

  - Array removal

  - Unnesting of expressions

In the future, we should additionally:

     - remove if/then/else

"""

from pycparser import c_parser, c_ast, c_generator
from utils import NodeCopyVisitor, NodeCopyVisitorWithEnv
from . import identifiers
from .alphaconvert import AlphaConverter
import sys
import re

class Normalizer(NodeCopyVisitor):
    def normalize(self, ast):
        # Some constraints on the order of the passes:
        #
        #  - Converting ~ into "^ 0xffffffff" should be done before
        #    converting hexa integers, so that 0xffffffff can then be
        #    converted to decimal.
        #
        #  - Converting hexa integers into decimal ones should be done
        #    fairly easly so that all other passes can use 'int()' on
        #    c_ast.Constant values without causing any errors.
        #
        #  - ControlNormalizer must be called before expression
        #    unnesting, or weird things could happen in For/While/If
        #    when their bodies are not compound statements.
        #
        #  - Inlining must be done after expression unnesting, so that
        #    nested function calls are properly inlined.
        #
        #  - Inlining must be done before unrolling, because the
        #    bounds for the loop could be parameters of the function
        #    (they should be static, but we can only see their actual
        #    value after inlining).
        #
        #  - Removal of compound assignments should be done before
        #    unrolling (or before using any NodeCopyVisitorWithEnv for
        #    that matter) so that there are less cases to handle when
        #    evaluating static expressions: +=, -= etc. are not cases
        #    that we need to deal with.
        #
        #  - Array/Pointer removal should be done after Inlining and
        #    Unrolling. Indices in arrays/pointers could be a loop
        #    iterator (resp. function parameter), whose value we can
        #    only know after unrolling (resp. inlining).
        #
        # Put otherwise, leave the normalization passes in the same
        # order!
        # TODO: a few visitors could be merged to improve performance
        # a bit. Actually, most of them could be merged. I recommand
        # to keep:
        #  - A basic remover (everything until Unnester)
        #  - Inliner
        #  - ForRemover
        #  - ArrayRemover
        # Even then, some could probably be merged, but that would be
        # a good first step.
        ast = NotConverter().visit(ast)
        ast = IntConverter().visit(ast)
        ast = ControlNormalizer().visit(ast)
        ast = CompoundAsgnRemover().visit(ast)
        ast = Unnester().visit(ast)
        ast = Inliner().inline(ast)
        # Inlining can lead to multiple variables having the same
        # name. Randomizing variable names to avoid any issues because
        # of that.
        AlphaConverter().visit(ast)
        ast = ForRemover().remove_for_loops(ast)
        # Unrolling can also lead to multiple variables having the same name.
        AlphaConverter().visit(ast)
        (ast, returns) = ArrayRemover().remove_arrays(ast)
        return (ast, returns)


class ControlNormalizer(NodeCopyVisitor):
    """Makes sure that all control structures have compound statements as
    their bodies.

    """
    def visit_For(self, node):
        node = super().visit_For(node)
        if not isinstance(node.stmt, c_ast.Compound):
            node.stmt = c_ast.Compound([node.stmt])
        return node

    def visit_If(self, node):
        node = super().visit_If(node)
        if not isinstance(node.iftrue, c_ast.Compound):
            node.iftrue = c_ast.Compound([node.iftrue])
        if not isinstance(node.iffalse, c_ast.Compound):
            node.iftrue = c_ast.Compound([node.iffalse])
        return node

    def visit_While(self, node):
        node = super().visit_While(node)
        if not isinstance(node.stmt, c_ast.Compound):
            node.stmt = c_ast.Compound([node.stmt])
        return node

class CompoundAsgnRemover(NodeCopyVisitor):

    """Removes compound assignments such as +=, *=, etc.

    The exact list of supported operators is:

       +=, *=, -=, /=, %=, ^=, |=, &=, <<=, >>=

    """
    def visit_Assignment(self, node):
        node = super().visit_Assignment(node)
        try:
            op = re.match(r"^(..?)=$", node.op).group(1)
            return c_ast.Assignment('=', node.lvalue,
                                    c_ast.BinaryOp(op, node.lvalue, node.rvalue))
        except AttributeError:
            return node

class IntConverter(NodeCopyVisitor):

    def visit_Constant(self, node):
        node = super().visit_Constant(node)
        if node.value.startswith('0x'):
            node.value = str(int(node.value, 16))
        return node

class NotConverter(NodeCopyVisitor):
    def visit_UnaryOp(self, node):
        node = super().visit_UnaryOp(node)
        if node.op == "~":
            return c_ast.BinaryOp("^", node.expr,
                                  c_ast.Constant('unsigned int', '0xffffffff'))
        else:
            return node

class Unnester(NodeCopyVisitor):
    """Unnests expressions

    An expression is said to be nested if if contains
    sub-expressions. For instance:

        x + y + z

    or

        (x << 2) + (3 * y)

    When such an expression is encountered, we introduce a temporary
    variable to hold the result of a sub-expression, and use that
    temporary instead of the original sub-expression. The last example
    about would, for instance, be converted to:

        int tmp1 = x << 2;
        int tmp2 = 3 * y;
        tmp1 + tmp2

    """

    def visit_FileAST(self, ast):
        self.depth = 0 # Used in visit_BinaryOp and visit_UnaryOp, to
                       # determine if the binary/unaryop in question
                       # must be hoisted to its own variable.
        self.before = [] # Additional definitions resulting of the unnesting
        return super().visit_FileAST(ast)


    def visit_Decl(self, node):
        new_type = self.visit(node.type)
        new_bitsize = self.visit(node.bitsize)

        self.depth = 1
        self.before = []

        new_init = self.visit(node.init)

        node = c_ast.Decl(node.name, node.quals, node.align, node.storage,
                          node.funcspec, new_type, new_init, new_bitsize, node.coord)

        if self.before != []:
            node = self.before + [ node ]
            self.before = []
            self.depth  = 0

        return node

    def make_tmp(self, value):
        """Creates a new temporary to hold |value| and returns it.

        self.before is updated here to hold the definition of this new
        temporary.

        """
        tmp_name = identifiers.gen_next_ident(prefix='@subexpr_')
        self.before.append(c_ast.Decl(tmp_name, [], [], [], [],
                                      c_ast.TypeDecl(tmp_name, [], None,
                                                     c_ast.IdentifierType(['unsigned', 'int'])),
                                      value, None))
        return c_ast.ID(tmp_name)


    def commit_if_is_stmt(self, node):
        """Commits self.before right now is |node| is a statement

        If self.depth is 1, then |node| (which should be an expression
        (BinaryOp or UnaryOp)) was actually a statement on its own. We
        thus add the .before right now into a new Compound.

        """
        if self.depth == 1:
            if self.before != []:
                node = self.before + [ node ]
                self.before = []
        return node

    def visit_Compound(self, node):
        # Unnesting expressions will produce temporaries, which will
        # result in some statements being replaced by a list of
        # statement. We thus make sure here that those lists of
        # statement are flattended.
        #
        # It looks like another option would have been to replace
        # those statements by compound statements instead, but it
        # doesn't work because of scoping. For instance, consider:
        #
        #   int y = a + b + c;
        #
        # If we use a compound statement to avoid the list of
        # statements, we'd get:
        #
        #   {
        #      int tmp = a + b;
        #      int y = tmp + c;
        #   }
        #
        # And |y| is thus not visible after its declaration...
        new_block_items = [ self.visit(item) for item in (node.block_items or []) ]
        new_block_items = self.flatten_if_needed(new_block_items)

        return c_ast.Compound(new_block_items, node.coord)


    def visit_Assignment(self, node):
        new_lvalue = self.visit(node.lvalue)

        self.depth = 1
        self.before = []

        new_rvalue = self.visit(node.rvalue)

        node = c_ast.Assignment(node.op, new_lvalue, new_rvalue, node.coord)

        if self.before != []:
            node = self.before + [ node ]
            self.before = []

        return node

    def visit_Return(self, node):
        self.depth = 1
        node = super().visit_Return(node)

        if self.before != []:
            node = self.before + [ node ]
            self.before = []

        return node

    def visit_FuncCall(self, node):
        if self.depth >= 2:
            node = self.make_tmp(node)
        return node

    def visit_TernaryOp(self, node):
        self.depth += 1
        node = super().visit_TernaryOp(node)
        # Regardless of depth, we need to introduce temporaries for
        # all of the expressions in ternary ifs.
        cond = self.make_tmp(node.cond)
        iftrue = self.make_tmp(node.iftrue)
        iffalse = self.make_tmp(node.iffalse)
        node = c_ast.TernaryOp(cond, iftrue, iffalse, node.coord)
        self.commit_if_is_stmt(node)
        self.depth -= 1
        return node

    def visit_BinaryOp(self, node):
        self.depth += 1
        node = super().visit_BinaryOp(node)

        if self.depth > 2:
            # We need to store this expression inside a
            # variable. Since we never re-generate C from there, there
            # is no reason that the variable name should be a valid C
            # identifier. As such, we'll use '@subexpr_XXX', so that
            # there is no risk of having name conflicts between the
            # variables.
            node = self.make_tmp(node)

        self.commit_if_is_stmt(node)

        self.depth -= 1
        return node

    def visit_UnaryOp(self, node):
        self.depth += 1
        node = super().visit_UnaryOp(node)

        if node.op == "&":
            # &arr[..] ===> leaving as is
            return node
        if "++" in node.op or "--" in node.op:
            op = "+" if "++" in node.op else "-"
            incr_decr_expr = c_ast.BinaryOp(op, node.expr, c_ast.Constant('unsigned int', '1'))

            if "p" in node.op:
                # Decrement is postfix. Saving value in temporary,
                # then performing increment, and using temporary in
                # the following.
                old_value = self.make_tmp(node.expr)
                self.before.append(c_ast.Assignment('=', node.expr, incr_decr_expr))
                node = old_value
            else:
                # Decrement is prefix. Performing it before, and using
                # node.expr instead of node in the following
                self.before.append(c_ast.Assignment('=', node.expr, incr_decr_expr))
                node = node.expr
        elif self.depth > 2:
            node = self.make_tmp(node)
        else:
            assert(node.op == "-" and self.depth <= 2)

        self.commit_if_is_stmt(node)

        self.depth -= 1
        return node

    def visit_For(self, node):
        # Making sure to just visit the body of the for
        new_stmt = self.visit(node.stmt)
        return c_ast.For(node.init, node.cond, node.next, new_stmt, node.coord)

    def visit_While(self, node):
        # Making sure to just visit the body of the while
        new_stmt = self.visit(node.stmt)
        return c_ast.While(node.cond, new_stmt, node.coord)

    def visit_ArrayRef(self, node):
        # Not unnesting inside array indices
        return node



class Inliner(NodeCopyVisitor):
    """Inlines function calls

    Function calls are allowed to be in only 4 places:

      - variable declarations. Eg, int x = f(args)

      - right hand-side of assignments. Eg, x = f(args)

      - returns. Eg, return f(args)

      - a statement. Eg, f(args);

    Function calls cannot be anywhere else. In particular, they are
    not allowed inside expressions. For instance, "f(_) + g(_)" is not
    handled by this compiler.

    Note that early returns are not allowed in functions. As such, we
    don't have to deal with constructions such as:

        if (...) {
            return 42;
        }
        ....
        return 5;

    Instead, a return should always be the last instruction of a function.

    """


    class InliningHelper(NodeCopyVisitor):
        """A helper class that performs the actual inlining"""

        def inline(self, return_var, funcall, funs):
            self.funs = funs
            self.return_var = return_var

            fun = funs[funcall.name.name]

            # Generating variables to hold params
            params_init = [ c_ast.Decl(param.name, param.quals, param.align, param.storage,
                                       param.funcspec, param.type, arg, None)
                            for (param, arg) in zip(fun.decl.type.args, funcall.args) ]

            # Inlining now mostly means updating the "return" in the
            # function's body. Still, We start by cloning the body, in
            # order to avoid having shared pointers between multiple
            # inlinings of the same function.
            body = NodeCopyVisitor().visit(fun.body)
            body = self.visit(body)

            return c_ast.Compound( params_init + body.block_items )

        def visit_Return(self, node):
            return c_ast.Assignment('=', self.return_var, node.expr)



    def inline(self, ast):
        # Collecting all functions
        self.funs = dict()
        new_exts = []
        for ext in ast.ext:
            if isinstance(ext, c_ast.FuncDef):
                new_ext = c_ast.FuncDef(ext.decl, ext.param_decls,
                                        self.visit(ext.body), ext.coord)
                name = new_ext.decl.name
                self.funs[name] = new_ext
                last_fun = new_ext
            else:
                new_exts.append(ext)

        new_exts.append(last_fun)

        return c_ast.FileAST(new_exts, ast.coord)

    def visit_Decl(self, node):
        if (node.init is not None) and isinstance(node.init, c_ast.FuncCall):
            # The declaration should declare a scalar. For instance:
            #
            #   x = f(...).
            #
            # We don't allow to return arrays from functions (C
            # without malloc doesn't really allow it anyways).
            assert(isinstance(node.type, c_ast.TypeDecl) and
                   isinstance(node.type.type, c_ast.IdentifierType))
            decl_stmt = c_ast.Decl(node.name, node.quals, node.align, node.storage,
                                   node.funcspec, node.type, None, node.bitsize, node.coord)
            fun_stmt = self.InliningHelper().inline(c_ast.ID(node.name), node.init, self.funs)
            return [decl_stmt, fun_stmt]
        else:
            return node


    def visit_Assignment(self, node):
        if isinstance(node.rvalue, c_ast.FuncCall):
            assert(node.op == '=')
            return self.InliningHelper().inline(node.lvalue, node.rvalue, self.funs)
        else:
            return node

    def visit_Return(self, node):
        """
        return f(args);

        becomes:

        tmp = f(args);
        return tmp;

        which results in being the same thing as a function call
        inside an assignment.
        """
        if isinstance(node.expr, c_ast.FuncCall):
            ret_ident = identifiers.gen_next_ident(prefix="ret_")
            ret_type = self.funs[node.expr.name.name].decl.type.type
            ret_type.declname = ret_ident

            asgn = c_ast.Decl(ret_ident, [], [], [], [], ret_type, node.expr, None)

            return c_ast.Compound(self.visit_Decl(asgn) +
                                  [c_ast.Return(c_ast.ID(ret_ident))])
        else:
            return node


    def visit_Compound(self, node):
        new_block_items = [ self.visit(item) for item in (node.block_items or []) ]
        new_block_items = self.flatten_if_needed(new_block_items)

        return c_ast.Compound(new_block_items, node.coord)

    def visit_FuncCall(self, node):
        # A void function being called
        return self.InliningHelper().inline(None, node, self.funs)



class ForRemover(NodeCopyVisitorWithEnv):
    """Unroll "for" loop

    The only loops that we support for now are of the form:

    for (var = const; x op const; incr)

    where:

      - "var" is "int varname" or "varname"

      - "op" is one of  "<", "<=", ">", ">=", "==", "!="

      - "incr" is
         * one of "var++", "var--", "++var", "--var"
         * or, "var = expr", where expr is a C expression that has the
           same semantics in C and Python.

    """

    def remove_for_loops(self, ast):
        return self.visit(ast)

    def visit_For(self, node):
        entry_data = self.enter_scope()

        # Extracting initialisation
        if isinstance(node.init, c_ast.Assignment):
            init_stmt   = self.visit(node.init)
            it_init_val = self.eval_expr(init_stmt.rvalue)
            it_name     = init_stmt.lvalue.name
        elif isinstance(node.init, c_ast.DeclList):
            assert len(node.init.decls) == 1
            init_stmt   = self.visit(node.init.decls[0])
            it_init_val = self.eval_expr(init_stmt.init)
            it_name     = init_stmt.name
            self.defs.add(it_name)
        else:
            sys.exit("Invalid 'for' loop initializer.")

        self.env[it_name] = it_init_val

        # Extracting increment
        next_expr = self.get_next_expr(node.next)

        # Extracting end condition
        assert isinstance(node.cond, c_ast.BinaryOp) and \
            (node.cond.op == "<"  or node.cond.op == "<=" or
             node.cond.op == ">"  or node.cond.op == ">=" or
             node.cond.op == "==" or node.cond.op == "!=")
        stop_cond = self.eval_expr(node.cond.right)
        is_not_done = lambda x : eval(str(x) + node.cond.op + str(stop_cond))

        # Extracting body
        unrolled = [ self.visit(init_stmt) ]
        while is_not_done(self.env[it_name]):
            unrolled.append(self.visit(node.stmt))
            unrolled.append(self.visit(next_expr)) # A side-effect of this is to update
                                                   # self.env[it_name].

        self.exit_scope(entry_data)

        return c_ast.Compound(unrolled)


    def get_next_expr(self, node):
        """Generates a Python lambda that increment the loop variable"""
        if isinstance(node, c_ast.UnaryOp):
            assert (node.op == "p--" or node.op == "--" or
                    node.op == "p++" or node.op == "++")
            return c_ast.Assignment("=",
                                    node.expr,
                                    c_ast.BinaryOp("+" if "++" in node.op else "-",
                                                   node.expr,
                                                   c_ast.Constant('int','1')))
        if isinstance(node, c_ast.Assignment):
            if re.match(r"^([-+*/^$|]|<<|>>)=$", node.op):
                # Replace compound assignment with simple assignment
                op = re.match(r"^([-+*/^$|]|<<|>>)=$", node.op).group(1)
                return c_ast.Assignment("=", node.lvalue,
                                        c_ast.BinaryOp(op, node.lvalue, node.rvalue))

        return node



class ArrayRemover(NodeCopyVisitorWithEnv):
    """Remove arrays and pointers

    Each pointer may only alias to a single other pointer (or array)
    during its lifetime, and this aliasing must be done at the
    pointer's initialization. In order word, a pointer must be
    initialized when its declared, and should never be re-assigned.

    Note that in this class, we assume that variable names are uniques
    (ie, we assume that alpha-converting was done prior to calling
    this function).

    """

    class Alias:
        def __init__(self, name, offset):
            self.name   = name
            self.offset = offset

        def __str__(self):
            return f"{self.name}+{self.offset}"


    class ArraySizeCalculator(NodeCopyVisitorWithEnv):
        # This class does not return anything and would thus have been
        # better suited as a c_ast.NodeVisitor. However, it requires
        # the environment to compute .get_val(node.subcript) in
        # visit_ArrayRef, and the environment is only available in
        # NodeCopyVisitorWithEnv. (this may indicate bad design: maybe
        # I should have done NodeVisitorWithEnv and then extend it
        # into NodeVisitorWithEnvCopy instead of doing it the other
        # way around...)
        def get_array_sizes(self, ast):
            self.pointers = set()
            self.aliases = dict()
            self.array_sizes = dict()
            self.visit(ast)
            for ptr, aliases_to in self.aliases.items():
                (real_aliases_to, offset) = self.resolve_alias(aliases_to.name, aliases_to.offset)
                size = max(self.array_sizes.get(ptr, 0)+offset,
                           self.array_sizes.get(real_aliases_to, 0))
                self.array_sizes[real_aliases_to] = size
            return self.array_sizes

        def visit_ArrayRef(self, node):
            name = node.name.name
            idx  = self.get_val(node.subscript)
            self.array_sizes[name] = max(self.array_sizes.get(name, 0), idx+1)
            return node

        def visit_ptr_assignment(self, ptr_name, init):
            if isinstance(init, c_ast.ID):
                # p = q
                self.aliases[ptr_name] = \
                    self.make_alias(self.resolve_alias(init.name))

            elif isinstance(init, c_ast.UnaryOp) and \
                 init.op == "&":
                # Pointer aliasing to the middle of an array:
                # p = &q[42]
                self.aliases[ptr_name] = \
                    self.make_alias(self.resolve_alias(init.expr.name.name,
                                                       self.get_val(init.expr.subscript)))

            elif isinstance(init, c_ast.BinaryOp):
                # Pointer aliasing to after a pointer:
                # p = q + 42
                left  = init.left
                right = init.right
                if (val := self.get_val(left)) != None:
                    assert isinstance(right, c_ast.ID)
                    (ident, offset) = (right.name, val)
                elif (val := self.get_val(right)) != None:
                    assert isinstance(left, c_ast.ID)
                    (ident, offset) = (left.name, val)
                else:
                    sys.exit("Invalid pointer initializer")
                self.aliases[ptr_name] = \
                    self.make_alias(self.resolve_alias(ident, offset))


        def visit_Assignment(self, node):
            if isinstance(node.lvalue, c_ast.ID) and \
               node.lvalue.name in self.pointers:
                self.visit_ptr_assignment(node.lvalue.name, node.rvalue)
            else:
                return super().visit_Assignment(node)

        def visit_Decl(self, node):
            # Removing declaration of arrays and putting declarations of
            # scalars instead.
            if isinstance(node.type, c_ast.ArrayDecl) or \
               isinstance(node.type, c_ast.PtrDecl):
                self.pointers.add(node.name)
                self.visit_ptr_assignment(node.name, node.init)
            else:
                # Calling super() because this Decl could be declaring
                # a constant that need to go in the environment
                super().visit_Decl(node)
            self.visit(node.init)

        def make_alias(self, alias):
            (target, offset) = alias
            return ArrayRemover.Alias(target, offset)

        def resolve_alias(self, name, offset=0):
            # Finds out what "name" aliases to (if it aliases to
            # anything), and returns it. This is to deal with cases where
            # we would do:
            #
            #     int* a = x;
            #     int* b = a;
            #     int* c = b;
            #
            # In this example, we want to say that "c" aliases to "x"; not
            # to "b".
            #
            # Also, it takes offsets into account. For instance, if you do:
            #
            #    int* a = x[2];
            #    int* b = a[1];
            #    int* c = b[3];
            #
            # Then "c" is an alias to &x[6].
            if name in self.aliases and \
               self.aliases[name].name != name : # Checking just in case that
                                                 # there are no circular
                                                 # aliases, in order to allow "a = a"
                return self.resolve_alias(self.aliases[name].name,
                                          offset+self.aliases[name].offset)
            else:
                return (name, offset)



    def remove_arrays(self, ast):
        self.array_sizes = self.ArraySizeCalculator().get_array_sizes(ast)
        self.pointers = set() # List of pointers/arrays
        self.aliases = dict() # List of aliases
        self.aliases_offset = dict() # Offset for aliases in the middle of arrays
        self.returns = set() # List of values to return
        self.is_param = False # Used to track is an array should be returned or not
        ast = self.visit(ast)
        return (ast, self.returns)

    # visit_Decl will generate lists of Decl where a single Decl is
    # expected. This Will result in either Compound or ParamList to
    # have lists where Decl are expected. We thus override
    # visit_ParamList and visit_Compound to flatten those lists.
    def visit_ParamList(self, node):
        self.is_param = True
        new_params = [ self.visit(param) for param in (node.params or []) ]
        new_params = self.flatten_if_needed(new_params)
        self.is_param = False

        return c_ast.ParamList(new_params, node.coord)


    def visit_Compound(self, node):
        new_block_items = [ self.visit(item) for item in (node.block_items or []) ]
        new_block_items = self.flatten_if_needed(new_block_items)

        return c_ast.Compound(new_block_items, node.coord)

    def visit_ptr_assignment(self, ptr_name, init):
        # Computes the alias generated by the initialization of a
        # pointer or array.
        if isinstance(init, c_ast.ID):
            # p = q
            self.aliases[ptr_name] = \
                self.make_alias(self.resolve_alias(init.name))
            return True

        elif isinstance(init, c_ast.UnaryOp) and \
             init.op == "&":
            # Pointer aliasing to the middle of an array:
            # p = &q[42]
            self.aliases[ptr_name] = \
                self.make_alias(self.resolve_alias(init.expr.name.name,
                                                   self.get_val(init.expr.subscript)))
            return True

        elif isinstance(init, c_ast.BinaryOp):
            # Pointer aliasing to after a pointer:
            # p = q + 42
            left  = init.left
            right = init.right
            if (val := self.get_val(left)) != None:
                assert isinstance(right, c_ast.ID)
                (ident, offset) = (right.name, val)
            elif (val := self.get_val(right)) != None:
                assert isinstance(left, c_ast.ID)
                (ident, offset) = (left.name, val)
            else:
                sys.exit("Invalid pointer initializer")
            self.aliases[ptr_name] = \
                self.make_alias(self.resolve_alias(ident, offset))
            return True

        else:
            # Not an initializer that this function can handle
            return False


    def visit_Assignment(self, node):
        if isinstance(node.lvalue, c_ast.ID) and \
           node.lvalue.name in self.pointers:
            self.visit_ptr_assignment(node.lvalue.name, node.rvalue)
            return c_ast.EmptyStatement()
        else:
            return super().visit_Assignment(node)

    def visit_Decl(self, node):
        # Removing declaration of arrays and putting declarations of
        # scalars instead.
        if isinstance(node.type, c_ast.ArrayDecl) or \
           isinstance(node.type, c_ast.PtrDecl):
            self.pointers.add(node.name)
            if self.visit_ptr_assignment(node.name, node.init):
                # p=q, p=&q[42], p=q+42 are handled by visit_ptr_assignment
                return c_ast.EmptyStatement()
            elif node.init is None and isinstance(node.type, c_ast.PtrDecl) and \
                 not self.is_param:
                # uninitialized pointer declaration
                return c_ast.EmptyStatement()
            else:
                # The only case left is p = { initializer }
                if isinstance(node.type, c_ast.ArrayDecl):
                    size = int(node.type.dim.value)
                elif node.name in self.array_sizes:
                    size = self.array_sizes[node.name]
                else:
                    sys.exit("Unable to compute size of input pointer: " + node.name)
                decls = []
                is_to_return = self.is_param and ('const' not in node.quals)
                inits = self.get_array_init(node.init, size)
                for i in range(size):
                    name = f'{node.name}[{i}]'
                    decls.append(c_ast.Decl(name, [], [], [], [],
                                            c_ast.TypeDecl(name, [], None, node.type.type.type),
                                            inits[i], None))
                    if is_to_return:
                        self.returns.add(name)
                return decls
        return super().visit_Decl(node)


    def get_array_init(self, init, size):
        # The only initializers we support are of the type:
        #
        #    int arr[3] = { ... };
        #
        # Where the "..." can be either 0 or a non-empty list of
        # integers or identifiers
        #
        # If no initializer is present initially, we leave the
        # elements of the array uninitialized.
        if isinstance(init, c_ast.InitList):
            return [ init.exprs[i] if i < len(init.exprs)
                     else c_ast.Constant('unsigned int', '0')
                     for i in range(size) ]
        return [ None ] * size

    def visit_ArrayRef(self, node):
        # Removing array accesses
        alias = self.aliases.get(node.name.name, ArrayRemover.Alias(node.name.name, 0))
        value = self.get_val(node.subscript)

        return c_ast.ID(f'{alias.name}[{alias.offset+value}]')


    def make_alias(self, alias):
        (target, offset) = alias
        return ArrayRemover.Alias(target, offset)

    def resolve_alias(self, name, offset=0):
        # Finds out what "name" aliases to (if it aliases to
        # anything), and returns it. This is to deal with cases where
        # we would do:
        #
        #     int* a = x;
        #     int* b = a;
        #     int* c = b;
        #
        # In this example, we want to say that "c" aliases to "x"; not
        # to "b".
        #
        # Also, it takes offsets into account. For instance, if you do:
        #
        #    int* a = x[2];
        #    int* b = a[1];
        #    int* c = b[3];
        #
        # Then "c" is an alias to &x[6].
        if name in self.aliases and \
           self.aliases[name].name != name : # Checking just in case that
                                             # there are no circular
                                             # aliases, in order to allow "a = a"
            return self.resolve_alias(self.aliases[name].name,
                                      offset+self.aliases[name].offset)
        else:
            return (name, offset)
