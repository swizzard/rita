from collections import Counter

from requests_html import HTMLSession
import spacy
from wordcloud import WordCloud


SPACY = spacy.load('en_core_web_sm')
ROOT = 'https://dailymail.co.uk/home/search.html'
SESSION = HTMLSession()


class OutOfArticles(Exception):
    pass


def params(offset):
    return {
        'offset': offset,
        'size': 50,
        'sel': 'site',
        'searchPhrase': 'Rita Ora',
        'sort': 'recent',
        'channel': 'tvshowbiz',
        'type': 'article',
        'days': 'all'
    }


def req(offset):
    return SESSION.get(ROOT, params=params(offset))


def titles(res):
    ts = res.html.find('.sch-res-title a')
    if ts:
        for t in ts:
            title = t.text
            if 'Rita Ora' in title:
                yield title
    else:
        raise OutOfArticles


def filter_by_pos(txt, pos):
    for token in SPACY(txt):
        if token.pos_ == pos:
            yield token.text


def page(offset):
    res = req(offset)
    for title in titles(res):
        yield title


def postprocess(counter):
    tot = sum(counter.values())
    return {k: v / tot for k, v in counter.items()}


def get():
    offset = 0
    inc_by = 50
    while True:
        try:
            for t in page(offset):
                yield SPACY(t)
        except OutOfArticles:
            break
        else:
            offset += inc_by


def get_pos(pos, sp):
    for token in sp:
        if token.pos_ == pos:
            yield token.text


def pos_freqs(pos='ADJ'):
    counter = Counter()
    for t in get():
        counter.update(get_pos(pos, t))
    return postprocess(counter)


def heads():
    counter = Counter()
    for t in get():
        for tk in t:
            if tk.dep_ == 'ROOT' and tk.left_edge.text == 'Rita':
                counter.update([tk.text])
    return counter


def to_wc(freqs, dest):
    wc = WordCloud()
    wc.fit_words(freqs)
    wc.to_file(dest)
