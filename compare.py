from pathlib import Path

import pandas as pd


LEFT_CSV = Path("yamaha_tracer_7.csv")
RIGHT_CSV = Path("yamaha_tracer_7_strict.csv")
KEY_COLUMNS = ["url"]


def load_csv(path: Path) -> pd.DataFrame:
	df = pd.read_csv(path)
	for column in KEY_COLUMNS:
		df[column] = df[column].astype(str).str.strip()
	return df


def main() -> None:
	left = load_csv(LEFT_CSV)
	right = load_csv(RIGHT_CSV)

	left_keys = left[KEY_COLUMNS].drop_duplicates()
	right_keys = right[KEY_COLUMNS].drop_duplicates()

	only_in_left = left.merge(right_keys, on=KEY_COLUMNS, how="left", indicator=True)
	only_in_left = only_in_left[only_in_left["_merge"] == "left_only"].drop(columns=["_merge"])

	only_in_right = right.merge(left_keys, on=KEY_COLUMNS, how="left", indicator=True)
	only_in_right = only_in_right[only_in_right["_merge"] == "left_only"].drop(columns=["_merge"])

	print(f"Compared {len(left)} rows in {LEFT_CSV} against {len(right)} rows in {RIGHT_CSV}\n")

	print(f"Only in {LEFT_CSV} ({len(only_in_left)} rows):")
	if only_in_left.empty:
		print("  None")
	else:
		print(only_in_left.to_string(index=False))

	print(f"\nOnly in {RIGHT_CSV} ({len(only_in_right)} rows):")
	if only_in_right.empty:
		print("  None")
	else:
		print(only_in_right.to_string(index=False))


if __name__ == "__main__":
	main()
