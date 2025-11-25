import csv
import xml.etree.ElementTree as ET
import requests
from io import StringIO


def parse_pib_data(xml_source, source_type="file"):
    try:
        if source_type == "url":
            response = requests.get(xml_source)
            root = ET.fromstring(response.content)
        elif source_type == "file":
            tree = ET.parse(xml_source)
            root = tree.getroot()
        else:  # string
            root = ET.fromstring(xml_source)

        facts = []


        for item in root.findall(".//item"):
            title = item.find("title").text
            link = item.find("link").text

            if title:
                # Clean up newlines or excessive whitespace in titles
                clean_title = " ".join(title.split())
                facts.append({"fact": clean_title, "source": link})

        return facts

    except Exception as e:
        print(f"Error parsing XML: {e}")
        return []


def save_to_csv(facts, filename="facts.csv"):
    if not facts:
        return

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["id", "text", "source"])
        writer.writeheader()
        for idx, f in enumerate(facts):
            writer.writerow({
                "id": idx + 1,
                "text": f["fact"],
                "source": f["source"]
            })
    print(f"Successfully saved {len(facts)} facts to {filename}")


if __name__ == "__main__":

    url = "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3"
    print(f"Fetching data from {url}...")
    facts = parse_pib_data(url, source_type="url")
    save_to_csv(facts)