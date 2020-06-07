import re
import lxml

from bs4.element import Tag
from bs4.element import NavigableString


def clean_tags(page, tag):
    reTRIM = r'<{0}[^<>]*?>([\s\S]*?)<\/{0}>'
    return re.sub(reTRIM.format(tag), "", page, flags=re.I)

def clean_tags_hasprop(page, tag, prop):
    reTRIM = r'<{0}[^<>]+?{1}.*?>([\s\S]*?)<\/{0}>'
    return re.sub(reTRIM.format(tag,prop), "", page, flags=re.I)

def clean_tags_only(page, tag):
    reTRIM = r'<\/?{0}[^<>]*?>'
    return re.sub(reTRIM.format(tag), "", page, flags=re.I)

def clean_tags_exactly(page, tag):
    reTRIM = r'<\/?{0}>'
    return re.sub(reTRIM.format(tag), "", page, flags=re.I)

def pick_listed_tags(page, tag):
    res = []
    doc = lxml.html.fromstring(page)
    for bad in doc.xpath("//{}".format(tag)):
        if len(bad)>2:
            res.append(bad)
    return res

def clean_nolisted_tags(doc, tag):
    for bad in doc.xpath("//{}".format(tag)):
        if len(bad)<3:
            bad.drop_tag()
    return doc

def clean_ainp_tags(doc, tag):
    for bad in doc.xpath("//p/{}".format(tag)):
        bad.drop_tag()
    return doc

def gettext(item):
    if isinstance(item, Tag):
        res = re.sub('[\t ]+', ' ', item.get_text('\n','br/')).strip()
        res = re.sub('[\n]{2,}', '\n', res)
        if not res:
            res = item.select_one('a').get('href') if item.select_one('a') else ""
        return res
    else:
        res = re.sub('[\t ]+', ' ', item).strip()
        res = re.sub('[\n]{2,}', '\n', res)
        return res
        
def countchildren(line):
    items = line.children
    children = [item for item in items if isinstance(item, Tag) or (isinstance(item, NavigableString) and gettext(item))]
    return len(children)