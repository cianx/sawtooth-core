# Copyright 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------

import os
import shutil


def add_reset_parser(subparsers, parent_parser):
    subparsers.add_parser('reset', parents=[parent_parser])


def do_reset(args, config):
    home = os.path.expanduser("~")
    config_dir = os.path.join(home, ".sawtooth")
    if os.path.exists(config_dir):
        shutil.rmtree(config_dir)
