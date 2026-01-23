# api/api.py
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
import yaml
import json
import subprocess
from jinja2 import Template
import uuid
import os
from pathlib import Path

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent

# --- input token ---
class DeployRequest(BaseModel):
    token: str

# --- stato dei job ---
jobs = {}  # job_id -> {"status": "pending/running/done/failed", "logs": ""}

# --- orchestrator ---
def run_orchestrator(os_token: str, job_id: str):
    jobs[job_id] = {"status": "running", "logs": ""}

    try:
        work_dir = Path(f"tmp_run_{job_id}")
        work_dir.mkdir(exist_ok=True)

        # --- Terraform ---
        TF_DIR = BASE_DIR / "terraform"
        jobs[job_id]["logs"] += "Starting Terraform init...\n"
        subprocess.run(["terraform", "init"], cwd=TF_DIR, check=True)

        jobs[job_id]["logs"] += "Terraform apply...\n"
        subprocess.run(
            ["terraform", "apply", "-auto-approve", f"-var=os_token={os_token}"],
            cwd=TF_DIR,
            check=True
        )

        # --- output Terraform ---
        tf_output = subprocess.check_output(["terraform", "output", "-json"], cwd=TF_DIR)
        nodes = json.loads(tf_output)

        # --- Inventory Ansible ---
        ANSIBLE_DIR = BASE_DIR / "ansible"
        inventory_path = work_dir / "inventory.ini"

        inventory_template = """
        [webservers]
        {% for node in nodes %}
        {{ node.name }} ansible_host={{ node.ip }} ansible_user=rocky ansible_ssh_private_key_file=~/.ssh/private ansible_ssh_common_args='-o ProxyJump=ubuntu@212.189.205.254 -o StrictHostKeyChecking=no -o ForwardAgent=yes'
        {% endfor %}
        """
        t = Template(inventory_template)
        rendered_inventory = t.render(nodes=nodes['vm_info']['value'])
        with open(inventory_path, "w") as f:
            f.write(rendered_inventory)

        # --- Ansible ---
        jobs[job_id]["logs"] += "Installing Ansible roles...\n"
        subprocess.run(["ansible-galaxy", "install", "-r", "requirements.yml"], cwd=ANSIBLE_DIR, check=True)

        jobs[job_id]["logs"] += "Running Playbook...\n"
        subprocess.run(["ansible-playbook", "-i", str(inventory_path), "deploy-galaxy.yml"], cwd=ANSIBLE_DIR, check=True)

        jobs[job_id]["status"] = "done"

    except subprocess.CalledProcessError as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["logs"] += f"Error: {str(e)}\n"

# --- endpoint ---
@router.post("/deploy")
def deploy(req: DeployRequest, background_tasks: BackgroundTasks):
    # generate job_id
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "pending", "logs": ""}

    background_tasks.add_task(run_orchestrator, req.token, job_id)

    return {"job_id": job_id, "status": "pending"}

@router.get("/deploy/{job_id}")
def get_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return {"error": "Job not found"}
    return {"job_id": job_id, "status": job["status"], "logs": job["logs"]}



