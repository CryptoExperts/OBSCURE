OBSCURE: Versatile Software Obfuscation from a Lightweight Secure Element
===

OBSCURE is a versatile framework for practical and cryptographically strong software obfuscation relying on a simple stateless secure element.

Scientific paper: [OBSCURE: Versatile Software Obfuscation from a Lightweight Secure Element](https://eprint.iacr.org/2024/077) 


# Directories
- ``compiler``: source code of the compiler.
- ``runtime``: source code of the interpreter and the secure element.
- ``programs``: source code of the benchmarked programs. These programs are refactored (in order to be compatible with our compiler) and compared to their reference implementations (in order to ensure the correctness).
- ``benchs``: source code used to automatically run the benchmarks.
- ``tests``: many C programs used for testing the compiler and the interpreter.
    * ``tests/automated/basic``: Some basic programs used for debugging during the development.
    * ``tests/automated/medium``: Some more complex programs for debugging during the development.
    * ``tests/automated/program``: Programs to be benchmarked. These programs are copied from ``programs`` and configured to be automatically run in the benchmark.
    * ``tests/vrac``: Some test programs that are rather meant to be used manually when developing.
- ``run_tests.pl``: Script to run automated tests.

# Installation
Please follow the steps in [INSTALL.md](INSTALL.md)

# Usage

(All the commands below should be ran from the root of the repository)

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


To compile a C program, we have to specify the following parameters: `-r`, `-lin`, `-lout`, `-s`, `-o` and an input C program. Note that the values of these parameters must be compatible with those of the secure element in `runtime/SEconfig.h`. The other parameters are optional.

Let us take the C program ``tests/automated/vrac/t.c``, for example. To compile it, run:

    python3 compiler/compiler.py -r 40 -lin 8 -lout 8 -s 32 tests/vrac/t.c -o bytecode.bin


## Intepreter
In the ``runtime`` folder, besides the source code of the interpreter and the secure element, there is a folder named ``sparkle`` which contains the implementations of the AEAD ``SCHWAEMM`` and the hash ``ESCH``.

To compile the interpreter, simply run:

    make -C runtime

**Note**: The chosen configuration of the secure element in ``runtime/SEconfig.h`` must be compatible with those (`-r`, `-lin`, `-lout`, `-s`) specified when compiling the program.

We now execute the file ``bytecode.bin`` using the interpreter. Note that the function in `tests/automated/vrac/t.c` requires 3 input values and returns 1 output value. We run:

    ./runtime/interpreter --inputs 111,222,333 --out_count 1 bytecode.bin

where 111,222,333 are some arbitrary input values. The output should be:

    19257

# Tests

The script ``run_tests.pl`` is used to automatically run the tests. The main steps to test a program in this script are:

1. Compile the C program to generate a bytecode file.
2. Randomize the input values of the C program.
3. Run the C program (as a normal C program with a main function) given the random input values.
4. Execute the bytecode with the interpreter given the same input values.
5. Compare the returned output values of the two steps above.

To automatically test all the C programs in the ``tests`` folder, simply run:

    perl run_tests.pl

You might need to install `coreutils` for the `timeout` command in this script. (`sudo apt install coreutils` on Debian-like or `brew install coreutils` on MacOS).

To test a particular C program, for example ``tests/automated/program/TinyJambu.c``, run:

    perl run_tests.pl tests/automated/programs/TinyJambu.c

To add a new test to be run automatically, we follow the steps below:

1. Add your C program file into the ``tests`` folder. For instance, the following function is put into ``tests/vrac/t.c``:

```
unsigned int f(unsigned int a, unsigned int b, unsigned int c) {
  unsigned int k = a + b;
  unsigned int l = 42;
  unsigned int m = c + l;
  unsigned int o = l + m;
  unsigned int e = m + o;
  l = l | k;
  o = e & m;
  o = o - a;
  o = o ^ c;
  m = l ^ o;
  o = m << 4;
  a = m * m;
  return a + o;
}
```
2. In the same folder, create an information file with the same name, but extension ``.info``. This file is then read by ``run_tests.pl`` to automatically generate the main function for the test. In the information file, we have to provide the following:

- ``MAIN``: name of the root function of the program. In the above example, ``MAIN=f`` (see `tests/vrac/t.info` for more details).
- ``INPUT_COUNT``: the number of inputs. In the above example, `INPUT_COUNT=3`.
- ``INPUT_TYPES``: the corresponding types of the inputs. We have several cases:
    * ``unsigned int``: a variable
    * ``unsigned int[n]``: an array of `n` elements where `n` must be specified
    * ``unsigned int[n]+``: an array of `n` elements where `n` must be specified. `+` means these `n` elements are then returned at the output.
    
    In the above example, the types of the inputs are written as the following (no space after commas):

    ```
    INPUT_TYPES=unsigned int,unsigned int,unsigned int
    ``` 
    
    Let's take `tests/programs/Ascon.info` as another example. The prototype of the main function is
    ```
    int crypto_aead_encrypt_struc(unsigned int* c,
                            const unsigned int* m,
                            const unsigned int* ad,
                            const unsigned int* npub,
                            const unsigned int* k)
    ```
    
    We note that the `unsigned int* c` must be returned at the output. The declaration of the corresponding inputs' types is:

    ```
    INPUT_TYPES=unsigned int[8]+,unsigned int[4],unsigned int[4],unsigned int[4],unsigned int[4]
    ```

- ``OUTPUT_COUNT``: the number of outputs. This is the sum of all numbers of elements that must be returned at the output. If it is not specified, it is 1 by default (this is the case for the above example `tests/vrac/t.c`). 

    Let's take `tests/programs/Ascon.info` as an example, this number is 9, including 8 for `unsigned int *c` and 1 for `return 0` at the end of the function.

- ``VOID_MAIN``: if the root function is void, this is set to be ``true``. For instance, in the file ``tests/programs/AES.info``, we have ``VOID_MAIN=true``. If this information is not specifed, it is ``false`` by default.


**Important**: Always make sure that the configuration of the secure element in the two files ``run_tests.pl`` and ``runtime/SEconfig.h`` are identical. This configuration includes:
- ``lin`` (LLMI_MAX_INPUT_COUNT): number of input values of a multi-instruction
- ``lout`` (LLMI_MAX_OUTPUT_COUNT): number of output values of a multi-instruction (equal to ``lin``)
- ``s`` (LLS_MAX_LENGTH): number of instructions in each multi-instruction
- ``r`` (REGISTER_COUNT): size of internal memory in a secure element

# Benchmarks

We use `pypy3` instead of `python3` to speed up the benchmarks. To install `pypy3`, we first download a proper binary from [https://www.pypy.org/download.html](https://www.pypy.org/download.html). Our benchmarks use pypy3.10 on MacOS x86_64.

We create a symlink to `pypy3` (stored in, for example, `/usr/local/bin/`), which links to the binary file in the downloaded folder:
    
    ln -s <path-to-downloaded-folder>/bin/pypy3 /usr/local/bin/pypy3

Then, we have to install `pip` in `pypy3`:

    pypy3 -m ensurepip

Next, we install necessary packages in `pypy3` as in `python3`:

    pypy3 -m pip install "pycparser>=2.21" pysodium graphviz

Also, we have to install `schwaemm` in `pypy3`:

    cd compiler/schwaemm && pypy3 setup.py install && cd -

To automatically generate table 2 and 3 in the paper, we run

    perl all_ciphers.pl

The results will be generated in `benchs/results/dump_all_ciphers.txt`. To automatically parse this file into a table in LaTeX, we run

    perl parse_all_ciphers.pl

To automatically generate table 5 (Impact of the SE parameters on TinyJAMBU) in the paper, we run

    perl full_tinyjambu.pl

