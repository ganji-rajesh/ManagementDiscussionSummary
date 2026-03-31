from fpdf import FPDF

def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.multi_cell(0, 10, "Hello World\nLine 2")
    pdf_bytes = pdf.output()
    with open("test.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("PDF bytes generated.", type(pdf_bytes))

create_pdf()
