import os
import subprocess
import pdfkit
import argparse
import json
import subprocess
from xlrd import open_workbook
from docxtpl import DocxTemplate
from jinja2 import FileSystemLoader, Environment
from PyPDF2 import PdfFileWriter, PdfFileReader
from PyPDF2.generic import BooleanObject, NameObject, IndirectObject

FILE_HTML = 'html'
FILE_DOCX = 'docx'
TMP_HTML_TEMPLATE = 'template.html'
FILE_PDF = 'pdf'


# Checks if the folder already exists
# and if not then creates it
def create_folder(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except PermissionError:
        print("Path not found")
        exit()


# Verifies the correctness of the indicated paths
def verification_of_paths(path_1, path_2):
    if not os.path.exists(path_1) or not os.path.exists(path_2):
        print("Path not found")
        exit()
    if not os.access(path_1, os.R_OK) or not os.access(path_2, os.R_OK):
        print("No permission to access the file")
        exit()


# Scans rows of the table and populates the dictionary
# where the key is the name of the colum and the value
# is a record
def parser_excel_file(sheet, number):
    data = {}
    j = 0
    for row in sheet.row(0):
        if type(sheet.row(number)[j].value) == float and sheet.row(number)[j].value == int(sheet.row(number)[j].value):
            data[row.value.replace(" ", "")] = int(sheet.row(number)[j].value)
        else:
            data[row.value.replace(" ", "")] = sheet.row(number)[j].value

        j = j + 1

    return data


# Substitute the value from the dictionary into
# the tamplate and create as many records as the rows
def substitution_into_a_template(sheet, path_to_the_template, output_folder):
    if path_to_the_template[-4:] == FILE_HTML:
        print('Invalid file format')
        exit()
    if path_to_the_template[-3:] == FILE_PDF:
        print('Inavalif file format')
        exit()
    for i in range(1, len(sheet.col(0))):
        doc = DocxTemplate(path_to_the_template)
        exel_data = parser_excel_file(sheet, i)

        doc.render(exel_data)

        if exel_data.get('Name', False):
            doc.save(output_folder + '/' + str(exel_data['Name']) + '.docx')
        else:
            doc.save(output_folder + '/Invoice{}.docx'.format(i))


# Looks for the path to the template. Enters the necessary data into a template
# and saves it in a temporary  html file, then converts it into a PDF
def create_pdf_from_html_template(sheet, path_to_the_template, output_folder):
    if path_to_the_template[-4:] == FILE_DOCX:
        print('Invalid file format')
        exit()

    WKHTMLTOPDF_CMD = subprocess.Popen(
        ['which', os.environ.get('WKHTMLTOPDF_BINARY', 'wkhtmltopdf')],
        # Note we default to 'wkhtmltopdf' as the binary name
        stdout=subprocess.PIPE).communicate()[0].strip()

    pdfkit_config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_CMD)
    template_html_file = path_to_the_template.split("/")[-1]
    path_to_the_template = path_to_the_template[:-len(template_html_file)]
    template = Environment(loader=FileSystemLoader(searchpath=path_to_the_template)).get_template(template_html_file)

    for i in range(1, len(sheet.col(0))):
        exel_data = parser_excel_file(sheet, i)
        outputText = template.render(exel_data)
        html_file = open(TMP_HTML_TEMPLATE, 'w')
        html_file.write(outputText)
        html_file.close()
        if exel_data.get('Name', False):
            pdfkit.from_file('template.html', output_folder + '/' + str(exel_data['Name']) + '.pdf',
                             configuration=pdfkit_config)
        else:
            pdfkit.from_file('template.html', output_folder + '/Invoice{0}.pdf'.format(i), configuration=pdfkit_config)

    os.remove(TMP_HTML_TEMPLATE)


def set_need_appearances_writer(writer):
    try:
        catalog = writer._root_object
        # get the AcroForm tree and add "/NeedAppearances attribute
        if "/AcroForm" not in catalog:
            writer._root_object.update({
                NameObject("/AcroForm"): IndirectObject(len(writer._objects), 0, writer)})

        need_appearances = NameObject("/NeedAppearances")
        writer._root_object["/AcroForm"][need_appearances] = BooleanObject(True)
        return writer

    except Exception as e:
        print('set_need_appearances_writer() catch : ', repr(e))
        return writer


# Reads a pdf-file, searches in it for the same keys from the file
# and dictionary and replaces the values in the file. Saves a new file
def record_in_pdf_template(template, output_folder, data_dict):
    if template[-4:] == FILE_DOCX:
        print('Inavalif file format')
        exit()

    inputStream = open(template, "rb")
    pdf_reader = PdfFileReader(inputStream, strict=False)

    if "/AcroForm" in pdf_reader.trailer["/Root"]:
        pdf_reader.trailer["/Root"]["/AcroForm"].update(
            {NameObject("/NeedAppearances"): BooleanObject(True)})

    pdf_writer = PdfFileWriter()
    set_need_appearances_writer(pdf_writer)
    if "/AcroForm" in pdf_writer._root_object:
        pdf_writer._root_object["/AcroForm"].update(
            {NameObject("/NeedAppearances"): BooleanObject(True)})

    pdf_writer.addPage(pdf_reader.getPage(0))
    pdf_writer.updatePageFormFieldValues(pdf_writer.getPage(0), data_dict)

    outputStream = open(output_folder, "wb")
    pdf_writer.write(outputStream)

    inputStream.close()
    outputStream.close()


# Reads the json file by replacing the values in the dictionary
# and passes it to record_in_pdf_template
def create_pdf_templates(sheet, json_file, template, output_folder):
    data_json = json.load(open(json_file))
    for i in range(1, len(sheet.col(0))):
        data_dict = {}
        data_execl = parser_excel_file(sheet, i)

        for data in data_json:
            for exel_row in data_execl:
                if data_json[data] == exel_row:
                    data_dict[data] = data_execl[exel_row]

        if data_execl.get('Name', False):
            record_in_pdf_template(template, output_folder + '/' + str(data_execl['Name']) + '.pdf', data_dict)
        else:
            record_in_pdf_template(template, output_folder + '/Invoice{0}.pdf'.format(i), data_dict)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Template script')
    parser.add_argument('-t', action="store", default=None, dest="type_file", help="type file: docx - d, pdf - p")
    parser.add_argument('data', action="store", help="path to the data file")
    parser.add_argument('template', action="store", help="path to the template file")
    parser.add_argument('output_folder', action="store", help="folder path with output")

    args = parser.parse_args()

    verification_of_paths(args.data, args.template)

    book = open_workbook(args.data, on_demand=True)
    sheet = book.sheet_by_name(book.sheet_names()[0])

    create_folder(args.output_folder)

    if args.type_file is None:
        print('Enter the file type')
        exit()
    elif args.type_file == 'd':
        substitution_into_a_template(sheet, args.template, args.output_folder)
    elif args.type_file == 'h':
        create_pdf_from_html_template(sheet, args.template, args.output_folder)
    else:
        print('Incorrect key for document type entered')
