from pathlib import Path
import pandas as pd
import scrape


def get_csv_filename(brand: str, model: str) -> Path:
    return Path(f"data/{brand.lower()} {model.lower()}.csv".replace(" ", "_"))

if __name__ == "__main__":
    brand = "ford"
    model = "focus st"
    exclude_terms = ["line", "sw", "wagon", "1.0", "1.5", "2.3"]

    csv_path = get_csv_filename(brand, model)

    if csv_path.exists():
        print(f"Using existing file: {csv_path}")   
        listings = pd.read_csv(csv_path)
    else:
        listings = scrape.main(brand, model, exclude_terms)

    print(listings)


