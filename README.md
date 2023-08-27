# Nearly Chat GPT

This is a fork of the repo [here](https://github.com/microsoft/az-oai-chatgpt-streamlit-harness).

My version of this package has a number of modifications:

- Poetry for package management
- Can use azure or openai APIs
- UI enhancements
- Cleaned up files

To use the code, download the repo, unzip, and do the following:

- copy example.env to a new .env file with your settings

Run the following in a terminal:

- pip install poetry
- poetry install
- poetry run streamlit run app.py
