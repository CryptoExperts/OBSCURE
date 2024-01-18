## Debian-like systems and MacOS

(all the commands below should be ran from the root of the repository)

### Quick setup

To get quickly ready on Debian-like systems, run the following commands:

    sudo apt install python3 swig libsodium-dev gcc
    pip3 install "pycparser>=2.21" pysodium
    cd compiler/schwaemm && sudo python3 setup.py install && cd -
    make -C runtime

To get quickly ready on MacOS, run the following commands:

    xcode-select --install # install cc and gcc
    brew install python3 swig libsodium
    pip3 install pysodium
    cd compiler/schwaemm && sudo python3 setup.py install && cd -
    make -C runtime

### Detailed setup

This section gives more detail on what the command presented above
actually do, and why. Read it if you are curious, if you don't want to
run random `sudo apt` or `brew` commands, or if you are a developper of this
project.

#### Compiler

The compiler is written in Python 3. To install Python 3 on Debian-like systems:

    sudo apt install python3

On MacOS, you can either use the following command or download the installer from [https://www.python.org/downloads/macos/](https://www.python.org/downloads/macos/):

    brew install python3

It uses a few Python modules:

  * `pycparser` for parsing C code and building the syntax tree.
  **Warning**: you'll need at least version 2.21 of pycparser. Any
  lower version will not work.

  * `pysodium` to encrypt the shared key during bytecode generation

To install all of those modules at once, run:

    pip3 install "pycparser>=2.21" pysodium

(depending on your setup, you might want to run `sudo pip3` instead of `pip3`)


Finally, encryption of the bytecode is done use the Schwaemm cipher,
which is embedded in this repo in `compiler/schwaemm`. To build it and
install it, you'll need the `swig` package, which you can install on Debian-like systems with:

    sudo apt install swig

On MacOS, you can execute the following command:

    brew install swig

You can then build and install Schwaemm:

    cd compiler/schwaemm && sudo python3 setup.py install && cd -

#### Interpreter

The interpreter is written in C. To install gcc (a C compiler) on Debian-like systems, run:

    sudo apt install gcc

On MacOS, you have to install `Command Line Tools`. This supports both cc and gcc:

    xcode-select --install

You'll also need the `libsodium` library. To install it on Debian-like system:

    sudo apt install libsodium-dev

On MacOS, run:

    brew install libsodium

You can now build the interpreter:

    make -C runtime


### Test file

To make sure that you have everything properly install, and that the
compiler works properly, you can compiler the file `tests/vrac/t.c`:

    python3 compiler/compiler.py tests/vrac/t.c -o out.bin -r 4 -s 2 -lin 2 -lout 2

You can then run it with the interpreter:

    ./runtime/interpreter --inputs 111,222,333 --out_count 1 out.bin

The output should be:

    19257
