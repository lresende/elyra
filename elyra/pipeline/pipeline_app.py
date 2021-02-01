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
import json
import os
import requests
import sys

from elyra.pipeline import PipelineParser, PipelineProcessorManager
from elyra.util.app_utils import AppBase, CliOption
from jupyter_server.serverapp import list_running_servers


class PipelineSubcommandBase(AppBase):

    pipeline = CliOption("--pipeline",
                         name='pipeline',
                         description='Pipeline to be processed',
                         required=True)

    runtime = CliOption('--runtime',
                        name='runtime',
                        description='Runtime type where the pipeline should be processed',
                        default_value="local")

    runtime_config = CliOption('--runtime-config',
                               name='runtime-config',
                               description='Runtime config where the pipeline should be processed',
                               default_value='local')

    work_dir = CliOption("--work-dir",
                         name='work-dir',
                         description='Base working directory for finding pipeline dependencies',
                         default_value=os.getcwd())

    # 'List' options
    options = [pipeline,
               runtime,
               runtime_config,
               work_dir]

    def __init__(self, **kwargs):
        super(PipelineSubcommandBase, self).__init__(**kwargs)

    def _preprocess_pipeline(self, pipeline_path, runtime, runtime_config, working_dir):

        pipeline_path = os.path.expanduser(pipeline_path)
        working_dir = os.path.expanduser(working_dir)
        pipeline_abs_path = os.path.join(working_dir, pipeline_path)
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


class Run(PipelineSubcommandBase):
    """
    Run pipeline locally.
    """

    name = "elyra-pipeline"
    description = "Run a given pipeline."
    subcommand_description = "Submit a pipeline to be executed on the srver."

    def __init__(self, **kwargs):
        super(Run, self).__init__(**kwargs)

    def start(self):
        self.process_cli_options(self.options)  # process options

        pipeline_definition = self._preprocess_pipeline(self.pipeline.value,
                                                        self.runtime.value,
                                                        self.runtime_config.value,
                                                        self.work_dir.value)

        try:
            pipeline = PipelineParser().parse(pipeline_definition)

            asyncio.get_event_loop().run_until_complete(PipelineProcessorManager.instance().process(pipeline))
        except ValueError as ve:
            print(f'Error parsing pipeline: \n {ve}')
            raise ve
        except RuntimeError as re:
            print(f'Error parsing pipeline: \n {re} \n {re.__cause__}')
            raise re

    def print_help(self):
        super(AppBase, self).print_help()
        self.print_subcommands()


class Submit(PipelineSubcommandBase):
    """
    Submit pipeline to be executed in the context of the Notebook Server.
    """

    name = "elyra-pipeline"
    description = "Submit a given pipeline."
    subcommand_description = "Submit a pipeline to be executed on the server."

    def __init__(self, **kwargs):
        super(Submit, self).__init__(**kwargs)

    def start(self):
        self.process_cli_options(self.options)  # process options

        pipeline_definition = self._preprocess_pipeline(self.pipeline.value,
                                                        self.runtime.value,
                                                        self.runtime_config.value,
                                                        self.work_dir.value)

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

    def print_help(self):
        super(Submit, self).print_help()
        self.print_subcommands()


class PipelineApp(AppBase):
    """Help submit pipelines to be executed."""

    name = "elyra-pipeline"
    description = """Manage Elyra pipeline execution."""

    subcommands = {
        'run': (Run, Run.description.splitlines()[0]),
        'submit': (Submit, Submit.description.splitlines()[0])
    }

    @classmethod
    def main(cls):
        elyra_pipeline = cls(argv=sys.argv[1:])
        elyra_pipeline.start()

    def __init__(self, **kwargs):
        super(PipelineApp, self).__init__(**kwargs)

    def start(self):
        subcommand = self.get_subcommand()
        if subcommand is None:
            self.exit_no_subcommand()

        subinstance = subcommand[0](argv=self.argv)
        return subinstance.start()

    def print_help(self):
        super(PipelineApp, self).print_help()
        self.print_subcommands()


if __name__ == '__main__':
    PipelineApp.main()
