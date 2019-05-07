# IBM Quantum Information Science Kit (Qiskit)
The [Quantum Information Software Kit](https://qiskit.org/) (officially named Qiskit) is a software framework produced by
IBM Research’s IBM Q group. As one of the oldest quantum software frameworks, Qiskit has attracted a considerable amount of
developer attention since its initial release on March 7th, 2017. This attention is fueled in part by IBM’s Q Experience,
a free-to-use, publicly-accessible collection of IBM’s own quantum computers that support running code written with Qiskit
on actual quantum processing hardware.

Since its initial release, the framework has steadily matured – it now has over 50 releases as of the time of this evaluation.
The exact number is difficult to quantify because Qiskit is comprised of several different packages, each with their own
independent versioning. These packages are named after the four classical elements:
- **Terra** is the core package that contains the classes for constructing and visualizing quantum circuits, and running
    quantum circuit execution jobs. It also contains basic simulators written in Python that can simulate quantum circuits.
    Technically, Terra can stand on its own without the other packages.
- **Aer** is the primary simulator package. It contains highly optimized simulators for quantum circuits written in C++ that
    are much faster than the basic simulators included in Terra. These simulators can also emulate realistic noise and
    environmental decoherence, making the circuits behave as they would while running on physical quantum hardware.
- **Ignis** provides functionality for characterizing the noise inherent in physical quantum computing platforms. It can
    essentially generate a noise and error profile for physical devices and their individual quantum gates, and construct
    error correction codes specifically for that device which can be applied to general-purpose quantum circuits.
- **Aqua** is intended to capture the practical applications of quantum computers. It contains canonical implementations of
    useful quantum algorithms in domains such as chemistry, optimization, machine learning, and finance.

Qiskit is written primarily for Python 3 development, though some limited ports for Swift, Java, and JavaScript are also
available. Our evaluation focused on the Python version. As Python is a classical development language, engineers can
leverage all of the libraries and utilities built for it in the classical portions of quantum algorithms as they would for any
other code. Qiskit is used primarily to develop and execute the quantum portions. It features an easy-to-use type model that
revolves around quantum circuits, gates, and registers (which can be comprised of one or more qubits) to build quantum programs.

## Installation and Usage
To use Qiskit, you'll need Python 3 installed. We used the miniconda distribution that is included as an optional component in
Visual Studio's installer. Ensure this (or an equivalent distribution) is installed prior to following the rest of these
instructions.

#### Network Configuration (Optional)
To install Qiskit, first ensure that conda and pip both have the proper configuration for your network. In our case, we had to
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

#### Installing Qiskit
- Create a shortcut that will start a miniconda command prompt, if you don't have one already.
    - Right-click on your desktop and select New -> Shortcut.
    - Put this in the location box:
        `%windir%\System32\cmd.exe /K "C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\
        Common7\IDE\Extensions\Microsoft\Python\Miniconda\Miniconda3-x64\Scripts\activate.bat"`
    - Name it "Miniconda Prompt" or something similar, and move it somewhere more convenient (for example,
        **C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Visual Studio 2019\\Visual Studio Tools** which is where
        the Visual Studio Developer Command Prompt shortcut is).
    - If you want, pin it to the Start menu.
- Run a miniconda prompt. **Run it as Administrator**, or Qiskit won't install properly.
- Create a new conda environment with pip installed:

  `> conda create -n QiskitEnv pip`

    NOTE: the console is going to tell you to update Anaconda, DO NOT DO THIS! Leave it as the version VS installed or else
    everything will break.
- Activate the environment:

  `> conda activate QiskitEnv`

- Make sure that pip is at least version 19.0.3, because this version fixes a Qiskit installation bug. Also, make sure the
    environment is using the local version of pip (instead of the global version attached to the Visual Studio miniconda
    installation):
```
    > pip --version
    pip 19.0.3 from C:\Users\<username>\.conda\envs\QiskitEnv\lib\site-packages\pip (python 3.7)
```

- Note that it's the correct version, and it's using pip from the conda environment directory. **If pip is an older version,
    upgrade it:**

  `> python -m pip install --upgrade pip`

- Install qiskit:

    `pip install qiskit qiskit-aqua qiskit-chemistry`

- You're going to see this message during the setup:
```
  running bdist_wheel

  ----------------------------------------
  Failed building wheel for qiskit
  Running setup.py clean for qiskit
```

- This isn't actually an error, it's fine and you can ignore it. See https://github.com/Qiskit/qiskit/issues/197  for more info.
- Once this command completes, Qiskit is installed and ready to use.


#### Running the Tests
The unit tests included in our code are supported by Visual Studio's Test Explorer. You should be able to load the solution and
wait for Visual Studio to finish parsing it - the tests will show up automatically in the Test Explorer.

**NOTE:** each project assumes you have a conda environment named QiskitEnv where Qiskit is installed. If you have a different
configuration, you'll need to update the Python environment in each project to match your setup.