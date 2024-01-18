#!perl

=head Description

TODO

=cut

use strict;
use warnings;
use feature qw(say);
use autodie qw(open close);
$| = 1; # Disabling output buffering

use Cwd;
use File::Path qw(make_path);
use File::Basename;

my @secure_elements = (
    { name => 'small',    l => 8,  s => 32 },
    { name => 'medium',   l => 16, s => 64 },
    { name => 'large',    l => 32, s => 128 },
    { name => 'xlarge',   l => 64, s => 256 }
    );

my @ciphers_no_universal = qw(AES Ascon Photon TinyJambu tracingAES mnist);
my @ciphers_universal = qw(AES Ascon Photon TinyJambu tracingAES sum_naive sum_tree findmax_naive findmax_tree);
my $path_to_ciphers = "tests/automated/programs";
my $python = "pypy3";
my $path_to_dump      = "benchs/results/dump_all_ciphers.txt";
my $path_to_compiler  = "compiler/compiler.py";

# Moving to upper directory if inside "bench"
if (getcwd() =~ m{/benchs$}) {
    say "$0... moving one directory up.";
    chdir "..";
}

# Making sure that $path_to_ciphers is valid
if (! -d $path_to_ciphers) {
    die "Cannot find cipher directory (should be located at '$path_to_ciphers')";
}
for my $cipher (@ciphers_no_universal) {
    if (! -f "$path_to_ciphers/$cipher.c") {
        die "Cannot find cipher $cipher at '$path_to_ciphers/$cipher.c'";
    }
}
for my $cipher (@ciphers_universal) {
    if (! -f "$path_to_ciphers/$cipher.c") {
        die "Cannot find cipher $cipher at '$path_to_ciphers/$cipher.c'";
    }
}

# Making sure that $path_to_compiler is valid
if (! -f $path_to_compiler) {
    die "Cannot find compiler (should be located at '$path_to_compiler')";
}

# Creating the results directory if needed
if (! -f $path_to_dump) {
    my (undef, $path) = fileparse($path_to_dump);
    make_path $path;
}

open my $FH, '>>', $path_to_dump;

my $total = @secure_elements * @ciphers_no_universal;
my $count = 1;

say $FH "Universalization: -no-universal";
for my $cipher (@ciphers_no_universal) {
    for my $se (reverse @secure_elements) {
        print "\r$0... Running: $count/$total";
        $count++;

        my $path_to_cipher = "$path_to_ciphers/$cipher.c";

        my ($name, $l, $s) = @$se{qw(name l s)};
        my $r = $l * 5;
        say $FH "$cipher -- $name ($l/$s)";

        my $output = `$python compiler/compiler.py $path_to_cipher -o /tmp/bench_all_ciphers.bc -r $r -lin $l -lout $l -s $s -no-universal -stats`;
        say $FH $output;
        say $FH "\n\n";
    }
}

$total = @secure_elements * @ciphers_universal;
$count = 1;

say $FH "Universalization: -universal";
for my $cipher (@ciphers_universal) {
    for my $se (reverse @secure_elements) {
        print "\r$0... Running: $count/$total";
        $count++;

        my $path_to_cipher = "$path_to_ciphers/$cipher.c";

        my ($name, $l, $s) = @$se{qw(name l s)};
        my $r = $l * 5;
        say $FH "$cipher -- $name ($l/$s)";

        my $output = `$python compiler/compiler.py $path_to_cipher -o /tmp/bench_all_ciphers.bc -r $r -lin $l -lout $l -s $s -universal -stats`;
        say $FH $output;
        say $FH "\n\n";
    }
}

print "\r$0... done.                 \n";
