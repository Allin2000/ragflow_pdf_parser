import copy
import re
from collections import Counter

from api.db import ParserType
from rag.nlp import rag_tokenizer, tokenize, tokenize_table, add_positions, bullets_category, title_frequency, \
    tokenize_chunks
from deepdoc.parser import PdfParser, PlainParser
import numpy as np
from rag.utils import num_tokens_from_string

from fastapi import FastAPI, File, UploadFile, Form, APIRouter
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from typing import Optional
import uvicorn

from PIL import Image
from io import BytesIO
import base64

import pandas as pd


class Pdf(PdfParser):
    def __init__(self):
        self.model_speciess = ParserType.PAPER.value
        super().__init__()

    @staticmethod
    def sort_X_by_page(arr, threashold):
        # sort using y1 first and then x1
        arr = sorted(arr, key=lambda r: (r["page_number"], r["x0"], r["top"]))
        for i in range(len(arr) - 1):
            for j in range(i, -1, -1):
                # restore the order using th
                if abs(arr[j + 1]["x0"] - arr[j]["x0"]) < threashold \
                        and arr[j + 1]["top"] < arr[j]["top"] \
                        and arr[j + 1]["page_number"] == arr[j]["page_number"]:
                    tmp = arr[j]
                    arr[j] = arr[j + 1]
                    arr[j + 1] = tmp
        return arr
    

    # @staticmethod
    # def process_pdf_data(pdf_data):
    #     page_groups = defaultdict(list)
    #     for item in pdf_data:
    #         page_groups[item['page_number']].append(item)

    #     for page, items in page_groups.items():
    #         x0_groups = defaultdict(list)
    #         for item in items:
    #             x0_group_key = item['x0'] // 10
    #             x0_groups[x0_group_key].append(item)

    #         for x0_key, x0_items in x0_groups.items():
    #             x0_items.sort(key=lambda x: x['top'])

    #         page_groups[page] = x0_groups

    #     result = []
    #     for page, x0_groups in page_groups.items():
    #         for x0_key, items in x0_groups.items():
    #             result.extend(items)

    #     return result

    # def sort_boxes(self):
    #     page_groups = defaultdict(list)
    #     for item in self.boxes:
    #         page_groups[item['page_number']].append(item)

    #     for page, items in page_groups.items():
    #         x0_groups = defaultdict(list)
    #         for item in items:
    #             x0_group_key = item['x0'] // 10
    #             x0_groups[x0_group_key].append(item)

    #         for x0_key, x0_items in x0_groups.items():
    #             x0_items.sort(key=lambda x: x['top'])

    #         page_groups[page] = x0_groups

    #     sorted_boxes = []
    #     for page, x0_groups in page_groups.items():
    #         for x0_key, items in x0_groups.items():
    #             sorted_boxes.extend(items)

    #     self.boxes = sorted_boxes

    # def sort_boxes(self):
    #     page_groups = defaultdict(list)
    #     for item in self.boxes:
    #         page_groups[item['page_number']].append(item)

    #     sorted_boxes = []

    #     for page, items in page_groups.items():
    #         if page == 1:
    #             pre_keyword_boxes = []
    #             post_keyword_boxes = []
    #             keyword_found = False

    #             for item in items:
    #                 if not keyword_found:
    #                     if item['text'].strip().lower().startswith(("关键词", "keywords")):
    #                         keyword_found = True
    #                         pre_keyword_boxes.append(item)
    #                     else:
    #                         pre_keyword_boxes.append(item)
    #                 else:
    #                     post_keyword_boxes.append(item)

    #             pre_keyword_boxes.sort(key=lambda x: x['top'])

    #             x0_groups = defaultdict(list)
    #             for item in post_keyword_boxes:
    #                 x0_group_key = item['x0'] // 10
    #                 x0_groups[x0_group_key].append(item)

    #             for x0_key, x0_items in x0_groups.items():
    #                 x0_items.sort(key=lambda x: x['top'])

    #             sorted_boxes.extend(pre_keyword_boxes)
    #             for x0_key, items in x0_groups.items():
    #                 sorted_boxes.extend(items)
    #         else:
    #             x0_groups = defaultdict(list)
    #             for item in items:
    #                 x0_group_key = item['x0'] // 10
    #                 x0_groups[x0_group_key].append(item)

    #             for x0_key, x0_items in x0_groups.items():
    #                 x0_items.sort(key=lambda x: x['top'])

    #             for x0_key, items in x0_groups.items():
    #                 sorted_boxes.extend(items)

    #     self.boxes = sorted_boxes

    # def save_boxes_to_csv(self, file_name):
    #     df = pd.DataFrame(self.boxes)
    #     df.to_csv(file_name, index=False)
 
    def sort_boxes(self):
        # 初始化两个空的列表
        list1 = []
        list2 = []

        self.boxes= sorted(self.boxes, key=lambda x: x['top'])


        keywords = ("摘要", "abstract", "关键词", "key words")

        # Find the index
        # Find all indices
        indices = []
        for i, item in enumerate(self.boxes):
            if item['page_number'] == 1 and any(item['text'].strip().lower().startswith(kw) for kw in keywords):
                indices.append(i)

        # Split the list into two sublists
        if len(indices)>0:
            list1 = self.boxes[:indices[-1]]
            list2 = self.boxes[indices[-1]:]
        else:
            # If no index is found, add all data to the first list
            list2 = self.boxes

        sorted_list1 = sorted(list1, key=lambda x: x['top'])



        list2_df = pd.DataFrame(list2)

        # Drop rows with NaN values in 'x0'
        list2_df = list2_df.dropna(subset=['x0'])

    

        sorted_by_page_number = list2_df.sort_values(by='page_number')

        sorted_list = []

        for page, group in sorted_by_page_number.groupby('page_number'):
            group['x0_group'] = pd.cut(group['x0'], bins=range(0, int(group['x0'].max()) + 50, 50), right=False)
            sorted_group = group.sort_values(by=['x0_group', 'top'])
                   # Drop rows with NaN values in 'x0'
            sorted_group = sorted_group.dropna(subset=['x0_group'])
            sorted_list.append(sorted_group)

        # for i in sorted_list:
        #     print(i[['page_number', 'x0', 'x0_group']])

        sorted_by_page_number = pd.concat(sorted_list)


        df = sorted_by_page_number.drop('x0_group', axis=1)

        df = df.fillna('')

        list2 = df.to_dict('records')

        self.boxes = sorted_list1+list2

    def save_boxes_to_csv(self, file_name):
        df = pd.DataFrame(self.boxes)
        df.to_csv(file_name, index=False)

    def __call__(self, filename, binary=None, from_page=0,
                 to_page=100000, zoomin=3, callback=None):
        callback(msg="OCR is running...")
        self.__images__(
            filename if not binary else binary,
            zoomin,
            from_page,
            to_page,
            callback
        )
        callback(msg="OCR finished.")

        from timeit import default_timer as timer
        start = timer()
        self._layouts_rec(zoomin)
        callback(0.63, "Layout analysis finished")
        print("layouts:", timer() - start)
        self._table_transformer_job(zoomin)
        callback(0.68, "Table analysis finished")
        # self._text_merge()
        tbls = self._extract_table_figure(True, zoomin, True, True)

        
        # self.all_boxes += self.boxes

        # self.save_boxes_to_csv('boxes.csv')
        # self.all_boxes = self.all_boxes[0:100]
        # for i in self.all_boxes:
        #     print(i)

        # print("tttttttttttttttttttttttttttttt")


        column_width = np.median([b["x1"] - b["x0"] for b in self.boxes])
        self._concat_downward()
        # self._filter_forpages()
        callback(0.75, "Text merging finished.")

        # clean mess
        if column_width < self.page_images[0].size[0] / zoomin / 2:
            print("two_column...................", column_width,
                  self.page_images[0].size[0] / zoomin / 2)
            self.boxes = self.sort_X_by_page(self.boxes, column_width / 2)


        self.sort_boxes()

        
        # self.save_boxes_to_csv('boxes.csv')
        
        # self.all_boxes = self.all_boxes[0:100]
        # for i in self.all_boxes:
        #     print(i)

        # print("tttttttttttttttttttttttttttttt")

        self.save_boxes_to_csv('boxes.csv')
        

        for b in self.boxes:
            b["text"] = re.sub(r"([\t 　]|\u3000){2,}", " ", b["text"].strip())



        # def _begin(txt):
        #     return re.match(
        #         "[0-9. 一、i]*(introduction|abstract|摘要|引言|keywords|key words|关键词|background|背景|目录|前言|contents)",
        #         txt.lower().strip())

        # if from_page > 0:
        #     return {
        #         "title": "",
        #         "authors": "",
        #         "abstract": "",
        #         "sections": [(b["text"] + self._line_tag(b, zoomin), b.get("layoutno", "")) for b in self.boxes if
        #                      re.match(r"(text|title)", b.get("layoutno", "text"))],
        #         "tables": tbls
        #     }
        # # get title and authors
        # title = ""
        # authors = []
        # i = 0
        # while i < min(32, len(self.boxes) - 1):
        #     b = self.boxes[i]
        #     i += 1
        #     if b.get("layoutno", "").find("title") >= 0:
        #         title = b["text"]
        #         if _begin(title):
        #             title = ""
        #             break
        #         for j in range(3):
        #             if _begin(self.boxes[i + j]["text"]):
        #                 break
        #             authors.append(self.boxes[i + j]["text"])
        #             break
        #         break
        # # get abstract
        # abstr = ""
        # i = 0
        # while i + 1 < min(32, len(self.boxes)):
        #     b = self.boxes[i]
        #     i += 1
        #     txt = b["text"].lower().strip()
        #     if re.match("(abstract|摘要)", txt):
        #         if len(txt.split(" ")) > 32 or len(txt) > 64:
        #             abstr = txt + self._line_tag(b, zoomin)
        #             break
        #         txt = self.boxes[i]["text"].lower().strip()
        #         if len(txt.split(" ")) > 32 or len(txt) > 64:
        #             abstr = txt + self._line_tag(self.boxes[i], zoomin)
        #         i += 1
        #         break
        # if not abstr:
        #     i = 0

        # callback(
        #     0.8, "Page {}~{}: Text merging finished".format(
        #         from_page, min(
        #             to_page, self.total_page)))
        # for b in self.boxes:
        #     print(b["text"], b.get("layoutno"))
        # print(tbls)

        # return {
        #     "title": title,
        #     "authors": " ".join(authors),
        #     "abstract": abstr,
        #     "sections": [(b["text"] + self._line_tag(b, zoomin), b.get("layoutno", "")) for b in self.boxes[i:] if
        #                  re.match(r"(text|title)", b.get("layoutno", "text"))],
        #     "tables": tbls
        # }

       
        sections = []
        for b in self.boxes:
            print(b["text"], b.get("layoutno"))
            sections.append(b["text"])
        print(tbls)

        return sections
    

    





