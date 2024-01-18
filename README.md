OBSCURE: Versatile Software Obfuscation from a Lightweight Secure Element
===

OBSCURE is a versatile framework for practical and cryptographically strong software obfuscation relying on a simple stateless secure element.

Scientific paper: [OBSCURE: Versatile Software Obfuscation from a Lightweight Secure Element](https://eprint.iacr.org/2024/077) 


# Directories
- ``compiler``: contains the source code of the compiler.
- ``runtime``: contains the source code of the interpreter and the secure element.
- ``programs``: contains the source code of the benchmarked programs.
- ``benchs``: contains the source code used to run the benchmarks.
- ``tests``: contains many C programs used for testing the compiler and the interpreter.
- ``run_tests.pl``: is the script to run automated tests.

# Installation
Please follow the steps in [INSTALL.md](INSTALL.md)

# Usage

## Compiler

```
usage: compiler.py [-h] -o OUTFILE [-v VERBOSE] -r R -lin L_IN -lout L_OUT -s S [-w WORD_SIZE] [-version VERSION]
                   [-stats] [-width WIDTH] [-depth DEPTH] [-fast | -no-fast] [-universal | -no-universal]
                   inputfile

positional arguments:
  inputfile             name of the input file

options:
  -h, --help            show this help message and exit
  -o OUTFILE, --outfile OUTFILE
                        name of the output file
  -v VERBOSE, --verbose VERBOSE
                        set verbosity level. If >= 5, prints all major representations of the program (AST, HLIR,
                        LLIR). If >= 10, prints minor representations (before SSA, before copy propagation, etc).
  -r R                  number of internal registers in the secure element
  -lin L_IN             number of inputs of the secure element
  -lout L_OUT           number of outputs of the secure element
  -s S                  number of maximal instructions in the secure element
  -w WORD_SIZE          word size
  -version VERSION      version of the compiler
  -stats                print helpful statistics on the compilation
  -width WIDTH          minimal width of the program
  -depth DEPTH          minimal depth of the program
  -fast                 faster compilation, but maybe worse generated code (default: -fast)
  -no-fast              slower compilation, but maybe better generated code (default: -fast)
  -universal            enable universalization to protect the data-flow (default: -universal)
  -no-universal         disable universalization (default: -universal)
```


To compile a C program, we have to specify `-r`, `-lin`, `-lout`, `-s`, `-o` and an input C program. The other parameters are optional.

Let us take the C program ``tests/automated/program/TinyJambu.c``, for example. To compile it, run:

    python3 compiler/compiler.py -r 24 -lin 8 -lout 8 -s 16 tests/automated/program/TinyJambu.c -o bytecode.bin


## Intepreter
In the ``runtime`` folder, besides the source code of the interpreter and the secure element, there is a folder named ``sparkle`` which contains the implementations of the AEAD ``SCHWAEMM`` and the hash ``ESCH``.

To compile the interpreter, simply run:

    make -C runtime

**Note**: For the configuration of the secure element, please see in ``SEconfig.h``.

Given a bytecode file, for example, ``bytecode.bin``. Suppose that the C program of this bytecode file requires 3 inputs and returns 2 outputs. To run the interpreter, run:

    ./runtime/interpreter --inputs 111,222,333 --out_count 2 bytecode.bin

where 111,222,333 are some inputs.

# Tests
The steps to test a C program:
- Compile the C program to generate a bytecode file.
- Randomize the inputs of the C program.
- Run the C program (as a normal C program with a main function) given the random inputs.
- Execute the bytecode with the interpreter given the same inputs.
- Compare the returned outputs of the two steps above.

To automatically test all the C programs in the ``tests`` folder, simply run:

    perl run_tests.pl

To test a particular C program, for example ``tests/automated/program/TinyJambu.c``, run:

    perl run_tests.pl tests/automated/program/TinyJambu.c

**Important**: To test a C program with your preferred configuration of the secure element, you have to modify the parameters ``lin`` (LLMI_MAX_INPUT_COUNT), ``lout`` (LLMI_MAX_OUTPUT_COUNT), ``s`` (LLS_MAX_LENGTH) and ``r`` (REGISTER_COUNT) in the two files: ``run_tests.pl`` and ``runtime/SEconfig.h``.

# License
This project is licensed under the terms of MIT License.