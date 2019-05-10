# ========================================================================
# Copyright (C) 2019 The MITRE Corporation.
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
# ========================================================================


# This file provides a workaround for a problem where Visual Studio's unit
# test runner doesn't properly get its environment variables set when it
# activates a conda environment to run a unit test. This means it misses
# a lot of additional directories in the PATH variable that are specific
# to the conda environment; for example, PATH won't have 
# "C:\Users\<username>\.conda\envs\<env_name>\Library\bin", which is where
# a lot of the DLLs that pyQuil needs live. Without this path,
# the unit test runner won't load it properly and it will brick the test.
# 
# It took me a week to figure this out, because this problem only happens
# with the VS unit test runner. Aer works fine from the python console
# in VS (or a plain old conda prompt). I ended up having to use Process
# Monitor to see what was happening. No idea who I would even report this
# to, but something needs to get fixed.


import sys
import os

 # Get the directory of the currently-running python executable, which should
 # be the conda environment directory
env_dir = os.path.dirname(sys.executable)

# Append "\\Library\\bin" to the end of the environment directory
lib_dir = os.path.join(env_dir, "Library", "bin")

# Add this to the system's PATH variable, so the test runner will know where
# to look for Aer's DLLs
os.environ["PATH"] += ";" + lib_dir
