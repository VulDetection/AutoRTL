from openai import OpenAI
import pandas as pd
from openpyxl import Workbook
from openpyxl import load_workbook
import os
from pathlib import Path
from tqdm import tqdm
import json


input_path = Path('../rtllm_v1_1/problems_rtllm.jsonl')
output_path = Path('../rtllm_v1_1/problems_rtllm_gpt4o_cot.jsonl')


df = pd.read_json('../rtllm_v1_1/problems_rtllm.jsonl',lines=True)

# 设置OpenAI客户端
client = OpenAI(
    base_url='',
    api_key='',
)


def analyze_code(Prompt):
    messages = [
        {
            "role": "user",
            "content": "You are an expert software engineer specializing in algorithmic reasoning for hardware and code implementation."
                       "Your task is to transform a plain Verilog (or code) design prompt into a concise General Chain-of-Thought (CoT) reasoning sequence that reflects how a developer logically plans the implementation."
                       "Given a natural-language Verilog or hardware design requirement (the “Input Prompt”), "
                       "rewrite it into a step-by-step reasoning chain (CoT) that captures how to design and implement the described functionality."
                       "Each step should:"
                       "Be short, clear, and written in natural language only (no code)."
                       "Follow logical implementation reasoning, not syntax-level details."
                       "Include key design intentions, modular breakdown, and signal or logic relationships if relevant."
                       "Avoid structural terms like “always block” or “assign” — focus on function-level thinking."
                       "Example:"
                       "Input Prompt:"
                       "Please act as a professional verilog designer. Implement a module of a 16-bit full adder in combinational logic."
                       "Module name: adder_16bit."
                       "Input ports: a[15:0]: 16-bit input operand A. b[15:0]: 16-bit input operand B. Cin: Carry-in input."
                       "Output ports: y[15:0]: 16-bit output representing the sum of A and B. Co: Carry-out output."
                       "Implementation: In the adder_16bit module, you need to design a small bit-width adder (8-bit adder),"
                       " which will be instantiated multiple times. Give me the complete code."
                       "Output CoT:"
                       "1. I need to implement a 16-bit adder that takes two 16-bit inputs a and b, and a carry-in Cin.  "
                       "2. I can create a smaller 8-bit adder module to simplify the design.  "
                       "3. Each 8-bit adder will output an 8-bit sum and a carry-out.  "
                       "4. I will instantiate two 8-bit adders: the first handles bits [7:0], the second handles bits [15:8].  "
                       "5. The carry-out of the first adder connects to the carry-in of the second adder.  "
                       "6. The final carry-out Co comes from the second adder.  "
                       "7. The output y is the concatenation of the two 8-bit results."
                       "Input Prompt: ``` {} ```".format(Prompt),
        }
    ]

    response = client.chat.completions.create(
        messages=messages,
        # model="gpt-5",
        model="gpt-4o",
        # temperature= 0.1,
        # top_p=1,
    )

    full_text = response.choices[0].message.content.strip()
    return {'CoT': full_text}  # 不再截取
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
        while score < 90:  #
            chk = consistency_check(item['prompt'], item['cot'])
            score = chk['score']
            if score < 90:
                cot_dict = analyze_code(item['prompt'])
                cot_raw = cot_dict.get('CoT', '')
                item['cot'] = cot_raw[len('Output CoT:'):].lstrip() if cot_raw.startswith('Output CoT:') else cot_raw
        # ===================================

        print("item:::", item['cot'])
        fw.write(json.dumps(item, ensure_ascii=False) + '\n')