# combined json ''api''

import json
import subprocess
from typing import Optional, Dict
from pydantic import BaseModel, Field, ValidationError, model_validator
###############
import argparse
###############

#se mancano qui pydantic blocca, ereditiamo da pyd. basemodel
class OpenStackInputs(BaseModel):
    flavor: str
    image: str
    storage_size: Optional[str] = None
    os_distribution: Optional[str] = None
    os_version: Optional[str] = None

    model_config = {"extra": "ignore"} # extra = "forbid" per lanciare errore qualora ci sia un campo che non vogliamo

class AWSInputs(BaseModel):
    instance_type: str
    image: str
    storage_size: Optional[str] = None
    os_distribution: Optional[str] = None
    os_version: Optional[str] = None
    model_config = {"extra": "ignore"}

# -----------------
# provider
# -----------------

class OpenStackProvider(BaseModel):
    os_auth_url: str
    os_project_id: str
    os_region_name: str
    ssh_key: str
    private_network_proxy_host: Optional[str] = None
    template: Optional[Dict] = None
    inputs: OpenStackInputs
    model_config = {"extra": "ignore"}

class AWSProvider(BaseModel):
    region: str
    ssh_key: str
    aws_access_key: str
    aws_secret_key: str
    bastion_ip: Optional[str] = None
    template: Optional[Dict] = None
    inputs: AWSInputs
    model_config = {"extra": "ignore"}

class CloudProviders(BaseModel):
    aws: Optional[AWSProvider] = None
    openstack: Optional[OpenStackProvider] = None
    model_config = {"extra": "forbid"}

# ---------------
# choose only one
# ---------------
#    @model_validator(mode="after") # after (or before) validation 
#    def exactly_one_provider(self):
#        if bool(self.aws) == bool(self.openstack):
#            raise ValueError(
#                    "Devi specificare solamente un provider tra 'aws' o 'openstack'"  # TODO: openstack garr, recas, ..#            )
#        return self

class OrchestratorConfig(BaseModel):
    target_provider: str
    desired_orchestrator: str = "terraform"   # AUTOMATICO TODO:altri non ancora implementati
    endpoint: Optional[str] = None            # TODO: come mettere endpoint automatico? poi ci penso
    model_config = {"extra": "ignore"}

class Job(BaseModel):
    job_id: str
    description: Optional[str] = None  # TODO: si potrebbe mettere una description artificiale con [user] [data] ha creato [xxxxx]
    selected_provider: str
    orchestrator: OrchestratorConfig
    cloud_providers: CloudProviders
    model_config = {"extra": "ignore"}

    @model_validator(mode="after")
    def validate_provider_selection(self):
        provider = self.selected_provider.lower()
        self.orchestrator.target_provider = provider

        if provider == "aws":
            if not self.cloud_providers.aws:
                raise ValueError("AWS selezionato ma configurazione aws mancante")
        elif provider == "openstack":
            if not self.cloud_providers.openstack:
                raise ValueError("OpenStack selezionato ma configurazione mancante")
        else:
            raise ValueError(f"Provider non supportato: {provider}")

        return self

def run_terraform(job: Job):

    provider_name = job.orchestrator.target_provider.lower()

    apply_cmd = ["terraform", "apply", "-auto-approve"]

    print(f"Esecuzione job: {job.job_id}")
    print(f"Orchestrator scelto: {job.orchestrator.desired_orchestrator}") # solo terraform ora

    if provider_name == "aws":
        aws = job.cloud_providers.aws

        apply_cmd.extend([
            f"-var=aws_access_key={aws.aws_access_key}",
            f"-var=aws_secret_key={aws.aws_secret_key}",
            f"-var=aws_region={aws.region}",
            f"-var=instance_type={aws.inputs.instance_type}",
            f"-var=image={aws.inputs.image}",
            f"-var=ssh_key={aws.ssh_key}"
        ])

    elif provider_name == "openstack":
        os = job.cloud_providers.openstack

        apply_cmd.extend([
            f"-var=auth_url={os.os_auth_url}",          
            f"-var=os_token={token}",           ################
            f"-var=os_tenant_id={os.os_project_id}",      
            f"-var=region={os.os_region_name}",         
            f"-var=flavor_name={os.inputs.flavor}",     
            f"-var=image_name={os.inputs.image}",       
            f"-var=ssh_public_key={os.ssh_key}",    
            f"-var=bastion_ip={os.private_network_proxy_host}"
        ])

    # INIT
    subprocess.run(["terraform", "init"], cwd="terraform", check=True)

    # APPLY
    subprocess.run(apply_cmd, cwd="terraform", check=True)

    # OUTPUT
    tf_output = subprocess.check_output(
        ["terraform", "output", "-json"],
        cwd="terraform"
    )

    return json.loads(tf_output)


if __name__ == "__main__":
    ############################################################################
    parser = argparse.ArgumentParser(description="Cloud Orchestrator")
    parser.add_argument("--token", required=True, help="Token sessione Cloud")
    args = parser.parse_args()
    token = args.token
    ############################################################################
    with open("combined_json.json") as f:
        raw_data = json.load(f)

    try:
        job = Job(**raw_data)  # validazione automatica, spacchetta il dizionario
    except ValidationError as e:
        print("Errore di validazione:")
        print(e.json())
        exit(1)

    if job.orchestrator.desired_orchestrator == "terraform":
        output = run_terraform(job)
        print("Output Terraform:")
        print(output)

    else:
        print("Orchestrator non ancora implementato")

