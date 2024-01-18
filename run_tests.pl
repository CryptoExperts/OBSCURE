#!perl

=head1 Description

This script runs all the continuous integration (CI) tests of this project.


If some arguments are provided, then those arguments are assumed to be
the names of the specific tests to run. For instance,

    perl run_tests.pl tests/automated/add.c

Runs the "add.c" test only.


The test files are C programs, which we try to compile/interpreter,
and check if their behaviors is the same when obfuscated or not. The
overall process of running a test is:

  * Compile this test with our compiler (produces the obfuscated
    bytecode)

  * Generate a C main for this test, compile it with gcc (produces the
    clear binary)

  * Run the obfuscated bytecode (with the interpreter) and the clear
    binary on several random inputs, and check that their outputs are
    the same.


## Format of the .info files

Example:

   MAIN=f
   INPUT_COUNT=5
   INPUT_TYPES=unsigned int,unsigned int[2]+,unsigned int[2]
   OUTPUT_COUNT=3

Details:

  - MAIN: the name of the main fuction in the test

  - INPUT_COUNT: the number of inputs (an array of size n counts as n
    inputs)

  - INPUT_TYPES: the types of the inputs. The only scalar type
    supported for now is "unsigned int". 1D arrays are
    supported. Arrays are represented as "type[dimension]", where
    "dimension" is an integer (and type can only be "unsigned int" for
    now). If a "+" follows the array, then it means this array is both
    an input and an output: its elements can be updated by the
    program, and are part of the output.

  - OUTPUT_COUNT: the number of outputs. Can be omitted is equal to 1
    (ie, if the main only has a "return" and doesn't return additional
    items via pointers). For arrays, each element of the array counts
    for 1 (eg, "unsigned int[2]+" counts as 2 outputs).

=cut

use strict;
use warnings;
use feature qw(say);
use autodie qw(open close);

use File::Copy;
use File::Temp qw(tempfile);
use List::Util qw(max);

my $C_FLAG;
my $timeout_cmd;
if ($^O =~ /linux/i) {
    $timeout_cmd = 'timeout';
    $C_FLAG = '-Wno-discarded-qualifiers';
} elsif ($^O =~ /darwin/i) {
    $timeout_cmd = 'gtimeout';
    $C_FLAG = '-Wno-incompatible-pointer-types-discards-qualifiers';
} else {
    die "Unsupported OS: $^O";
}

$| = 1; # Enables auto-flushing

my $TEST_DIR = 'tests/automated';
my @TEST_FILES;
my $TIMEOUT = 12000; # 20 minutes
my $C_COMPILER = 'gcc';
my $REPEAT_COUNT = 5; # How many different inputs to test for each file
my $COMPILER = 'compiler/compiler.py';
my $INTERPRETER_DIR = 'runtime';
my $INTERPRETER = "$INTERPRETER_DIR/interpreter";

if (@ARGV) {
    @TEST_FILES = @ARGV;
} else {
    @TEST_FILES = glob "$TEST_DIR/*/*.c";
}

# Setting params
# TODO: we should consider generating those randomly, or testing some
# specific params for each tests...
my $r    = 80;
my $s    = 64;
my $lin  = 16;
my $lout = 16;

# Computing max filename length
my $max_len = max(map { m{((?:[^/]+/)?[^/]+)\.c}; length($1) } @TEST_FILES, "./0123456789.c");

# Compiling the interpreter
print "Compiling interpreter" . ("." x ($max_len - 9)) . " ";
if (system "make -s -C $INTERPRETER_DIR 2>/dev/null") {
    say "Error. Exiting.\n";
    exit 1;
}
say "OK\n";

my (undef, $bin_src) = tempfile();
my (undef, $bin_obf)  = tempfile();
my ($ok, $err) = (0, 0);

