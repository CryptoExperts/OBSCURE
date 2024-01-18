import IR
from pycparser import c_parser, c_ast, c_generator
import re

def debug_print_AST(trigger, title, ast):
    """Prints |title| and |ast| if |trigger| is true"""
    if trigger:
        print(title)
        ast.show(offset=2)
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n")


def debug_print_IR(trigger, title, ir):
    """Prints |title| and |ir| if |trigger| is true"""
    if trigger:
        print(title)
        print(ir)
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n")


class EvalExpr:
    """Evaluates an expression

    WARNING: CURRENTLY UNUSED

    returns None if the expression cannot be evaluated (either because
    it's not static (ie, some variables are missing), or because we
    don't know how to evaluate this from Python)

    """

    _method_cache = None
    def visit(self, node):
        if node is None:
            return None

        if self._method_cache is None:
            self._method_cache = {}

        visitor = self._method_cache.get(node.__class__.__name__, None)
        if visitor is None:
            method = 'visit_' + node.__class__.__name__
            visitor = getattr(self, method) # Will raise an exception if
                                            # method is not implemented.
            self._method_cache[node.__class__.__name__] = visitor

        return visitor(node)

    def eval_expr(self, expr, env):
        self.env = env
        try:
            return self.visit(expr)
        except Exception:
            return None

    def get_val(self, node):
        """Returns the integer value of |node|, which should be a constant or an identifier"""
        if isinstance(node, c_ast.Constant):
            return int(node.value)
        if isinstance(node, c_ast.ID):
            return self.env[node.name]
        return None

    def visit_ID(self, node):
        return self.env[node.name]

    def visit_Constant(self, node):
        return int(node.value)

    def visit_UnaryOp(self, node):
        if isinstance(node.expr, c_ast.ID) and \
           node.expr.name in self.env:
            if node.op == "-":
                return -self.get_val(node.expr)
            elif node.op == "p++":
                env[node.expr.name] = (env[node.expr.name] + 1) % (2 ** 32)
                return (env[node.expr.name] - 1) % (2 ** 32)
            elif node.op == "++":
                env[node.expr.name] = (env[node.expr.name] + 1) % (2 ** 32)
                return env[node.expr.name]
            elif node.op == "p--":
                env[node.expr.name] = (env[node.expr.name] - 1) % (2 ** 32)
                return (env[node.expr.name] + 1) % (2 ** 32)
            elif node.op == "--":
                env[node.expr.name] = (env[node.expr.name] - 1) % (2 ** 32)
                return env[node.expr.name]

        if node.op == "-":
            return -self.visit(node.expr)

        # Not really reachable right?
        return None

    def visit_BinaryOp(self, node):
        # It's possible that node.left is not static (ie, cannot be
        # computed now, at compile time), but node.right still
        # contains a ++ on a static variable. To account for this
        # possibility, we put self.visit(node.left) inside a
        # try/except.
        try:
            lval = self.visit(node.left)
        except Exception:
            pass
        rval = self.visit(node.right)

        if node.op == "+":
            return (lval + rval) % (2 ** 32)
        elif node.op == "-":
            return (lval - rval) % (2 ** 32)
        elif node.op == "*":
            return (lval * rval) % (2 ** 32)
        elif node.op == "/":
            return lval // rval
        elif node.op == "%":
            return lval % rval
        elif node.op == "&":
            return lval & rval
        elif node.op == "|":
            return lval | rval
        elif node.op == "^":
            return lval ^ rval
        elif node.op == "<<":
            return (lval << rval) % (2 ** 32)
        elif node.op == ">>":
            return lval >> rval
        else:
            print("Not implemented operator: ", node.op)
            return None



