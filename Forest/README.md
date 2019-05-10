# Rigetti Forest
*This summary is TBD.*

[Forest](https://www.rigetti.com/forest) is a software framework produced by Rigetti Computing.

The Forest SDK includes three components:

- [pyQuil](https://github.com/rigetti/pyquil), the Python framework for writing quantum code
- [Quilc](https://github.com/rigetti/quilc), the compiler (Forest uses 
    [Quil](https://en.wikipedia.org/wiki/Quil_(instruction_set_architecture)) as its intermediate language, which is an
    alternative to OpenQASM)
- [QVM](https://github.com/rigetti/qvm), the quantum simulator that runs Quil programs

## Installation and Usage
To use Forest, you'll need Python 3 installed. We used the miniconda distribution that is included as an optional component in
Visual Studio's installer. Ensure this (or an equivalent distribution) is installed prior to following the rest of these
instructions.

Rigetti provides very good installation and tutorial documentation here: http://docs.rigetti.com/en/latest/start.html
We recommend you use that to get started, but we've recapped the process here.


### QVM and Quilc
Rigetti has made the QVM and Quilc projects open source. You can compile them from their respective GitHub repositories, or you
can get the pre-built binaries from Rigetti. You'll need to [sign up for an account](https://www.rigetti.com/forest) with them
in order to download it. They offer installers for all operating systems, but assuming you're using Visual Studio, you'll want to
grab the Windows package.

Once you download and install it, QVM and Quilc will be added in `C:\Program Files\Rigetti Computing\Forest SDK for Windows`.
You can run them both from here.

**NOTE: There is currently [a bug in QVM and Quilc](https://github.com/rigetti/qvm/issues/86) that prevents them from working
in environments with network proxies. We built a workaround for this, which we've provided in the `RigettiUpdateProxy` project
in this repository.**


### pyQuil
#### Network Configuration (Optional)
To install pyQuil, first ensure that conda and pip both have the proper configuration for your network. In our case, we had to
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

#### Installing pyQuil
- Create a shortcut that will start a miniconda command prompt, if you don't have one already.
    - Right-click on your desktop and select New -> Shortcut.
    - Put this in the location box:
        `%windir%\System32\cmd.exe /K "C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\
        Common7\IDE\Extensions\Microsoft\Python\Miniconda\Miniconda3-x64\Scripts\activate.bat"`
    - Name it "Miniconda Prompt" or something similar, and move it somewhere more convenient (for example,
        **C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Visual Studio 2019\\Visual Studio Tools** which is where
        the Visual Studio Developer Command Prompt shortcut is).
    - If you want, pin it to the Start menu.
- Create a new conda environment with pip installed:

  `> conda create -n ForestEnv pip`

    NOTE: the console is going to tell you to update Anaconda, DO NOT DO THIS! Leave it as the version VS installed or else
    everything will break.
- Activate the environment:

  `> conda activate ForestEnv`

- Make sure the environment is using the local version of pip (instead of the global version attached to the Visual Studio
    miniconda installation):
```
    > pip --version
    pip 19.0.3 from C:\Users\<username>\.conda\envs\ForestEnv\lib\site-packages\pip (python 3.7)
```

- Note that it's using pip from the conda environment directory.

- Install pyQuil:

    `pip install pyquil`

- Once this command completes, Forest is installed and ready to use.


#### Running the Tests
The unit tests included in our code are supported by Visual Studio's Test Explorer. You should be able to load the solution and
wait for Visual Studio to finish parsing it - the tests will show up automatically in the Test Explorer.

**NOTE:** each project assumes you have a conda environment named ForestEnv where pyQuil is installed. If you have a different
configuration, you'll need to update the Python environment in each project to match your setup.