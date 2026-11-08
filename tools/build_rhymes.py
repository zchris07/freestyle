"""Build the rhyme banks and write them into index.html: BANK (1-syllable) and BANK2 (2-syllable).

A 1-syllable pure rhyme matches from the word's only vowel to the end:
  time T [AY1 M]   climb K L [AY1 M]   rhyme R [AY1 M]
Only true one-syllable words go in (no "sublime" or "routine"), so the 1-syllable pool never deals a longer word.
Common function words are left out.

A 2-syllable ("feminine") pure rhyme: two words whose sounds match from the stressed vowel of the
second-to-last syllable to the end, while the consonants right before that vowel differ.
  fiction  F [IH1 K SH AH0 N]     autumn  [AO1 T AH0 M]
  diction  D [IH1 K SH AH0 N]     bottom B [AA1 T AH0 M]   (AO = AA under the cot-caught merger)

Pipeline:
  1. CMU Pronouncing Dictionary -> first pronunciation of every plain lowercase word.
  2. 1-syllable: exactly one vowel.
     2-syllable: primary stress on the second-to-last vowel, last vowel unstressed.
  3. Rhyme key = phones from that stressed vowel to the end, normalized for how people actually hear them:
     stressed AO -> AA except before R (cot-caught merger; "corner" stays apart from "partner"),
     unstressed AH0/IH0/UH0 -> one schwa (cmudict writes "basket" with AH0 but "casket" with IH0).
  4. Keep real, common, clean words: a lowercase stem in the Hunspell en_US dictionary (drops names and
     inflected duplicates like "matters"), wordfreq Zipf >= MIN_ZIPF (MIN_ZIPF1 for 1-syllable), not on the
     LDNOOBW list or EXTRA_BLOCK (and not a STOP word for 1-syllable).
  5. Group by key. Inside a family keep one word per onset (the consonants that start the stressed syllable), the
     most common one, so every pair is a true rhyme and never an identical one (diction/addiction, metal/medal,
     circle/encircle, courage/encourage, inherent/adherent, patient/impatient). A word that is a common prefix plus
     another word of its family (another/other, enable/able, disorder/order) is also dropped for the commoner one.
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
MIN_ZIPF = 3.25     # ~1.8 uses per million words and up (raised from 2.5 on 2026-11-08: no sarcoma, henna, larval...)
MIN_WORDS = 2       # a pair is enough for AABB-style groups; the app prefers bigger families for bigger groups
MAX_WORDS = 12      # words kept per family
MAX_FAMILIES = 800
# 1-syllable bank: more common words, bigger families
MIN_ZIPF1, MIN_WORDS1, MAX_WORDS1, MAX_FAMILIES1 = 3.1, 3, 16, 400
# words that pass every filter but read as names or are crude or not useful in a trainer
EXTRA_BLOCK = set("""harry terry jenny eddy jerry larry gary barry perry kerry sherry mary betty patty
peeing pissing erection whiting dildo condom""".split())
# too obscure, technical or bookish for a freestyle prompt, though common enough in text (2026-11-08, Chris asked:
# "apostolic, sarcoma, henna, senna, larval, fauna, theta, claimant"): medical, scientific, legal, church and Latin
# words, surnames and archaic ones
EXTRA_BLOCK |= set("""fauna theta claimant apostolic sarcoma henna senna larval abbot adherence amino ante appellate
appraisal aquatic arbor archival assay bowman chandler cleric coercion communion concerted cortex curator cutler deacon
derrick dharma distal divergent dominion draper dyer eclectic enamel equator feral fetal fetus feudal focal fodder
fungal gamma glacial harmonic hector hepatitis herring hydraulic lama lattice laurel levy libel liter lymphoma maxi
mercer meta midi morrow mortar muster myrtle nasal natal neural newton oceanic papal para parasitic parry penal
periodic plasma plural poly porous precursor primer prism pursuant quasi quota recital rector referral renal retrieval
rotor sawyer sclerosis serum sigma sinus sporadic spatial sterile sturgeon subpoena surrey surveyor systemic tandem
tanner tariff thatcher theorem tidal treatise treble tribunal tucker vaginal vector vicar viola vortex wally whaling
wicket willy apostle ascension archaic chassis cedar communal connector corrosion directive erosion extortion flora
floral genetics granite highland hoover kaiser manila marrow mosaic pharaoh pious prairie solace stature usher""".split())
# function words: real rhymes, but useless as prompts
STOP = set("""the and but for nor yet with from into onto upon than then that this these those there here where when
what which who whom whose why how are was were been being have has had does did will would shall should can could
may might must not its his her hers him she they them their theirs our ours your yours you we me my mine us
off out over per via also just very such each much some any all both few own same too so if or as at by of to in on
is am be it an a i oh ah uh um yeah yes""".split())
# 1-syllable only: abbreviations, names and filler that the dictionary filters let through
EXTRA_BLOCK1 = set("""ab alt aw bob cal cam co cos cox dis ed en er gal gay gov ha hon hp hr id inc jay jun ken lee ma mac
mag mar max meg mi min mod non oi om op oz pa pm pol pr reg rem rep sec sim sis sol sup ta tam tat ted tom val wan wen
ya ye yep yup nah ugh he re xi mg pee em
aft basque brig burr cad cert croft dirk duff dyke fife firth fob git grange hast hind lea leach ling mead moi moot oft
quid rook shire squire tome tong tort tram truss weir whence thine thrice fritz ca""".split())
# always in (Chris's request): skip the dictionary, frequency and blocklist filters, and always keep their place in
# their rhyme family (they win their onset slot, so "cum" stands in for "come" and "thot" for "thought").
# A pronunciation is given for words cmudict lacks.
ALLOW = {"fuck": None, "bitch": None, "shit": None, "pussy": None, "dick": None, "hoe": None, "thot": "TH AA1 T",
         "ass": None, "slut": None, "glock": None, "tits": None, "cum": None}
SCHWA = {"AH0", "IH0", "UH0"}
# consonant clusters that can begin an English syllable (besides any single consonant other than NG); used to find
# where the stressed syllable really starts inside a word (maximal onset), so "encircle" (en-cir-cle) has the same
# onset as "circle" and the two are never paired as a rhyme
CLUSTERS = set(tuple(c.split()) for c in (
    "P L,P R,B L,B R,T R,D R,K L,K R,G L,G R,F L,F R,TH R,SH R,T W,D W,K W,G W,"
    "S P,S T,S K,S M,S N,S L,S W,S F,S P L,S P R,S T R,S K R,S K W,S K L,P Y,B Y,F Y,K Y,M Y,V Y,HH Y").split(","))


# A word that is another word of its family with a whole extra syllable in front is the same rhyme with a prefix on
# it (antarctic/arctic, another/other, enable/able, disorder/order, whatever/ever): only the more common of the two is
# kept. The front part has to hold a vowel; consonants alone make a real rhyme (brother/other, thunder/under).
def prefixed(a, b):
    """True if one of the two words is the other with an extra syllable (letters including a vowel) in front"""
    for x, y in ((a, b), (b, a)):
        if len(x) > len(y) >= 2 and x.endswith(y) and any(ch in "aeiouy" for ch in x[:len(x) - len(y)]):
            return True
    return False


def syllable_onset(cons, word_start):
    """the consonants that start the stressed syllable: a word-initial cluster entirely; inside a word, the longest
    final run that can begin a syllable (the rest closes the syllable before)"""
    if word_start or not cons:
        return cons
    for n in range(len(cons), 0, -1):
        tail = tuple(cons[-n:])
        if (n == 1 and tail[0] != "NG") or tail in CLUSTERS:
            return list(tail)
    return []


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
    """(key, onset): the rhyme key from the stressed vowel at `start` to the end, normalized, and the onset of the
    stressed syllable (see syllable_onset)"""
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
    return " ".join(key), " ".join(syllable_onset(phones[j:start], j == 0))


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
    """1-syllable: (key, onset) for a word with exactly one vowel, else None."""
    vi = [i for i, p in enumerate(phones) if is_vowel(p)]
    if len(vi) != 1:
        return None
    return key_from(phones, vi[0])


def families(fams, min_words, max_words, max_families, prefix_rule=False):
    """one word per onset (the most common; an ALLOW word always wins its onset), families with >= min_words,
    best-known first; ALLOW words are always kept"""
    out = []
    for key, items in fams.items():
        items.sort(key=lambda x: (x[1] in ALLOW, x), reverse=True)
        seen, words = set(), []
        for z, w, onset in items:
            if onset in seen or (prefix_rule and any(prefixed(w, k) for _, k in words)):
                continue
            seen.add(onset)
            words.append((z, w))
        need = 2 if any(w in ALLOW for _, w in words) else min_words   # a family with a requested word stays
        if len(words) >= need:
            words.sort(reverse=True)
            forced = [x for x in words[max_words:] if x[1] in ALLOW]
            words = words[:max_words - len(forced)] + forced if forced else words[:max_words]
            words.sort(reverse=True)
            score = sum(z for z, _ in words[:4]) / 4
            # ALLOW words go first, so they are always inside the window of best-known words a session deals from
            words.sort(key=lambda x: x[1] not in ALLOW)
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
    lines = fetch("cmudict.dict") + [w + " " + pr for w, pr in ALLOW.items() if pr]
    for line in lines:
        line = line.split("#")[0].strip()
        if not line:
            continue
        word, *phones = line.split()
        allow = word in ALLOW
        if not allow and (not re.fullmatch(r"[a-z]{2,9}", word) or word not in stems or word in bad or word in EXTRA_BLOCK):
            continue
        z = zipf_frequency(word, "en")
        if z < min(MIN_ZIPF, MIN_ZIPF1) and not allow:
            continue
        parts = rhyme_parts(phones) if len(word) >= 3 and (z >= MIN_ZIPF or allow) else None   # 2-syllable floor
        if parts:
            fams[parts[0]].append((z, word, parts[1]))
        parts1 = rhyme_parts1(phones)
        if parts1 and (allow or (z >= MIN_ZIPF1 and word not in STOP and word not in EXTRA_BLOCK1)):
            fams1[parts1[0]].append((z, word, parts1[1]))

    out = families(fams, MIN_WORDS, MAX_WORDS, MAX_FAMILIES, prefix_rule=True)   # 2-syllable only: in one syllable,
    # spelling vowels are silent (heart/art), so the extra-syllable test would misfire
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
