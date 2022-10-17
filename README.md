# Plumber

Plumber is a framework to facilitate generating Leakage Templates, leveraging instruction and operand fuzzing and statistical analysis.

For detailed information refer to the research paper [Microarchitectural Leakage Templates and Their Application to Cache-Based Side Channels](https://doi.org/10.1145/3548606.3560613) ([accepted version, PDF](https://publications.cispa.saarland/3775/1/paper.pdf)) by Ahmad Ibrahim, Hamed Nemati, Till Schlüter, Nils Ole Tippenhauer, and Christian Rossow, published at [ACM CCS 2022](https://www.sigsac.org/ccs/CCS2022/).

# Folders and organization

- `plumber/`: Core components of Plumber: Preprocessor and Instantiator for Plumber GTSes in our domain-specific language, Classifier, and Analyzer.
- `executor/`: The bare-metal execution environment and Runner for Plumber
- `matcher/`: Proof-of-concept Leakage Template code pattern matcher. Contains a modified version of asmregex[^1].

# Preprocessor and Instantiator

The script `plumber/main.py` implements the parser and testcase instantiator and calls the testcase runner.
It takes a GTS as input, parses and expands it, generates assembly code and runs the assembly code on the target platform.

## Writing a GTS

A GTS consists of *directives* and *operators*.

### Directives
Directives are the most basic building blocks of a GTS. Each directive directly corresponds to a sequence of assembly instructions.

A directive is expressed as a single capital letter, e.g., `M` (memory load directive). Most directives can be parameterized with attributes, such as `M_s=s1` (add an underscore, then a comma-separated list of `attribute_key=attribute_value` pairs).

A general concept that many of the directives have in common is the concept of *placeholders*. It allows the user to express abstract relations between, for example, loaded memory addresses, without computing actual addresses manually. For instance, for a memory load directive `M`, a placeholder like `s1` can be provided for the cache set attribute (`M_s=s1`). Plumber ensures that all directives with an attribute set to the same placeholder share the same value for this attribute in the assembly code. In the aforementioned example, all memory directives with the attribute `s=s1` will produce loads from memory addresses mapping to the same cache set. Note that the actual value (here: the set index) is not specified in the GTS; it will be chosen by Plumber at runtime, based on the relations expressed by the attribute.

Placeholders consist of a single lowercase letter and a number. The number can freely be chosen by the user.

If a placeholder attribute is omitted, it is implicitly set to a default value. All directives that omit the attribute will therefore share the same value for this attribute in the resulting assembly code. For instance, `M` is equivalent to `M_s=sDEFAULT,t=tDEFAULT`.

We define the following five directives:

#### `M`: Memory load

Generates a load instruction that loads some value from memory into a register. The directive attributes allow to control parts of the loaded address.

##### Attributes
- **`s=<placeholder 's'>`: Set**: Selects the address bits that indicate the cache set.
- **`t=<placeholder 't'>`: Tag**: Selects the address bits that indicate the cache tag.

Both attributes can further be extended with a simple arithmetic expression. Allowed arithmetic operators are `+` and `-`. The attribute `s=s1+1` translates to "the set index `s1` plus 1". If the directive appears within a power operator, loop variable identifiers are also allowed: `s=s1+i` means "the set index `s1` plus the current value of loop variable `i`"

##### Examples
- `M`
- `M_t=t1`
- `M_s=s1`
- `M_s=s1+2`
- `M_s=s1+i+1`
- `M_s=s1,t=t1`

#### `A`: Arithmetic or logic operation

Generates an arithmetic or logic instruction (`add` or `xor`). The operands are always read from registers, the result is stored in a register. Thus, the `A` directive does not perform any memory operations. The directive attributes allow to control the operand registers. For each operand `o<N>`, a different register will be reserved and initialized with a random value during setup.

##### Attributes
- **`u=<placeholder 'o'>`: Operand 1**: Selects the first operand register.
- **`v=<placeholder 'o'>`: Operand 2**: Selects the second operand register.

##### Examples
- `A`
- `A_u=o1`
- `A_v=o2`
- `A_u=o1,v=o2`

#### `B`: Branch

Generates a sequence of instructions that:
1. Loads a value from memory
2. Compares the loaded value with an immediate value
3. Branches based on the result of the comparison.

The value loaded from memory and the immediate value that it is compared with can be controlled via attributes. Further, the distance of the jump that is performed in case of a taken branch can be specified.

The value loaded from memory can be further controlled with the `S` directive.

##### Attributes
- **`c=<placeholder 'c'>`: Condition**: Selects the first operand of the comparison, which is loaded from memory.
- **`b=<'T'/'F'>`: Boolean**: Controls the immediate operand that the loaded value is compared to. If both operands are set to `T`, the branch will be taken, otherwise, it will not.
- **`d=<int>`: Jump Distance**: Integer attribute. Indicates the jump distance in case of a taken branch.

##### Examples
- `B`
- `B_c=c1`
- `B_c=c1,b=T,d=12`

#### `S`: Store branch condition operand
Generates a sequence of instructions that changes a branch condition operand in memory.

Recall that the `B` directive uses a value stored in memory as one of the operands of the comparison instruction. This value is loaded based on the placeholder specified in the attribute `c`. The `S` directive allows to change this value in memory before it is loaded.

The `S` directive takes the same placeholder in the `c` attribute as the branch directive. Further, it takes a boolean value (`T`/`F`) specifies the new value to be stored.

##### Attributes
- **`c=<placeholder 'c'>`: Condition**: Selects the memory-stored comparison operand that is to be changed.
- **`b=<'T'/'F'>`: Boolean**: Specifies the new value to be stored in memory.

##### Examples
- `S_b=T`
- `S_c=c1,b=T`
- `S_c=c1,b=F`

#### `N`: nop
Inserts a single `nop` instruction. There are no attributes to this directive.

##### Examples
- `N`

### Operators
Operators are shortcuts that allow to express complex sequences of directives in a more compact way. The following operators are supported:

#### Power: `[]n`, `[]end,step,loopvar`

The power operator repeats a directive multiple times. There are 2 variants: a reduced form for simple repetition and a more advanced loop syntax.

##### Simple loop: `[]n`

The directives specified within `[]` are simply repeated `n` times. `[M]3` is expanded to `M M M`, `[M N]2` is expanded to `M N M N`.

##### Loop with loop variable: `[]end,step,loopvar`
*(Note that the definition of this operator differs slightly from the definition in the paper. For the paper, we chose a less technical syntax that is easier to read.)*

This variant of the power expresses repetition similar to a for-loop in C. It allows to declare a loop variable that always starts at 0, is increased by `step` in each iteration, and is increased until it reaches the upper bound of `end` (exclusive).

To give an example: The GTS `[M_s=s1+i N]8,2,i` is comparable to the following C-like pseudocode:
```c
for (int i = 0 /* always 0 */; i < 8 /* end */; i += 2 /* step */) {
	M_s=s1+i
}
```

Consequently, it expands to the following sequence of directives: `M_s=s1+0 M_s=s1+2 M_s=s1+4 M_s=s1+6`

#### Wildcard `#n`

This operator expands to n arbitrary directives that do not perform memory operations (currently `N` or `A`). For example, `M #3 M` may expand to `M A A N M`, `M N N N M`, or similar.

#### Shuffle: `()!`

This operator generates all possible permutations of a GTS while omitting those with similar directives. For example, `([M]2 M_t=t1,s=s1)!` refers to the following  set of experiments: `{M M M_t=t1,s=s1 ; M M_t=t1,s=s1 M ; M_t=t1,s=s1 M M}`.

#### Subset: `()S`
This operator generates all possible subsets of a GTS while omitting those with similar directives. For example, `([M]2 M_t=t1,s=s1)S` refers to the set: `{M M ; M M_t=t1,s=s1 ; M ; M_t=t1,s=s1}`

#### Slide: `()n`

For a given GTS, this operator shifts all loaded addresses one set at a time up to n times. For example, `(M_t=t1,s=s1 M_t=t2,s=s2)3`
refers to the set: `{M_t=t1,s=s1 M_t=t1,s=s1 ; M_t=t1,s=s1+1 M_t=t1,s=s1+1 ; M_t=t1,s=s1+2 M_t=t1,s=s1+2}`

#### Merge: `(:)+`

This operator merges two requests by sliding the directives of the first over the second as demonstrated by the following example.
`(M_t=t1,s=s1 M_t=t2,s=s2 : M_t=t3,s=s3 M_t=t4,s=s4)+` refers to the following set of 4 experiments:
`{
	M_t=t1,s=s1 M_t=t2,s=s2 M_t=t3,s=s3 M_t=t4,s=s4 ;
	M_t=t1,s=s1 M_t=t3,s=s3 M_t=t2,s=s2 M_t=t4,s=s4 ;
	M_t=t3,s=s3 M_t=t1,s=s1 M_t=t4,s=s4 M_t=t2,s=s2 ;
	M_t=t3,s=s3 M_t=t4,s=s4 M_t=t1,s=s1 M_t=t2,s=s2
}`

#### Load offset fuzzing: `<>@`

For every load instructions, the operator signals generation of a testcase for every possible memory addresses with the indicated tag and set, i.e., it brute forces all possible word offsets. For example, `<M M>@` generates a set formed of all two loads having the same tag and set with all possible combinations of word offsets.

#### Cache line fuzzing: `<>$`

For every load instruction, this operator signals the generation of a testcase for every possible memory address having the indicated tag and word offset, i.e., it brute forces all possible sets. For example, `<M M>$` generates a set formed of all two loads that have the same tag for all possible combinations of sets, i.e., `{M_t=t1,s=s1 M_t=t1,s=s2}` for every set `s1` and `s2`.

#### Repetition: `||n`
This operator repeats the GTS `n` times. For example, the GTS `|M M_t=t1,s=s1|3` refers to the set: `{M M_t=t1,s=s1 ; M M_t=t1,s=s1 ; M M_t=t1,s=s1}`.

#### Precondition: `P()`
This operator allows setting up the state of different hardware components before the execution of actual testcase. For instance, the GTS `P(M_t=t1,s=s1 M_t=t2,s=s1) <M M>$` generates cache line fuzzing testcases over the cache, when two lines in `s1` are already occupied.

## Usage

```
$ python3 main.py -h
usage: main.py [-h] [-d [STATE_JSON_FILE]] [-v] [-o OUTDIR] gts

Transforms a Generative Testcase Specification (GTS) into assembly code.

positional arguments:
  gts                   String representation of a Generative Testcase Specification

optional arguments:
  -h, --help            show this help message and exit
  -d [STATE_JSON_FILE], --deterministic [STATE_JSON_FILE]
                        Keeps the mappings from placeholders (such as 's1' for sets) to actual
                        addresses across experiments instead of re-randomizing it. The mappings
                        will be stored in the specified json file and can later be reused for
                        other GTSes. If the filename is omitted, it defaults to state.json.
  -v, --verbose         Enables more detailed output
  -o OUTDIR, --outdir OUTDIR
                        Output directory to store the generated code files in. If this parameter
                        is not provided, the generated code is written to stdout.

```

## Collection of examples from this documentation
```
python3 main.py '[M]3'
python3 main.py '[M N]2'
python3 main.py '[M_s=s1+i N]8,2,i'
python3 main.py 'M #3 M'
python3 main.py '([M]2 M_t=t1,s=s1)!'
python3 main.py '([M]2 M_t=t1,s=s1)S'
python3 main.py '(M_t=t1,s=s1 M_t=t2,s=s2)3'
python3 main.py '(M_t=t1,s=s1 M_t=t2,s=s2 : M_t=t3,s=s3 M_t=t4,s=s4)+'
python3 main.py '<M M>@'
python3 main.py '<M M>$'
python3 main.py '|M M_t=t1,s=s1|3'
python3 main.py 'P(M_t=t1,s=s1 M_t=t2,s=s1) <M M>$'
```

# Classifier and Analyzer

After the testcase runner executed all the testcases generated from a GTS, the script `plumber/classifier_analyzer.py` can be used to examine the collected data.

## Classification

First, the testcases are classified based on user-defined criteria. The criteria are defined in a configuration file that is then passed to the script via the `-c` command line parameter. A template for this config file is provided as `plumber/classifier.template.ini`.

The following classification methods are currently supported: `cache_count`, `cache_exact_address`, `int_threshold`, `int_pct_error`.

### `cache_count`

This method classifies the testcases based on the number of elements in the cache. For instance, if the cache contains seven elements after testcase execution, the testcase is classified into the class `7`.

This classification method requires the follwing additional parameters (specified in the configuration file):
- `cache_level`: The cache level to count the elements in.

### `cache_exact_address`

This method classifies the testcases based on the cache state of a specific address. If the specified address is cached after testcase execution, the testcase is classified into the class `1`, otherwise `0`.

This classification method requires the follwing additional parameters (specified in the configuration file):
- `cache_level`: The cache level to find the specified address in.
- `expected_address_index`: The address that is expected in cache, specified by means of a reference to a register. `0` refers to the address stored in the first register that is used in the testcase, `1` refers to the second register, and so on.


### `int_threshold`

This method classifies the testcases based on an integer threshold, for instance based on the result of a time measurement. The classification is based on the following comparison: `value RELATION threshold`, where `RELATION` is one of `lt` (<), `le` (<=), `eq` (==), `ge` (>=), `gt` (>), or `ne` (!=). If the comparison evaluates to `True`, the testcase is classified into the class `1`, otherwise `0`.

This classification method requires the follwing additional parameters (specified in the configuration file):
- `threshold`: The integer value to compare the observed value with.
- `relation`: The relation operator to use for the comparison.

### `int_pct_error`

This method classifies a testcases based on a percentage value (integer in the range 0..100). The range is split into a number of buckets. Each bucket forms a class, identified by `lower_bound + (upper_bound - lower_bound) // 2` (middle value of the bucket range).

This classification method requires the follwing additional parameters (specified in the configuration file):
- `bucket_size`: The size of the buckets used for classification.

## Note on inconclusive cases

For some experiments, the behavior of the microarchitectural component under investigation may not be deterministic. In other words, if an experiment with the exact same parameters is repeated multiple times, the observed behavior is not consistent. For example, when investigating prefetching, there might be parameters for which prefetching sometimes happens and sometimes not, or the number of prefetched cache lines differs. These cases can be recognized by the fact that different instances of the same experiment are classified into different classes. For the case studies in our paper, we excluded these cases from the relations in the leakage template, since no clear rule can be derived that describes the behavior in these cases accurately.

## Usage

```
$ python3 classifier_analyzer.py -h
usage: classifier_analyzer.py [-h] -o OUTDIR [-c CONFIG]

Classifies and analyzes the results of GTS execution based on user-defined criteria.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTDIR, --outdir OUTDIR
                        Output directory of the executor to load the logs from
  -c CONFIG, --config CONFIG
                        Configuration file for the classifier. Default: classifier.ini
```

[^1]: asmregex: https://github.com/Usibre/asmregex
