This repository corresponds to the paper "Follow the Playbook: Expert Behavior Model-driven RTL Code Generation Based on Large Language Models."

# How to use

# Step1: 

In the to_COT folder, we transform ordinary prompts into basic COT prompting and our module-level design prompting framework.

# Step2: 
In the ResBench folder, generate_api.py generates code using foundational models such as GPT, and generate_LLMs.py generates code using Code Models.
The other files in the ResBench folder contain our pre-generated code.functional_correctness.py is a computational metric.


# Step3: 
In the RTLLM V1.1 folder, generate_api.py generates code using foundational models such as GPT, and generate_LLMs.py generates code using Code Models.
The other files in the ResBench folder contain our pre-generated code.functional_correctness.py is a computational metric.

The figure below shows the behavioral model we have constructed. 

<img width="369" height="132" alt="image" src="https://github.com/user-attachments/assets/438c8c9c-3a09-4165-bc8f-a20738f49d9f" />


The figure below shows our workflow diagram.

<img width="449" height="164" alt="image" src="https://github.com/user-attachments/assets/c2e50dc0-c49a-4f1a-ae74-23172bb2cd17" />

