#!/usr/bin/env bash
export OS_AUTH_URL=https://keystone.recas.ba.infn.it/v3
export OS_AUTH_TYPE=v3oidcaccesstoken
export OS_PROJECT_ID=7f4c27e308d143e7b6a61b421173bdb1
export OS_PROTOCOL="openid"
export OS_IDENTITY_PROVIDER="recas-bari"
export OS_IDENTITY_API_VERSION=3
export OS_REGION_NAME="RegionOne"
export OS_INTERFACE=public
export OIDC_AGENT_ACCOUNT=rcaccia
export OS_ACCESS_TOKEN=$(oidc-token ${OIDC_AGENT_ACCOUNT})
export OS_AUTH_TOKEN=$OS_ACCESS_TOKEN
echo "OIDC Token retrieved and environment ready."
