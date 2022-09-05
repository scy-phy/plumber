# Matching Leakage Templates in Binaries

In the [paper](https://doi.org/10.1145/3548606.3560613), we follow a two-step approach to identify a prefetching-based vulnerability: First, we use static analysis to identify binary code sections that match the code section from the Leakage Template. Second, we use dynamic analysis to verify the relations given in the Leakage Template.

The folder `asmregex/` contains a modified version of [asmregex](https://github.com/Usibre/asmregex), which we used for the static analysis part. The modifications add support for a subset of the ARM architecture and implement backreferences.

The folder `dynamic/` contains the code we used to perform the dynamic analysis based on GDB and Valgrind.