#!perl

use strict;
use warnings;
use feature qw(say);
use autodie qw(open close);
$| = 1; # Disabling output buffering

chdir '..';

my $path_to_dump = "benchs/results/dump_all_ciphers.txt";

# Parsing dump file
open my $FH, '<', $path_to_dump;
my (%data, $cipher, $size, $uni);
while (<$FH>) {
    if (/Universalization: -universal/) {
        $uni = 'uni';
    } elsif (/Universalization: -no-universal/) {
        $uni = 'no_uni';
    } elsif (/^(\w+) -- (\w+) \(/) {
        ($cipher, $size) = ($1, $2);
    } elsif (/HLIR size: (\d+)/) {
        die if !$cipher || !$size;
        $data{$uni}{$cipher}{$size}{HLIR} = significant($1);
    } elsif (/MLIR size: (\d+)/) {
        die if !$cipher || !$size;
        push @{$data{$uni}{$cipher}{$size}{MLIR}}, significant($1);
    } elsif (/depth: (\d+)/) {
        die if !$cipher || !$size;
        $data{$uni}{$cipher}{$size}{depth} = significant($1);
    } elsif (/width: (\d+)/) {
        die if !$cipher || !$size;
        $data{$uni}{$cipher}{$size}{width} = significant($1);
    } elsif (/Total compilation time: (\d+(?:\.\d+)?)/) {
        die if !$cipher || !$size;
        my $time = $1;
        if ($time > 600) {
            $time = significant($time/60) . " min";
        } else {
            $time = significant($time) . " sec";
        }
        $data{$uni}{$cipher}{$size}{total_time} = $time;
    }
}

# Patching missing data
for my $uni (qw(uni no_uni)) {
    for my $cipher (qw(AES Ascon Photon TinyJambu sum_naive sum_tree findmax_naive findmax_tree tracingAES mnist)) {
        for my $size (qw(small medium large xlarge)) {
            for my $field (qw(depth width HLIR total_time)) {
                if (! exists $data{$uni}{$cipher}{$size}{$field}) {
                    $data{$uni}{$cipher}{$size}{$field} = "-";
                }
            }
            if (! exists $data{$uni}{$cipher}{$size}{MLIR}) {
                $data{$uni}{$cipher}{$size}{MLIR} = [ '-', '-', '-' ];
            }
        }
    }
}

# use Data::Printer;
# p %data;
# exit;

# {
#     for my $cipher (qw(AES Ascon Photon TinyJambu)) {
#         my $size = 'large';
#         say "$cipher: ", join " - ", @{$data{uni}{$cipher}{$size}}{qw(depth width HLIR)}, @{$data{uni}{$cipher}{$size}{MLIR}}, $data{uni}{$cipher}{$size}{total_time};
#     }
# }

# Printing results
printf '
\\textbf{Cipher}                     & \\makecell{\\textbf{Secure}\\\\\\textbf{Element}} & \\textbf{\\#HLIs} & \\textbf{Depth} & \\textbf{Width} & \\makecell{\\textbf{\\#MLMIs}\\\\\\textbf{(clusterized)}} & \\makecell{\\textbf{\\#MLMIs}\\\\\\textbf{(rectangular)}} & \\makecell{\\textbf{\\#LLMIs}\\\\\\textbf{(final)}} & \\makecell{\\textbf{Compilation}\\\\\\textbf{time}} \\\\ \\hline
\\multirow{4}{*}{AES}       & small  &   \\multirow{4}{*}{%s}    &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & medium &                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & large  &                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & xlarge&                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
\\hline
\\multirow{4}{*}{Ascon}     & small  &   \\multirow{4}{*}{%s}    &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & medium &                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & large  &                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & xlarge&                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
\\hline
\\multirow{4}{*}{Photon}    & small  &   \\multirow{4}{*}{%s}    &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & medium &                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & large  &                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & xlarge&                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
\\hline
\\multirow{4}{*}{TinyJAMBU} & small  &   \\multirow{4}{*}{%s}    &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & medium &                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & large  &                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & xlarge&                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
\\hline
\\multirow{4}{*}{sum(naive)}& small  &   \\multirow{4}{*}{%s}    &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & medium &                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & large  &                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & xlarge&                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
\\hline
\\multirow{4}{*}{sum(tree)} & small  &   \\multirow{4}{*}{%s}    &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & medium &                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & large  &                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & xlarge&                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
\\hline
\\multirow{4}{*}{findmax(naive)} & small  &   \\multirow{4}{*}{%s}    &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & medium &                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & large  &                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & xlarge&                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
\\hline
\\multirow{4}{*}{findmax(tree)} & small  &   \\multirow{4}{*}{%s}    &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & medium &                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & large  &                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & xlarge&                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
\\hline
\\multirow{4}{*}{tracing AES} & small  &   \\multirow{4}{*}{%s}    &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & medium &                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & large  &                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
                            & xlarge&                           &    %s     &    %s     &         %s          &             %s            &      %s        &        %s        \\\\
',
    map { my $cipher = $_;
          $data{uni}{$cipher}{$size}{HLIR},
          map { my $size = $_;
                @{$data{uni}{$cipher}{$size}}{qw(depth width)}, @{$data{uni}{$cipher}{$size}{MLIR}}, $data{uni}{$cipher}{$size}{total_time} }
          qw(small medium large xlarge)
        } qw(AES Ascon Photon TinyJambu sum_naive sum_tree findmax_naive findmax_tree tracingAES);

say "\n\n\n";

printf '
\\textbf{Cipher}                     & \\makecell{\\textbf{Secure}\\\\\\textbf{Element}} & \\textbf{\\#HLIs} & \\makecell{\\textbf{\\#LLMIs}\\\\\\textbf{(final)}} & \\makecell{\\textbf{Compilation}\\\\\\textbf{time}} \\\\
\\hline
\\multirow{4}{*}{AES}      & small                       &   \\multirow{4}{*}{%s}   &           %s                &       %s                     \\\\
                           & medium                       &      &           %s                &       %s                     \\\\
                           & large                        &      &           %s                &       %s                     \\\\
                           & xlarge                      &      &           %s                &       %s                     \\\\
\\hline
\\multirow{4}{*}{Ascon}     &small                       &   \\multirow{4}{*}{%s}   &           %s                &       %s                     \\\\
                           & medium                      &      &           %s                &       %s                     \\\\
                           & large                       &      &           %s                &       %s                     \\\\
                           & xlarge                     &      &           %s                &       %s                     \\\\
\\hline
\\multirow{4}{*}{Photon}    &small                       &   \\multirow{4}{*}{%s}   &           %s                &       %s                     \\\\
                           & medium                      &      &           %s                &       %s                     \\\\
                           & large                       &      &           %s                &       %s                     \\\\
                           & xlarge                     &      &           %s                &       %s                     \\\\
\\hline
\\multirow{4}{*}{TinyJAMBU} &small                       &   \\multirow{4}{*}{%s}   &           %s                &       %s                     \\\\
                           & medium                      &      &           %s                &       %s                     \\\\
                           & large                       &      &           %s                &       %s                     \\\\
                           & xlarge                     &      &           %s                &       %s                     \\\\
\\hline
\\multirow{4}{*}{tracing AES} & small                       &   \\multirow{4}{*}{%s}   &           %s                &       %s                     \\\\
                             & medium                      &      &           %s                &       %s                     \\\\
                             & large                      &      &           %s                &       %s                     \\\\
                             & xlarge                       &      &           %s                &       %s                     \\\\
\\hline
\\multirow{4}{*}{MNIST} & small                       &   \\multirow{4}{*}{%s}   &           %s                &       %s                     \\\\
                             & medium                      &      &           %s                &       %s                     \\\\
                             & large                      &      &           %s                &       %s                     \\\\
                             & xlarge                       &      &           %s                &       %s                     \\\\
',
    map { my $cipher = $_;
          $data{no_uni}{$cipher}{large}{HLIR},
          map { my $size = $_;
                $data{no_uni}{$cipher}{$size}{MLIR}[-1], $data{no_uni}{$cipher}{$size}{total_time} }
          qw(small medium large xlarge)
        } qw(AES Ascon Photon TinyJambu tracingAES mnist);



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
