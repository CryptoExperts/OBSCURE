Benchmarks for OBSCURE
===

This folder contains 2 benchmarks:

 - `full_tinyjambu.pl` compiles TinyJAMBU with various _s_ and _l_
   parameters, and records the number of LLMIs produced.
   
 - `all_ciphers.pl` compiles AES, Ascon, TinyJambu and Photon with 4
   different secure element configurations, with and without
   universalization, and outputs their statistics in
   `results`. `parse_all_ciphers.pl` can then be used to format nicely
   those statistic in LaTeX.