class NodeCopyVisitor:
    """A visitor that builds a new AST instead of modifying the old one in place

    Warning: lists fields that are not visited are copied by
    reference, not by value. For instance, the field "quals" of the
    class TypeDecl is not visited (because it does not contain c_ast
    objects), and is thus copied by reference.

    """

    _method_cache = None
    def visit(self, node):
        if node is None:
            return None

        if self._method_cache is None:
            self._method_cache = {}

        visitor = self._method_cache.get(node.__class__.__name__, None)
        if visitor is None:
            method = 'visit_' + node.__class__.__name__
            visitor = getattr(self, method) # Will raise an exception if
                                            # method is not implemented.
            self._method_cache[node.__class__.__name__] = visitor

        return visitor(node)

    def flatten_if_needed(self, l):
        """Transforms a list of list/non-list into a list on non-list

        For instance,

            flatten_if_needed([1, [2, 3], 4, [5]])

        will produce:

            [1, 2, 3, 4, 5]

        It only handles one level of nested lists. Put otherwise,

            flatten_if_needed([1, [2, [3]]])

        produces:

            [1, 2, [3]]

        rather than:

            [1, 2, 3]

        This function is not used in this class, but is used by
        several classes that extend this one, so it seemed appropriate
        to put it here.
        """
        flattened = []
        for item in l:
            if isinstance(item, list):
                flattened.extend(item)
            else:
                flattened.append(item)
        return flattened


    def visit_ArrayDecl(self, node):
        new_type = self.visit(node.type)
        new_dim  = self.visit(node.dim)

        return c_ast.ArrayDecl(new_type, new_dim, node.dim_quals, node.coord)

    def visit_ArrayRef(self, node):
        new_name      = self.visit(node.name)
        new_subscript = self.visit(node.subscript)

        return c_ast.ArrayRef(new_name, new_subscript, node.coord)

    def visit_Assignment(self, node):
        new_lvalue = self.visit(node.lvalue)
        new_rvalue = self.visit(node.rvalue)

        return c_ast.Assignment(node.op, new_lvalue, new_rvalue, node.coord)

    def visit_Alignas(self, node):
        new_alignment = self.visit(node.alignment)

        return c_ast.Alignas(new_alignment, node.coord)

    def visit_BinaryOp(self, node):
        new_left  = self.visit(node.left)
        new_right = self.visit(node.right)

        return c_ast.BinaryOp(node.op, new_left, new_right, node.coord)

    def visit_Break(self, node):
        return c_ast.Break(node.coord)

    def visit_Case(self, node):
        new_expr  = self.visit(node.expr)
        new_stmts = [ self.visit(child) for child in (node.stmts or []) ]

        return c_ast.Case(new_expr, new_stmts, node.coord)

    def visit_Cast(self, node):
        new_to_type = self.visit(node.to_type)
        new_expr    = self.visit(node.expr)

        return c_ast.Cast(new_to_type, new_expr, node.coord)

    def visit_Compound(self, node):
        new_block_items = [ self.visit(item) for item in (node.block_items or []) ]

        return c_ast.Compound(new_block_items, node.coord)

    def visit_CompoundLiteral(self, node):
        new_type = self.visit(node.type)
        new_init = self.visit(node.init)

        return c_ast.CompoudLiteral(new_type, new_init, node.coord)

    def visit_Constant(self, node):
        return c_ast.Constant(node.type, node.value, node.coord)

    def visit_Continue(self, node):
        return c_ast.Continue(node.coord)

    def visit_Decl(self, node):
        new_type = self.visit(node.type)
        new_init = self.visit(node.init)
        new_bitsize = self.visit(node.bitsize)

        return c_ast.Decl(node.name, node.quals, node.align, node.storage,
                          node.funcspec, new_type, new_init, new_bitsize, node.coord)

    def visit_DeclList(self, node):
        new_decls = [ self.visit(decl) for decl in (node.decls or []) ]
        return c_ast.DeclList(new_decls, node.coord)

    def visit_Default(self, node):
        new_stmts = [ self.visit(stmt) for stmt in (node.stmts or []) ]
        return c_ast.Default(new_stmts, node.coord)

    def visit_DoWhile(self, node):
        new_cond = self.visit(node.cond)
        new_stmt = self.visit(node.stmt)

        return c_ast.DoWhile(new_cond, new_stmt, node.coord)

    def visit_EllipsisParam(self, node):
        return c_ast.EllipsisParam()

    def visit_EmptyStatement(self, node):
        return c_ast.EmptyStatement()

    def visit_Enum(self, node):
        new_values = [ self.visit(value) for value in (node.values or []) ]

        return c_ast.Enum(node.name, new_values, node.coord)

    def visit_Enumerator(self, node):
        new_value = self.visit(node.value)

        return c_ast.Enumerator(node.name, new_value, node.coord)

    def visit_EnumeratorList(self, node):
        new_enumerators = [ self.visit(enumerator) for enumerator in (node.enumerators or []) ]

        return c_ast.EnumeratorList(new_enumerators, node.coord)

    def visit_ExprList(self, node):
        new_exprs = [ self.visit(expr) for expr in (node.exprs or []) ]

        return c_ast.ExprList(new_exprs, node.coord)

    def visit_FileAST(self, node):
        new_ext = [ self.visit(child) for child in (node.ext or []) ]

        return c_ast.FileAST(new_ext, node.coord)

    def visit_For(self, node):
        new_init = self.visit(node.init)
        new_cond = self.visit(node.cond)
        new_next = self.visit(node.next)
        new_stmt = self.visit(node.stmt)

        return c_ast.For(new_init, new_cond, new_next, new_stmt, node.coord)

    def visit_FuncCall(self, node):
        new_name = self.visit(node.name)
        new_args = self.visit(node.args)

        return c_ast.FuncCall(new_name, new_args, node.coord)

    def visit_FuncDecl(self, node):
        new_args = self.visit(node.args)
        new_type = self.visit(node.type)

        return c_ast.FuncDecl(new_args, new_type, node.coord)

    def visit_FuncDef(self, node):
        new_decl = self.visit(node.decl)
        new_body = self.visit(node.body)
        new_param_decls = [ self.visit(param_decl) for param_decl in (node.param_decls or []) ]

        return c_ast.FuncDef(new_decl, new_param_decls, new_body, node.coord)

    def visit_Goto(self, node):
        return c_ast.Goto(node.name, node.coord)

    def visit_ID(self, node):
        return c_ast.ID(node.name, node.coord)

    def visit_IdentifierType(self, node):
        return c_ast.IdentifierType(node.names, node.coord)

    def visit_If(self, node):
        new_cond    = self.visit(node.cond)
        new_iftrue  = self.visit(node.iftrue)
        new_iffalse = self.visit(node.iffalse)

        return c_ast.If(new_cond, new_iftrue, new_iffalse, node.coord)

    def visit_InitList(self, node):
        new_exprs = [ self.visit(expr) for expr in (node.exprs or []) ]

        return c_ast.InitList(new_exprs, node.coord)

    def visit_Label(self, node):
        new_stmt = self.visit(node.stmt)

        return c_ast.Label(node.name, new_stmt, node.coord)

    def visit_NamedInitializer(self, node):
        new_expr = self.visit(node.expr)
        new_name = [ self.visit(child) for child in (node.name or []) ]

        return c_ast.NamedInitializer(new_name, new_expr, node.coord)

    def visit_ParamList(self, node):
        new_params = [ self.visit(param) for param in (node.params or []) ]

        return c_ast.ParamList(new_params, node.coord)

    def visit_PtrDecl(self, node):
        new_type = self.visit(node.type)

        return c_ast.PtrDecl(node.quals, new_type, node.coord)

    def visit_Return(self, node):
        new_expr = self.visit(node.expr)

        return c_ast.Return(new_expr, node.coord)

    def visit_StaticAssert(self, node):
        new_cond = self.visit(node.cond)
        new_message = self.visit(node.message)

        return c_ast.StaticAssert(new_cond, new_message, node.coord)

    def visit_Struct(self, node):
        new_decls = [ self.visit(decl) for decl in (node.decls or []) ]

        return c_ast.Struct(node.name, new_decls, node.coord)

    def visit_StructRef(self, node):
        new_name = self.visit(node.name)
        new_field = self.visit(node.field)

        return c_ast.StructRef(new_name, node.type, new_field, node.coord)

    def visit_Switch(self, node):
        new_cond = self.visit(node.cond)
        new_stmt = self.visit(node.stmt)

        return c_ast.Switch(new_cond, new_stmt, node.coord)

    def visit_TernaryOp(self, node):
        new_cond    = self.visit(node.cond)
        new_iftrue  = self.visit(node.iftrue)
        new_iffalse = self.visit(node.iffalse)

        return c_ast.TernaryOp(new_cond, new_iftrue, new_iffalse, node.coord)

    def visit_TypeDecl(self, node):
        new_type = self.visit(node.type)

        return c_ast.TypeDecl(node.declname, node.quals, node.align, new_type, node.coord)

    def visit_TypeDef(self, node):
        new_type = self.visit(node.type)

        return c_ast.TypeDef(node.name, node.quals, node.storage, new_type, node.coord)

    def visit_Typename(self, node):
        new_type = self.visit(node.type)

        return c_ast.Typename(node.name, node.quals, node.align, new_type, node.coord)

    def visit_UnaryOp(self, node):
        new_expr = self.visit(node.expr)

        return c_ast.UnaryOp(node.op, new_expr, node.coord)

    def visit_Union(self, node):
        new_decls = [ self.visit(decl) for decl in (node.decls or []) ]

        return c_ast.Union(node.name, new_decls, node.coord)

    def visit_While(self, node):
        new_cond = self.visit(node.cond)
        new_stmt = self.visit(node.stmt)

        return c_ast.While(new_cond, new_stmt, node.coord)

    def visit_Pragma(self, node):
        return c_ast.Pragma(node.string, node.coord)




