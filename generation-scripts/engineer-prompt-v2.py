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
    "for {local_as}", "on {local_as}", "in {local_as}", "from {local_as}", "to be applied to {local_as}"
]
targets = [
    "to {remote_as}", "with {remote_as}", "towards {remote_as}", "and {remote_as}", "for peering with {remote_as}"
]

# Generate 500 unique combinations
generated_prompts = set()
i = 0
while len(generated_prompts) < 10:
    if i >= 5: 
        prompt = f"{verbs[i]} {objects[i]} {actions[i]} {random.choice(sources)} {random.choice(targets)}."
    else: 
        prompt = f"{verbs[i]} {objects[i]} {actions[i]} {sources[i]} {targets[i]}."
    generated_prompts.add(prompt)
    i += 1 

# Optional: print or save the prompts
for p in list(generated_prompts)[:10]:  # Preview first 10
    print(p)

# Save to file
with open("bgp_prompts-10.txt", "w") as f:
    for p in generated_prompts:
        f.write(p + "\n")

