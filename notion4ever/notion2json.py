from notion_client import APIResponseError
import notion_client
import json
import logging

def update_notion_file(filename:str, notion_json:dict):
    """Writes notion_json dictionary to a json file."""
    with open(filename, 'w+', encoding='utf-8') as f:
        json.dump(notion_json, f, ensure_ascii=False, indent=4)

def block_parser(block: dict, notion: "notion_client.client.Client")-> dict:
    """Parses block for obtaining all nested blocks
    
    This function does recursive search over all nested blocks in a given block.

    Args:
        block (dict): Notion block, which is obtained from a list returned by 
            function notion.blocks.children.list().
        notion (notion_client.client.Client): Client for python API for 
            Notion from https://github.com/ramnes/notion-sdk-py is used here.

    Returns:
        block (dict): Notion block, which contains additional "children" key, 
            which is a list of nested blocks of a given block.
    """

    if block["has_children"]:
        block["children"] = []
        start_cursor = None
        while True:
            if start_cursor is None:
                blocks = notion.blocks.children.list(block["id"])
            start_cursor = blocks["next_cursor"]
            block["children"].extend(blocks['results'])
            if start_cursor is None:
                break  
        
        for child_block in block["children"]:
            block_parser(child_block, notion)
    return block

def notion_page_parser(page_id: str, notion: "notion_client.client.Client", 
                       filename: str, notion_json: dict):
    """Parses notion page with all its nested content and subpages

    This function does recursive search over all nested subpages and databases.
    The result of parsing incrementally saves in 'notion_json' dict and locally
    in the 'filename' file.

    Args:
        page_id (str): ID of the Notion page for parsing
        notion (notion_client.client.Client): Client for python API for 
            Notion from https://github.com/ramnes/notion-sdk-py is used here.
        filename (str): Name of the JSON file to be saved.
        notion_json (dict): Dictionary with raw Notion data. Keys of this 
            dictionary is the unique ID for each notion page. Each page contains
            a key 'blocks' which is a list of blocks with a content inside the 
            page. Some blocks may be nested pages and databases.
    """
    try:
        page = notion.pages.retrieve(page_id)
        page_type = 'page'

    except APIResponseError:
        page = notion.databases.retrieve(page_id)
        page_type = 'database'
        pass
    
    notion_json[page['id']] = page
    logging.debug(f"🤖 Retrieved {page['id']} of type {page_type}.")
    update_notion_file(filename, notion_json)
    start_cursor = None
    notion_json[page['id']]['blocks'] = []

    while True:
        if start_cursor is None:
            if page_type == 'page':
                blocks = notion.blocks.children.list(page_id)
            elif page_type == 'database':
                blocks = notion.databases.query(page_id)
        else:
            if page_type == 'page':
                blocks = notion.blocks.children.list(page_id, 
                                                     start_cursor=start_cursor)
            elif page_type == 'database':
                blocks = notion.databases.query(page_id, 
                                                start_cursor=start_cursor)
        
        start_cursor = blocks['next_cursor']
        notion_json[page['id']]['blocks'].extend(blocks['results'])
        update_notion_file(filename, notion_json)
        if start_cursor is None:
            break  
    
    logging.debug(f"🤖 Parsed content of {page['id']}.")

    for i_block, block in enumerate(notion_json[page['id']]['blocks']):
        if page_type == 'page':
            if block["type"] in ['page', 'child_page', 'child_database']:
                notion_page_parser(block['id'], notion, filename, notion_json)
            else:
                block = block_parser(block, notion)
                notion_json[page['id']]['blocks'][i_block] = block
                update_notion_file(filename, notion_json)
        elif page_type == 'database':
            block["type"] = "db_entry"
            notion_json[page['id']]['blocks'][i_block] = block
            update_notion_file(filename, notion_json)
            if block["object"] in ['page', 'child_page', 'child_database']:
                notion_page_parser(block['id'], notion, filename, notion_json)