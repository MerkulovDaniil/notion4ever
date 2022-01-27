# Most of the code was taken from the Notion2md repository
# https://github.com/echo724/notion2md/tree/main/notion2md

from pathlib import Path
from urllib.parse import urljoin
from urllib.parse import urlparse

def paragraph(information:dict) -> str:
    return information['text']

def heading_1(information:dict) -> str:
    return f"# {information['text']}"

def heading_2(information:dict) -> str:
    return f"## {information['text']}"

def heading_3(information:dict) -> str:
    return f"### {information['text']}"

def callout(information:dict) -> str:
    return f"{information['icon']} {information['text']}"

def quote(information:dict) -> str:
    return f"> {information['text']}"

#toggle item will be changed as bulleted list item
def bulleted_list_item(information:dict) -> str:
    return f"* {information['text']}"

# numbering is not supported
def numbered_list_item(information:dict) -> str:
    """
    input: item:dict = {"number":int, "text":str}
    """
    return f"1. {information['text']}"

def to_do(information:dict) -> str:
    """
    input: item:dict = {"checked":bool, "test":str}
    """
    return f"- {'[x]' if information['checked'] else '[ ]'} {information['text']}"

def code(information:dict) -> str:
    """
    input: item:dict = {"language":str,"text":str}
    """
    return f"```{information['language'].replace(' ', '_')}\n{information['text']}\n```"

def embed(information:dict) -> str:
    """
    input: item:dict ={"url":str,"text":str}
    """
    embed_link = information["url"]

    block_md =f"""<p><div class="res_emb_block">
<iframe width="640" height="480" src="{embed_link}" frameborder="0" allowfullscreen></iframe>
</div></p>"""

    return block_md

def image(information:dict) -> str:
    """
    input: item:dict ={"url":str,"text":str,"caption":str}
    """
    image_name = information['url']

    if information['caption']:
        return f"![{information['caption']}]({image_name})"
    else:
        return f"![]({image_name})"

def file(information:dict) -> str:
    filename = information['url']
    clean_url = urljoin(filename, urlparse(filename).path)
    return f"[📎 {Path(clean_url).name}]({filename})"

def bookmark(information:dict) -> str:
    """
    input: item:dict ={"url":str,"text":str,"caption":str}
    """
    if information['caption']:
        return f"![{information['caption']}]({information['url']})"
    else:
        return f"![]({information['url']})"

def equation(information:dict) -> str:
    return f"$$ {information['text']} $$"

def divider(information:dict) -> str:
    return f"---"

def blank() -> str:
    return "<br/>"

def table_row(information:list) -> list:
    """
    input: item:list = [[richtext],....]
    """
    column_list = []
    for column in information['cells']:
        column_list.append(richtext_convertor(column))
    return column_list

def video(information:dict) -> str:
    youtube_link = information["url"]

    block_md =f"""<p><div class="res_emb_block">
<iframe width="640" height="480" src="{youtube_link}" frameborder="0" allowfullscreen></iframe>
</div></p>"""

    return block_md

block_type_map = {
    "paragraph": paragraph,
    "heading_1": heading_1,
    "heading_2": heading_2,
    "heading_3": heading_3,
    "callout": callout,
    "toggle":bulleted_list_item,
    "quote": quote,
    "bulleted_list_item": bulleted_list_item,
    "numbered_list_item": numbered_list_item,
    "to_do": to_do,
    # "child_page": child_page,
    "code": code,
    "embed": embed,
    "image": image,
    "bookmark": bookmark,
    "equation": equation,
    "divider": divider,
    "file": file,
    'table_row': table_row,
    "video": video
}

def blocks_convertor(blocks:object, structured_notion, page_id) -> str:
    results = []
    for block in blocks:
        block_md = block_convertor(block,0, structured_notion, page_id)
        results.append(block_md)

    outcome_blocks = "".join([result for result in results])
    return outcome_blocks

def information_collector(payload:dict, structured_notion: dict, page_id) -> dict:
    information = dict()
    if "text" in payload:
        information['text'] = richtext_convertor(payload['text'])
    if "icon" in payload:
        information['icon'] = payload['icon']['emoji']
    if "checked" in payload:
        information['checked'] = payload['checked']
    if "expression" in payload:
        information['text'] = payload['expression']
    if "url" in payload:
        information['url'] = payload['url']
        if "dont_download" not in payload:
            structured_notion["pages"][page_id]["files"].append(payload['url'])
    if "caption" in payload:
        information['caption'] = richtext_convertor(payload['caption'])
    if "external" in payload:
        information['url'] = payload['external']['url']
        if "dont_download" not in payload:
            structured_notion["pages"][page_id]["files"].append(payload['external']['url'])
    if "language" in payload:
        information['language'] = payload['language']
    
    # internal url
    if "file" in payload:
        information['url'] = payload['file']['url']
        if "dont_download" not in payload:
            structured_notion["pages"][page_id]["files"].append(payload['file']['url'])
    
    # table cells
    if "cells" in payload:
        information['cells'] = payload['cells']

    return information

