/*
 * Copyright 2018-2021 Elyra Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { ReactWidget } from '@jupyterlab/apputils';
import { KernelSpec } from '@jupyterlab/services';
import { HTMLSelect } from '@jupyterlab/ui-components';
import React from 'react';

const DROPDOWN_CLASS = 'jp-Notebook-toolbarCellTypeDropdown bp3-minimal';

/**
 * Class: Holds properties for toolbar dropdown.
 */
class DropDownProps {
  kernelSpecs: KernelSpec.ISpecModels;
}

/**
 * Class: A toolbar dropdown component populated with available kernel specs.
 */
class DropDown extends React.Component<DropDownProps, string> {
  readonly specs: KernelSpec.ISpecModels;
  // private updateKernel: Function;

  /**
   * Construct a new dropdown widget.
   */
  constructor(props: DropDownProps) {
    super(props);
    this.specs = props.kernelSpecs;
    this.state = props.kernelSpecs.default;
    // this.updateKernel = this.props.updateKernel;
  }

  getSelected = (): string => {
    return this.state;
  };

  /**
   * Handles kernel selection from dropdown options.
   */
  private handleSelection = (event: any): void => {
    const selection: string = event.target.value;
    this.setState(selection);
  };

  /**
   * Creates drop down options with available kernel specs.
   */
  private createOptionElements = (): Record<string, any>[] => {
    let kernelOptionElements: Record<string, any>[];
    let i = 0;
    for (const name of Object.keys(this.specs.kernelspecs)) {
      const spec = this.specs.kernelspecs[name];
      const displayName = spec.display_name ? spec.display_name : name;
      const elem = React.createElement(
        'option',
        { key: i++, value: name },
        displayName
      );
      kernelOptionElements.push(elem);
    }

    return kernelOptionElements;
  };

  render(): React.ReactElement {
    return this.specs.kernelspecs
      ? React.createElement(
          HTMLSelect,
          {
            className: DROPDOWN_CLASS,
            onChange: this.handleSelection.bind(this),
            defaultValue: this.specs.default
          },
          this.createOptionElements
        )
      : React.createElement('span', null, 'Fetching kernel specs...');
  }
}

/**
 * Class: A CellTypeSwitcher widget that renders the Dropdown component.
 */
export class KernelDropdown extends ReactWidget {
  private kernelSpecs: KernelSpec.ISpecModels;

  /**
   * Construct a new CellTypeSwitcher widget.
   */
  constructor(kernelSpecs: KernelSpec.ISpecModels) {
    super();
    this.kernelSpecs = kernelSpecs;
  }

  render(): React.ReactElement {
    return <DropDown {...{ kernelSpecs: this.kernelSpecs }} />;
  }
}
