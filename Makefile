.PHONY: setup seed dashboard api test clean

setup:
	pip install -r requirements.txt

seed:
	python -m src.seed

dashboard:
	streamlit run dashboard.py

api:
	uvicorn src.api:app --reload --port 8000

test:
	pytest tests/ -v

clean:
	rm -f verdeazul.db

all: setup seed
