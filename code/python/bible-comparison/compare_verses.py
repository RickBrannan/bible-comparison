import re
import dataclasses
from biblelib.word import BCVID
from greek_normalisation.utils import nfkc, strip_accents
import diff_match_patch as dmp_module


@dataclasses.dataclass
class Word:
    identifier: str
    text: str

@dataclasses.dataclass
class Verse:
    identifier: str
    book: str
    chapter: str
    verse: str
    usfm: str
    # the str is the Word.identifier so we can sort to ensure word order
    words: dict[str, Word] = dataclasses.field(default_factory=list)


def load_lines(edition, edition_file_name):
    print(f"Loading {edition}")
    return_lines = {}
    previous_verse_id = "40001001"
    current_verse_id = ""
    words = {}
    with open(f'{git_dir}data/tsv/{edition_file_name}', 'r', encoding='utf-8') as infile:
        lines = infile.readlines()
        for line in lines:
            if line.startswith('Verse'):
                continue
            line = line.rstrip('\n')
            # split the line on tabs and stitch things together
            cols = line.split('\t')
            bcv = BCVID(cols[0])
            # create the verse object if it doesn't exist
            current_verse_id = bcv.book_ID + bcv.chapter_ID + bcv.verse_ID
            if previous_verse_id != current_verse_id:
                # we need to dump verse info.
                previous_bcv = BCVID(previous_verse_id)
                return_lines[previous_verse_id] = Verse(previous_verse_id, previous_bcv.book_ID, previous_bcv.chapter_ID,
                                                        previous_bcv.verse_ID, previous_bcv.to_usfm(), words)
                previous_verse_id = current_verse_id
                words = {}

            # create the word object
            # split on space
            verse_words = cols[1].split(' ')
            word_in_verse = 1
            for current_word in verse_words:
                # zeropad word_in_verse with leading zeros
                word_id = current_verse_id + str(word_in_verse).zfill(3)
                # remove non-word chars from word.text. option to ignore case, remove accents, etc.?
                word = Word(word_id, current_word)
                word.text = re.sub(r'\W+', '', word.text)
                words[word.identifier] = word
                word_in_verse += 1

        bcv = BCVID(current_verse_id)
        return_lines[current_verse_id] = Verse(current_verse_id, bcv.book_ID, bcv.chapter_ID, bcv.verse_ID, bcv.to_usfm(), words)

    return return_lines


def get_verse_text(verse):
    return_text = ""
    # case-insensitive? strip accents?
    for word in verse.words:
        return_text += strip_accents(verse.words[word].text) + " "
    return nfkc(return_text.rstrip().lower())

# added RWB 2023-10-21 for word-level diffs
def diff_wordMode(text1, text2):
    dmp = dmp_module.diff_match_patch()
    initial_diff = dmp.diff_linesToWords(text1, text2)
    wordText1 = initial_diff[0]
    wordText2 = initial_diff[1]
    lineArray = initial_diff[2]
    diffs = dmp.diff_main(wordText1, wordText2, False)
    dmp.diff_charsToLines(diffs, lineArray)
    # diff_cleanupSemantic() causes issues when comparing word-level
    # dmp.diff_cleanupSemantic(diffs)
    return diffs


# some globals
git_dir = "C:/git/RickBrannan/bible-comparison/"

# need to load editions in a lines format
# both source_gnt_lines and compare_gnt_lines are dict[Verse.identifier, Verse] so verses can be sorted properly
source_edition = "n1904"
compare_edition = "sblgnt"
source_gnt_lines = load_lines(source_edition, f"{source_edition}-verses.tsv")
compare_gnt_lines = load_lines(compare_edition, f"{compare_edition}-verses.tsv")

# get keys from source_gnt_lines and sort
# because I don't know if dicts in python preserve order
source_gnt_keys = list(source_gnt_lines.keys())
source_gnt_keys.sort()

# some counters
verse_match_count = 0
verse_difference_count = 0

for source_gnt_verse in source_gnt_keys:
    bcv = BCVID(source_gnt_verse)
    print(f"Current: {bcv.to_usfm()} ({source_gnt_verse})")
    # we have the same verse in SBLGNT?
    if compare_gnt_lines.__contains__(source_gnt_verse):
        source_gnt_verse_text = get_verse_text(source_gnt_lines[source_gnt_verse])
        compare_gnt_verse_text = get_verse_text(compare_gnt_lines[source_gnt_verse])

        # if the verses are exact, we skip everything and log it
        if source_gnt_verse_text == compare_gnt_verse_text:
            print("Exact match for " + source_gnt_verse)
            verse_match_count += 1
            continue

        # do the diff
        #  0 == text that matches between editions
        # -1 == text that is in source_edition but not compare_edition
        #  1 == text that is in compare_edition but not source_edition
        diff = diff_wordMode(source_gnt_verse_text, compare_gnt_verse_text)
        verse_difference_count += 1
        print(diff)
    else:
        print(f"{source_edition} {bcv.to_usfm()} ({source_gnt_verse}) not in {compare_edition}")

# we also need to find the compare_edition verses that are not in source_edition (e.g. 3Jn 1:15)
for compare_verse in compare_gnt_lines:
    if not source_gnt_lines.__contains__(compare_verse):
        bcv = BCVID(compare_verse)
        print(f"{compare_edition} {bcv.to_usfm()} ({compare_edition}) not in {source_edition}")

print(f"Verse match count: {verse_match_count}")
print(f"Verse difference count: {verse_difference_count}")
