#!/bin/env python
#encoding=utf-8
import re
import lxml
import lxml.html
from lxml import etree
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
from bs4 import BeautifulSoup as Bs
from bs4.element import Tag
from bs4.element import NavigableString
from .tags_util import clean_tags_only, clean_tags_hasprop, clean_tags, clean_ainp_tags, gettext, countchildren
from .region import Region


class PageModel(object):
    def __init__(self, page, url = ""):
        try:
            assert type(page) is unicode
        # Python3
        except NameError:
            pass
        for tag in ['style','script','sup','noscript','form','cite']:
            page = clean_tags(page, tag)
        page = clean_tags_hasprop(page, "div", "(display:.?none|comment|measure)")
        page = clean_tags_hasprop(page, "tr", "display:.?none")
        page = clean_tags_only(page, "(span|section|font|em|i)")
        self.doc = lxml.html.fromstring(page)
        self.doc = clean_ainp_tags(self.doc, 'a')
        self.url = url
        self.region = Region(self.doc)
        self.impurity_threshold = 30
        self.impurity_threshold_min = 4
        self.anchor_ratio_limit = 0.3
        self.table_min_length = 2
        self.stripper = re.compile(r'\s+')
        self.key_length = 19
        self.min_key_len = 1
        

    def simi_table(self, region):
        candidates = region.xpath('.//*[contains(text(),":")]')
        parent_map = dict()
        for item in candidates:
            if len(item.text_content().split(':')[0].strip()) > self.key_length:
                continue
            parent_map.setdefault(item.getparent(), []).append(item)
        final_key = None
        max_len = 0
        tbody = None
        for key in parent_map:
            if len(parent_map[key]) > self.table_min_length and len(parent_map[key]) > max_len and key.tag not in ('tbody','table','aside'):
                final_key = key
                max_len = len(parent_map[key])
        if final_key is not None:
            tableitems = parent_map[final_key]
            if tableitems[1] not in tableitems[0].xpath('./following-sibling::%s[1]'%tableitems[0].tag):
                return None
            tbody = etree.fromstring("<table></table>")
            for t in tableitems:
                t.tag = 'td'
                tbody.append(t)
        return tbody

    def extract_content(self, region):
        tablestrs = ""
        items = region.xpath('.//text()|.//img|./table|//ul|//aside')
        contents = []
        if not region.xpath('./table'):
            added_tables = region.xpath('//table')
            items.extend(added_tables)
        othertable = self.simi_table(region)
        if othertable is not None:
            ot_s = lxml.html.tostring(othertable)
            tablestrs += ot_s.decode()
            contents.append({"type":"html","data":ot_s})
        tag_hist = {}
        for item in items:
            if hasattr(item,'tag'):
                continue
            t = item.getparent().tag
            if t not in tag_hist:
                tag_hist[t] = 0
            tag_hist[t] += len(item.strip())
        winner_tag = None
        try:
            if len(tag_hist) > 0:
                winner_tag = max((c, k) for k, c in tag_hist.items())[1]
        # problem here in Python3
        except TypeError:
            pass
        
        for item in items:
            if not hasattr(item,'tag'):
                txt = item.strip()
                parent_tag = item.getparent().tag
                if  parent_tag != winner_tag \
                    and len(self.stripper.sub("",txt)) < self.impurity_threshold \
                    and (parent_tag != 'li' \
                    or len(self.stripper.sub("",txt)) < self.impurity_threshold_min) \
                    or (parent_tag == 'li' and not txt.endswith('.')):
                    continue
                if txt == "" or txt in tablestrs:
                    continue
                contents.append({"type":"text","data":txt})
            elif item.tag == 'table':
                if winner_tag == 'td':
                    continue
                if item.xpath(".//p"):
                    continue
                if item != region:
                    table_s = lxml.html.tostring(item)
                    tablestrs += item.text_content()
                    contents.append({"type":"html","data":table_s})
                else:
                    for sub_item in item.xpath("//td/text()"):
                        contents.append({"type":"text","data":sub_item})
            elif item.tag == 'aside':
                if len(item.xpath(".//dl"))==0:
                    continue
                if item != region:
                    aside_s = lxml.html.tostring(item)
                    tablestrs += item.text_content()
                    contents.append({"type":"html","data":aside_s})
            elif item.tag == 'ul':
                if len(item.xpath('.//ul'))>0: 
                    continue
                if item != region:
                    licount = len(item.xpath("./li"))
                    childcount = len(item.xpath("./li/child::*"))
                    textcount = len([i for i in item.xpath("./li/text()") if len(i.strip())>self.min_key_len])
                    if licount==0 or childcount+textcount!=licount*2 or item==othertable:
                        continue
                    ul_s = lxml.html.tostring(item)
                    tablestrs += item.text_content()
                    contents.append({"type":"html","data":ul_s})
            elif item.tag == 'img':
                for img_prop in ('original', 'file', 'data-original', 'src-info', 'data-src', 'src'):
                    src =  item.get(img_prop)
                    if src is not None:
                        break
                if self.url != "":
                    if not src.startswith("/") and not src.startswith("http") and not src.startswith("./"):
                        src = "/" + src
                    src = urlparse.urljoin(self.url, src, False)
                contents.append({"type":"image","data":{"src": src}})    
            else:
                pass   
        return contents
    
    def judgeintable(self, item):
        p = item.getparent()
        while(p is not None and p.tag != "body" and p.tag != 'head'):
            if p.tag == 'tbody' or p.tag == 'aside':
                return True
            p = p.getparent()
        return False


    def extract_title(self):
        doc = self.doc
        tag_title = doc.xpath("/html/head/title/text()")
        s_tag_title = "".join(re.split(r'_|-',"".join(tag_title))[:1])
        title_candidates = doc.xpath('//h1/text()|//h2/text()|//h3/text()|//p[@class="title"]/text()')
        for c_title in title_candidates:
            c_title = c_title.strip()
            if c_title!="" and (s_tag_title.startswith(c_title) or s_tag_title.endswith(c_title)):
                return c_title
        sort_by_len_list = sorted((-1*len(x.strip()),x) for x in ([s_tag_title] + title_candidates))
        restitle = sort_by_len_list[0][1]
        if type(restitle)!=str:
            restitle = s_tag_title
        return restitle

    def extract(self):
        title = self.extract_title()
        region = self.region.locate()
        if region == None:
            return {'title':'', 'content':[]}
        rm_tag_set = set([])
        for p_el in region.xpath(".//p|.//li"):
            child_links = p_el.xpath(".//a/text()")
            count_p = len(" ".join(p_el.xpath(".//text()")))
            count_a = len(" ".join(child_links))
            if float(count_a) / (count_p + 1.0) > self.anchor_ratio_limit and not self.judgeintable(p_el):
                p_el.drop_tree()
        for el in region.xpath(".//a"):
            rm_tag_set.add(el)
        for el in region.xpath(".//strong|//b"):
            rm_tag_set.add(el)
        for el in rm_tag_set:
            el.drop_tag()
        content = self.extract_content(region)
        return {"title":title , "content": content}
    
    @staticmethod
    def processtable(table_str):
        table = Bs(table_str, 'lxml')
        res_dict = []
        table = table.select_one('tbody') or table.select_one('aside') or table.select_one('ul') or table.select_one('table')
        if table is None: 
            return res_dict
        lines = [line for line in table.children if isinstance(line, Tag) and gettext(line)]
        if table.name=='ul':
            if [countchildren(line) for line in lines].count(2)!=len(lines):
                return res_dict
        for line in lines:
            ths = line.select('th')
            tds = line.select('td')
            if table.name=="tbody" and len(ths)==0 and len(tds) and [countchildren(l) for l in lines].count(2)<len(lines):
                newline = []
                for td in tds:
                    eles = [span for span in td.children if isinstance(span, Tag) and span.text.strip()]
                    if len(eles)==0: 
                        pairs = [ele for ele in td.contents if isinstance(ele, NavigableString) and ele.strip()]
                        for pair in pairs:
                            children = re.split('[\s]{2}|:', pair, maxsplit=1)
                            if len(children)==2:
                                res_dict.append((children[0].strip(), children[1].strip()))
                            elif len(children)==1:
                                if len(gettext(children[0]).split())>1 and len(gettext(children[0]))>self.key_length:
                                    res_dict.append((children[0].strip(), "Header"))
                            elif len(children)>2:
                                continue
                    else:
                        newline.extend(eles)
                for span in newline:
                    children = [item for item in span.children if (isinstance(item, Tag) and item.text.strip())]
                    if len(children)==3:
                        return []
                    if len(children)==2:
                        res_dict.append((gettext(children[0]), gettext(children[1])))
                    elif len(children)==1 and len(children[0].text.strip())>self.key_length:
                        res_dict.append((gettext(children[0]), "Header"))
                    elif len(children)>2:
                        continue
            else:
                items = line.children
                children = [item for item in items if isinstance(item, Tag) or (isinstance(item, NavigableString) and gettext(item))]
                if len(children)==3:
                    return []
                if len(children)==2:
                    res_dict.append((gettext(children[0]), gettext(children[1])))
                elif len(children)==1 and gettext(children[0]):
                    if len(re.split('[\s]{2}|:', gettext(children[0]), maxsplit=1))==2:
                        res_dict.append((re.split('[\s]{2}|:', gettext(children[0]), maxsplit=1)[0].strip(), re.split('[\s]{2}|:', gettext(children[0]), maxsplit=1)[1].strip()))
                    elif table.name!='ul':
                        if len(gettext(children[0]).split())>1 and len(gettext(children[0]))>self.key_length:
                            res_dict.append((gettext(children[0]), "Header"))
                elif len(children)>2:
                    continue
        return res_dict
    
