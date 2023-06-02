import pypandoc
import re
import requests

from bs4 import BeautifulSoup
from functools import reduce
from requests.adapters import HTTPAdapter, Retry


def flatten(t):
    return [item for sublist in t for item in sublist if item]


def to_html(md):
    return pypandoc.convert_text(md, 'html5', format = 'md')


def get_url(url, s):
    response = s.get(url)

    if response.ok:
        results = BeautifulSoup(response.text, "lxml")
        return results
    else:
        return


def read_file(path):
    with open(path, encoding="utf-8") as f:
        content = f.read()

    return content


def scrap_fs(s):
    def scrap_fs_page(page, s):
      url = "https://www.strategie.gouv.fr/publications?page={page}".format(page = page)
      result = get_url(url, s)
      raw_links = [link for link in result.find_all("a") if link and link.get('href')]
      pdf_links = [link for link in raw_links if link.get('href').endswith('pdf')]
      parsed_links = [(re.sub("\(.*?\)", "", link.text).strip(), link.get('href')) for link in pdf_links]
      return parsed_links

    return reduce(lambda x,y: x+y, [scrap_fs_page(i, s) for i in range(0,3)])


def scrap_cae(s):
    def find_cae_pdf(page, s):
      result = get_url(page, s)
      raw_links = [h2.find("a") for h2 in result.find_all("h2")]
      pdf_link = [link.get('href') for link in raw_links if link.get('href').endswith("pdf")]
      if len(pdf_link) == 1:
        return "https://www.cae-eco.fr{pdf}".format(pdf = pdf_link.pop())

    def scrap_cae_page(page, s):
      url = "https://www.cae-eco.fr/{page}-CAE-0".format(page = page)
      result = get_url(url, s)
      raw_links = [h2.find("a") for h2 in result.find_all("h2")]
      parsed_links = [(link.text, find_cae_pdf("https://www.cae-eco.fr/{}".format(link.get('href')), s)) for link in raw_links]
      return parsed_links

    return scrap_cae_page("Notes", s)


def generate_html(source, data):
    papiers = to_html('\n'.join(sorted(["- [{titre}]({lien})".format(titre = titre, lien = lien) for titre, lien in data])))

    html_chunk = """
<details>
<summary>{source}</summary>
{papiers}
<br>
</details>
""".format(source = source, papiers = papiers)
    return html_chunk



def main():
    s = requests.Session()

    retries = Retry(
        total = 20,
        backoff_factor = 0.1,
        status_forcelist = [500, 502, 503, 504]
        )

    s.mount('https://', HTTPAdapter(max_retries=retries))

    scrap_function_by_source = {
        "France Stratégie": scrap_fs,
        "Conseil d'analyse économique": scrap_cae
        }

    results = [(source, scrap_source(s)) for source, scrap_source in scrap_function_by_source.items()]
    html_chunks = [generate_html(source, data) for source, data in results]

    text = \
        read_file("programs/header.html") \
        + "\n".join(html_chunks) \
        + read_file("programs/footer.html")

    with open("output/index.html", "w") as f:
        f.write(text)

if __name__ == "__main__":
    main()

