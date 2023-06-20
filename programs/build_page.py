import json
import pypandoc



def to_html(md):
    return pypandoc.convert_text(md, 'html5', format = 'md')


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


def read_file(path):
    with open(path, encoding="utf-8") as f:
        content = f.read()

    return content


def main():
    with open('output/results.json', 'r') as json_file:
          results = json.load(json_file)

    html_chunks = [generate_html(source, data) for source, data in results.items()]

    text = \
        read_file("programs/header.html") \
        + "\n".join(html_chunks) \
        + read_file("programs/footer.html")

    with open("output/index.html", "w") as f:
        f.write(text)

if __name__ == "__main__":
    main()