class NodeCopyVisitorWithEnv(NodeCopyVisitor):
    """A NodeCopyVisitor that keeps an environment of constant variables

    This visitor also performs simplification of constant expressions,
    and replaces constant variables with their values. For instance,
    visiting:

       int x = 42;
       int y = x * 2;
       int z = y - 2*x;
       return x + y + z;

    Would result in:

       int x = 42;
       int y = 84;
       int z = 0;
       return 128

    The reason for that is that we need to evaluate constant
    expressions because they could be used in array indices or as loop
    stopping conditions or increment. And since we are evaluating
    those expressions, we might as well simplify them. If, at some
    point, we want to stop performing those simplifications, then we
    should re-introduce the use of EvalExpr to evaluate expressions,
    and this visitor will not simplify anything, but call
    EvalExpr.eval_expr when it needs the result of an expression.

    Doing this EvalExpr.eval_expr version has one drawback though: it
    requires a bit of care on how to handle ++/--: postfix ++/--
    should be done after returning the value it increments, and thus,
    it needs to be done _after_ calling EvalExpr.eval_expr. But
    EvalExpr.eval_expr needs to be called _after_ a node has been
    visited (because of later visitor that might inherit from this
    class). As a result, we are in an awkward situation, where
    updating the environment after encountering ++ should be done in
    EvalExpr, although it really _feels_ like it should be done in
    this class (NodeCopyVisitorWithEnv)...


    Note that the only place variables can be declared are:
      - Function definitions
      - Compound statements
      - For loops initializer
    As such, when visiting those construct, we start a new environment,
    which is dropped at the end of the said construct.

    """

    def visit_FileAST(self, ast):
        self.env = dict() # Environment of all static variables and their values
        self.defs = set() # List of variables that were declared in the current scope
        return super().visit_FileAST(ast)

    def enter_scope(self):
        old_defs = self.defs
        self.defs = set()
        return (dict(self.env), old_defs)

    def exit_scope(self, entry_data):
        (old_env, old_defs) = entry_data
        old_keys = set(old_env.keys())
        new_keys = set(self.env.keys())

        # Removing variables that were declared in this scope
        for var in self.defs:
            if var not in new_keys:
                # Var was declared, but its value is not statically known
                continue
            if var in old_keys:
                self.env[var] = old_env[var]
            else:
                del self.env[var]

        self.defs = old_defs

    def visit_FuncDef(self, fun):
        entry_data = self.enter_scope()
        res = super().visit_FuncDef(fun)
        self.exit_scope(entry_data)
        return res

    def visit_Compound(self, compound):
        entry_data = self.enter_scope()
        res = super().visit_Compound(compound)
        self.exit_scope(entry_data)
        return res

    def visit_For(self, forloop):
        entry_data = self.enter_scope()
        res = super().visit_For(foloop)
        self.exit_scope(entry_data)
        return res

    def visit_Assignment(self, node):
        new_lvalue = self.visit(node.lvalue)
        new_rvalue = self.visit(node.rvalue)

        if isinstance(new_lvalue, c_ast.ID):
            val = self.get_val(new_rvalue)
            if val is not None:
                self.env[new_lvalue.name] = val
                new_rvalue = c_ast.Constant('unsigned int', str(val))
            else:
                # The rhs is not computable, which means that the
                # lvalue is not statically computable. If it was
                # computable before, then we need to make sure to
                # remove its old value from the environment.
                self.env.pop(new_lvalue.name, None)

        return c_ast.Assignment(node.op, new_lvalue, new_rvalue)

    def visit_Decl(self, node):
        new_type = self.visit(node.type)
        new_init = self.visit(node.init)
        new_bitsize = self.visit(node.bitsize)

        if (node.type is not None) and \
           isinstance(node.type, c_ast.TypeDecl) and \
           (node.type.type is not None) and \
           isinstance(node.type.type, c_ast.IdentifierType) and \
           (node.type.type.names == ['unsigned', 'int']) and \
           (new_init is not None):
            # This node is declaring an integer
            val = self.get_val(new_init)
            if val is not None:
                self.env[node.name] = val
                new_init = c_ast.Constant('unsigned int', str(val))
            else:
                # The rhs is not computable, which means that the
                # lvalue is not statically computable. If it was
                # computable before, then we need to make sure to
                # remove its old value from the environment.
                self.env.pop(node.name, None)

            self.defs.add(node.name)

        return c_ast.Decl(node.name, node.quals, node.align, node.storage,
                          node.funcspec, new_type, new_init, new_bitsize, node.coord)


    def visit_UnaryOp(self, node):
        if node.op == "-":
            expr = self.visit(node.expr)
            try:
                return c_ast.Constant('unsigned int', str(-self.get_val(expr)))
            except Exception:
                return c_ast.UnaryOp("-", expr)

        expr = self.visit(node.expr)

        if expr.name in self.env:
            if node.op == "p++":
                self.env[expr.name] = (self.env[expr.name] + 1) % (2 ** 32)
                return c_ast.Constant('unsigned int', str((env[expr.name] - 1)%(2**32)))
            elif node.op == "++":
                self.env[expr.name] = (self.env[expr.name] + 1) % (2 ** 32)
                return c_ast.Constant('unsigned int', str(env[expr.name]))
            elif node.op == "p--":
                self.env[expr.name] = (self.env[expr.name] - 1) % (2 ** 32)
                return c_ast.Constant('unsigned int', str((env[expr.name] + 1)%(2**32)))
            elif node.op == "--":
                self.env[expr.name] = (self.env[expr.name] - 1) % (2 ** 32)
                return c_ast.Constant('unsigned int', str(env[expr.name]))
        else:
            return c_ast.UnaryOp(node.op, expr)

        assert False

    def visit_BinaryOp(self, node):
        # It's possible that one of node.left or node.right is not
        # static (ie, cannot be computed now, at compile time), but
        # the other one still contains a ++ on a static variable. To
        # account for this possibility, we put self.visit(node.left)
        # and self.visit(node.right) inside a try/except.
        left  = node.left
        right = node.right
        try:
            left = self.visit(left)
        except Exception:
            pass
        try:
            right = self.visit(right)
        except Exception:
            pass

        try:
            lval = self.get_val(left)
            rval = self.get_val(right)
            if node.op == "+":
                res = (lval + rval) % (2 ** 32)
            elif node.op == "-":
                res = (lval - rval) % (2 ** 32)
            elif node.op == "*":
                res = (lval * rval) % (2 ** 32)
            elif node.op == "/":
                res = lval // rval
            elif node.op == "%":
                res = lval % rval
            elif node.op == "&":
                res = lval & rval
            elif node.op == "|":
                res = lval | rval
            elif node.op == "^":
                res = lval ^ rval
            elif node.op == "<<":
                res = (lval << rval) % (2 ** 32)
            elif node.op == ">>":
                res = lval >> rval
            elif node.op == "<":
                res = lval < rval
                res = int(res)
            elif node.op == "==":
                # Tricky because None == None returns True
                res = (lval ^ rval) == 0
                res = int(res)
            else:
                print("Not implemented operator: ", node.op)
                return None
            return c_ast.Constant('unsigned int', str(res))
        except Exception:
            return c_ast.BinaryOp(node.op, left, right)

    def get_val(self, node):
        """Returns the integer value of |node|.

        If this value is not known at this point (ie, node is not a
        Constant or a static variable), then None is returned.

        """
        if isinstance(node, c_ast.Constant):
            return int(node.value)
        if isinstance(node, c_ast.ID) and node.name in self.env:
            return self.env[node.name]
        return None

    def eval_expr(self, expr):
        return self.get_val(self.visit(expr))
