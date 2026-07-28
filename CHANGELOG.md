# Changelog

## Add single-species preparation and training commands

RNAmining can now prepare and train one species without changing the established
16-species S5 workflow. `rnamining prepare-species` accepts a ZIP containing one
matching `<species>.<assembly>.cds.all.fa.gz` and
`<species>.<assembly>.ncrna.fa.gz` pair, then writes the existing raw, split,
evaluation, and statistics formats.

`rnamining train-species` trains only the explicitly selected species from the
prepared training split and writes its existing `<species>.pkl` model format.
The original `prepare-data` and `train` commands remain available unchanged.

## Fix ambiguous nucleotides in trinucleotide feature extraction

The trinucleotide counter could fail with `local variable 'first' referenced before assignment` when a triplet contained an unsupported nucleotide such as `N`. If the variable had been assigned while processing an earlier triplet, its stale value could instead be reused and produce an incorrect count.

The counter now validates all three bases before converting them to array indices. Triplets composed entirely of `A`, `C`, `G`, or `T` continue to be counted normally, while triplets containing ambiguous or unsupported nucleotides are skipped.
