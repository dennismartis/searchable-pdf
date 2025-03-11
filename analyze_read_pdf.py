from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
import numpy as np
import os
import argparse
import json

def format_bounding_box(bounding_box):
    if not bounding_box:
        return "N/A"
    reshaped_bounding_box = np.array(bounding_box).reshape(-1, 2)
    return ", ".join(["[{}, {}]".format(x, y) for x, y in reshaped_bounding_box])

def analyze_read(file_path, endpoint, key, output_path):
    # Check if file exists
    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' not found.")
        return

    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )
    
    # Open and read the local file
    with open(file_path, "rb") as f:
        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-read", body=f
        )
    
    result = poller.result()

    print("Document contains content: ", result.content)

    for idx, style in enumerate(result.styles):
        print(
            "Document contains {} content".format(
                "handwritten" if style.is_handwritten else "no handwritten"
            )
        )

    output_data = []

    for page in result.pages:
        print("----Analyzing Read from page #{}----".format(page.page_number))
        print(
            "Page has width: {} and height: {}, measured with unit: {}".format(
                page.width, page.height, page.unit
            )
        )

        page_data = {
            "page_number": page.page_number,
            "width": page.width,
            "height": page.height,
            "unit": page.unit,
            "lines": []
        }
        for line_idx, line in enumerate(page.lines):
            print(
                "...Line # {} has text content '{}' within bounding box '{}'".format(
                    line_idx,
                    line.content,
                    format_bounding_box(line.polygon),
                )
            )
            line_data = {
                "line_number": line_idx,
                "content": line.content,
                "bounding_box": format_bounding_box(line.polygon)
            }
            page_data["lines"].append(line_data)
        output_data.append(page_data)

        for word in page.words:
            print(
                "...Word '{}' has a confidence of {}".format(
                    word.content, word.confidence
                )
            )

    with open(os.path.join(output_path, "output.json"), "w") as json_file:
        json.dump(output_data, json_file, indent=4)

    print("Output saved to output.json")

    with open(os.path.join(output_path, "output.txt"), "w") as text_file:
        text_file.write("Document contains content: " + result.content + "\n")
        for page in result.pages:
            for line_idx, line in enumerate(page.lines):
                text_file.write(line.content + "\n")

    print("Raw text output saved to output.txt")

    print("----------------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze text from a local PDF file")
    parser.add_argument("file_path", help="Path to the local PDF file")
    parser.add_argument("--endpoint", required=True, help="Azure Document Intelligence endpoint")
    parser.add_argument("--key", required=True, help="Azure Document Intelligence key")
    parser.add_argument("--path", help="Path to save the output files", default=".")
    args = parser.parse_args()
    
    analyze_read(args.file_path, args.endpoint, args.key, args.path)