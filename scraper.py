import errno
import os
import re
import shutil
import time
import httpcore

import requests
from bs4 import BeautifulSoup
from googletrans import Translator

translation = Translator()
URL = "https://www.classcentral.com"
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
}


def Scraper():
    try:
        print(f"New page request has been made ")
        print("Scraping...")

        page = requests.get(URL, headers=headers)
        soup = BeautifulSoup(page.content, "html.parser")
        find_resources(soup)
        find_tags(
            [
                "p",
                "nav",
                "strong",
                "a",
                "span",
                "button",
                "i",
                "input[placeholder]",
            ],
            soup=soup,
        )
        heading_text = soup.find_all(re.compile(r"^h[1-6]$"))
        translate_to_hindi(heading_text)
        main_page = open("index.html", "w", encoding="utf-8")
        main_page.write(soup.prettify())
        pages = soup.body.find_all("a")

        for link in pages:
            a_link = link.attrs["href"]
            if link.attrs["href"] != "/" and not os.path.exists(
                os.path.abspath("") + a_link.replace('https://www.classcentral.com', '')
            ):
                print(f"{pages.index(link)} from {len(pages)}")
                if re.search("www.classcentral.com", link.attrs["href"]):
                    new_page = requests.get(link.attrs["href"], headers=headers)
                else:
                    new_page = requests.get(URL + link.attrs["href"], headers=headers)
                new_soup = BeautifulSoup(new_page.content, "html.parser")
                find_resources(new_soup)
                find_tags(
                    [
                        "p",
                        "strong",
                        "a",
                        "span",
                        "button",
                        "i",
                        "input[placeholder]",
                    ],
                    soup=new_soup,
                )
                sub_heading_text = new_soup.find_all(re.compile(r"^h[1-6]$"))
                translate_to_hindi(sub_heading_text)
                page_name = link.attrs["href"].strip()
                if re.search('www.classcentral.com', page_name):
                    page_name = page_name.replace('https://www.classcentral.com', '')
                    link.attrs["href"] = page_name

                make_dirs(page_name)                
                sub_page = open(
                    f"{os.path.abspath('')}{page_name}/index.html",
                    "w",
                    encoding="utf-8",
                )
                sub_page.write(new_soup.prettify())
                # copyanything("images", page_name + "/images")

        print("All data has been scraped")
        return
    except requests.exceptions.ChunkedEncodingError:
        time.sleep(1)


