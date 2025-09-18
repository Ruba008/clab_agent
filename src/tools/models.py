import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# Model to NLU to understand in technical terms what the user wants 
def intent_explain(client_question: str):
    MODEL_NAME = "google/flan-t5-base"
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float16
    ).to(DEVICE)
    
    prompt = f"""Transform the client's question into an ultra-concise technical reformulation for networking and Containerlab.

    Rules:
    - Replace plain language with technical terms.
    - Use Containerlab nomenclature whenever relevant. Refer to this keyword list for guidance:
    - Top-Level: name, prefix, mgmt, network, ipv4-subnet, ipv6-subnet
    - Topology Block: defaults, kinds, nodes, links
    - Node Attributes: name, kind, image, startup-config, binds, ports, env, exec, mgmt-ipv4, mgmt-ipv6, config, vars
    - Link Attributes: endpoints, vars, mtu
    - Do not invent unstated requirements; keep it generic when necessary.
    - Output in TWO lines only.
    - Line 1 (≤2 sentences, ≤40 words): 'Technical reformulation: ...'
    - Line 2: 'Keywords: ' 8–15 terms in English, lowercase, comma-separated, no repetitions.
    - No extra markdown, lists, or comments.

    ---
    EXAMPLE 1
    CLIENT QUESTION:
    I need to connect two Docker containers on the same network so they can talk to each other.

    CORRECT OUTPUT:
    Technical reformulation: Define a Containerlab topology with two nodes of kind 'docker' connected via a single L2 link.
    Keywords: containerlab, topology, nodes, kind, docker, link, l2, endpoints, interfaces
    ---

    NOW, DO THE SAME FOR THIS QUESTION:
    CLIENT QUESTION:
    {client_question}

    CORRECT OUTPUT:
    """
    
    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            num_beams=4,
            early_stopping=True
        )
    
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    del model
    del tokenizer
    del inputs
    del outputs
    torch.cuda.empty_cache()
    
    return result