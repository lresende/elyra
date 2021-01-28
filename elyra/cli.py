#
# Copyright 2018-2020 Elyra Authors
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
import os
import json
import asyncio
import warnings

import click
from yaspin import yaspin
from colorama import Fore, Style

from ._version import __version__
from .pipeline.parser import PipelineParser
from .pipeline.processor import PipelineProcessorManager


async def submit_pipeline(pipeline):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        response = await PipelineProcessorManager.instance().process(pipeline)

    return response.to_json()


def prepare_pipeline(pipeline_path, name=None, runtime='local', runtime_config='local'):
    pipeline_abs_path = os.path.join(os.getcwd(), pipeline_path)
    pipeline_dir = os.path.dirname(pipeline_abs_path)

    if name is None:
        name = os.path.splitext(os.path.basename(pipeline_abs_path))[0]

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
    pipeline_definition["pipelines"][0]["app_data"]["name"] = name
    pipeline_definition["pipelines"][0]["app_data"]["runtime"] = runtime
    pipeline_definition["pipelines"][0]["app_data"]["runtime-config"] = runtime_config

    return pipeline_definition


def print_banner(title):
    click.echo(Fore.CYAN + "────────────────────────────────────────────────────────────────" + Style.RESET_ALL)
    click.echo(Fore.CYAN + "  {}".format(title) + Style.RESET_ALL)
    click.echo(Fore.CYAN + "────────────────────────────────────────────────────────────────" + Style.RESET_ALL)
    click.echo()


def print_info(title, info_list):
    click.echo(Fore.CYAN + "❯ {}".format(title) + Style.RESET_ALL)
    for info_item in info_list:
        if isinstance(info_item, str):
            click.echo("  {}".format(info_item))
        else:
            click.echo("  {}: {}".format(info_item[0], info_item[1]))
    click.echo()


def print_version():
    print_info("Version", ["elyra {}".format(__version__)])


@click.group()
def cli():
    pass


@click.command()
@click.argument('pipeline_path', type=click.Path(exists=True))
@click.option('-n', '--name')
def submit(pipeline_path, name):
    """TODO: Description"""
    click.echo()

    print_banner("Elyra Pipeline Submission")
    print_version()

    pipeline_definition = prepare_pipeline(pipeline_path, name=name, runtime='kfp', runtime_config='fun')
    pipeline = PipelineParser().parse(pipeline_definition)

    print_info("Info", [("name", pipeline.name)])
    print_info("Runtime", [("type", pipeline.runtime), ("config", pipeline.runtime_config)])

    with yaspin(text="Submitting Pipeline..."):
        os.environ["ELYRA_METADATA_PATH"] = os.path.join(os.path.expanduser("~"), ".elyra")
        msg = asyncio.get_event_loop().run_until_complete(submit_pipeline(pipeline))

    print_banner("Elyra Pipeline Submission Complete")

    print_info("Run Url", [msg["run_url"]])
    print_info("Object Storage Output", [msg["object_storage_path"]])


@click.command()
@click.argument('pipeline_path', type=click.Path(exists=True))
def run(pipeline_path):
    """TODO: Description"""
    click.echo()

    print_banner("Elyra Pipeline Local Run")
    print_version()

    pipeline_definition = prepare_pipeline(pipeline_path)
    pipeline = PipelineParser().parse(pipeline_definition)

    asyncio.get_event_loop().run_until_complete(submit_pipeline(pipeline))
    click.echo()

    print_banner("Elyra Pipeline Local Run Complete")


cli.add_command(submit)
cli.add_command(run)
