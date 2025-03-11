# Searchable PDF Converter

## Description
This project converts PDFs to searchable PDFs using OCR (Optical Character Recognition).

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/searchable-pdf.git
   ```
2. Navigate to the project directory:
   ```sh
   cd searchable-pdf
   ```
3. Install the dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage
Run the following command to convert a PDF to a searchable PDF:
```sh
python pdf_to_searchable.py --input input.pdf --output output.pdf --endpoint YOUR_ENDPOINT --key YOUR_KEY
```

### Parameters
- `--input` or `-i`: Input PDF file path or directory containing PDFs (required)
- `--output` or `-o`: Output directory for searchable PDFs (optional, defaults to same as input)
- `--endpoint` or `-e`: Azure Document Intelligence endpoint (required)
- `--key` or `-k`: Azure Document Intelligence key (required)