def find_resources(the_soup):
    try:
        for script in the_soup.find_all("script"):
            if script.attrs.get("src"):
                url = script.attrs.get("src")
                dir_name = re.sub(r"[^\/]+$", "", url).replace("\n", "")
                dir_name_local = dir_name.replace("/", "\\")
                split = dir_name.split("/")
                file_name = re.sub(r"[^+$]+\/+", "", url)
                if re.search("http", url):
                    continue
                else:
                    if os.path.abspath("") + "\\" + dir_name.replace("/", "\\"):
                        if os.path.exists(
                            f"{os.path.abspath('')}\\{dir_name}{file_name}"
                        ):
                            continue
                        else:
                            download_files(url, dir_name_local, file_name)
                    else:
                        make_dirs(split)
                        download_files(url, dir_name_local, file_name)
                    script.attrs["src"] = ""

        for media in the_soup.find_all("link"):
            if media.attrs.get("href"):
                media_url = media.attrs.get("href")
                dir_name = re.sub(r"[^\/]+$", "", media_url).replace("\n", "")
                dir_name_local = dir_name.replace("/", "\\")
                split = dir_name.split("/")
                file_name = re.sub(r"[^+$]+\/+", "", media_url)
                if re.search("http|.com|.net", media_url):
                    continue
                else:
                    if os.path.abspath("") + "\\" + dir_name.replace("/", "\\"):
                        if os.path.exists(
                            f"{os.path.abspath('')}\\{dir_name}{file_name}"
                        ):
                            continue
                        else:
                            download_files(media_url, dir_name_local, file_name)
                    else:
                        make_dirs(split)
                        download_files(media_url, dir_name_local, file_name)

        for img in the_soup.find_all("img"):
            if img.attrs.get("src"):
                if re.search("www.classcentral.com", img.attrs.get("src")):
                    img_url = (
                        re.sub(r"[^+$]+\/+", "", img.attrs.get("src"))
                        .replace("%2F", "/")
                        .replace("%3A", ":")
                    )
                    dir_name = re.sub(r"[^\/]+\?\S*", "", img_url).replace(
                        "https://www.classcentral.com/", ""
                    )
                elif re.search("cloudfront.net", img.attrs.get("src")):
                    img_url = img.attrs.get("src")
                    continue
                else:
                    img_url = img.attrs.get("src")
                    dir_name = re.sub(r"[^\/]+$", "", img_url)
                    dir_name_local = dir_name.replace("/", "\\")
                    img_url = URL + "/" + img_url
                split = dir_name.split("/")
                file_name = re.sub(r"[^+\/+]\?\S*", "g", img_url).split("/")[-1]

                if os.path.abspath("") + "\\" + dir_name.replace("/", "\\"):
                    if os.path.exists(f"{os.path.abspath('')}\\{dir_name}{file_name}"):
                        continue
                    else:
                        download_files(img_url, dir_name_local, file_name)
                else:
                    make_dirs(split)
                    download_files(img_url, dir_name_local, file_name)
                img.attrs["src"] = img.attrs["data-src"] = f"{dir_name}{file_name}"

        for source in the_soup.find_all("source"):
            if source.attrs.get("srcset"):
                srcs = source.attrs.get("srcset").split(",")
                resolutions = ["900w", "1500w", "2400w"]
                for src in srcs:
                    dir_name = re.sub(r"[^\/]+$", "", src).strip()
                    dir_name_local = dir_name.replace("/", "\\")
                    split = dir_name.split("/")
                    file_name = re.sub(r"[+\.\w+$]+\/+|\s\d+\w+", "", src).strip()
                    if os.path.abspath("") + "\\" + dir_name.replace("/", "\\"):
                        if os.path.exists(
                            f"{os.path.abspath('')}\\{dir_name}{file_name}"
                        ):
                            continue
                        else:
                            download_files(
                                URL + "/" + dir_name + file_name,
                                dir_name_local,
                                file_name,
                            )
                    else:
                        make_dirs(split)
                        download_files(
                            URL + "/" + dir_name + file_name, dir_name_local, file_name
                        )
                    srcs[
                        srcs.index(src)
                    ] = f"{dir_name}{file_name} {resolutions[srcs.index(src)]}"
                img.attrs["srcset"] = ",".join(srcs)
    except IndexError as e:
        print(e)
        pass


def make_dirs(content):
    seperator = "\\"
    temp_dir = os.path.abspath("") + seperator
    if type(content) == list:
        split = content
    else:
        split = content.split("/")

    try:
        for dir_ in split:
            if not os.path.isfile(dir_):
                if (
                    len(dir_) > 1
                    and not os.path.exists(temp_dir+dir_)
                    and not re.search(r'^[^:]+://([^.]+\.)+[^/]+/([^/]+/)+[^#]+(#.+)?$', dir_)
                    and not re.search(r'^[^:]+://([^.]+\.)+[^/]+/([^/]+/)+[^#]+(#.+)?$', temp_dir)
                ):
                    temp_dir += dir_
                    os.mkdir(temp_dir)
                    temp_dir += seperator
                else:
                    if dir_ != '':
                        temp_dir += dir_ + seperator
                    continue
    except FileExistsError as e:
        print(e)
        pass
    except OSError as e:
        print(e)
        return


def download_files(url, dir_name, file_name):
    try:
        if dir_name is not None or file_name is not None:
            if re.search("http|ftp", url):
                download_file = requests.get(url, headers=headers)
            else:
                download_file = requests.get(URL + "/" + url, headers=headers)

            if re.search("js", file_name):
                with open(
                    f"{os.path.abspath('')}\\{dir_name}{file_name}",
                    "w",
                ) as f:
                    f.write(download_file.text)
            else:
                with open(
                    f"{os.path.abspath('')}\\{dir_name}{file_name}",
                    "wb",
                ) as f:
                    f.write(download_file.content)

    except Exception as e:
        print(e)
        pass


