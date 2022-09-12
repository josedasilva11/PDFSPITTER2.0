import os
from io import BytesIO, StringIO

import dateutil.parser
from PyPDF2 import PdfReader, PdfWriter, PdfFileReader
from PyPDF2.generic import createStringObject, NameObject
from flask import send_file
from fpdf import FPDF

from pdf_app.pdf_test import fill_pdf

PDF_CONSTANTS = {
    1: {"file_name": "root_2", "footer": "1. ORIGINAL"},
    2: {"file_name": "root_2_page2", "footer": "2. AUTORIDADE"},
    3: {"file_name": "root_2_page3", "footer": "3. CLIENTE"},
}


def get_store_key():
    with open("store_id.txt") as f:
        lines = f.readlines()
        return lines[0].strip()


STORE_KEY = get_store_key()


def print_pdf(data):
    fix_dates(data)
    data["text_48csyn"] = STORE_KEY + str(data["id"])
    data["textarea_1deug"] = data["obs"]
    data["text_38bfne"] = data["car_license"]
    buf = BytesIO()
    fill_pdf("root_2.pdf", buf, data)
    buf.seek(0)
    return send_file(
        buf,
        mimetype="application/pdf",
        download_name=f"{STORE_KEY}{data['client_renter_name']}.{data['id']}.pdf",
    )


def add_mark(out_file, text):
    pdf = FPDF(format="letter", unit="pt")

    pdf.add_page()
    pdf_style = "B"

    pdf.set_font("Arial", size=7)
    pdf.set_xy(480, 730)
    pdf.cell(1, 1, txt=text, ln=0)
    pdf.output(out_file + "_tmp.pdf")
    pdf.close()

    reader = PdfReader(out_file)
    overlay_pdf = PdfReader(out_file + "_tmp.pdf")
    writer = PdfWriter()

    reader.getPage(0).mergePage(overlay_pdf.getPage(0))
    writer.addPage(reader.getPage(0))
    writer.set_need_appearances_writer()
    writer.write(out_file + "_marked.pdf")
    os.unlink(out_file + "_tmp.pdf")


def fix_dates(data):
    for key in data:
        if key.count("_date") or key.count("date_"):
            if isinstance(data[key], str):
                try:
                    data[key] = dateutil.parser.parse(data[key]).strftime("%d/%m/%Y")

                except BaseException as b:
                    print(b)
            else:
                data[key] = data[key].strftime("%d/%m/%Y")


def add_suffix(data, param):
    new_dict = {}
    for a in data:
        new_dict[a + param] = data[a]

    return new_dict


def generate_pdf_file(pdf_name, data, index=0):
    with open(pdf_name, "wb") as outfile:
        if index > 0:
            data["footertext"] = PDF_CONSTANTS[index]["footer"]
        fill_pdf(
            f"{PDF_CONSTANTS[index]['file_name']}.pdf",
            outfile,
            data if index == 1 else add_suffix(data, f"_page{index}"),
        )
        return pdf_name


def print_three_pdf(data):
    pdfs = []
    fix_dates(data)
    buf = BytesIO()
    data["text_38bfne"] = data["car_license"]
    data["textarea_1deug"] = data["obs"]
    data["text_48csyn"] = STORE_KEY + str(data["id"])
    for i in range(1, 4):
        pdf_name = f"{STORE_KEY}{data['client_renter_name']}.{data['id']}_{i}.pdf"
        pdfs.append(generate_pdf_file(pdf_name, data, i))

    writer = PdfWriter()
    # Merge the overlay page onto the template page
    files = []
    for pdf in pdfs:
        reader = PdfReader(pdf)
        for page in reader.pages:
            writer.addPage(page)

    writer.set_need_appearances_writer()
    writer.write(buf)
    for item in files:
        item.close()

    buf.seek(0)
    for pdf in pdfs:
        os.unlink(pdf)

    return send_file(
        buf,
        mimetype="application/pdf",
        download_name=f"{data['client_renter_name']}{STORE_KEY}.{data['id']}_combined.pdf",
    )
