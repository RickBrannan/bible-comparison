# bible-comparison

Python code that uses [a customized version](https://github.com/google/diff-match-patch/wiki/Line-or-Word-Diffs) of [Google's `diff-match-patch`](https://github.com/google/diff-match-patch) to compare bible versions and determine word differences

This was developed to compare text editions of the Greek New Testament, on a verse-by-verse basis, at the word level and determine differences.

Note that the algorithm used in `diff-match-patch` essentially states the minimal set of changes to be made to the `source` text to convert it into the `compare` text.

This is slightly different than variation units one finds in a standard Greek NT, where there are additions, omissions, differences, and word order differences. The output here is stated solely in terms of plusses (additions) and minuses (omissions).

That said, `diff-match-patch` is easily accessible, well-proven, and provides a easy way to compute differences between two similar strings.

## History

Note that this code was originally developed for other purposes (specifically, migrating the basis of textual alignments from one Greek edition to another), but I found the basics useful so wanted to make a stripped-down version available for others.

## License

This work (`compare_verses.py`) is licensed under the [MIT license](LICENSE).

* Google's diff-match-patch is used under the Apache License 2.0. The copy in this repo has been modified according to [these instructions](https://github.com/google/diff-match-patch/wiki/Line-or-Word-Diffs).
* SBLGNT is available under a CC-BY 4.0 license from [Logos Bible Software](https://github.com/LogosBible/SBLGNT).
* Nestle 1904 is available from [Clear Bible (Biblica)](https://github.com/Clear-Bible/macula-greek/Nestle1904).

# input format

The input format is a simple tab-delimited file that uses an encoded verse number (supported by biblelib) and Greek text.

```
Verse	Words
40001001	Βίβλος γενέσεως Ἰησοῦ χριστοῦ υἱοῦ Δαυὶδ υἱοῦ Ἀβραάμ.
40001002	Ἀβραὰμ ἐγέννησεν τὸν Ἰσαάκ, Ἰσαὰκ δὲ ἐγέννησεν τὸν Ἰακώβ, Ἰακὼβ δὲ ἐγέννησεν τὸν Ἰούδαν καὶ τοὺς ἀδελφοὺς αὐτοῦ,
40001003	Ἰούδας δὲ ἐγέννησεν τὸν Φαρὲς καὶ τὸν Ζάρα ἐκ τῆς Θαμάρ, Φαρὲς δὲ ἐγέννησεν τὸν Ἑσρώμ, Ἑσρὼμ δὲ ἐγέννησεν τὸν Ἀράμ,
```

The `data/tsv/` folder provides two examples:

* Nestle 1904, sourced from [Clear-Bible's Macula Greek project](https://github.com/Clear-Bible/macula-greek) and in the public domain
* SBLGNT, sourced from [Clear-Bible's Macula Greek project](https://github.com/Clear-Bible/macula-greek) and [CC-BY licensed by Logos Bible Software](https://github.com/LogosBible/SBLGNT)

# output format

For this we're simply dumping the output from diff-match-patch to STDOUT. It looks like this:

```
Current: REV 22:5 (66022005)
[(0, 'και νυξ οὐκ ἐσται ἐτι και οὐκ ἐχουσιν χρειαν φωτος λυχνου και '), (-1, 'φωτος '), (1, 'φως '), (0, 'ἡλιου ὁτι κυριος ὁ θεος φωτισει ἐπ αὐτους και βασιλευσουσιν εἰς τους αἰωνας των αἰωνων')]
Current: REV 22:6 (66022006)
Exact match for 66022006
Current: REV 22:7 (66022007)
Exact match for 66022007
Current: REV 22:8 (66022008)
[(0, 'κἀγω '), (-1, 'ἰωανης '), (1, 'ἰωαννης '), (0, 'ὁ ἀκουων και βλεπων ταυτα και ὁτε ἠκουσα και ἐβλεψα ἐπεσα προσκυνησαι ἐμπροσθεν των ποδων του ἀγγελου του δεικνυοντος μοι ταυτα')]
```

In this view:

* `0` indicates words in common between the `source` and `compare` editions.
* `-1` indicates words in the `source` edition but not in the `compare` edition.
* `1` indicates words in the `compare` edition but not in the `source` edition.

Note that the compared texts have been normalized for case (lower-case) and accents have been removed.

