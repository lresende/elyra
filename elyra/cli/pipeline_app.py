#
# Copyright 2018-2021 Elyra Authors
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
import asyncio
import click
import json
import os
import requests

from elyra.pipeline import PipelineParser, PipelineProcessorManager
from jupyter_server.serverapp import list_running_servers


def _preprocess_pipeline(pipeline_path, runtime, runtime_config, work_dir):
    pipeline_path = os.path.expanduser(pipeline_path)
    work_dir = os.path.expanduser(work_dir)
    pipeline_abs_path = os.path.join(work_dir, pipeline_path)
    pipeline_dir = os.path.dirname(pipeline_abs_path)
    pipeline_name = os.path.splitext(os.path.basename(pipeline_abs_path))[0]

    with open(pipeline_abs_path) as f:
        pipeline_definition = json.load(f)

    for pipeline in pipeline_definition["pipelines"]:
        for node in pipeline["nodes"]:
            if node["app_data"]["filename"]:
                abs_path = os.path.join(os.getcwd(), pipeline_dir, node["app_data"]["filename"])
                node["app_data"]["filename"] = abs_path

    # NOTE: The frontend just set the info for first pipeline, but shouldn't it
    # search for the primary pipeline and set that?
    # Setting `pipeline_definition["pipelines"][0]` for consistency.
    pipeline_definition["pipelines"][0]["app_data"]["name"] = pipeline_name
    pipeline_definition["pipelines"][0]["app_data"]["runtime"] = runtime
    pipeline_definition["pipelines"][0]["app_data"]["runtime-config"] = runtime_config

    return pipeline_definition


@click.group()
def pipeline():  # *args, **kwargs
    print('>>> pipeline')
    click.echo('>>> pipeline')


@click.command()
@click.argument('pipeline')
@click.option('--work-dir', default=os.getcwd(), help='Working directory')
def run(pipeline, work_dir):
    pipeline_definition = _preprocess_pipeline(pipeline, "local", "local", work_dir)

    try:
        pipeline = PipelineParser().parse(pipeline_definition)

        asyncio.get_event_loop().run_until_complete(PipelineProcessorManager.instance().process(pipeline))
    except ValueError as ve:
        print(f'Error parsing pipeline: \n {ve}')
        raise ve
    except RuntimeError as re:
        print(f'Error parsing pipeline: \n {re} \n {re.__cause__}')
        raise re


@click.command()
@click.argument('pipeline', type=click.Path(exists=True))
@click.option('--runtime',
              required=True,
              type=click.Choice(['local', 'kfp', 'airflow'], case_sensitive=False),
              default='local',
              help='Runtime platform keyword')
@click.option('--runtime-config', required=True, default='local', help='Runtime config keyword')
@click.option('--work-dir', default=os.getcwd(), help='Working directory')
def submit(pipeline, runtime, runtime_config, work_dir):
    pipeline_definition = _preprocess_pipeline(pipeline, runtime, runtime_config, work_dir)

    try:
        serverinfo = list(list_running_servers())[0]
        server_url = f'{serverinfo["url"]}?token={serverinfo["token"]}'
        server_api_url = f'{serverinfo["url"]}elyra/pipeline/schedule'

        with requests.Session() as session:
            session.get(server_url)
            xsfr_header = {'X-XSRFToken': session.cookies.get('_xsrf')}
            session.post(url=server_api_url,
                         data=json.dumps(pipeline_definition),
                         headers=xsfr_header)
    except RuntimeError as re:
        print(f'Error parsing pipeline: \n {re} \n {re.__cause__}')
        raise re


pipeline.add_command(run)
pipeline.add_command(submit)
