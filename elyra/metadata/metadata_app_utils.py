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
import logging

from elyra.util import CliOption

"""Utility functions and classes used for metadata applications and classes."""

logging.basicConfig(level=logging.INFO, format='[%(levelname)1.1s %(asctime)s.%(msecs).03d] %(message)s')


def schema_to_options(schema):
    """Takes a JSON schema and builds a list of SchemaProperty instances corresponding to each
       property in the schema.  There are two sections of properties, one that includes
       schema_name and display_name and another within the metadata container - which
       will be separated by class type - SchemaProperty vs. MetadataSchemaProperty.
    """
    options = {}
    properties = schema['properties']
    for name, value in properties.items():
        if name == 'schema_name':  # already have this option, skip
            continue
        if name != 'metadata':
            options[name] = SchemaProperty(name, value)
        else:  # process metadata properties...
            metadata_properties = properties['metadata']['properties']
            for md_name, md_value in metadata_properties.items():
                options[md_name] = MetadataSchemaProperty(md_name, md_value)

    # Now set required-ness on MetadataProperties and top-level Properties
    required_props = properties['metadata'].get('required')
    for required in required_props:
        options.get(required).required = True

    required_props = schema.get('required')
    for required in required_props:
        # skip schema_name & metadata, already required, and metadata is not an option to be presented
        if required not in ['schema_name', 'metadata']:
            options.get(required).required = True
    return list(options.values())


class SchemaProperty(CliOption):
    """Represents the necessary information to handle a property from the schema.
       No validation is performed on corresponding instance values since the
       schema validation in the metadata service applies that.
       SchemaProperty instances are initialized from the corresponding property stanza
       from the schema
    """
    # Skip the following meta-properties when building the description.  We will already
    # have description and type and the others are difficult to display in a succinct manner.
    # Schema validation will still enforce these.
    skipped_meta_properties = ['description', 'type', 'items', 'additionalItems', 'properties'
                               'propertyNames', 'dependencies', 'examples', 'contains',
                               'additionalProperties', 'patternProperties']
    # Turn off the inclusion of meta-property information in the printed help messages  (Issue #837)
    print_meta_properties = False

    def __init__(self, name, schema_property):
        self.schema_property = schema_property
        cli_option = '--' + name
        type = schema_property.get('type')

        super(SchemaProperty, self).__init__(cli_option=cli_option, name=name,
                                             description=schema_property.get('description'),
                                             default_value=schema_property.get('default'),
                                             type=type)

    def print_description(self):

        additional_clause = ""
        if self.print_meta_properties:  # Only if enabled
            for meta_prop, value in self.schema_property.items():
                if meta_prop in self.skipped_meta_properties:
                    continue
                additional_clause = self._build_clause(additional_clause, meta_prop, value)

        print("\t{}{}".format(self.description, additional_clause))

    def _build_clause(self, additional_clause, meta_prop, value):
        if len(additional_clause) == 0:
            additional_clause = additional_clause + "; "
        else:
            additional_clause = additional_clause + ", "
        additional_clause = additional_clause + meta_prop + ": " + str(value)
        return additional_clause


class MetadataSchemaProperty(SchemaProperty):
    """Represents the property from the schema that resides in the Metadata stanza.
    """
    def __init__(self, name, schema_property):
        super(MetadataSchemaProperty, self).__init__(name, schema_property)
