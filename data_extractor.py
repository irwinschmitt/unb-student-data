from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter
import io
import camelot
import re
import sys
import json


def acceptable_file(file_name):
    if re.findall("[.]", file_name):
        return True
    else:
        return False


def extract_text(pdf_path):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle)
    page_interpreter = PDFPageInterpreter(resource_manager, converter)

    with open(pdf_path, 'rb') as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            page_interpreter.process_page(page)

        text = fake_file_handle.getvalue()

    converter.close()
    fake_file_handle.close()

    if text:
        return text


def get_info(text):
    return {
        "nome": re.search("(?<=Nome:)(.*)(?=Curso:)", text).group(),
        "matricula": re.search("(?<=Matrícula:)(.*)(?=Vínculo:)", text).group(),
        "vinculo": re.search("(?<=Vínculo:)(.*)(?=Nome:)", text).group(),
        "nivel": re.search("(?<=Nível:)(.*)(?=Matrícula:)", text).group(),
        "curso": re.search(
            "(?<=Curso:)(.*)(?=TURMAS MATRICULADAS:)", text).group() if re.search(
            "(?<=Curso:)(.*)(?=TURMAS MATRICULADAS:)", text) else "",
        "periodo": re.search("(?<=Período Letivo:)(.*)(?=Nível:)", text).group()
    }


def get_table(file_name):
    return camelot.read_pdf(file_name)[0].df


if __name__ == '__main__':
    if (len(sys.argv) != 2):
        exit("Please, follow the format example: 'python data_extractor.py file_input.pdf'.")

    file_path = sys.argv[1].split(".")[0] + ".pdf"

    pdf_text = extract_text(file_path)

    user_data = get_info(pdf_text)

    pdf_table = get_table(file_path)

    data = user_data
    data["componentes"] = []

    for row in pdf_table.drop(0).itertuples():
        componente = {
            "cod": row[1],
            "nome": re.split("\n", row[2])[0],
            "professor": re.split("\n", row[2])[1],
            "tipo": re.search("(?<=Tipo: )(.*)(?= \n)", row[2]).group(),
            "local": re.search("(?<=Local: )(.*)", row[2]).group() if re.search("(?<=Local: )(.*)", row[2]) else "",
            "turma": row[3],
            "status": row[4],
            "horario": row[5],
        }
        data["componentes"].append(componente)

    with open(sys.argv[1].split(".")[0] + ".json", "w") as fp:
        json.dump(data, fp)

