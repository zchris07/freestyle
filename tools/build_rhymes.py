"""Build the 2-syllable pure rhyme bank (BANK2) and write it into index.html.

A 2-syllable ("feminine") pure rhyme: two words whose sounds match from the stressed vowel of the
second-to-last syllable to the end, while the consonants right before that vowel differ.
  fiction  F [IH1 K SH AH0 N]     autumn  [AO1 T AH0 M]
  diction  D [IH1 K SH AH0 N]     bottom B [AA1 T AH0 M]   (AO = AA under the cot-caught merger)

Pipeline:
  1. CMU Pronouncing Dictionary -> first pronunciation of every plain lowercase word.
  2. Keep words whose primary stress sits on the second-to-last vowel and whose last vowel is unstressed.
  3. Rhyme key = phones from that stressed vowel to the end, normalized for how people actually hear them:
     stressed AO -> AA except before R (cot-caught merger; "corner" stays apart from "partner"),
     unstressed AH0/IH0/UH0 -> one schwa (cmudict writes "basket" with AH0 but "casket" with IH0).
  4. Keep real, common, clean words: a lowercase stem in the Hunspell en_US dictionary (drops names and
     inflected duplicates like "matters"), wordfreq Zipf >= MIN_ZIPF, 3-9 letters, not on the LDNOOBW list
     or EXTRA_BLOCK.
  5. Group by key. Inside a family keep one word per onset (the consonants before the stressed vowel), the
     most common one, so every pair is a true rhyme and never an identical one (diction/addiction, metal/medal).
  6. Families with >= MIN_WORDS words, best-known first, are written between the RHYME2 markers in index.html.

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
MIN_ZIPF = 2.5      # ~1 use per 3 million words and up; families list their most common words first
MIN_WORDS = 2       # a pair is enough for AABB-style groups; the app prefers bigger families for bigger groups
MAX_WORDS = 12      # words kept per family
MAX_FAMILIES = 800
# words that pass every filter but read as names or are crude or not useful in a trainer
EXTRA_BLOCK = set("""harry terry jenny eddy jerry larry gary barry perry kerry sherry mary betty patty
peeing pissing erection whiting dildo condom""".split())
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


def rhyme_parts(phones):
    """(key, onset) for a word with stress on its second-to-last vowel, else None."""
    vi = [i for i, p in enumerate(phones) if is_vowel(p)]
    if len(vi) < 2:
        return None
    pen, last = vi[-2], vi[-1]
    if phones[pen][-1] != "1" or phones[last][-1] != "0":
        return None
    key = []
    for i in range(pen, len(phones)):
        p = phones[i]
        if i == pen:
            v = p[:-1]
            if v == "AO" and not (i + 1 < len(phones) and phones[i + 1] == "R"):
                v = "AA"
            key.append(v)
        elif p in SCHWA:
            key.append("AX")
        else:
            key.append(p.rstrip("012"))
    j = pen
    while j > 0 and not is_vowel(phones[j - 1]):
        j -= 1
    return " ".join(key), " ".join(phones[j:pen])


def main():
    stems = {l.split("/")[0] for l in fetch("en_US.dic")[1:]}
    bad = {l.strip().lower() for l in fetch("badwords.txt") if l.strip()}
    fams = defaultdict(list)
    for line in fetch("cmudict.dict"):
        line = line.split("#")[0].strip()
        if not line:
            continue
        word, *phones = line.split()
        if not re.fullmatch(r"[a-z]{3,9}", word) or word not in stems or word in bad or word in EXTRA_BLOCK:
            continue
        z = zipf_frequency(word, "en")
        if z < MIN_ZIPF:
            continue
        parts = rhyme_parts(phones)
        if parts:
            fams[parts[0]].append((z, word, parts[1]))

    out = []
    for key, items in fams.items():
        items.sort(reverse=True)
        seen, words = set(), []
        for z, w, onset in items:
            if onset in seen:
                continue
            seen.add(onset)
            words.append((z, w))
        if len(words) >= MIN_WORDS:
            words = words[:MAX_WORDS]
            score = sum(z for z, _ in words[:4]) / 4
            out.append((score, key, [w for _, w in words]))
    out.sort(reverse=True)
    out = out[:MAX_FAMILIES]

    body = "\n".join('"' + " ".join(ws) + '",' for _, _, ws in out)
    block = ("// RHYME2-BEGIN generated by tools/build_rhymes.py, do not edit by hand\n"
             "// 2-syllable pure rhyme families (stress on the second-to-last syllable), best-known first\n"
             "const BANK2=[\n" + body + "\n].map(s=>s.split(\" \"));\n// RHYME2-END")
    html_path = os.path.join(ROOT, "index.html")
    html = open(html_path, encoding="utf-8").read()
    new, n = re.subn(r"// RHYME2-BEGIN.*?// RHYME2-END", lambda m: block, html, flags=re.S)
    if n != 1:
        sys.exit("RHYME2 markers not found in index.html")
    with open(html_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)

    words = sum(len(ws) for _, _, ws in out)
    print(f"{len(out)} families, {words} words, {len(body) / 1024:.0f} KB")
    find = lambda w: next((k for _, k, ws in out if w in ws), None)
    for a, b in [("fiction", "friction"), ("autumn", "bottom")]:
        print(f"  {a}/{b}: {'same family [' + find(a) + ']' if find(a) and find(a) == find(b) else 'NOT matched'}")


if __name__ == "__main__":
    main()
