from pathlib import Path
import random
import uuid
import subprocess
import string

NQUESTIONS = 20
SCALE = 1.25

def compile_tex_prime(tex_path):
    if not tex_path.exists():
        print(f"File {tex_path} doesn't exist.")
        return

    # Ejecuta pdflatex en el mismo directorio que el archivo .tex
    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", tex_path.name],
        cwd=tex_path.parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False
    )
    # if result.returncode != 0:
    #     print("Compilation Error...")
    #     #print(result.stdout)
    #     print(result.stderr)

def compile_tex(tex_path):
    compile_tex_prime(tex_path)
    compile_tex_prime(tex_path)

def findAnswer(question):
    question_path = Path(question)
    question = question_path.read_text(encoding='utf-8')
    arr = question.split("\n")
    n = next((i for i, s in enumerate(arr) if "\\begin{choices}" in s), -1) # Get first position...
    m = next((i for i, s in enumerate(arr) if  "\\CorrectChoice" in s), -1)
    answer = string.ascii_uppercase[m - n - 1]
    return(answer)

# Create array of options for questions...
A = [f"A{i}" for i in range(1, NQUESTIONS + 1)]
B = [f"B{i}" for i in range(1, NQUESTIONS + 1)]
C = [f"C{i}" for i in range(1, NQUESTIONS + 1)] 
questions_sample = random.sample(A + B + C, NQUESTIONS)  # Sample 20 unique questions...

# Generate 20 input lines...
random_inputs = [f"\t\t\\input{{../DB_Questions/{question}}}" for question in questions_sample]
random_answers = [findAnswer(f"DB_Questions/{question}.tex") for question in questions_sample]

# Generate a unique identifier...
unique_id = uuid.uuid4().hex[:6].upper()  # 6-character unique suffix
print(f"Working on {unique_id} exam...")

# Generate the questions...
questions = f"\t\\begin{{questions}}\n{'\n'.join(random_inputs)}\n\t\\end{{questions}}\n"

# Select exam header...
document_class = "\\documentclass[11pt, addpoints]{exam}"

# Read the header...
header_path = Path("header.tex")
header = header_path.read_text(encoding='utf-8').replace("<<unique_id>>", f"{unique_id}")

# Read the footer...
footer_path = Path("footer.tex")
footer = footer_path.read_text(encoding='utf-8')

# Read the answer table...
table_path = Path("answer_table_template.tex")
table = table_path.read_text(encoding='utf-8').replace("<<nquestions>>", f"{NQUESTIONS + 1}").replace("<<scale>>", f"{SCALE}")
table_path = Path("answer_table.tex")
table_path.write_text(table)
compile_tex(table_path)

exam = f"{document_class}{header}{questions}{footer}"
#print(exam)

# Save the exam as a .tex file
exam_path = Path(f"exams/exam{unique_id}.tex")
exam_path.write_text(exam)

compile_tex(exam_path)

# Select answers header...
document_class = "\\documentclass[11pt, addpoints, answers]{exam}"
exam = f"{document_class}{header}{questions}{footer}"

# Save the solutions as a .tex file
exam_path = Path(f"exams/exam{unique_id}_solutions.tex")
exam_path.write_text(exam)

compile_tex(exam_path)

answers = '\n'.join([f"{unique_id}\t{i + 1}\t{answer}" for i, answer in list(enumerate(random_answers))])
answers_path = Path(f"exams/{unique_id}.tsv")
answers_path.write_text(f"{answers}\n")

print("Done!")
