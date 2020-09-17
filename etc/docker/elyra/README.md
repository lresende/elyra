<!--
{% comment %}
Copyright 2018-2020 IBM Corporation

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
{% endcomment %}
-->

This image installs Elyra and [Jupyter Lab](https://github.com/jupyterlab/jupyterlab) on top of image
[jupyterhub/k8s-singleuser-sample](https://hub.docker.com/r/jupyterhub/k8s-singleuser-sample). It also supports
mounting an S3 (Cloud Object Storage) bucket inside the user home/notebooks to be used as its workspace.

# What it Gives You
This image is configured to be run against [Jupyter Enterprise Gateway](http://jupyter-enterprise-gateway.readthedocs.io/en/latest/)
instances if the `gateway url` is provided. It also provides necessary support to be used in a `JupyterHub` environment.

# Mounting S3 working directory

Create a S3 credentials file

    mkdir ${HOME}/.ibm
    echo ACCESS_KEY_ID:SECRET_ACCESS_KEY > ${HOME}/.s3/.passwd-s3fs
    chmod 600 ${HOME}/.passwd-s3fs

To start Elyra with your S3 working directory, mount a volume pointing to the S3 credentials

    docker run --privileged -t --rm \
    -p 8888:8888 \
    -v <folder with COS credential in s3fs format>:/home/jovyan/.s3 \
    -v <host-notebook-directory>:/home/jovyan/work aiworkspace/jupyterlab-nb2kg:<tag> \
    -v <metadata dir>:/home/jovyan/.local/share/jupyter \
    elyra/elyra:dev /usr/local/bin/start-elyra-on-cloud.sh

    docker run --privileged -it -p 8888:8888 \
    -v ${HOME}/.s3/:/home/jovyan/.s3  \
    -w /home/jovyan/work elyra/elyra:dev /usr/local/bin/start-elyra-on-cloud.sh
    -v $HOME/Library/Jupyter:/home/jovyan/.local/share/jupyter \

 
### Jupyter Hub
This image can also be used as a _spawner target_ in Jupyter Hub configurations.
For instructions on how to run within a Hub configuration, please check Elyra docs:
[Deploying Elyra & JupyterHub in a Kubernetes environment](https://elyra.readthedocs.io/en/latest/recipes/deploying-elyra-in-a-jupyterhub-environment.html).
