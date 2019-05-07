# Cirq
[Cirq](https://github.com/quantumlib/Cirq) is a quantum software framework that was formerly under development by Google, and has
since become maintained by a dedicated team that is separate from Google. It is written in Python 3. Functionally, Cirq is almost
identical to Qiskit but its code is a bit more user-friendly (especially with the way it treats qubit measurements). 

*A full summary is still TBD.*

## Installation and Usage
To use Cirq, you'll need Python 3 installed. We used the miniconda distribution that is included as an optional component in
Visual Studio's installer. Ensure this (or an equivalent distribution) is installed prior to following the rest of these
instructions.

#### Network Configuration (Optional)
To install Cirq, first ensure that conda and pip both have the proper configuration for your network. In our case, we had to
set proxy settings for both components prior to installation.

- Create (or open) the file **C:\\Users\\\<username>\\.condarc**. You'll probably have to use a command prompt to do this,
because Windows Explorer won't let you make a file without a name like this. Here's an example of how to do it:
```
    > cd C:\Users\<username>
    > copy NUL .condarc
```

- Open it in a text editor, and put this inside:
```
    proxy_servers:
        http: http://<proxy_url>
        https: https://<proxy_url>
```

- Create (or open) the file **C:\\Users\\\<username>\\AppData\\Roaming\\pip\\pip.ini** and put this inside:
```
    [global]
    proxy = http://<proxy_url>
```

#### Installing Cirq
- Create a shortcut that will start a miniconda command prompt, if you don't have one already.
    - Right-click on your desktop and select New -> Shortcut.
    - Put this in the location box:
        `%windir%\System32\cmd.exe /K "C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\
        Common7\IDE\Extensions\Microsoft\Python\Miniconda\Miniconda3-x64\Scripts\activate.bat"`
    - Name it "Miniconda Prompt" or something similar, and move it somewhere more convenient (for example,
        **C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Visual Studio 2019\\Visual Studio Tools** which is where
        the Visual Studio Developer Command Prompt shortcut is).
    - If you want, pin it to the Start menu.
- Run a miniconda prompt. **Run it as Administrator**, or Cirq won't install properly.
- Create a new conda environment with pip installed:

  `> conda create -n CirqEnv pip`

    NOTE: the console is going to tell you to update Anaconda, DO NOT DO THIS! Leave it as the version VS installed or else
    everything will break.
- Activate the environment:

  `> conda activate CirqEnv`

- Make sure the environment is using the local version of pip (instead of the global version attached to the Visual Studio
    miniconda installation):
```
    > pip --version
    pip 19.0.3 from C:\Users\<username>\.conda\envs\CirqEnv\lib\site-packages\pip (python 3.7)
```

- Note that it's the correct version, and it's using pip from the conda environment directory.
- Install cirq:

    `pip install cirq`

- Once this command completes, Cirq is installed and ready to use.


#### Running the Tests
The unit tests included in our code are supported by Visual Studio's Test Explorer. You should be able to load the solution and
wait for Visual Studio to finish parsing it - the tests will show up automatically in the Test Explorer.

**NOTE:** each project assumes you have a conda environment named CirqEnv where Cirq is installed. If you have a different
configuration, you'll need to update the Python environment in each project to match your setup.