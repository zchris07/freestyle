"""Build the rhyme banks and write them into index.html: BANK (1-syllable) and BANK2 (2-syllable).

A 1-syllable ("masculine") pure rhyme matches from the last vowel, which carries the stress, to the end:
  time T [AY1 M]   climb K L [AY1 M]   sublime S AH0 B L [AY1 M]
(monosyllables, plus longer words stressed on their final syllable). Common function words are left out.

A 2-syllable ("feminine") pure rhyme: two words whose sounds match from the stressed vowel of the
second-to-last syllable to the end, while the consonants right before that vowel differ.
  fiction  F [IH1 K SH AH0 N]     autumn  [AO1 T AH0 M]
  diction  D [IH1 K SH AH0 N]     bottom B [AA1 T AH0 M]   (AO = AA under the cot-caught merger)

Pipeline:
  1. CMU Pronouncing Dictionary -> first pronunciation of every plain lowercase word.
  2. 1-syllable: the last vowel has primary stress (or it is the only vowel).
     2-syllable: primary stress on the second-to-last vowel, last vowel unstressed.
  3. Rhyme key = phones from that stressed vowel to the end, normalized for how people actually hear them:
     stressed AO -> AA except before R (cot-caught merger; "corner" stays apart from "partner"),
     unstressed AH0/IH0/UH0 -> one schwa (cmudict writes "basket" with AH0 but "casket" with IH0).
  4. Keep real, common, clean words: a lowercase stem in the Hunspell en_US dictionary (drops names and
     inflected duplicates like "matters"), wordfreq Zipf >= MIN_ZIPF (MIN_ZIPF1 for 1-syllable), not on the
     LDNOOBW list or EXTRA_BLOCK (and not a STOP word for 1-syllable).
  5. Group by key. Inside a family keep one word per onset (the consonants before the stressed vowel), the
     most common one, so every pair is a true rhyme and never an identical one (diction/addiction, metal/medal).
  6. Families with enough words, best-known first, are written between the RHYME1 / RHYME2 markers in index.html.

Usage:  pip install wordfreq   then   python tools/build_rhymes.py
Downloads are cached in tools/.cache/.
"""
import os, re, sys, urllib.request
from collections import defaultdict
from wordfreq import zipf_frequency

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "tools", ".cache")
SOURCES = {
    "cmudict.dict": "https://raw.githubusercontent.com/cmusphinx/cmudict/master/cmudict.dict",
    "en_US.dic": "https://raw.githubusercontent.com/LibreOffice/dictionaries/master/en/en_US.dic",
    "badwords.txt": "https://raw.githubusercontent.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words/master/en",
}
# 2-syllable bank
MIN_ZIPF = 2.5      # ~1 use per 3 million words and up; families list their most common words first
MIN_WORDS = 2       # a pair is enough for AABB-style groups; the app prefers bigger families for bigger groups
MAX_WORDS = 12      # words kept per family
MAX_FAMILIES = 800
# 1-syllable bank: more common words, bigger families
MIN_ZIPF1, MIN_WORDS1, MAX_WORDS1, MAX_FAMILIES1 = 3.1, 4, 16, 400
# words that pass every filter but read as names or are crude or not useful in a trainer
EXTRA_BLOCK = set("""harry terry jenny eddy jerry larry gary barry perry kerry sherry mary betty patty
peeing pissing erection whiting dildo condom""".split())
# function words: real rhymes, but useless as prompts
STOP = set("""the and but for nor yet with from into onto upon than then that this these those there here where when
what which who whom whose why how are was were been being have has had does did will would shall should can could
may might must not its his her hers him she they them their theirs our ours your yours you we me my mine us
off out over per via also just very such each much some any all both few own same too so if or as at by of to in on
is am be it an a i oh ah uh um yeah yes""".split())
# 1-syllable only: abbreviations, names and filler that the dictionary filters let through
EXTRA_BLOCK1 = set("""ab alt aw bob cal cam co cos cox dis ed en er gal gay gov ha hon hp hr id inc jay jun ken lee ma mac
mag mar max meg mi min mod non oi om op oz pa pm pol pr reg rem rep sec sim sis sol sup ta tam tat ted tom val wan wen
ya ye yep yup nah ugh he re xi mg pee em""".split())
SCHWA = {"AH0", "IH0", "UH0"}


def fetch(name):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        print("downloading", SOURCES[name])
        urllib.request.urlretrieve(SOURCES[name], path)
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()


def is_vowel(p):
    return p[-1].isdigit()


