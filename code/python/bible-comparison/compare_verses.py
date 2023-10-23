# import os
import re
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
    previous_verse_id = "41001001"
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
            word = Word(cols[0], cols[1], cols[2], cols[3], cols[4], cols[5], cols[6], cols[7])
            # remove non-word chars from word.text
            word.text = re.sub(r'\W+', '', word.text)
            # word.text = word.text.replace('*', '').replace('|', '')
            words[word.identifier] = word

        bcv = BCVID(current_verse_id)
        return_lines[current_verse_id] = Verse(current_verse_id, bcv.book_ID, bcv.chapter_ID, bcv.verse_ID, bcv.to_usfm(), words)

    return return_lines

def load_sblgnt_lines():
    print("Loading SBLGNT")
    return_lines = {}
    previous_verse_id = "41001001"
    current_verse_id = ""
    words = {}
    sblgnt_tsv = 'C:/git/Clear/macula-greek/SBLGNT/tsv/macula-greek-SBLGNT.tsv'
    df = pd.read_csv(sblgnt_tsv, sep='\t', header=0, dtype=str, encoding='utf-8', keep_default_na=False)
    for row in df.index:
        # remove initial 'n' from identifier
        identifier = df['xml:id'][row][1:]
        bcv = BCVWPID(identifier)
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
        # id, alt-id, text, strongs, gloss, gloss2, pos, morph
        word = Word(identifier, "", df['text'][row], df['strong'][row], df['gloss'][row], df['english'][row],
                    df['class'][row], df['morph'][row])
        # remove non-word chars from word.text
        word.text = re.sub(r'\W+', '', word.text)
        words[word.identifier] = word

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
    # does this cause problems with splitting variations within words? (e.g. Mt 14:27; 15:30)?
    # dmp.diff_cleanupSemantic(diffs)
    return diffs


def get_words_and_ids(gnt, gnt_verse, gnt_count):
    return_words_and_ids = {}
    for word in gnt:
        gnt_word = list(gnt_verse.words.items())[gnt_count][1]
        # regex to remove non-word chars from gnt_word.text
        gnt_word_text = re.sub(r'\W+', '', gnt_word.text)
        return_words_and_ids[gnt_word_text] = gnt_word.identifier
        gnt_count += 1
    return return_words_and_ids


