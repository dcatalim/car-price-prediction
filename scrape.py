from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime as dt

headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"}

def match_query(query: str, title: str, exclude_terms: list) -> bool:
    # Convert both to lowercase and split the query into individual words/tokens
    query_words = query.lower().split()
    title_lower = title.lower()

    # Check if every single word from the query is present in the title
    return all(word in title_lower for word in query_words) and not any(exclude.lower() in title_lower for exclude in exclude_terms)

def get_soup(url: str, page_number: int) -> BeautifulSoup:
    params = {"page": page_number} if page_number > 1 else None
    response = requests.get(url, params=params, headers=headers, timeout=20)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def get_total_pages(soup: BeautifulSoup) -> int:
    pagination_nav = soup.find("nav", {"data-nx-name": "NexusPagination"})
    if not pagination_nav:
        return 1

    pages = {1}

    for page_link in pagination_nav.find_all("a", href=True):
        href = str(page_link.get("href", ""))
        parsed_link = urlparse(href)
        page_value = parse_qs(parsed_link.query).get("page", ["1"])[0]
        if page_value.isdigit():
            pages.add(int(page_value))

    for page_button in pagination_nav.find_all("button"):
        button_text = page_button.get_text(strip=True)
        if button_text.isdigit():
            pages.add(int(button_text))

    return max(pages)



def main(brand, model, exclude_terms): 

    query = f"{model}".replace(" ", "-").lower()

    mode= "carros"  # "carros" | "motociclos-scooters"

    url = f"https://www.olx.pt/carros-motos-e-barcos/{mode.lower()}/{brand.lower()}/q-{query}/"

    print(f"Fetching data from: {url}")

    first_page_soup = get_soup(url, 1)
    total_pages = get_total_pages(first_page_soup)

    rows = []
    seen_urls = set()


    for page_number in range(1, total_pages + 1):
        soup = first_page_soup if page_number == 1 else get_soup(url, page_number)
        filtered_listings = soup.find_all("div", {"data-testid": "l-card"})

        for listing in filtered_listings:
            card_title = listing.find("div", {"data-testid": "ad-card-title"})
            if not card_title:
                continue

            h4_tag = card_title.find("h4")
            if not h4_tag:
                continue
            title_text = h4_tag.find(string=True, recursive=False)
            if not title_text:
                continue
            title = title_text.strip()

            p_tag = card_title.find("p", {"data-testid": "ad-price"})
            price_text = p_tag.find(string=True, recursive=False) if p_tag else None
            price = price_text.replace("€", "").replace(".", "").replace(",", ".").strip() if price_text else "N/A"
            price = price if price != "Troca" else "N/A"

            negotiable = "negociável" in p_tag.get_text(strip=True).lower() if p_tag != "N/A" else False

            link_tag = card_title.find("a", href=True)
            if not link_tag:
                continue
            listing_url = str(link_tag.get("href", ""))
            if not listing_url:
                continue

            if listing_url.startswith("/"):
                listing_url = "https://www.olx.pt" + listing_url

            clean_url = urlparse(listing_url)._replace(query="").geturl()
            if clean_url in seen_urls:
                continue
            seen_urls.add(clean_url)

            promoted = "promoted" in listing_url.lower()

            location_date_tag = listing.find("p", {"data-testid": "location-date"})
            location_date_text = location_date_tag.get_text(strip=True) if location_date_tag else "N/A"
            location_date = location_date_text.split("-")[0].strip()

            age_mileage = listing.find("span", {"data-nx-name": "P5"})
            age_mileage_list = age_mileage.get_text(strip=True).split("-") if age_mileage else []

            first_part = age_mileage_list[0].strip() if age_mileage_list else "N/A"

            if "km" in first_part.lower():
                year = "N/A"
                mileage = first_part.replace("km", "").replace(".", "").replace(",", ".").strip()
            else:
                year = first_part
                mileage = age_mileage_list[1].replace("km", "").replace(".", "").replace(",", ".").strip() if len(age_mileage_list) > 1 else "N/A"

            if match_query(model, title, exclude_terms):
                rows.append(
                    {
                        "title": title,
                        "price": price,
                        "negotiable": negotiable,
                        "location": location_date,
                        "year": year,
                        "age": dt.datetime.now().year - int(year) if year.isdigit() else "N/A",
                        "mileage": mileage,
                        "promoted": promoted,
                        "url": clean_url,
                    }
                )

    df = pd.DataFrame(rows)

    print(df)

    filename = f"{brand.lower()} {model.lower()}.csv".replace(" ", "_")

    df.to_csv(filename, index=False)

    return df

if __name__ == "__main__":
    brand = "Yamaha"
    model = "Tracer 7"
    exclude_terms = ["Tracer 900", "Tracer 9"]

    main(brand, model, exclude_terms)
