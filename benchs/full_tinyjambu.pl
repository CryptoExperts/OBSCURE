#!perl

=head Description

Compiles TinyJambu with various options for l_in/l_out and s, and
collects the number of MLMIs in the final program. The goal being to
see how l_in/l_out and s impact the final program.

The number of registers (r) is fixed to l_in*3 (this allows enough
registers for all the inputs/outputs + a few registers for
intermediate computations).

This script outputs the results as LaTeX macros in
bench_full_tinyjambu.tex.

The values for l_in/l_out are the same, and are defined in the @L
variable. The values for s are defined in the @S variable.

=cut

use strict;
use warnings;
use feature qw(say);
use autodie qw(open close);
use feature 'say';
$| = 1; # Disabling output buffering

use Cwd;
use File::Path qw(make_path);
use File::Basename;

my @L = qw(2 4 8 16 32 64 128 256);
my @S = qw(2 4 8 16 32 64 128 256);
my $python = "pypy3";
my $path_to_tinyjambu = "tests/automated/programs/TinyJambu.c";
my $path_to_results   = "benchs/results/bench_full_tinyjambu.tex";
my $path_to_compiler  = "compiler/compiler.py";

# Moving to upper directory if inside "bench"
if (getcwd() =~ m{/benchs$}) {
    say "$0... moving one directory up.";
    chdir "..";
}

# Making sure that $path_to_tinyjambu is valid
if (! -f $path_to_tinyjambu) {
    die "Cannot find TinyJambu (should be located at '$path_to_tinyjambu')";
}

# Making sure that $path_to_compiler is valid
if (! -f $path_to_compiler) {
    die "Cannot find compiler (should be located at '$path_to_compiler')";
}

# Creating the results directory if needed
if (! -f $path_to_results) {
    my (undef, $path) = fileparse($path_to_results);
    make_path $path;
}

open my $FH, '>', $path_to_results;

my $total = @L * @S;
my $count = 1;
my %d;
for my $l (@L) {
    for my $s (@S) {
        print "\r$0... Running: $count/$total";
        $count++;
        if ($s >= $l) {
            my $r = $l * 5;
            my $output = `$python compiler/compiler.py $path_to_tinyjambu -o /tmp/bench_full_tinyjambu.bc -r $r -lin $l -lout $l -s $s -stats`;
            my ($final_size) = $output =~ /Universalization:.*\n\s*MLIR size: (\d+)/;
            $d{$l}{$s} = significant($final_size);
        }
    }
}
print "\r$0... done.                 \n\n";


say "\\backslashbox{\$s\$}{\$\\ell\$}
             & \\textbf{2} & \\textbf{4} & \\textbf{8} & \\textbf{16} & \\textbf{32} & \\textbf{64} & \\textbf{128} & \\textbf{256} \\\\
\\hline
\\textbf{2}   & $d{2}{2}   &     -      &     -      &      -      &      -      &      -      &    -         &    -     \\\\
\\textbf{4}   & $d{2}{4}   & $d{4}{4}   &     -      &      -      &      -      &      -      &    -         &    -     \\\\
\\textbf{8}   & $d{2}{8}   & $d{4}{8}   & $d{8}{8}   &      -      &      -      &      -      &    -         &    -     \\\\
\\textbf{16}  & $d{2}{16}  & $d{4}{16}  & $d{8}{16}  & $d{16}{16}  &      -      &      -      &    -         &    -     \\\\
\\textbf{32}  & $d{2}{32}  & $d{4}{32}  & $d{8}{32}  & $d{16}{32}  & $d{32}{32}  &      -      &    -         &    -     \\\\
\\textbf{64}  & $d{2}{64}  & $d{4}{64}  & $d{8}{64}  & $d{16}{64}  & $d{32}{64}  & $d{64}{64}  &    -         &    -     \\\\
\\textbf{128} & $d{2}{128} & $d{4}{128} & $d{8}{128} & $d{16}{128} & $d{32}{128} & $d{64}{128} & $d{128}{128} &    -     \\\\
\\textbf{256} & $d{2}{256} & $d{4}{256} & $d{8}{256} & $d{16}{256} & $d{32}{256} & $d{64}{256} & $d{128}{256} & $d{256}{256}";



sub significant {
    # Keeps only 2 significant digits in $n
    my $n = shift;
    for (1 .. 2) {
        # Repeating twice because the $incr can increase the number of significant digits
        my ($start, $end) = $n =~ /^(\d(?:\d|\.\d)?)(.*)$/; # Extracting significant and non-significant parts
        my $incr =  $end =~ /^\.?[5-9]/; # Extracting increment if $end starts with 5, 6, 7, 8, or 9
        if ($start =~ /\./) {
            # Adding only 0.1 (or 0)
            $start += "0.$incr";
        } else {
            # Adding 1 (or 0)
            $start += $incr;
        }
        $n = $start . ($end =~ s/\d/0/gr); # Replacing non-significant digits by 0s
    }
    $n =~ s/\..*?\K0+$//; # Removing trailing 0s after the comma
    $n =~ s/\.$//; # Removing trailing "." (if all digits after the comma were removed)
    if ($n > 1000) {
        $n = ($n / 1000) . "k";
    }
    return $n;
}
