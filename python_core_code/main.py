import argparse
import json
import subprocess
import os
from jinja2 import Template

parser = argparse.ArgumentParser(description='Orchestratore Cloud')
parser.add_argument('--token', required=True, help='Token sessione Cloud')
args = parser.parse_args()

TF_DIR = "terraform"
ANSIBLE_DIR = "ansible"
JSON_FILE = "job_test.json" # Assicurati che il nome sia corretto

with open(JSON_FILE, "r") as f:
    job = json.load(f)

cloud = job['cloud_provider']
inputs = job['inputs']

print(f"Esecuzione Job: {job['job_id']}")

# 3. Terraform Init
subprocess.run(["terraform", "init"], cwd=TF_DIR, check=True)

# 4. Terraform Apply
print("Esecuzione Terraform Apply...")
apply_cmd = [
    "terraform", "apply", "-auto-approve",
    f"-var=auth_url={cloud['auth_url']}",
    f"-var=os_tenant_id={cloud['os_tenant_id']}",
    f"-var=region={inputs['region']}",
    f"-var=flavor_name={inputs['flavor_name']}",
    f"-var=image_name={inputs['image_name']}",
    f"-var=bastion_ip={inputs['bastion_ip']}",
    f"-var=ssh_public_key={inputs['ssh_public_key']}",
    f"-var=laniakea_description={job['laniakea_description']}",
]

subprocess.run(apply_cmd, cwd=TF_DIR, check=True)

print("Recupero output Terraform...")
tf_output = subprocess.check_output(["terraform", "output", "-json"], cwd=TF_DIR)
nodes = json.loads(tf_output)
