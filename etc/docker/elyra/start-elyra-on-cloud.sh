#!/bin/bash
#!/bin/bash
#
# Copyright 2018-2020 IBM Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

export NB_PORT=${NB_PORT:-8888}
export KERNEL_USERNAME=${KERNEL_USERNAME:-${NB_USER}}

echo "Kernel user: " ${KERNEL_USERNAME}
echo "JupyterLab port: " ${NB_PORT}
echo "Gateway URL: " ${JUPYTER_GATEWAY_URL}

echo "${@: -1}"

sudo s3fs jupyter-notebooks /home/jovyan/work -o uid=1000 -o gid=100 -o allow_other -o passwd_file=/home/jovyan/.s3/.passwd-s3fs -o url=https://s3.us.cloud-object-storage.appdomain.cloud

. /usr/local/bin/start.sh jupyter lab --debug $*
