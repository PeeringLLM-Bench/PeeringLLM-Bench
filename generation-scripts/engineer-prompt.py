import random

verbs = [
    "Generate", "Write", "Produce", "Create", "Construct", "Output", "Provide", "Develop", "Formulate", "Design"
]
objects = [
    "configuration code", "config", "router configuration", "setup code", "network config", "peering config", "configuration elements",
    "configuration script", "routing config", "peer configuration"
]
actions = [
    "to establish BGP peering", "to configure BGP peering", "for setting up BGP peering", "to form a BGP peering session", 
    "for BGP peer establishment", "to enable BGP peering", "to initiate BGP peering", "to set up a BGP peer", 
    "to configure a BGP session", "for BGP peering setup"
]
sources = [
    "for AS9821", "on AS9821", "in AS9821", "from AS9821", "to be applied to AS9821"
]
targets = [
    "to AS9299", "with AS9299", "towards AS9299", "and AS9299", "for peering with AS9299"
]

# Generate 500 unique combinations
generated_prompts = set()
while len(generated_prompts) < 10:
    prompt = f"{random.choice(verbs)} {random.choice(objects)} {random.choice(actions)} {random.choice(sources)} {random.choice(targets)}."
    generated_prompts.add(prompt)

# Optional: print or save the prompts
for p in list(generated_prompts)[:10]:  # Preview first 10
    print(p)

# Save to file
with open("bgp_prompts.txt", "w") as f:
    for p in generated_prompts:
        f.write(p + "\n")

