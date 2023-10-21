# import os
import json as json
import dataclasses
import pandas as pd
from biblelib.word import BCVWPID, BCVID
from greek_normalisation.utils import nfkc, strip_accents
from greek_normalisation.normalise import Normaliser
import diff_match_patch as dmp_module


@dataclasses.dataclass
class Word:
    identifier: str
    alt_id: str
    text: str
    strongs: str
    gloss: str
    gloss2: str
    pos: str
    morph: str

@dataclasses.dataclass
class Verse:
    identifier: str
    book: str
    chapter: str
    verse: str
    usfm: str
    # the str is the Word.identifier so we can sort to ensure word order
    words: dict[str, Word] = dataclasses.field(default_factory=list)


def load_bsbgnt_lines():
    print("Loading BSBGNT")
    return_lines = {}
    previous_verse_id = ""
    current_verse_id = ""
    words = {}
    with open('C:/git/Clear/internal-Alignments/data/bsb/BGNT-BSB_source.tsv', 'r', encoding='utf-8') as infile:
        lines = infile.readlines()
        for line in lines:
            if line.startswith('identifier'):
                continue
            line = line.rstrip('\n')
            # split the line on tabs and stitch things together
            cols = line.split('\t')
            bcv = BCVWPID(cols[0])
            # create the word object
            word = Word(cols[0], cols[1], cols[2], cols[3], cols[4], cols[5], cols[6], cols[7])
            # remove '*' and '|' from word.text
            word.text = word.text.replace('*', '').replace('|', '')
            words[word.identifier] = word
            # create the verse object if it doesn't exist
            current_verse_id = bcv.book_ID + bcv.chapter_ID + bcv.verse_ID
            if previous_verse_id != current_verse_id:
                # we need to dump verse info.
                return_lines[current_verse_id] = Verse(current_verse_id, bcv.book_ID, bcv.chapter_ID, bcv.verse_ID, bcv.to_usfm(), words)
                previous_verse_id = current_verse_id
                words = {}

        bcv = BCVID(current_verse_id)
        return_lines[current_verse_id] = Verse(current_verse_id, bcv.book_ID, bcv.chapter_ID, bcv.verse_ID, bcv.to_usfm(), words)

    return return_lines

def load_sblgnt_lines():
    print("Loading SBLGNT")
    return_lines = {}
    previous_verse_id = ""
    current_verse_id = ""
    words = {}
    sblgnt_tsv = 'C:/git/Clear/macula-greek/SBLGNT/tsv/macula-greek-SBLGNT.tsv'
    df = pd.read_csv(sblgnt_tsv, sep='\t', header=0, dtype=str, encoding='utf-8', keep_default_na=False)
    for row in df.index:
        # remove initial 'n' from identifier
        identifier = df['xml:id'][row][1:]
        bcv = BCVWPID(identifier)
        # create the word object
        # id, alt-id, text, strongs, gloss, gloss2, pos, morph
        word = Word(identifier, "", df['text'][row], df['strong'][row], df['gloss'][row], df['english'][row],
                    df['class'][row], df['morph'][row])
        words[word.identifier] = word
        # create the verse object if it doesn't exist
        current_verse_id = bcv.book_ID + bcv.chapter_ID + bcv.verse_ID
        if previous_verse_id != current_verse_id:
            # we need to dump verse info.
            return_lines[current_verse_id] = Verse(current_verse_id, bcv.book_ID, bcv.chapter_ID, bcv.verse_ID, bcv.to_usfm(), words)
            previous_verse_id = current_verse_id
            words = {}

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
    dmp.diff_cleanupSemantic(diffs)
    return diffs

# need to load in SBLGNT in a lines format
# both bsbgnt_lines and sblgnt_lines are dict[Verse.identifier, Verse] so verses can be sorted properly
# bsbgnt loads from the 'source' text alignment tab-delimited file
bsbgnt_lines = load_bsbgnt_lines()
# sblgnt loads from the Macula Greek SBLGNT tsv file
sblgnt_lines = load_sblgnt_lines()

# get keys from bsbgnt_lines and sort
# because I don't know if dicts in python preserve order
bsbgnt_keys = list(bsbgnt_lines.keys())
bsbgnt_keys.sort()

verse_match_count = 0
verse_difference_count = 0

for bsb_verse in bsbgnt_keys:
    bcv = BCVID(bsb_verse)
    print(f"Current: {bcv.to_usfm()}, {bsb_verse}")
    # we have the same verse in SBLGNT?
    if sblgnt_lines.__contains__(bsb_verse):
        bsbgnt_verse_text = get_verse_text(bsbgnt_lines[bsb_verse])
        sblgnt_verse_text = get_verse_text(sblgnt_lines[bsb_verse])

        # if the verses are exact, we skip everything and log it
        if bsbgnt_verse_text == sblgnt_verse_text:
            print("Exact match for " + bsb_verse)
            verse_match_count += 1
            continue

        # do the diff
        diff = diff_wordMode(bsbgnt_verse_text, sblgnt_verse_text)
        verse_difference_count += 1
        print(diff)
    else:
        print(f"BSB {bsb_verse} not in SBLGNT")

print(f"Verse match count: {verse_match_count}")
print(f"Verse difference count: {verse_difference_count}")
