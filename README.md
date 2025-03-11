# Searchable PDF Converter

## Table of Contents
- [Description](#description)
- [Installation](#installation)
- [Usage](#usage)
  - [Convert PDF to Searchable PDF](#convert-pdf-to-searchable-pdf)
  - [Analyze Read PDF](#analyze-read-pdf)
- [Parameters](#parameters)

## Description
This project provides tools to convert PDFs to searchable PDFs using OCR (Optical Character Recognition) and to analyze text from local PDF files. It includes two main scripts:
1. `pdf_to_searchable.py`: Converts PDFs to searchable PDFs.
2. `analyze_read_pdf.py`: Analyzes text from local PDF files.

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/dennismartis/searchable-pdf.git
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
### Convert PDF to Searchable PDF
Run the following command to convert a PDF to a searchable PDF:
```sh
python pdf_to_searchable.py --input input.pdf --output output.pdf --endpoint YOUR_ENDPOINT --key YOUR_KEY
```

### Analyze Read PDF
Run the following command to analyze text from a local PDF file:
```sh
python analyze_read_pdf.py <file_path> --endpoint YOUR_ENDPOINT --key YOUR_KEY --path OUTPUT_PATH
```

## Parameters
### Convert PDF to Searchable PDF
- `--input` or `-i`: Input PDF file path or directory containing PDFs (required)
- `--output` or `-o`: Output directory for searchable PDFs (optional, defaults to same as input)
- `--endpoint` or `-e`: Azure Document Intelligence endpoint (required)
- `--key` or `-k`: Azure Document Intelligence key (required)

### Analyze Read PDF
- `<file_path>`: Path to the local PDF file (required)
- `--endpoint`: Azure Document Intelligence endpoint (required)
- `--key`: Azure Document Intelligence key (required)
- `--path`: Path to save the output files (optional, defaults to current directory)