def key_from(phones, start):
    """(key, onset): the rhyme key from the stressed vowel at `start` to the end, normalized, and the consonants
    right before that vowel"""
    key = []
    for i in range(start, len(phones)):
        p = phones[i]
        if i == start:
            v = p[:-1]
            if v == "AO" and not (i + 1 < len(phones) and phones[i + 1] == "R"):
                v = "AA"
            key.append(v)
        elif p in SCHWA:
            key.append("AX")
        else:
            key.append(p.rstrip("012"))
    j = start
    while j > 0 and not is_vowel(phones[j - 1]):
        j -= 1
    return " ".join(key), " ".join(phones[j:start])


def rhyme_parts(phones):
    """2-syllable: (key, onset) for a word with stress on its second-to-last vowel, else None."""
    vi = [i for i, p in enumerate(phones) if is_vowel(p)]
    if len(vi) < 2:
        return None
    pen, last = vi[-2], vi[-1]
    if phones[pen][-1] != "1" or phones[last][-1] != "0":
        return None
    return key_from(phones, pen)


def rhyme_parts1(phones):
    """1-syllable: (key, onset) for a word whose last vowel carries the primary stress (or is its only vowel)."""
    vi = [i for i, p in enumerate(phones) if is_vowel(p)]
    if not vi:
        return None
    last = vi[-1]
    if len(vi) > 1 and phones[last][-1] != "1":
        return None
    return key_from(phones, last)


def families(fams, min_words, max_words, max_families):
    """one word per onset (the most common), families with >= min_words, best-known first"""
    out = []
    for key, items in fams.items():
        items.sort(reverse=True)
        seen, words = set(), []
        for z, w, onset in items:
            if onset in seen:
                continue
            seen.add(onset)
            words.append((z, w))
        if len(words) >= min_words:
            words = words[:max_words]
            score = sum(z for z, _ in words[:4]) / 4
            out.append((score, key, [w for _, w in words]))
    out.sort(reverse=True)
    return out[:max_families]


def write_block(html, marker, name, comment, out):
    body = "\n".join('"' + " ".join(ws) + '",' for _, _, ws in out)
    block = ("// " + marker + "-BEGIN generated by tools/build_rhymes.py, do not edit by hand\n// " + comment + "\n"
             "const " + name + "=[\n" + body + "\n].map(s=>s.split(\" \"));\n// " + marker + "-END")
    new, n = re.subn(r"// " + marker + r"-BEGIN.*?// " + marker + r"-END", lambda m: block, html, flags=re.S)
    if n != 1:
        sys.exit(marker + " markers not found in index.html")
    return new, body


def main():
    stems = {l.split("/")[0] for l in fetch("en_US.dic")[1:]}
    bad = {l.strip().lower() for l in fetch("badwords.txt") if l.strip()}
    fams, fams1 = defaultdict(list), defaultdict(list)
    for line in fetch("cmudict.dict"):
        line = line.split("#")[0].strip()
        if not line:
            continue
        word, *phones = line.split()
        if not re.fullmatch(r"[a-z]{2,9}", word) or word not in stems or word in bad or word in EXTRA_BLOCK:
            continue
        z = zipf_frequency(word, "en")
        if z < MIN_ZIPF:
            continue
        parts = rhyme_parts(phones) if len(word) >= 3 else None
        if parts:
            fams[parts[0]].append((z, word, parts[1]))
        parts1 = rhyme_parts1(phones)
        if parts1 and z >= MIN_ZIPF1 and word not in STOP and word not in EXTRA_BLOCK1:
            fams1[parts1[0]].append((z, word, parts1[1]))

    out = families(fams, MIN_WORDS, MAX_WORDS, MAX_FAMILIES)
    out1 = families(fams1, MIN_WORDS1, MAX_WORDS1, MAX_FAMILIES1)
    html_path = os.path.join(ROOT, "index.html")
    html = open(html_path, encoding="utf-8").read()
    html, body = write_block(html, "RHYME2", "BANK2", "2-syllable pure rhyme families (stress on the second-to-last syllable), best-known first", out)
    html, body1 = write_block(html, "RHYME1", "BANK", "1-syllable pure rhyme families (stress on the last syllable), best-known first", out1)
    with open(html_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)

    w1 = sum(len(ws) for _, _, ws in out1)
    print(f"BANK (1-syllable): {len(out1)} families, {w1} words, {len(body1) / 1024:.0f} KB")
    w2 = sum(len(ws) for _, _, ws in out)
    print(f"BANK2 (2-syllable): {len(out)} families, {w2} words, {len(body) / 1024:.0f} KB")
    find = lambda fams_out, w: next((k for _, k, ws in fams_out if w in ws), None)
    for fams_out, pairs in [(out, [("fiction", "friction"), ("autumn", "bottom")]), (out1, [("time", "climb"), ("night", "light"), ("cold", "gold")])]:
        for a, b in pairs:
            k = find(fams_out, a)
            print(f"  {a}/{b}: {'same family [' + k + ']' if k and k == find(fams_out, b) else 'NOT matched'}")


if __name__ == "__main__":
    main()
