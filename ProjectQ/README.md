# ProjectQ
*This summary is TBD.*

[ProjectQ](http://projectq.ch/) is a software framework produced by a small team of independent researchers and developers.
Unlike all of the other frameworks, this one isn't backed by a major corporation with a vested interest in promoting software
that works on their hardware platforms - it is first and foremost a software framework, meant to make development as easy as
possible. That being said, it also provides a robust backend engine system that can connect to actual quantum devices (right
now it seems like IBM's Q systems are the only ones that have been hooked up).

ProjectQ is different from the other Python frameworks in that it doesn't treat quantum circuits as discrete objects that get
built through classical code, then passed to a quantum computer or simulator for execution. Instead, it treats a quantum computer
as an extension of the classical computer, and runs quantum code on it line-by-line, instruction-by-instruction. This makes it
trivial to interweave quantum and classical code inside a Python program. This is much like the way Q# works, which I (personally)
prefer as it makes debugging and development much easier.

## Installation and Usage
To use ProjectQ, you'll need Python 3 installed. We used the miniconda distribution that is included as an optional component in
Visual Studio's installer. Ensure this (or an equivalent distribution) is installed prior to following the rest of these
instructions.

The ProjectQ team provides basic installation instructions here: https://projectq.readthedocs.io/en/latest/tutorials.html#getting-started
Note that ProjectQ comes with a C++ simulator, so you'll need to have a C++ compiler installed for it to build sucessfully. Since
you're looking at this repository, I'm going to assume you already have Visual Studio up and running, so you should be all set in
this respect.


#### Network Configuration (Optional)
To install ProjectQ, first ensure that conda and pip both have the proper configuration for your network. In our case, we had to
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

#### Installing ProjectQ
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

  `> conda create -n ProjectQEnv pip`

    NOTE: the console is going to tell you to update Anaconda, DO NOT DO THIS! Leave it as the version VS installed or else
    everything will break.
- Activate the environment:

  `> conda activate ProjectQEnv`

- Make sure the environment is using the local version of pip (instead of the global version attached to the Visual Studio
    miniconda installation):
```
    > pip --version
    pip 19.0.3 from C:\Users\<username>\.conda\envs\ProjectQEnv\lib\site-packages\pip (python 3.7)
```

- Note that it's using pip from the conda environment directory.

- Install ProjectQ:

    `pip install projectq`

- In our case, it tried to install twice. First it tried to build the C++ simulator but ran into a missing dependency (pybind11),
  then it downloaded those dependencies and tried to build the C++ simulator again, which succeeded. After that, the install
  reported that it was successful.
- Once this command completes, ProjectQ is installed and ready to use.


#### Running the Tests
The unit tests included in our code are supported by Visual Studio's Test Explorer. You should be able to load the solution and
wait for Visual Studio to finish parsing it - the tests will show up automatically in the Test Explorer.

**NOTE:** each project assumes you have a conda environment named ProjectQEnv where ProjectQ is installed. If you have a different
configuration, you'll need to update the Python environment in each project to match your setup.