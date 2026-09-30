from openai import OpenAI
import pandas as pd
from openpyxl import Workbook
from openpyxl import load_workbook
import os
from pathlib import Path
from tqdm import tqdm
import json


input_path = Path('../')
output_path = Path('../')


df = pd.read_json('../human/problems_human.jsonl',lines=True)


client = OpenAI(
    base_url='',
    api_key='',
)



def analyze_code(Prompt):
    messages = [
        {
            "role": "user",
            "content": "You are an expert Verilog hardware designer and logic reasoning instructor."
                       "Your task is to transform a plain Verilog design prompt into a structured Verilog Chain-of-Thought (CoT-V) reasoning process."
                       "The CoT-V should describe how a professional designer thinks before writing Verilog code."
                       "Given a natural-language Verilog design requirement (the “original prompt”), rewrite it into a structured CoT-V reasoning chain with six concise steps:"
                       "Define Module — Identify the module name, purpose, and I/O ports."
                       "Declare Internal Signals — Determine key internal wires, registers, or intermediate variables."
                       "Design Module — Describe the overall logic design or hierarchy plan."
                       "Instantiate Modules — Explain how submodules (if any) are instantiated and connected."
                       "Continuous Assignment Analysis — Explain the logic and dependencies implemented via assign statements."
                       "Always Block Analysis — Explain the sequential or procedural behavior implemented in always blocks."
                       "Each step should be expressed purely in natural language — do not include Verilog code. "
                       "Keep sentences concise, engineering-oriented, and faithful to the original intent."
                       ""
                       "Example:"
                       "Input Prompt:"
                       "Please act as a professional verilog designer. Implement a module of a 16-bit full adder in combinational logic."
                       "Module name: adder_16bit."
                       "Input ports: a[15:0]: 16-bit input operand A. b[15:0]: 16-bit input operand B. Cin: Carry-in input."
                       "Output ports: y[15:0]: 16-bit output representing the sum of A and B. Co: Carry-out output."
                       "Implementation: In the adder_16bit module, you need to design a small bit-width adder (8-bit adder),"
                       " which will be instantiated multiple times. Give me the complete code."
                       "Output CoT:"
                       "1. Define Module. The module adder_16bit performs a 16-bit addition of two inputs and a carry-in, producing a 16-bit sum and a carry-out.  "
                       "2. Declare Internal Signals. Internal wires are used to connect intermediate carries and partial sums between 8-bit submodules. "
                       "3. Design Module. The design divides the 16-bit addition into two 8-bit operations for modularity and reusability.  "
                       "4. Instantiate Modules. Two 8-bit adder modules are instantiated: the first processes bits [7:0] and generates a carry, which is input to the second adder handling bits [15:8]. "
                       "5. Continuous Assignment Analysis. Each 8-bit adder continuously drives its output sum and carry; the final sum is formed by concatenating upper and lower results.  "
                       "6. Always Block Analysis. No sequential behavior is used since this is a purely combinational adder. "
                       "Input Prompt: ``` {} ```".format(Prompt),
        }
    ]

    response = client.chat.completions.create(
        messages=messages,
        # model="gpt-5",
        # model="gpt-5",
        model="gpt-4o",
        # temperature= 0.1,
        # top_p=1,
    )

    full_text = response.choices[0].message.content.strip()
    return {'CoT': full_text}
    # for message in response.choices:
    #     print(message.message.content)
    # result = {}
    # for message in response.choices:
    #     for line in message.message.content.split('\n'):
    #         if line.startswith('Output CoT:'):
    #             result['CoT'] = line[len('Output CoT: '):].strip()
    # return result

def consistency_check(prompt: str, cot: str) -> dict:
    chk_msg = [
        {"role": "system", "content":
         "You are a design-review expert. Given the original prompt and its Chain-of-Thought (CoT), "
         "judge whether the CoT accurately and completely reflects the prompt's intent.\n"
         "Output format:\n"
         "Score: <0-100>\n"
         "OK: <yes/no>\n"
         "Comment: <one sentence>\n"
         "FixedCoT: <if not ok, write a corrected CoT; else, write none>"},

        {"role": "user", "content": f"Prompt: {prompt}\nCoT: {cot}"}
    ]
    try:
        resp = client.chat.completions.create(model="gpt-3.5-turbo", messages=chk_msg, temperature=0)
        txt = resp.choices[0].message.content.strip()
    except Exception as e:
        txt = f"Score: 0\nOK: no\nComment: API error {e}\nFixedCoT: none"


    score, ok, comment, fixed = 0, False, "", ""
    for line in txt.splitlines():
        if line.startswith("Score:"):
            score = int(line.split(":", 1)[1].strip())
        elif line.startswith("OK:"):
            ok = line.split(":", 1)[1].strip().lower() == "yes"
        elif line.startswith("Comment:"):
            comment = line.split(":", 1)[1].strip()
        elif line.startswith("FixedCoT:"):
            fixed = line.split(":", 1)[1].strip()
            if fixed.lower() == "none":
                fixed = ""
    return {"score": score, "ok": ok, "comment": comment, "cot_fixed": fixed}

with output_path.open('w', encoding='utf-8') as fw:
    for line in tqdm(input_path.read_text(encoding='utf-8').splitlines(), desc='Processing'):
        if not line.strip():
            continue
        item = json.loads(line)                     #
        cot_dict = analyze_code(item['prompt'])     #
        # cot_raw = cot_dict.get('CoT', '')
        # item['cot'] = cot_raw.removeprefix('Output CoT:').lstrip()

        cot_raw = cot_dict.get('CoT', '')
        item['cot'] = cot_raw[len('Output CoT:'):].lstrip() if cot_raw.startswith('Output CoT:') else cot_raw


        score = 0
        while score < 90:
            chk = consistency_check(item['prompt'], item['cot'])
            score = chk['score']
            if score < 90:
                cot_dict = analyze_code(item['prompt'])
                cot_raw = cot_dict.get('CoT', '')
                item['cot'] = cot_raw[len('Output CoT:'):].lstrip() if cot_raw.startswith('Output CoT:') else cot_raw
        # ===================================

        print("item:::", item['cot'])
        fw.write(json.dumps(item, ensure_ascii=False) + '\n')