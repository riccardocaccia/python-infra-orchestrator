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
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

# Terraform execution
# Is necessary to pass the token in the --token argument
print("Starting Terraform...")
# 1. Terraform Init
# Usiamo check=True così se l'init fallisce, lo script Python si ferma subito
TF_DIR = "terraform"

print("Starting Terraform...")

subprocess.run(
    ["terraform", "init"],
    cwd=TF_DIR,
    check=True
)

print("Terraform Apply...")

subprocess.run(
    [
        "terraform",
        "apply",
        "-auto-approve",
        f"-var=os_token={args.token}"
    ],
    cwd=TF_DIR,
    check=True
)


print("output retrive...")

tf_output = subprocess.check_output(["terraform", "output", "-json"], 
                                     cwd=TF_DIR)
nodes = json.loads(tf_output)

# Ansible PATH
ANSIBLE_DIR = "ansible"
inventory_path = f"{ANSIBLE_DIR}/inventory.ini"

# Inventory Ansible
inventory_template = """
[webservers]
{% for node in nodes %}
{{ node.name }} ansible_host={{ node.ip }} ansible_user=rocky ansible_ssh_private_key_file=~/.ssh/private ansible_ssh_common_args='-o ProxyJump="ubuntu@212.189.205.254 -i ~/.ssh/private" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
{% endfor %}
"""

t = Template(inventory_template)
rendered_inventory = t.render(nodes=nodes['vm_info']['value'])

with open(inventory_path, "w") as f:
    f.write(rendered_inventory)

# Ansible execution

print("Installing ansible roles...")

subprocess.run(
    ["ansible-galaxy", "install", "-r", "requirements.yml"],
    cwd=ANSIBLE_DIR,
    check=True
)

print("Playbook installed...")

subprocess.run(["ansible-playbook", "-i", "inventory.ini", "deploy-galaxy.yml"], 
                cwd=ANSIBLE_DIR,
                check=True)
