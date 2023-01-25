<div align="center">
  <br>
  <img src="https://raw.githubusercontent.com/MerkulovDaniil/notion4ever/assets/cb.svg" width="256" alt="">
  <h1>NOTION4EVER</h1>
</div>

Notion4ever is a small python tool that allows you to free your content and export it as a collection of markdown and HTML files via the official Notion API.

# ✨ Features
* Export ready to deploy static HTML pages from your Notion.so pages.
    ![root_page](https://raw.githubusercontent.com/MerkulovDaniil/notion4ever/assets/root_page.png)
* Supports nice urls.
* Downloads all your Notion content, which is accessible via API to a raw JSON file. 
* Uses official Notion API (via [notion-sdk-py](https://github.com/ramnes/notion-sdk-py), but you can use curls if you want).
* Supports arbitrary page hierarchy.
    ![breadcrumb](https://raw.githubusercontent.com/MerkulovDaniil/notion4ever/assets/breadcrumb.png)
*  Supports galleries and lists
    ![gallery](https://raw.githubusercontent.com/MerkulovDaniil/notion4ever/assets/gallery.png)

    ![list](https://raw.githubusercontent.com/MerkulovDaniil/notion4ever/assets/list.png)

    Note that Notion API does not provide information about the database view yet. That is why notion4ever will render the database as a list if any database entries do not have a cover. Suppose all entries have covers, then it will be displayed as a gallery.
* Lightweight and responsive.
* Downloads all your images and files locally (you can turn this off if you prefer to store images\files somewhere else).

# 💻 How to run it locally
Just copy or clone the content of this repository and run.

```python
python -m notion4ever -n NOTION_TOKEN -p NOTION_PAGE_ID -bl True
``` 
# 🤖 How to run it automatically with Github actions
I will demonstrate it on the specific example of my site.
[Notion page](https://fmin.notion.site/Danya-Merkulov-12e3d1659a444678b4e2b6a989a3c625) -> [Github repository](https://github.com/MerkulovDaniil/merkulovdaniil.github.io/)

## ✅ Step 1. Create/choose some page in Notion.
1. We will need the page ID. For example, the page with URL
`https://fmin.notion.site/Danya-Merkulov-12e3d1659a444678b4e2b6a989a3c625` has the following ID: `12e3d1659a444678b4e2b6a989a3c625`.
1. Also, we will need to create a Notion API token. Go to [Notion.so/my-integrations](https://www.notion.so/my-integrations) -> `Create new integration`. Type the name of the integration and press `submit`. Now you can see your token, which starts with `secret_***` under the `Internal Integration Token` field.
1. Do not forget to grant access for your integration to edit your page. Go to `Share -> invite -> {YOUR INTEGRATION NAME}`.

## ✅ Step 2. Set up a repository for your static site.
In my case, it is [github.com/MerkulovDaniil/merkulovdaniil.github.io/](https://github.com/MerkulovDaniil/merkulovdaniil.github.io/). 
1. You need to specify your Notion settings in a Github action secret. Jump to the `Settings -> Secrets -> Actions -> New repository secret` and create two secrets:
    a. NOTION_PAGE_ID
    b. NOTION_TOKEN

    ![github_secret](https://raw.githubusercontent.com/MerkulovDaniil/notion4ever/assets/github_secret.png)

1. Create and configure the following GitHub action in your repository:

<details> <summary><code>publish.yml</code></summary>        

```yaml
name: Deploy from Notion to Pages

# on: [workflow_dispatch]
on:
  schedule:
    - cron: "0 */12 * * *" 
    
jobs:
  download_old-generate-push:
    runs-on: ubuntu-latest
    
    steps:
        # Download packages
      - name: Submodule Update
        run: |
          wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
          sudo apt install ./google-chrome-stable_current_amd64.deb
          sudo apt-get update
          
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.10.0
          
      - name: Download notion4ever
        uses: actions/checkout@v2
        with:
          repository: 'MerkulovDaniil/notion4ever'
          
      - name: Install packages
        run: pip install -r requirements.txt
        
      - name: Download current version of the site
        uses: actions/checkout@v2
        with:
          # HERE, YOU NEED TO PLACE YOUR REPOSITORY
          repository: 'MerkulovDaniil/merkulovdaniil.github.io'
          # TARGET BRANCH
          ref: main
          # THE FOLDER, WHERE NOTION4EVER EXPORTS YOUR CONTENT BY DEFAULT
          path: _site
          
      - name: Run notion4ever
        run: python -m notion4ever
        env:
            # HERE YOU NEED TO PLACE URL OF THE ROOT PAGE. PROBABLY IT IS "https://<username>.github.io"
            SITE_URL: "https://merkulov.top"
            NOTION_TOKEN: ${{secrets.NOTION_TOKEN}}
            NOTION_PAGE_ID: ${{secrets.NOTION_PAGE_ID}}
      
      - name: Deploy to Pages
        uses: JamesIves/github-pages-deploy-action@3.7.1
        with:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          BRANCH: main
          FOLDER: _site
          COMMIT_MESSAGE: 🤖 Deployed via notion4ever.
``` 
</details>

This script will run every 12 hours, and you can change it. Note that the first run could be slow if your page contains a lot of content, but all the subsequent runs will not download existing files.
Congratulations 🤗!

# 🛠 How it works
1. Given your notion token and ID of some page, notion4ever downloads all your content from this page and all nested subpages and saves it in a JSON file, `notion_content.json`.
1. Given your raw Notion data, notion4ever structures the page's content and generates file `notion_structured.json` with markdown content of all pages and relations between them. Markdown parsing is done via modification of [notion2md](https://github.com/echo724/notion2md) library.
1. Given structured notion content, notion4ever generates site from [jinja](https://github.com/pallets/jinja/) templates located in `./_templates` directory. All styles are located in `./_sass` directory and compiled with [libsass-python](https://github.com/sass/libsass-python) library. By default, site is located in `./_site` directory

# 🌈 Alternatives
## 🆓 Free
* [loconotion](https://github.com/leoncvlt/loconotion) - Python tool to turn Notion.so pages into lightweight, customizable static websites.
* [NotoCourse](https://github.com/MerkulovDaniil/NotoCourse) - properly configured github actions + structuring for loconotion.
* [notablog](https://github.com/dragonman225/notablog) - blog-oriented static site generator from Notion database.
* [popsy.co](popsy.co) - turns your Notion docs into a site with custom domain.

## 💰 Paid
* [helpkit.so](helpkit.so) - turns your Notion docs into a hosted self-service knowledge base. 
* [float.so](float.so) - turns your docs in Notion into online course.
* [super.so](super.so) - turns your Notion docs into a site.
* [potion.so](https://potion.so/) - turns your Notion docs into a site.

# 🦄 Examples
Please, add your sites here if you are using Notion4ever.
| <img src="https://raw.githubusercontent.com/MerkulovDaniil/notion4ever/assets/notion_logo.svg" width="15" height="15"> Notion public page | <img src="https://raw.githubusercontent.com/MerkulovDaniil/notion4ever/assets/cb.svg" width="15" height="15"> Notion4ever web page  |
|---|---|
| [My personal page](https://fmin.notion.site/Danya-Merkulov-12e3d1659a444678b4e2b6a989a3c625)  |  [My personal page](https://merkulov.top) |
| [MIPT optimization course](https://fmin.notion.site/00ef4311866942fd8efd351cc976959c)  |  [MIPT optimization course](https://opt.mipt.ru) |
 

# ToDo
- [ ] Proper documentation.
- [ ] Create pip package.
- [ ] Add parallel files downloading.
- [ ] Add search field. 
