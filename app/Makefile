.PHONY: install data run test
install:
	python -m pip install -r requirements.txt
data:            # re-download (cached) + rebuild the cleaned CSV and quality report
	python scripts/build_data.py
run:
	python -m streamlit run app.py
