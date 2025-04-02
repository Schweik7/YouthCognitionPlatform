import camelot
pdf="server/阅读流畅性-三分钟阅读.pdf"
tables = camelot.read_pdf(pdf, pages="all", strip_text='\n')
tables.export("output.csv", f="csv", compress=False)