def chunk(filename, binary=None, from_page=0, to_page=100000,
          lang="Chinese", callback=None, **kwargs):
    """
        Only pdf is supported.
        The abstract of the paper will be sliced as an entire chunk, and will not be sliced partly.
    """

    pdf_parser = None
    if re.search(r"\.pdf$", filename, re.IGNORECASE):
        if not kwargs.get("parser_config", {}).get("layout_recognize", True):
            pdf_parser = PlainParser()
            sections = pdf_parser(filename if not binary else binary, from_page=from_page, to_page=to_page)[0]
        else:
            pdf_parser = Pdf()
            sections = pdf_parser(filename if not binary else binary,
                               from_page=from_page, to_page=to_page, callback=callback)
    else:
        raise NotImplementedError("file type not supported yet(pdf supported)")
    

    return sections

    # doc = {"docnm_kwd": filename, "authors_tks": rag_tokenizer.tokenize(paper["authors"]),
    #        "title_tks": rag_tokenizer.tokenize(paper["title"] if paper["title"] else filename)}
    # doc["title_sm_tks"] = rag_tokenizer.fine_grained_tokenize(doc["title_tks"])
    # doc["authors_sm_tks"] = rag_tokenizer.fine_grained_tokenize(doc["authors_tks"])
    # # is it English
    # eng = lang.lower() == "english"  # pdf_parser.is_english
    # print("It's English.....", eng)

    # res = tokenize_table(paper["tables"], doc, eng)

    # if paper["abstract"]:
    #     d = copy.deepcopy(doc)
    #     txt = pdf_parser.remove_tag(paper["abstract"])
    #     d["important_kwd"] = ["abstract", "总结", "概括", "summary", "summarize"]
    #     d["important_tks"] = " ".join(d["important_kwd"])
    #     d["image"], poss = pdf_parser.crop(
    #         paper["abstract"], need_position=True)
    #     add_positions(d, poss)
    #     tokenize(d, txt, eng)
    #     res.append(d)

    # sorted_sections = paper["sections"]
    # # set pivot using the most frequent type of title,
    # # then merge between 2 pivot
    # # for i in sorted_sections:
    # #     print(i)
    # # print("&&&&&&&&&&&&&&&")
    # bull = bullets_category([txt for txt, _ in sorted_sections])
    # most_level, levels = title_frequency(bull, sorted_sections)
    # assert len(sorted_sections) == len(levels)
    # sec_ids = []
    # sid = 0
    # for i, lvl in enumerate(levels):
    #     if lvl <= most_level and i > 0 and lvl != levels[i - 1]:
    #         sid += 1
    #     sec_ids.append(sid)
    #     print(lvl, sorted_sections[i][0], most_level, sid)

    # chunks = []
    # last_sid = -2
    # for (txt, _), sec_id in zip(sorted_sections, sec_ids):
    #     if sec_id == last_sid:
    #         if chunks:
    #             chunks[-1] += "\n" + txt
    #             continue
    #     chunks.append(txt)
    #     last_sid = sec_id
    # res.extend(tokenize_chunks(chunks, doc, eng, pdf_parser))
    # return res

