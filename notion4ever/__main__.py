from notion4ever import notion2json
from notion4ever import structuring
from notion4ever import site_generation

import logging
import json
from pathlib import Path
import shutil
import argparse
import os

from notion_client import Client

def main():
    parser = argparse.ArgumentParser(description=("Notion4ever: Export all your"
        "notion content to markdown and html and serve it as static site."))
    parser.add_argument('--notion_token', '-n', 
        type=str, help="Set your notion API token.",
        default=os.environ.get("NOTION_TOKEN"))
    parser.add_argument('--notion_page_id', '-p', 
        type=str, help="Set page_id of the target page.",
        default=os.environ.get("NOTION_PAGE_ID"))
    parser.add_argument('--output_dir', '-od', 
        type=str, default="./_site")
    parser.add_argument('--templates_dir', '-td', 
        type=str, default="./_templates")
    parser.add_argument('--sass_dir', '-sd', 
        type=str, default="./_sass")
    parser.add_argument('--build_locally', '-bl', 
        type=bool, default=False)
    parser.add_argument('--download_files', '-df', 
        type=bool, default=True)
    parser.add_argument('--site_url', '-su', 
        type=str, default=os.environ.get("SITE_URL"))
    parser.add_argument('--remove_before', '-rb', 
        type=bool, default=False)
    parser.add_argument('--include_footer', '-if', 
        type=bool, default=False)
    parser.add_argument('--logging_level', '-ll', 
        type=str, default="INFO")
    
    config = vars(parser.parse_args())
    config["include_footer"] = os.environ.get("INCLUDE_FOOTER")

    if config["logging_level"] == "DEBUG":
        llevel = logging.DEBUG
    else:
        llevel = logging.INFO
    
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", 
                    level=llevel)

    if config["remove_before"]:
        if Path(config["output_dir"]).exists():
            shutil.rmtree(config["output_dir"])
            logging.debug("🤖 Removed old site files")

    notion = Client(auth=config["notion_token"])
    logging.info("🤖 Notion authentification completed successfully.")

    # It will rewrite this file
    raw_notion = {}
    filename = "./notion_content.json"
    filename_structured = "./notion_structured.json"

    # Stage 1. Downloading (reading) raw notion content and save it to json file
    if Path(filename).exists():
        logging.info("🤖 Reading existing raw notion content.")
        with open(filename, "r") as f:
            raw_notion = json.load(f)
    else:
        logging.info("🤖 Started raw notion content parsing.")
        notion2json.notion_page_parser(config["notion_page_id"], 
                                notion=notion,
                                filename=filename,
                                notion_json=raw_notion)
        logging.info(f"🤖 Downloaded raw notion content. Saved at {filename}")

    # Stage 2. Structuring data
    logging.info(f"🤖 Started structuring notion data")
    structured_notion = structuring.structurize_notion_content(raw_notion,
                                                            config)
    with open(filename_structured, "w+", encoding="utf-8") as f:
        json.dump(structured_notion, f, ensure_ascii=False, indent=4)

    logging.info(f"🤖 Finished structuring notion data")
    
    if Path(filename_structured).exists():
        logging.info("🤖 Reading existing raw notion content.")
        with open(filename_structured, "r") as f:
            structured_notion = json.load(f)

    # Stage 3. Generating site from template and data
    if config["build_locally"]:
        structured_notion['base_url'] = \
            str(Path(config["output_dir"]).resolve())
    else:
        structured_notion['base_url'] = config["site_url"]

    logging.info(("🤖 Started generating site "
                 f"{'locally' if config['build_locally'] else ''} "
                 f"to {config['output_dir']}"))

    site_generation.generate_site(structured_notion, config)

    logging.info("🤖 Finished generating site.")

if __name__ == "__main__":
    main()