def map_variant_verse(diff, bsbgnt_verse, sblgnt_verse, map_bsbgnt_to_sblgnt):
    bsbgnt_count = 0
    sblgnt_count = 0
    bsbgnt_ids = list(bsbgnt_verse.words.keys())
    sblgnt_ids = list(sblgnt_verse.words.keys())

    diff_item_count = 0
    bool_skip = False

    for item in diff:
        if item[0] == 0:
            # same for both verses
            for word in item[1].strip().split(' '):
                map_bsbgnt_to_sblgnt[bsbgnt_ids[bsbgnt_count]] = sblgnt_ids[sblgnt_count]
                bsbgnt_count += 1
                sblgnt_count += 1
            bool_skip = False
        # need to determine if -1 and 1 are a paired instance, or it is marking presence vs. absence
        elif (item[0] == -1) and (len(diff) == (diff_item_count + 1)):
            # this is a bsb addition at end of verse. there is nothing to map it to in sblgnt.
            bsb = item[1].strip().split(' ')
            for word in bsb:
                # map to nothing in SBLGNT
                map_bsbgnt_to_sblgnt[bsbgnt_ids[bsbgnt_count]] = ""
                bsbgnt_count += 1
            sblgnt_count += 1
            bool_skip == False
        elif (item[0] == -1 and diff[diff_item_count + 1][0] == 1) and bool_skip == False:
            # paired?
            # trim whitespace from item[1]
            bsb = item[1].strip().split(' ')
            sbl = diff[diff_item_count + 1][1].strip().split(' ')

            if (len(bsb) == 1) and (len(sbl) == 1):
                map_bsbgnt_to_sblgnt[bsbgnt_ids[bsbgnt_count]] = sblgnt_ids[sblgnt_count]
                bsbgnt_count += 1
                sblgnt_count += 1
            elif (len(bsb) == 1) and (len(sbl) > 1):
                # one-to-many mapping
                sbl_ids = []
                for word in sbl:
                    sbl_ids.append(sblgnt_ids[sblgnt_count])
                    sblgnt_count += 1
                map_bsbgnt_to_sblgnt[bsbgnt_ids[bsbgnt_count]] = sbl_ids
                bsbgnt_count += 1
            elif (len(sbl) == 1) and (len(bsb) > 1):
                # many-to-one mapping. Unsure how to accomplish that in present model.
                for word in bsb:
                    map_bsbgnt_to_sblgnt[bsbgnt_ids[bsbgnt_count]] = sblgnt_ids[sblgnt_count]
                    bsbgnt_count += 1
                sblgnt_count += 1
            elif len(sbl) == len(bsb):
                # if the length is equivalent, then we should be able to sort the words
                # alphabetically (dict[word.text, word.identifier] and map most (all?)
                # of them correctly based on word matching
                bsb_words_and_ids = get_words_and_ids(bsb, bsbgnt_verse, bsbgnt_count)
                sbl_words_and_ids = get_words_and_ids(sbl, sblgnt_verse, sblgnt_count)
                # sort the words
                bsb_words = list(bsb_words_and_ids.keys())
                bsb_words.sort()
                sbl_words = list(sbl_words_and_ids.keys())
                sbl_words.sort()
                # map the words
                var_word_count = 0
                for word in bsb_words:
                    sbl_var_word = list(sbl_words_and_ids.items())[var_word_count][0]
                    map_bsbgnt_to_sblgnt[bsb_words_and_ids[word]] = sbl_words_and_ids[sbl_var_word]
                    var_word_count += 1
                    bsbgnt_count += 1
                    sblgnt_count += 1
            # elif counts are both greater than one but unequal. likely some word-matching gymnastics
            else:
                print("Huh?")
            bool_skip = True
        else:
            # huh?
            bool_skip = False
        diff_item_count += 1

    return map_bsbgnt_to_sblgnt




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
# this is a word-level map
map_bsbgnt_to_sblgnt = {}


for bsb_verse in bsbgnt_keys:
    bcv = BCVID(bsb_verse)
    # we have the same verse in SBLGNT?
    if sblgnt_lines.__contains__(bsb_verse):
        bsbgnt_verse_text = get_verse_text(bsbgnt_lines[bsb_verse])
        sblgnt_verse_text = get_verse_text(sblgnt_lines[bsb_verse])

        # if the verses are exact, we skip everything and log it
        if bsbgnt_verse_text == sblgnt_verse_text:
            print("Exact match for " + bsb_verse)
            verse_match_count += 1
            # update word map
            for word in bsbgnt_lines[bsb_verse].words:
                # same verse, same number of words, equality between verses, means ids are the same.
                map_bsbgnt_to_sblgnt[word] = word
            continue

        # do the diff
        diff = diff_wordMode(bsbgnt_verse_text, sblgnt_verse_text)
        verse_difference_count += 1
        print(f"Current: {bcv.to_usfm()} ({bsb_verse})")
        print(diff)
        map_bsbgnt_to_sblgnt = map_variant_verse(diff, bsbgnt_lines[bsb_verse], sblgnt_lines[bsb_verse],
                                                 map_bsbgnt_to_sblgnt)
        # print(diff)
    else:
        print(f"BSB {bcv.to_usfm()} ({bsb_verse}) not in SBLGNT")

# we also need to find the SBLGNT verses that are not in BSBGNT (e.g. 3Jn 1:15)

print(f"Verse match count: {verse_match_count}")
print(f"Verse difference count: {verse_difference_count}")
