#!/usr/bin/env python3
# Author: cbk914
import argparse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

def display_help():
    print("Usage: python script.py -c contract [-o output] [-p pdf] [-h]")
    print("Checks a smart contract for common security vulnerabilities using Mythril, Oyente, Securify, Slither, SmartCheck")
    print("  -c contract      path to the smart contract file")
    print("  -o output       specify the output file name")
    print("  -p pdf          generate a pdf file")
    print("  -h              display this help and exit")
    exit(0)

# Validate the input file path
def validate_file_path(file_path):
    if not os.path.isfile(file_path):
        print("[ERROR] Invalid file path: " + file_path)
        display_help()

# Parse command line arguments
parser = argparse.ArgumentParser(description="Checks a smart contract for common security vulnerabilities using Mythril, Oyente, Securify, Slither, SmartCheck")
parser.add_argument("-c", "--contract", type=str, required=True, help="path to the smart contract file")
parser.add_argument("-o", "--output", type=str, help="specify the output file name")
parser.add_argument("-p", "--pdf", help="generate a pdf report", action='store_true')
args = parser.parse_args()

validate_file_path(args.contract)

# Read the bytecode of the smart contract
with open(args.contract, "r") as file:
    bytecode = file.read()

# Create a disassembly object
disassembly = Disassembly(bytecode)

# Perform the security analysis using Mythril
issues = analysis.analyze(disassembly)

# Perform the security analysis using Oyente
oyente_issues = oyente.analyze(disassembly)

# Perform the security analysis using Slither
slither_issues = slither.analyze(disassembly)

# Perform the security analysis using SmartCheck
smartcheck_issues = smartcheck

# Perform the security analysis using Securify
securify_issues = securify.analyze(disassembly)

if args.pdf:
    # Create a PDF file
    if args.output:
        doc = SimpleDocTemplate(args.output, pagesize=landscape(letter))
    else:
        doc = SimpleDocTemplate("output.pdf", pagesize=landscape(letter))
    data = []
    t = Table([["Mythril"], ["Oyente"], ["Slither"], ["SmartCheck"], ["Securify"]])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    data.append(t)
    for issue in issues:
        data.append(["Mythril: "+issue.description])
    for issue in oyente_issues:
        data.append(["Oyente: "+issue.description])
    for issue in slither_issues:
        data.append(["Slither: "+issue.description])
    for issue in smartcheck_issues:
        data.append(["SmartCheck: "+issue.description])
    for issue in securify_issues:
        data.append(["Securify: "+issue.description])
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    doc.build([t])
    print("PDF file created successfully")
else:
    # Print the issues to the output file
    if args.output:
        with open(args.output, "w") as file:
            for issue in issues:
                file.write("Mythril: "+issue.description+"\n")
            for issue in oyente_issues:
                file.write("Oyente: "+issue.description+"\n")
            for issue in slither_issues:
                file.write("Slither: "+issue.description+"\n")
            for issue in smartcheck_issues:
                file.write("SmartCheck: "+issue.description+"\n")
            for issue in securify_issues:
                file.write("Securify: "+issue.description+"\n")
        print("Text file created successfully")
    else:
        for issue in issues:
            print("Mythril: "+issue.description)
        for issue in oyente_issues:
            print("Oyente: "+issue.description)
        for issue in slither_issues:
            print("Slither: "+issue.description)
        for issue in smartcheck_issues:
            print("SmartCheck: "+issue.description)
        for issue in securify_issues:
            print("Securify: "+issue.description)
