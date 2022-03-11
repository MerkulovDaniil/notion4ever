import dateutil.parser as dt_parser
import logging
from urllib.parse import urljoin
from urllib.parse import urlparse
from urllib.parse import unquote
from urllib.error import HTTPError
from pathlib import Path
from notion4ever import markdown_parser
from urllib import request
from itertools import groupby

def recursive_search(key, dictionary):
    """This function does recursive search for the 'key' in the 'dictionary'

    Args:
        key (str): key for searching.
        dictionary: dictionary with nested dictionaries and lists.
    
    Returns:
        value of a target key. 
    """
    if hasattr(dictionary,"items"):
        for k, v in dictionary.items():
            if k == key:
                yield v
            if isinstance(v, dict):
                for result in recursive_search(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in recursive_search(key, d):
                        yield result

def parse_headers(raw_notion: dict) -> dict:
    """Parses raw notion dict and returns dict with keys equal to each page_id,
        with values of dicts with the following fields:
            "type" (str):  "page", "database" or "db_entry", 
            "files" (list): list of urls for nested, 
            "title" (str): title of corresponding page, 
            "last_edited_time" (str): last edited time in iso format, 
            "date" (str): date start in iso format, 
            "date_end" (str): date end in iso format, 
            "parent" (str): id of parent page,
            "children" (list): list of ids of children page,
            "cover" (str): cover url,
            "emoji" (str): emoji symbol,
            "icon" (str): icon url.
    Returns: Example
        {
        "12e3d165-9a44-4678-b4e2-b6a989a3c625": 
            {
            "files": [
                "https://merkulov.top/ineq_constr_10.svg",
                "https://merkulov.top/dm_on_fire.jpg"
            ],
            "type": "page",
            "title": "Danya Merkulov",
            "last_edited_time": "2022-01-25T22:35:00.000Z",
            "parent": null,
            "children": [
                "89ae66ca-44a5-4819-9797-5bf321572676",
                "a2964f56-f0d3-43be-abf6-46cf508dff04",
                "c131810a-ca9b-41af-a5cb-8aa8dfd86971",
                "d4a7fb6a-fcb7-45f8-8a35-09c6c4f5c408"
            ],
            "cover": "https://merkulov.top/ineq_constr_10.svg",
            "icon": "https://merkulov.top/dm_on_fire.jpg",
            "emoji": null,
           },
        "89ae66ca-44a5-4819-9797-5bf321572676": 
            {
            "files": [],
            "type": "database",
            "title": "Papers",
            "last_edited_time": "2022-01-26T20:10:00.000Z",
            "parent": "12e3d165-9a44-4678-b4e2-b6a989a3c625",
            "children": [
                "88f6b858-14b3-4d51-baad-5c0cf7da52d0",
                "0649ea83-e30e-4bd5-8601-4fdcb2369378",
                "d6d08b27-3754-4f8d-97d0-8d0a8bac9ac3"
            ],
            "cover": null,
            "emoji": "📜",
            "icon": null,
            },
        "88f6b858-14b3-4d51-baad-5c0cf7da52d0": 
            {
            "files": [
                "https://merkulov.top/Papers/Empirical_Study_of_Extreme_Overfitting_Points_of_Neural_Networks/ResNet_CIFAR10.svg"
            ],
            "type": "db_entry",
            "title": "Empirical Study of Extreme Overfitting Points of Neural Networks",
            "last_edited_time": "2022-01-26T20:12:00.000Z",
            "parent": "89ae66ca-44a5-4819-9797-5bf321572676",
            "children": [],
            "cover": "https://merkulov.top/Papers/Empirical_Study_of_Extreme_Overfitting_Points_of_Neural_Networks/ResNet_CIFAR10.svg",
            "emoji": "🧠",
            "icon": null,
            }
        }
    """
    notion_pages = {}
    for page_id, page in raw_notion.items():
        notion_pages[page_id] = {}
        notion_pages[page_id]["files"] = []

        # Page type. Could be "page", "database" or "db_entry"
        notion_pages[page_id]["type"] = page["object"]
        if page["parent"]["type"] in ["database_id"]:
            notion_pages[page_id]["type"] = "db_entry"

        # Title
        if notion_pages[page_id]["type"] == "page":
            if len(page["properties"]["title"]["title"]) > 0:
                notion_pages[page_id]["title"] = \
                    page["properties"]["title"]["title"][0]["plain_text"]
            else:
                notion_pages[page_id]["title"] = None
        elif notion_pages[page_id]["type"] == "database":
            if len(page["title"]) > 0:
                notion_pages[page_id]["title"] = \
                    page["title"][0]["text"]["content"]
            else:
                notion_pages[page_id]["title"] = None
        elif notion_pages[page_id]["type"] == "db_entry":
            res = recursive_search("title", page["properties"])
            res = list(res)[0]
            if len(res) > 0:
                notion_pages[page_id]["title"] = res[0]["plain_text"]
            else:
                notion_pages[page_id]["title"] = None
                logging.warning(f"🤖Empty database entries could break the site building 😫.")
                

        # Time
        notion_pages[page_id]["last_edited_time"] = \
            page["last_edited_time"]
        if notion_pages[page_id]["type"] == "db_entry":
            if "Date" in page["properties"].keys():
                if page["properties"]["Date"]["date"] is not None:
                    notion_pages[page_id]["date"] = \
                        page["properties"]["Date"]["date"]["start"]
                    if page["properties"]["Date"]["date"]["end"] is not None:
                        notion_pages[page_id]["date_end"] = \
                            page["properties"]["Date"]["date"]["end"]

        # Parent
        if "workspace" in page["parent"].keys():
            parent_id = None
            notion_pages[page_id]["parent"] = parent_id
        elif notion_pages[page_id]["type"] in ["page", "database"]:
            parent_id = page["parent"]["page_id"]
            notion_pages[page_id]["parent"] = parent_id
        elif notion_pages[page_id]["type"] == "db_entry":
            parent_id = page["parent"]["database_id"]
            notion_pages[page_id]["parent"] = parent_id

        # Children
        if "children" not in notion_pages[page_id].keys():
            notion_pages[page_id]["children"] = []

        if parent_id is not None:
            notion_pages[parent_id]["children"].append(page_id)

        # Cover
        if page["cover"] is not None:
            cover = list(recursive_search("url", page["cover"]))[0]
            notion_pages[page_id]["cover"] = cover
            notion_pages[page_id]["files"].append(cover)
            
        else:
            notion_pages[page_id]["cover"] = None

        # Icon
        if type(page["icon"]) is dict:
            if "emoji" in page["icon"].keys():
                notion_pages[page_id]["emoji"] = \
                    page["icon"]["emoji"]
                notion_pages[page_id]["icon"] = None
            else:
                icon = page["icon"]["file"]["url"]
                notion_pages[page_id]["icon"] = icon
                notion_pages[page_id]["files"].append(icon)
                notion_pages[page_id]["emoji"] = None
        else:
            notion_pages[page_id]["icon"] = None
            notion_pages[page_id]["emoji"] = None

    return notion_pages

def find_lists_in_dbs(structured_notion: dict):
    """Determines the rule for considering database as list rather than gallery.
    
    Each database by default is treated as gallery, but if any child page does 
    not have a cover, we will treat it as list.
    """
    for page_id, page in structured_notion["pages"].items():
        if page["type"] == 'database':
            for child_id in page["children"]:
                if structured_notion["pages"][child_id]["cover"] is None:
                    structured_notion["pages"][page_id]["db_list"] = True
                    break
        
def parse_family_line(page_id: str, family_line: list, structured_notion: dict):
    """Parses the whole parental line for page with 'page_id'"""
    if structured_notion['pages'][page_id]["parent"] is not None:
        par_id = structured_notion["pages"][page_id]["parent"]
        family_line.insert(0, par_id)
        family_line = parse_family_line(par_id, family_line, structured_notion)
    
    return family_line
    
def parse_family_lines(structured_notion: dict):
    for page_id, page in structured_notion["pages"].items():
        page["family_line"] = parse_family_line(page_id, [], structured_notion)

def generate_urls(page_id:str, structured_notion: dict, config: dict):
    """Generates url for each page nested in page with 'page_id'"""
    if page_id == structured_notion["root_page_id"]:
        if config["build_locally"]:
            f_name = structured_notion["pages"][page_id]["title"].replace(" ",
                                                                          "_")
        else:
            f_name = 'index'

        f_name += '.html'

        if config["build_locally"]:
            f_url = str(Path(config["output_dir"]).resolve() / f_name)
        else:
            f_url = config["site_url"]
        structured_notion["pages"][page_id]["url"] = f_url
        structured_notion["urls"].append(f_url)
    else:
        if config["build_locally"]:
            parent_id = structured_notion["pages"][page_id]["parent"]
            parent_url = structured_notion["pages"][parent_id]["url"]
            f_name = structured_notion["pages"][page_id]["title"].replace(" ",
                                                                          "_")
            f_url = Path(parent_url).parent.resolve()
            f_url = f_url / f_name / f_name
            f_url = str(f_url.resolve()) + '.html'
            while f_url in structured_notion["urls"]:
                f_name += "_"
                f_url = Path(parent_url).parent
                f_url = f_url / f_name / f_name
                f_url = str(f_url.resolve()) + '.html'
            structured_notion["pages"][page_id]["url"] = f_url
            structured_notion["urls"].append(f_url)
        else:
            parent_id = structured_notion["pages"][page_id]["parent"]
            parent_url = structured_notion["pages"][parent_id]["url"]
            parent_url += '/'
            f_name = structured_notion["pages"][page_id]["title"].replace(" ",
                                                                          "_")
            f_url = urljoin(parent_url, f_name)
            while f_url in structured_notion["urls"]:
                f_name += "_"
                f_url = urljoin(parent_url, f_name) 
            structured_notion["pages"][page_id]["url"] = f_url
            structured_notion["urls"].append(f_url)
           
    for child_id in structured_notion["pages"][page_id]["children"]:
        generate_urls(child_id, structured_notion, config)

# ======================
# Properties handlers
# ======================

def p_rich_text(property:dict)->str:
    md_property = markdown_parser.richtext_convertor(property['rich_text'])
    return md_property

def p_number(property:dict)->str:
    md_property = ''
    logging.debug('🤖 Only number in the number block is supported')
    if property['number'] is not None:
        md_property = str(property['number'])
    return md_property

def p_select(property:dict)->str:
    md_property = ''
    if property['select'] is not None:
        md_property += str(property['select']['name'])
    return md_property

def p_multi_select(property:dict)->str:
    md_property = ''
    for tag in property['multi_select']:
        md_property += tag['name'] + '; '
    return md_property.rstrip('; ')

def p_date(property:dict)->str:
    md_property = ''
    if property['date'] is not None:
        dt = property['date']['start']
        md_property += dt_parser.isoparse(dt).strftime("%d %b, %Y")
        if property['date']['end'] is not None:
            dt = property['date']['end']
            md_property += ' - ' + dt_parser.isoparse(dt).strftime("%d %b, %Y")
    return md_property

def p_people(property:dict)->str:
    md_property = ''
    for tag in property['people']:
        md_property += tag['name'] + '; '
    return md_property.rstrip('; ')

def p_files(property:dict)->str:
    md_property = ''
    for file in property['files']:
        md_property += f"[📎]({file['file']['url']})" + "; "
    return md_property.rstrip('; ')

def p_checkbox(property:dict)->str:
    return f"- {'[x]' if property['checkbox'] else '[ ]'}"

def p_url(property:dict)->str:
    md_property = ''
    if property['url'] is not None:
        md_property = f"[🕸]({property['url']})"
    return md_property

def p_email(property:dict)->str:
    md_property = ''
    if property['email'] is not None:
        md_property = property['email']
    return md_property

def p_phone_number(property:dict)->str:
    md_property = ''
    if property['phone_number'] is not None:
        md_property = property['phone_number']
    return md_property

# def p_formula(property:dict)->str:
#     md_property = ''
#     return md_property

# def p_relation(property:dict)->str:
#     md_property = ''
#     return md_property

# def p_rollup(property:dict)->str:
#     md_property = ''
#     return md_property

def p_created_time(property:dict)->str:
    md_property = ''
    if property['created_time'] is not None:
        dt = property['created_time']
        md_property += dt_parser.isoparse(dt).strftime("%d %b, %Y")
    return md_property

# def p_created_by(property:dict)->str:
#     md_property = ''
#     return md_property

def p_last_edited_time(property:dict)->str:
    md_property = ''
    if property['last_edited_time'] is not None:
        dt = property['last_edited_time']
        md_property += dt_parser.isoparse(dt).strftime("%d %b, %Y")
    return md_property

# def p_last_edited_by(property:dict)->str:
#     md_property = ''
#     return md_property


def parse_db_entry_properties(raw_notion: dict, structured_notion:dict):
    properties_map = {
        "rich_text": p_rich_text, 
        "number": p_number,
        "select": p_select,
        "multi_select": p_multi_select,
        "date": p_date,
        "people": p_people,
        "files": p_files,
        "checkbox": p_checkbox,
        "url": p_url,
        "email": p_email,
        "phone_number": p_phone_number,
        # "formula": p_formula,
        # "relation": p_relation,
        # "rollup": p_rollup,
        "created_time": p_created_time,
        # "created_by": p_created_by,
        "last_edited_time": p_last_edited_time,
        # "last_edited_by": p_last_edited_by
    }    
    for page_id, page in structured_notion["pages"].items():
        if page["type"] == "db_entry":
            structured_notion["pages"][page_id]['properties'] = \
                raw_notion[page_id]['properties']
            structured_notion["pages"][page_id]['properties_md'] = {}
            for property_title, property in structured_notion["pages"][page_id]['properties'].items():
                if property['type'] == "title":
                    continue # We already have the title
                structured_notion["pages"][page_id]['properties_md'][property_title] = ''
                if property['type'] in properties_map:
                    if property['type'] == "files":
                        for file in property['files']:
                            structured_notion["pages"][page_id]["files"].append(file['file']['url'])
                    structured_notion["pages"][page_id]['properties_md'][property_title] = \
                        properties_map[property['type']](property)
                else:
                    if property['type'] != "title": # We already have the title
                        logging.debug(f"{property['type']} is not supported yet")

def download_and_replace_paths(structured_notion:dict, config: dict):
    for page_id, page in structured_notion["pages"].items():
        for i_file, file_url in enumerate(page["files"]):
            # Download file
            clean_url = urljoin(file_url, urlparse(file_url).path)

            if config["build_locally"]:
                folder = urljoin(page["url"], '.')
                filename = unquote(Path(clean_url).name)
                new_url = urljoin(folder, filename)
                local_file_location = str(Path(new_url).relative_to(Path(config["output_dir"]).resolve()))
            else:
                filename = unquote(Path(clean_url).name)
                new_url = urljoin(page["url"] + '/', filename)

                local_file_location = new_url.replace(config["site_url"], '', 1)
                local_file_location = local_file_location.lstrip("/")

            (config["output_dir"] / Path(local_file_location).parent).mkdir(parents=True, exist_ok=True)
            full_local_name = (Path(config["output_dir"]).resolve() / local_file_location)
            if Path(full_local_name).exists():
                logging.debug(f"🤖 {filename} already exists.")
            else:
                try:
                    request.urlretrieve(file_url, full_local_name)
                    logging.debug(f"🤖 Downloaded {filename}")
                except HTTPError:
                    logging.warning(f"🤖Cannot download {filename}.")
                except ValueError:
                    continue 

            # Replace url in structured_data
            structured_notion["pages"][page_id]["files"][i_file] = new_url

            # Replace url in markdown
            md_content = structured_notion["pages"][page_id]["md_content"]
            structured_notion["pages"][page_id]["md_content"] = md_content.replace(file_url, new_url)

            # Replace url in header
            for asset in ['icon', 'cover']:
                if page[asset] == file_url:
                    structured_notion["pages"][page_id][asset] = new_url
            
            # Replace url in files property:
            if page["type"] == "db_entry":
                for prop_name, prop_value in page["properties_md"].items():
                    if file_url in prop_value:
                        new_value = prop_value.replace(file_url, new_url)
                        structured_notion["pages"][page_id]["properties_md"][prop_name] = new_value

def sorting_db_entries(structured_notion: dict):
    for page_id, page in structured_notion["pages"].items():
        if page["type"] == "database":
            if len(page["children"]) > 1:
                first_child_id = page["children"][0]
                if "date" in structured_notion["pages"][first_child_id]:
                    structured_notion["pages"][page_id]["children"] =\
                        sorted(page['children'], key=lambda item: structured_notion["pages"][item]["date"])
            

def sorting_page_by_year(structured_notion: dict):
    structured_notion['sorted_pages'] = \
        {k: dt_parser.isoparse(v['date']) for k,v in structured_notion['pages'].items() if 'date' in v.keys()}
    structured_notion['sorted_pages'] = \
        {k: v for k, v in sorted(structured_notion['sorted_pages'].items(), key=lambda item: item[1], reverse=True)}
    # grouping by year
    structured_notion['sorted_id_by_year'] = {}
    for year, year_pages in groupby(structured_notion['sorted_pages'].items(), key=lambda item: item[1].year):
        structured_notion['sorted_id_by_year'][year] = []
        for page in year_pages: 
            structured_notion['sorted_id_by_year'][year].append(page[0])
    del structured_notion['sorted_pages']
            
def structurize_notion_content(raw_notion: dict, config: dict) -> dict:
    structured_notion = {}
    structured_notion["pages"] = {}
    structured_notion["urls"] = []
    structured_notion["root_page_id"] = list(raw_notion.keys())[0]
    structured_notion["pages"] = parse_headers(raw_notion)
    structured_notion["include_footer"] = config["include_footer"]
    find_lists_in_dbs(structured_notion)
    logging.debug(f"🤖 Structurized headers")

    parse_family_lines(structured_notion)
    logging.debug(f"🤖 Structurized family lines")

    generate_urls(structured_notion["root_page_id"], structured_notion, config)
    logging.debug(f"🤖 Generated urls")

    markdown_parser.parse_markdown(raw_notion, structured_notion)
    logging.debug(f"🤖 Parsed markdown content")

    parse_db_entry_properties(raw_notion, structured_notion)
    logging.debug(f"🤖 Parsed db_entries properties")

    if config["download_files"]:
        download_and_replace_paths(structured_notion, config)
        logging.debug(f"🤖 Downloaded files and replaced paths")

    sorting_db_entries(structured_notion)
    sorting_page_by_year(structured_notion)
    logging.debug(f"🤖 Sorted pages by date and grouped by year.")

    return structured_notion