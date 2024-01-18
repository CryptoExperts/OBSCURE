from pycparser import c_parser, c_ast, c_generator
from . import identifiers

class IdentsCollector(c_ast.NodeVisitor):
    """Collects all the identifiers of a program, in particular duplicated ones"""

    def __init__(self, ast):
        self.collect_idents(ast)

    def collect_idents(self, ast):
        self.dups = dict()
        self.generic_visit(ast)

    def visit_Struct(self, struct):
        # We don't care about struct's members names
        pass

    def visit_StructRef(self, node):
        # Same comment as above: we don't care about struct's members
        self.visit(node.name)

    def visit_NamedInitializer(self, node):
        # Same comment as above: we don't care about struct's members
        self.visit(node.expr)

    def visit_Decl(self, decl):
        if identifiers.ident_exists(decl.name):
            self.dups[decl.name] = self.dups.get(decl.name, 1) + 1
        identifiers.add_ident(decl.name)
        self.generic_visit(decl)



class AlphaConverter(c_ast.NodeVisitor):
    """Renames all identifiers that are used for multiple variables

    The names of such variables will be updated with a _n added at the
    end (with n an integer).

    """

    # Note that the only place variables can be declared are:
    #   - Function definitions
    #   - Compound statements
    #   - For loops initializer
    # As such, when visiting those construct, we start a new environment,
    # which is dropped at the end of the said construct.


    def __init__(self):
        self.env = dict()

    def visit_FileAST(self, ast):
        identifiers.reset()
        self.idents_collector = IdentsCollector(ast)
        self.env = dict()
        self.generic_visit(ast)

    def alpha_convert(self, old_ident):
        if old_ident in self.idents_collector.dups:
            new_ident = identifiers.gen_next_ident(prefix=old_ident)
            self.env[old_ident] = new_ident
            return new_ident
        else:
            return old_ident

    def visit_Struct(self, struct):
        # We don't want to rename struct's inner members.
        pass

    def visit_StructRef(self, node):
        # Same comment as above: we don't rename struct's members
        self.visit(node.name)

    def visit_NamedInitializer(self, node):
        # Same comment as above: we don't rename struct's members
        self.visit(node.expr)

    def visit_FuncDef(self, fun):
        old_env = self.env.copy()
        self.generic_visit(fun)
        self.env = old_env

    def visit_Compound(self, compound):
        old_env = dict(self.env)
        self.generic_visit(compound)
        self.env = old_env

    def visit_For(self, forloop):
        old_env = dict(self.env)
        self.generic_visit(forloop)
        self.env = old_env

    def visit_Decl(self, decl):
        typedecl = decl.type
        if isinstance(typedecl, c_ast.Struct):
            return
        while not isinstance(typedecl, c_ast.TypeDecl):
            typedecl = typedecl.type
        decl.name = self.alpha_convert(decl.name)
        typedecl.declname = decl.name

        if isinstance(decl.type, c_ast.FuncDecl) and decl.type.args:
            self.visit(decl.type.args)

        if decl.init:
            self.visit(decl.init)

    def visit_ID(self, ID):
        if ID.name in self.env:
            ID.name = self.env[ID.name]
