# Radiographics Pre-processing

This workflow is derived from [this repository](https://github.com/nsdf-fabric/nsdf-materialscience/tree/main/python/nsdf/materialscience/radiographics_preprocessing)
and data (private) is required to run it.

## Tutorial

We are going to be using [flux-cloud](https://converged-computing.github.io/flux-cloud/) to run tutorials. This means you can install it:

```bash
$ pip install flux-cloud[all]
```

And then proceed with your cluster of choice!

### MiniKube

#### Data

The data for this experiment is private. It is assumed you have access to a sample, and can
download and extract to a place to be mounted as a volume (e.g., `/tmp/data-volumes`). As an example:

```bash
mv /home/vanessa/Downloads/radiographic_scan_id_* /tmp/data-volumes/
cd /tmp/data-volumes/
for filename in $(ls *.zip); do unzip $filename; done
```

Let's create a small hierarchy for original, pre-processed, and averaged data,
and move the original data into it.

```bash
$ mkdir -p original preprocessed averaged
mv radiographic_scan_id* original/
```

It should have this structure:

```bash
$ tree -L 2
.
├── averaged
├── original
│   ├── radiographic_scan_id_112536
│   ├── radiographic_scan_id_112538
│   ├── radiographic_scan_id_112539
│   └── radiographic_scan_id_112541
└── preprocessed
```

#### Cluster

Now let's start with running a workflow locally using MiniKube! The [experiments.yaml](experiments.yaml)
file here defines our cluster, and we can bring it up as follows:

```bash
$ flux-cloud up --cloud minikube
```

This will bring up MiniKube and install the Flux Operator! Note that if you want to load
a local image you are developing first (e.g., from the build above that isn't in a registry)
you can do:

```bash
$ docker tag test ghcr.io/converged-computing/nsdf-materialscience:ubuntu-20.04
$ minikube image load ghcr.io/converged-computing/nsdf-materialscience:ubuntu-20.04
```

I found this really useful for development.

#### Mount Data

The Flux Operator is going to expect to find volumes on the host of a particular storage type.
Since we are early in development, we currently (as the default) define a "hostpath" storage type,
meaning the operator will expect the path to be present on the node where you are running the job.
This means that we need to mount the data on our host into MiniKube (where the cluster is running)
with `minikube mount`. 

Note that in our [minicluster-template.yaml](minicluster-template.yaml) we are defining the volume on the host to 
be at `/tmp/data` so let's tell MiniKube to mount our local path there:

```
echo "Copying local volume to /tmp/data in minikube"
# We don't care if this works or not - mkdir -p seems to bork
minikube ssh -- mkdir -p /tmp/data

minikube mount /tmp/data-volumes:/tmp/data
```
Leave that process running in a window and then open another terminal to interact with the cluster.
If you want to double check the data is in the MiniKube vm:

```bash
$ minikube ssh -- ls /tmp/data
```
```console
averaged  original  preprocessed
```

#### Jobs

Then run your job(s). Note that for MiniKube, if you want the image to be pulled (you don't load
above) it's important to have the image defined under the job in `experiments.yaml`. Here is how 
to run your jobs:

```bash
$ flux-cloud apply --cloud minikube
```

If you run something and need to cancel and remove the job, just do:

```bash
$ kubectl delete -f data/minikube/k8s-size-4-local/.scripts/minicluster-size-4.yaml 
minicluster.flux-framework.org "materials-science" deleted
```

And clean up:

```bash
$ flux-cloud down --cloud minikube
```

You can see the full log of output in the subdirectories of [data](data)
along with experiment metadata files! In the window running the mount, you can
press control+C to end it, and then see your results remain:

```bash
$ tree /tmp/data-volumes
```
```bash
$ tree /tmp/data-volumes/averaged/ | wc -l
64
```

## Development Notes

### Porting the Workflow

#### 1. Containerize

The first step to getting your workflow ported from HPC to cloud is containerization.
For a simple workflow, you can usually install all dependencies in one container.
You should look to one of these bases that can run Flux:

 - [fluxrm/flux-sched](https://hub.docker.com/r/fluxrm/flux-sched)
 - [spack flux container](https://github.com/orgs/rse-ops/packages?repo_name=spack-flux-container) provides bases with the full install + EFA
 
As you write your Dockerfile, make sure you think about what the entrypoint will be,
what the arguments need to be, and any data that might be needed. Generally, it's best to 
think or assume data will be at a single mount-point, under subdirectories if needed.
You should also create an automated build for your container to deploy to an OCI
registry like GitHub packages. You should ideally finish this step with a container in
a registry, and knowing the working directory, environment, and entrypoint needed for your container to run.
Also see the [container requirements](https://flux-framework.org/flux-operator/development/developer-guide.html#container-requirements) 
set out by the operator. For example, to time commands
you need to install `time`.

#### 2. Local Testing

It can make sense to test locally! Since the workflow runs in a container, as long as 
it doesn't need scaling and you have a small testing dataset, you can actually develop
locally quite easily. As an example, here is how I built the container in this repository,
ran it binding a script I wanted to work on and some testing data, and then was able to
test on my local machine.

```bash
$ docker build -t test .
$ docker run -it -v $PWD/:/code/ -v /tmp/data-volumes:/data test bash
```

In the above, I am planning to bind my volumes (either with MiniKube on the host or a persistent volume
claim in a cloud provided Kubernetes cluster) also at /data, so it's fairly consistent. I might
install IPython to interact with code, and then test running the entrypoint:

```bash
$ pip install ipython
$ python /code/preprocess_radiographs.py preprocess /data radiographic_scan_id_112536
```

#### 3. Pre-Commands

Often you need to source an environment or do other actions before you can run
Flux! Add these to the preCommand section of the minicluster template.

Once that works, you can fairly easily port that command into the `experiments.yaml`
to test with MiniKube first, then a cloud.