def block_convertor(block:object,depth=0, structured_notion={}, page_id='') -> str:
    outcome_block:str = ""
    block_type = block['type']
    #Special Case: Block is blank
    if block_type == "paragraph" and not block['has_children'] and not block[block_type]['text']:
        outcome_block = blank() +"\n\n"
    else:
        if block_type in ["child_page", "child_database", "db_entry"]:
            title = structured_notion['pages'][block['id']]['title']
            url = structured_notion['pages'][block['id']]['url']
            outcome_block = f"{title}]({url})\n\n"
            if structured_notion['pages'][block['id']]['emoji']:
                emoji = structured_notion['pages'][block['id']]['emoji']
                outcome_block = f"[{emoji} {outcome_block}"
            elif structured_notion['pages'][block['id']]['icon']:
                icon = structured_notion['pages'][block['id']]['icon']
                outcome_block = f"""[<span class="miniicon"> <img src="{icon}"></span> {outcome_block}"""
            else:
                outcome_block = f"[{outcome_block}"

        else:
            if block_type in block_type_map:
                if block_type in ["embed", "video"]:
                    block[block_type]["dont_download"] = True
                outcome_block = \
                    block_type_map[block_type](information_collector(block[block_type], 
                        structured_notion, page_id)) + "\n\n"
            else:
                outcome_block = f"[{block_type} is not supported]\n\n"
            
            if block_type == "code":
                outcome_block = outcome_block.rstrip('\n').replace('\n', '\n'+'\t'*depth)
                outcome_block += '\n\n'

            if block['has_children']:
                if block_type == 'table':
                    depth += 1
                    child_blocks = block["children"]
                    table_list = []
                    for cell_block in child_blocks:
                        cell_block_type = cell_block['type']
                        table_list.append(block_type_map[cell_block_type](
                            information_collector(
                                cell_block[cell_block_type], 
                                structured_notion, 
                                page_id)))
                    # convert to markdown table
                    for index,value in enumerate(table_list):
                        if index == 0:
                            outcome_block = " | " + " | ".join(value) + " | " + "\n"
                            outcome_block += " | " + " | ".join(['----'] * len(value)) + " | " + "\n"
                            continue
                        outcome_block += " | " + " | ".join(value) + " | " + "\n"
                    outcome_block += "\n"
                else:
                    depth += 1
                    child_blocks = block["children"]
                    for block in child_blocks:
                        block_md = block_convertor(block, depth, structured_notion, page_id)
                        outcome_block += "\t"*depth + block_md

    return outcome_block

#Link
def text_link(item:dict):
    """
    input: item:dict ={"content":str,"link":str}
    """
    return f"[{item['content']}]({item['link']['url']})"

#Annotations
def bold(content:str):
    return f"**{content}**"

def italic(content:str):
    return f"*{content}*"

def strikethrough(content:str):
    return f"~~{content}~~"

def underline(content:str):
    return f"<u>{content}</u>"

def code(content:str):
    return f"`{content}`"

def color(content:str,color):
    return f"<span style='color:{color}'>{content}</span>"

def equation(content:str):
    return f"$ {content} $"

annotation_map = {
    "bold": bold,
    "italic": italic,
    "strikethrough": strikethrough,
    "underline": underline,
    "code": code,
}

#Mentions
def _mention_link(content,url):
    return f"([{content}]({url}])"

def user(information:dict):
    return f"({information['content']})"

def page(information:dict):
    return _mention_link(information['content'], information['url'])

def date(information:dict):
    return f"({information['content']})"

def database(information:dict):
    return _mention_link(information['content'], information['url'])

def mention_information(payload:dict):
    information = dict()
    if payload['href']:
        information['url'] = payload['href']
        if payload['plain_text'] != "Untitled":
            information['content'] = payload['plain_text']
        else:
            information['content'] = payload['href']
    else:
        information['content'] = payload['plain_text']
    
    return information

mention_map = {
    "user": user,
    "page": page,
    "database": database,
    "date": date
}

def richtext_word_converter(richtext:dict) -> str:
    outcome_word = ""
    plain_text = richtext["plain_text"]
    if richtext['type'] == "equation":
        outcome_word = equation(plain_text)
    elif richtext['type'] == "mention":
        mention_type = richtext['mention']['type']
        if mention_type in mention_map:
            outcome_word = mention_map[mention_type](mention_information(richtext))
    else:
        if richtext["href"]:
            outcome_word = text_link(richtext["text"])
        else:
            outcome_word = plain_text
        annot = richtext["annotations"]
        for key,transfer in annotation_map.items():
            if richtext["annotations"][key]:
                outcome_word = transfer(outcome_word)
        if annot["color"] != "default":
            outcome_word = color(outcome_word,annot["color"])
    return outcome_word


def richtext_convertor(richtext_list:list) -> str:
    outcome_sentence = ""
    for richtext in richtext_list:
        outcome_sentence += richtext_word_converter(richtext)
    return outcome_sentence

def grouping(page_md: str) -> str:
    page_md_fixed = []
    prev_line_type = ''
    for line in page_md.splitlines():
        line_type = ''
        norm_line = line.lstrip('\t').lstrip()
        if norm_line.startswith('- [ ]') or norm_line.startswith('- [x]'):
            line_type = 'checkbox'
        elif norm_line.startswith('* '):
            line_type = 'bullet'
        elif norm_line.startswith('1. '):
            line_type = 'numbered'

        if prev_line_type != '':
            if line == '':
                continue

        if line_type != prev_line_type:
            page_md_fixed.append('')

        page_md_fixed.append(line)
        prev_line_type = line_type
    return "\n".join(page_md_fixed)

def parse_markdown(raw_notion: dict, structured_notion: dict):
    for page_id, page in raw_notion.items():
        structured_notion["pages"][page_id]["md_content"] = ""
        page_md = blocks_convertor(raw_notion[page_id]["blocks"], structured_notion, page_id)
        page_md = grouping(page_md)
        page_md = page_md.replace("\n\n\n", "\n\n")
        # page_md = code_aligner(page_md)
        structured_notion["pages"][page_id]["md_content"] = page_md