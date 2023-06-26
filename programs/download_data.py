import json
import re
import requests

from bs4 import BeautifulSoup
from functools import reduce
from requests.adapters import HTTPAdapter, Retry


def flatten(t):
    return [item for sublist in t for item in sublist if item]


def get_url(url, s):
    response = s.get(url)

    if response.ok:
        results = BeautifulSoup(response.text, "lxml")
        return results
    else:
        return


def scrap_jep(s):
    base_url = "https://www.aeaweb.org/journals/jep/issues"
    result = get_url(base_url, s)
    issues = [re.match("/issues/(.*)", link.get('href')).group(1) for link in result.find_all("a") if link and "/issues/" in link.get('href')]

    last_issue = max(map(int, issues))

    url = "https://www.aeaweb.org/issues/" + str(last_issue)
    result = get_url(url, s)
    links = [link for link in result.find_all("a") if link and "/articles?id=" in link.get('href')]
    get_pdf_link = lambda link: "https://www.aeaweb.org/articles/pdf/doi/" + re.match("\/articles\?id\=(.*)", link.get('href')).group(1)
    parsed_links = [(link.text.strip(), get_pdf_link(link)) for link in links]
    return parsed_links


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
        "Conseil d'analyse économique": scrap_cae,
        "Journal of Economic Perspectives": scrap_jep
        }

    with open('output/results.json', 'r') as json_file:
          old_results = json.load(json_file)

    results = {
        source: [link for link in scrap_source(s) if link[0] not in [old_link[0] for old_link in old_results.get(source, {})]]
        for source, scrap_source in scrap_function_by_source.items()
        }

    with open("output/results.json", 'w') as json_file:
        json.dump(results, json_file)


if __name__ == "__main__":
    main()

