<img src="./app/static/csq-logo.png?raw=true" width="400"/>

# CQ-Qube

[![CS-Cube Docker Image](https://github.com/ukbea/cs-qube/actions/workflows/build.yml/badge.svg)](https://github.com/ukbea/cs-qube/actions/workflows/build.yml)

CS-Qube is a demo bundle of a Kubernetes cluster deployment using **[kops](https://kops.sigs.k8s.io/)** and a demo **[Flask](https://flask.palletsprojects.com/en/3.0.x/)** application that is meant to be deployed on the same cluster using **[Helm](https://helm.sh/)** and **[Ansible](https://www.ansible.com/)**.


Below is the list of files with descriptions included in this repository.

| Usage | Files |
| --- | --- |
| Ansible Inventory | inventory/* |
| Ansible roles | roles/** |
| Ansible playbook | deploy.yml |
| Helm chart | cs-qube/** |
| Flash application | app/** |
| Kubernetes static manifest | manifest.yml |

## Cluster

Kubernetes cluster deployment is handled by preparing a `kops` cluster configuration. The cluster configuration is stored in [cluster.yml](./cluster.yml).


### Architecture

![Architecture](./docs/architecture.svg)


### Deployment

[Deploying Kubernetes clusters on AWS](https://kops.sigs.k8s.io/getting_started/aws/) using `kops` requires an S3 state bucket to be created with ]specific configuration](https://kops.sigs.k8s.io/getting_started/aws/#cluster-state-store).

Create the state bucket

```bash
aws s3api create-bucket \
    --bucket prefix-example-com-state-store \
    --region us-east-1
```

Enable versioning on state bucket.

```bash
aws s3api put-bucket-versioning --bucket prefix-example-com-state-store  --versioning-configuration Status=Enabled
```

Enable public ACL on the bucket.

```bash
aws s3api create-bucket \
    --bucket prefix-example-com-oidc-store \
    --region us-east-1 \
    --object-ownership BucketOwnerPreferred
aws s3api put-public-access-block \
    --bucket prefix-example-com-oidc-store \
    --public-access-block-configuration BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false
aws s3api put-bucket-acl \
    --bucket prefix-example-com-oidc-store \
    --acl public-read
```

Prepare environment variables for simplifying `kops` commands.

```bash
export NAME=myfirstcluster.example.com
export KOPS_STATE_STORE=s3://prefix-example-com-state-store
```

Create cluster.

```bash
kops create cluster -f cluster.yml
kops update cluster --name ${NAME} --yes --admin
```

Once the cluster is created `kops` will add a context in your `kubectl` config with admin credentials.

Delete cluster.

```bash
kops delete cluster --name ${NAME}
```

## Application

CS-Qube is a demo FLask application that lets users upload CSV files. It parses the CSV and uploads to the configured storage bucket.

<img src="./docs/screenshot.png?raw=true" width="1024"/>

### Build

Application Docker image is automatically built and pushed to Docker Hub repository [ukbe/cs-qube](https://hub.docker.com/r/ukbe/cs-qube) by [workflow](./.github/worklows/build.yml).

You can build the application on your local running the command below.

```bash
docker build -t cs-qube .
```

### Deployment

CS-Qube deployment requires `ansible-playbook` and `helm` commands to be installed. You also need to prepare the `kubeconfig` with access to target cluster. You can change the [kubeconfig path](inventory/dev/group_vars/all.yml#L7) that will be used to access the cluster.

`ansible-playbook` installs the Helm Chart with pre-defined variables per environment. You need to specify the relevant environment inventory folder in the command. For example `inventory/<environment>`. Environments currently set up include; `dev`, `qa`, `prod`. 

Deploy development environment.

```bash
ansible-playbook -i inventory/dev deploy.yml
```

### Undeploy

In order to remove the CS-Qube deployment on your Kubernetes cluster run the command below with relevant environment inventory.

```bash
ansible-playbook -i inventory/dev deploy.yml -t undeploy
```

Once the application is deployed, it should be accessible via https://dev.localtest.me
