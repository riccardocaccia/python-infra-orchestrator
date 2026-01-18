import argparse
import yaml
import json
import subprocess
from jinja2 import Template

# Parser
parser = argparse.ArgumentParser(description='Orchestratore Cloud')
parser.add_argument('--token', required=True, help='Token sessione Cloud')
args = parser.parse_args()

# PyYAML configuration reading
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Terraform execution
# Is necessary to pass the token in the --token argument
print("Starting Terraform...")
# 1. Terraform Init
# Usiamo check=True così se l'init fallisce, lo script Python si ferma subito
subprocess.run(["terraform", "init"], check=True)

print("Terraform Apply...")

subprocess.run([
    "terraform", 
    "apply", 
    "-auto-approve", 
    f"-var=cloud_token={args.token}"
], check=True)

print("output retrive...")

tf_output = subprocess.check_output(["terraform", "output", "-json"])
nodes = json.loads(tf_output)

# Inventory Ansible
inventory_template = """
[webservers]
{% for node in nodes %}
{{ node.name }} ansible_host={{ node.ip }}
{% endfor %}
"""
t = Template(inventory_template)
rendered_inventory = t.render(nodes=nodes['vm_info']['value'])

with open("inventory.ini", "w") as f:
    f.write(rendered_inventory)

# Ansible execution
subprocess.run(["ansible-playbook", "-i", "inventory.ini", "setup.yml"])