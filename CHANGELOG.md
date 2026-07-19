# Changelog

## Fix ambiguous nucleotides in trinucleotide feature extraction

The trinucleotide counter could fail with `local variable 'first' referenced before assignment` when a triplet contained an unsupported nucleotide such as `N`. If the variable had been assigned while processing an earlier triplet, its stale value could instead be reused and produce an incorrect count.

The counter now validates all three bases before converting them to array indices. Triplets composed entirely of `A`, `C`, `G`, or `T` continue to be counted normally, while triplets containing ambiguous or unsupported nucleotides are skipped.