"""
    readed = [0] * len(paper["lines"])
    # find colon firstly
    i = 0
    while i + 1 < len(paper["lines"]):
        txt = pdf_parser.remove_tag(paper["lines"][i][0])
        j = i
        if txt.strip("\n").strip()[-1] not in ":：":
            i += 1
            continue
        i += 1
        while i < len(paper["lines"]) and not paper["lines"][i][0]:
            i += 1
        if i >= len(paper["lines"]): break
        proj = [paper["lines"][i][0].strip()]
        i += 1
        while i < len(paper["lines"]) and paper["lines"][i][0].strip()[0] == proj[-1][0]:
            proj.append(paper["lines"][i])
            i += 1
        for k in range(j, i): readed[k] = True
        txt = txt[::-1]
        if eng:
            r = re.search(r"(.*?) ([\\.;?!]|$)", txt)
            txt = r.group(1)[::-1] if r else txt[::-1]
        else:
            r = re.search(r"(.*?) ([。？；！]|$)", txt)
            txt = r.group(1)[::-1] if r else txt[::-1]
        for p in proj:
            d = copy.deepcopy(doc)
            txt += "\n" + pdf_parser.remove_tag(p)
            d["image"], poss = pdf_parser.crop(p, need_position=True)
            add_positions(d, poss)
            tokenize(d, txt, eng)
            res.append(d)

    i = 0
    chunk = []
    tk_cnt = 0
    def add_chunk():
        nonlocal chunk, res, doc, pdf_parser, tk_cnt
        d = copy.deepcopy(doc)
        ck = "\n".join(chunk)
        tokenize(d, pdf_parser.remove_tag(ck), pdf_parser.is_english)
        d["image"], poss = pdf_parser.crop(ck, need_position=True)
        add_positions(d, poss)
        res.append(d)
        chunk = []
        tk_cnt = 0

    while i < len(paper["lines"]):
        if tk_cnt > 128:
            add_chunk()
        if readed[i]:
            i += 1
            continue
        readed[i] = True
        txt, layouts = paper["lines"][i]
        txt_ = pdf_parser.remove_tag(txt)
        i += 1
        cnt = num_tokens_from_string(txt_)
        if any([
            layouts.find("title") >= 0 and chunk,
            cnt + tk_cnt > 128 and tk_cnt > 32,
        ]):
            add_chunk()
            chunk = [txt]
            tk_cnt = cnt
        else:
            chunk.append(txt)
            tk_cnt += cnt

    if chunk: add_chunk()
    for i, d in enumerate(res):
        print(d)
        # d["image"].save(f"./logs/{i}.jpg")
    return res
"""





# if __name__ == "__main__":
#     import sys

#     def dummy(prog=None, msg=""):
#         pass
#     chunk(sys.argv[1], callback=dummy)



router = APIRouter()


class ChunkRequest(BaseModel):
    filename: str
    from_page: Optional[int] = 0
    to_page: Optional[int] = 100000
    lang: Optional[str] = "Chinese"
    parser_config: Optional[dict] = {}


@router.post("/chunk_paper")
async def chunk_endpoint(file: UploadFile = File(...), from_page: int = Form(0), to_page: int = Form(100000),
                         lang: str = Form("Chinese")):
    filename = file.filename
    binary = await file.read()

    def callback(prog=None, msg=None):
        print(f"Progress: {prog}, Message: {msg}")

    result = chunk(filename, binary, from_page, to_page, lang, callback=callback)



    return JSONResponse(content={"sections": result})  # Modified to return boxes