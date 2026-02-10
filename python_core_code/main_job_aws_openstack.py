import argparse
import json
import subprocess
import os
from jinja2 import Template

parser = argparse.ArgumentParser(description='Orchestratore Cloud')
parser.add_argument('--token', required=False, help='Token sessione Cloud')
args = parser.parse_args()

TF_DIR = "terraform"
ANSIBLE_DIR = "ansible"
JSON_FILE = "job.json" # Assicurati che il nome sia corretto

with open(JSON_FILE, "r") as f:
    job = json.load(f)

cloud = job['cloud_provider']
inputs = job['inputs']

# in comune
apply_cmd = ["terraform", "apply", "-auto-approve"]

apply_cmd.append(f'-var=laniakea_description="{job["laniakea_description"]}"')

print(f"Esecuzione Job: {job['job_id']}")

# Terraform Init
subprocess.run(["terraform", "init"], cwd=TF_DIR, check=True)


#Terraform Apply
print("Esecuzione Terraform Apply...")

if cloud['name'] == "aws":
    apply_cmd.extend([
        f"-var=aws_access_key={cloud['aws_access_key']}",
        f"-var=aws_secret_key={cloud['aws_secret_key']}",
        f"-var=aws_region={inputs['aws_region']}",
        f"-var=galaxy_instance_type={inputs['galaxy_instance_type']}",
        f"-var=public_ssh_key={inputs['public_ssh_key']}",
        f"-var=bastion_ip={inputs['bastion_ip']}"
    ])

elif cloud['name'] == "openstack":
      apply_cmd.extend([
         f"-var=auth_url={cloud['auth_url']}",
         f"-var=os_tenant_id={cloud['os_tenant_id']}",
         f"-var=region={inputs['region']}",
         f"-var=flavor_name={inputs['flavor_name']}",
         f"-var=image_name={inputs['image_name']}",
         f"-var=bastion_ip={inputs['bastion_ip']}",
         f"-var=ssh_public_key={inputs['ssh_public_key']}",
        ])
      pass

subprocess.run(apply_cmd, cwd=TF_DIR, check=True)

print("Recupero output Terraform...")
tf_output = subprocess.check_output(["terraform", "output", "-json"], cwd=TF_DIR)
nodes = json.loads(tf_output)
