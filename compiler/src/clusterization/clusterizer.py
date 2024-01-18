import IR
from . import naive_clusterizer
from . import basic_clusterizer
from utils import debug_print_IR

def clusterize(hlir:IR.HLIRProgram, config) -> IR.LLIRProgram :

    #llir = naive_clusterizer.clusterize(hlir, config)
    llir = basic_clusterizer.clusterize(hlir, config)
    debug_print_IR(config.verbose >= 5, "Clusterized LLIR:", llir)

    return llir