def copyanything(src, dst):
    try:
        shutil.copytree(src, dst)
    except OSError as exc:  # python >2.5
        if exc.errno in (errno.ENOTDIR, errno.EINVAL):
            shutil.copy(src, dst)
        else:
            raise


def find_tags(*args, soup):
    for arg in args[0]:
        arg_text = soup.select(arg)
        translate_to_hindi(arg_text)


def translate_to_hindi(items):
    try:
        # Iterate through each item in the list of items
        for item in items:
            # Check if the item has more than one content element
            if len(item.contents) > 1:
                # Iterate through each content element in the item
                for attr in item.contents:
                    # If the content element is not a newline character and has more contents,
                    # recursively call the function with the content element
                    if attr != "\n" and "contents" in attr:
                        sub_items(attr)
                    else:
                        # Check if the text of the content element doesn't contain a newline character,
                        # is at least 2 characters long and has a class attribute.
                        # If it matches any of the specified classes, continue iterating through the content elements.
                        # If it doesn't, call the new_content function with the item.
                        if not re.search("\n", attr.text):
                            if len(attr.text) >= 2:
                                if "class" in item.attrs:
                                    if (
                                        "cmpt-nav-logo" in item.attrs["class"]
                                        or "main-nav-dropdown__header-brand"
                                        in item.attrs["class"]
                                        or "scale-on-hover" in item.attrs["class"]
                                    ):
                                        continue
                                    else:
                                        new_content(item)
                        else:
                            continue
            # If the item has a placeholder attribute,
            # translate the placeholder text to Hindi and set it as the new placeholder value.
            elif "placeholder" in item.attrs:
                new_text = translation.translate(
                    item.attrs["placeholder"], "hi", "en"
                ).text
                new_text2 = translation.translate(
                    item.attrs["aria-label"], "hi", "en"
                ).text
                item["placeholder"] = new_text
                item["aria-label"] = new_text2
            # If the item doesn't have more than one content element and its text doesn't contain a newline character and isn't empty,
            # and it matches any of the specified classes, continue iterating through the items.
            # If it doesn't, call the new_content function with the item.
            elif not re.search("\n", item.text) and item.text != "":
                if "class" in item.attrs:
                    if (
                        "off-page" in item.attrs["class"]
                        or "main-nav-dropdown__header-brand" in item.attrs["class"]
                        or "scale-on-hover" in item.attrs["class"]
                    ):
                        continue
                    else:
                        new_content(item)
            # If the item's text is not empty, call the new_content function with the item.
            elif item.text != "":
                new_content(item)
            else:
                continue
    # Handle any exceptions that occur during execution.
    except Exception as e:
        # Print the error message and wait for 3 seconds before retrying.
        print("Error:", e)
        print("Retry in 3 seconds")
        time.sleep(3)


def new_content(var):
    try:
        new_text = translation.translate(var.text, "hi", "en").text
        var.find(string=True).replace_with(new_text)
    except httpcore._exceptions.ConnectTimeout as e:
        time.sleep(1)
    except TypeError as e:
        print(e)
        pass


def sub_items(attr):
    for sub in attr.contents:
        if sub.text != "":
            if "class" in sub.attrs:
                if (
                    "off-page" in sub.attrs["class"]
                    or "main-nav-dropdown__header-brand" in sub.attrs["class"]
                    or "scale-on-hover" in sub.attrs["class"]
                ):
                    continue
            else:
                new_content(sub)


def main():
    start_time = time.time()
    Scraper()
    print(f"Scraped in {(time.time() - start_time):.2f} seconds")


# clearing the console from unnecessary
def cls():
    return os.system("cls")


cls()

print("New session has been started")

if __name__ == "__main__":
    main()