say "Running the tests:";
main_loop: for my $c_source (@TEST_FILES) {
    my ($name) = $c_source =~ m{/?((?:basic/|medium/|programs/)?[^/]+)\.c$};

    print "  $name" . ("." x (($max_len - length($name)) + 10)) . " ";

    # Reading info
    my $info_file = $c_source =~ s/\.c/.info/r;
    open my $FH_info, '<', $info_file;
    my %info = map { chomp; split /\s*=\s*/ } <$FH_info>;
    $info{INPUT_TYPES} = [ split /\s*,\s*/, $info{INPUT_TYPES} ];
    if (grep { $_ !~ /^unsigned int(\s*\[\d+\]\s*\+?\s*)?$/ } @{$info{INPUT_TYPES}}) {
        say "Bad input format '$_'. Only 'unsigned int' and 'unsigned int [xxx]' " .
            "are accepted for now.";
        $err++;
        next;
    }
    $info{OUTPUT_COUNT} ||= 1;

    # Compiling/obfuscating the C file into bytecode
    if (system("$timeout_cmd $TIMEOUT python3 $COMPILER $c_source " .
               "-r $r -s $s -lin $lin -lout $lout -o $bin_obf -width 4 -depth 25")) {
        say "Fail: error during obfuscation.";
        $err++;
        next;
    }

    # Generating main for the non-obfuscated C code
    my (@C_vars, @args, @end_prints);
    my $prototype = sprintf "int %s(%s)", $info{MAIN},
        join ",", map { gen_C_proto_for_input($info{INPUT_TYPES}[$_], $_,
                                              \@C_vars, \@args, \@end_prints) }
                  0 .. $#{$info{INPUT_TYPES}};
    my $inputs_reading = join "\n    ", map {
        "$C_vars[$_-1] = atoi(argv[$_]);"
    } 1 .. $info{INPUT_COUNT};
    my $funcall = sprintf "%s(%s)", $info{MAIN},
        join ",", @args;
    my $funcall_with_maybe_print =
        $info{VOID_MAIN} ? $funcall : qq{printf("%u\\n", $funcall)};
    my $additional_prints = join "\n    ", @end_prints;
    open my $FH_C, '>', "$bin_src.c";
    say $FH_C "
#include <stdlib.h>
#include <stdio.h>

$prototype;

int main(int argc, char** argv) {
    // Reading inputs
    $inputs_reading

    // Calling the function
    $funcall_with_maybe_print;
    $additional_prints
}
";
    # Compiling the non-obfuscated C code
    if (system "$C_COMPILER $C_FLAG $bin_src.c $c_source -o $bin_src") {
        say "Fail: error during compilation of the source file.";
        $err++;
        next;
    }


    # Testing results from both versions
    for (1 .. $REPEAT_COUNT) {
        my @inputs = map { int(rand(1<<32)) } 1 .. $info{INPUT_COUNT};
        my $joined_inputs = join ",", @inputs;
        my $out_src = `$timeout_cmd $TIMEOUT $bin_src @inputs`;
        my $out_obf = `$timeout_cmd $TIMEOUT $INTERPRETER $bin_obf --inputs $joined_inputs --out_count $info{OUTPUT_COUNT}`;
        if ($out_src ne $out_obf) {
            say "Fail. Non-obfuscated output:\n------------\n" .
                "$out_src\n------------\nObfuscated output:\n------------\n$out_obf\n------------\n";
            say "For inputs: $joined_inputs (@inputs)\n";
            $err++;
            next main_loop;
        }
    }
    say "OK";
    $ok++;
}

my $tot = $err + $ok;
printf "\nRan $tot tests: $ok OK, $err fail%s\n\n", $err > 1 ? "s" : "";

if ($err == 0) {
    unlink $bin_obf, $bin_src, "$bin_src.c";
} else {
    say "Leaving temporary files: $bin_obf, $bin_src, $bin_src.c\n";
}


sub gen_C_proto_for_input {
    my ($input_type, $counter, $C_vars, $args, $end_prints) = @_;
    if ($input_type =~ /^unsigned int\s*\[\s*(\d+)\s*\]\s*\+?\s*$/) {
        my $arr_size = $1;
        # A small hack so that the array is declared right before its
        # first element is assigned to.
        push @$C_vars, "unsigned int v$counter\[$arr_size]; v$counter\[0]";
        push @$args, "v$counter";
        push @$end_prints, qq{printf("%u\\n", v$counter\[0]);} if $input_type =~ /\+/;
        for (1 .. $arr_size-1) {
            push @$C_vars, "v$counter\[$_]";
            push @$end_prints, qq{printf("%u\\n", v$counter\[$_]);} if $input_type =~ /\+/;
        }
        return "unsigned int v$counter\[$arr_size]";
    } else {
        push @$C_vars, "unsigned int v$counter";
        push @$args, "v$counter";
        return "unsigned int v$counter";
    }
}
