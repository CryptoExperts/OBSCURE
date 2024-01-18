from pathlib import Path
import sys
import argparse
import time

import IR
import frontend.frontend as frontend
import clusterization.clusterizer as clusterizer
import universalization.universalizer as universalizer
import lowering.lowering as lowering
import code_gen.serializer as serializer

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--outfile", dest="outfile",
                        help="name of the output file", required=True,
                        type=argparse.FileType('wb'))
    parser.add_argument("-v", "--verbose", dest="verbose",
                        type=int, help="set verbosity level. If >= 5, prints all major representations of the program (AST, HLIR, LLIR). If >= 10, prints minor representations (before SSA, before copy propagation, etc).",
                        default=0)
    parser.add_argument("inputfile", type=argparse.FileType('r'),
                        help="name of the input file");
    parser.add_argument("-r", dest="r",
                        help="number of internal registers in the secure element",
                        required=True, type=int)
    parser.add_argument("-lin", dest="l_in",
                        help="number of inputs of the secure element", required=True, type=int)
    parser.add_argument("-lout", dest="l_out",
                        help="number of outputs of the secure element", required=True, type=int)
    parser.add_argument("-s", dest="s",
                        help="number of maximal instructions in the secure element",
                        required=True, type=int)
    parser.add_argument("-w", dest="word_size", default=32, type=int,
                        help="word size")
    parser.add_argument("-version", dest="version", default=0, type=int,
                        help="version of the compiler")
    parser.add_argument("-stats", dest="stats", default=False,
                        help="print helpful statistics on the compilation",
                        action='store_true')
    parser.add_argument("-width", dest="width", default=0, type=int,
                        help="minimal width of the program")
    parser.add_argument("-depth", dest="depth", default=0, type=int,
                        help="minimal depth of the program")
    parser.add_argument("-simple-clusterizer", dest="simple_clusterizer", action="store_true",
                        help="faster compilation, but more multi-instructions")
    fast_group = parser.add_mutually_exclusive_group()
    fast_group.add_argument("-fast", action="store_true",
                            help="faster compilation, but maybe worse generated code (default: -fast)")
    fast_group.add_argument("-no-fast", action="store_true",
                            help="slower compilation, but maybe better generated code (default: -fast)")
    universal_group = parser.add_mutually_exclusive_group()
    universal_group.add_argument("-universal", action="store_true",
                                 help="enable universalization to protect the data-flow (default: -universal)")
    universal_group.add_argument("-no-universal", action="store_true",
                                 help="disable universalization (default: -universal)")

    config = parser.parse_args()


    if config.r < config.l_in + config.l_out:
        # If this constraint does not hold, we cannot have enough
        # registers inside the LLMI to store the inputs and the
        # outputs.
        sys.exit(f'`r` should be at least `l_in + l_out`. Provided: r={config.r}, l_in={config.l_in}, l_out={config.l_out}. Exiting.')

    if config.s < config.l_in or config.s < config.l_out:
        # If this constraint does not hold, an MLMI cannot contain
        # enough instructions to copy all of its inputs to outputs
        # (which it may need to do for rectangularization/universalization).
        sys.exit(f'`s` should be at least `l_in` and `l_out`. Provided: s={config.s}, l_in={config.l_in}, l_out={config.l_out}. Exiting.')

    # Enabling fast if neither -fast nor -no-fast were used
    if not config.fast and not config.no_fast:
        config.fast = True
    # Enabling universalization if neither -univeral nor -no-univeral were used
    if not config.universal and not config.no_universal:
        config.universal = True

    # -------------------------------------------------------------- #
    #                          Compiling!                            #
    # -------------------------------------------------------------- #
    global_start_time = time.time()

    # Frontend (C -> AST -> HLIR)
    pass_start_time = time.time()
    hlir_prog = frontend.file_to_IR(config.inputfile, config)
    pass_total_time = time.time() - pass_start_time
    if config.stats:
        print(f"Frontend: {pass_total_time:.2f} sec")
        print(f"  HLIR size: {len(hlir_prog.instrs)} HLIs")

    # Clusterizer (HLIR -> MLIR/DFG)
    pass_start_time = time.time()
    dfg = clusterizer.clusterize(hlir_prog, config)
    pass_total_time = time.time() - pass_start_time
    if config.stats:
        print(f"Clusterization: {pass_total_time:.2f} sec")
        print(f"  MLIR size: {len(dfg.nodes)} MLMIs")

    # Universalizer (MLIR/DFG -> MLIR/DFG)
    if config.universal:
        pass_start_time = time.time()
        dfg = universalizer.universalize(dfg, config)
        pass_total_time = time.time() - pass_start_time
        if config.stats:
            print(f"Universalization: {pass_total_time:.2f} sec")
            print(f"  MLIR size: {len(dfg.nodes)} MLMIs")

    # Lowering (MLIR/DFG -> LLIR)
    pass_start_time = time.time()
    llir_prog = lowering.lower(dfg, config)
    pass_total_time = time.time() - pass_start_time
    if config.stats:
        print(f"Lowering: {pass_total_time:.2f} sec")

    # Serializer (LLIR -> bytecode)
    pass_start_time = time.time()
    serializer.serialize(llir_prog, config)
    pass_total_time = time.time() - pass_start_time
    if config.stats:
        print(f"Serialization: {pass_total_time:.2f} sec")

    global_total_time = time.time() - global_start_time
    if config.stats:
        print(f"Total compilation time: {global_total_time:.2f} sec")


if __name__ == "__main__":
    main()
