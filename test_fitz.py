import fitz

def test_pdf():
    doc = fitz.open()
    page = doc.new_page()
    text = "Hello this is a test.\nLine 2 is here."
    # fitz.Rect(x0, y0, x1, y1)
    rect = fitz.Rect(50, 50, 550, 800)
    # 0 = left align
    rc = page.insert_textbox(rect, text, fontsize=12, fontname="helv", align=0)
    if rc < 0:
        print("Text didn't fit")
    doc.save("test_out.pdf")
    print("PDF saved.")

test_pdf()
