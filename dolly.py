import os
import pdfkit
import argparse
from xlrd import open_workbook
from docxtpl import DocxTemplate
from jinja2 import FileSystemLoader, Environment

FILE_HTML = 'html'
FILE_DOCX = 'docx'
TMP_HTML_TEMPLATE = 'template.html'


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
def substitution_into_a_template(sheet,path_to_the_template, output_folder):
    if path_to_the_template[-4:] == FILE_HTML:
        print('Invalid file format')
        exit()
    for i in range(1, len(sheet.col(0))):
        doc = DocxTemplate(path_to_the_template)
        doc.render(parser_excel_file(sheet,i))
        doc.save(output_folder + '/Invoice{0}.docx'.format(i))


# Looks for the path to the template. Enters the necessary data into a template
# and saves it in a temporary  html file, then converts it into a PDF
def create_pdf_from_html_template(sheet,path_to_the_template, output_folder):
    if path_to_the_template[-4:] == FILE_DOCX:
        print('Invalid file format')
        exit()

    template_html_file = path_to_the_template.split("/")[-1]
    path_to_the_template = path_to_the_template[:-len(template_html_file)]
    template = Environment(loader=FileSystemLoader(searchpath=path_to_the_template)).get_template(template_html_file)

    for i in range(1, len(sheet.col(0))):
        outputText = template.render(parser_excel_file(sheet,i))
        html_file = open(TMP_HTML_TEMPLATE, 'w')
        html_file.write(outputText)
        html_file.close()
        pdfkit.from_file('template.html', output_folder + '/Invoice{0}.pdf'.format(i))

    os.remove(TMP_HTML_TEMPLATE)


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
    elif args.type_file == 'p':
        create_pdf_from_html_template(args.template, args.output_folder)
    else:
        print('Incorrect key for document type entered')