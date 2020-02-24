# Nemesis-MBMI
Base repository for `Nemesis Model Builder` and `Nemesis Model Inspector`

## Installation

1. Download Python environment located at https://aviana1.sharepoint.com/:u:/s/Nemesis/EdIEXSEoLPlEv8D4_6TdNfEB7VVocojUgn_PfifoW2zpMA?e=kYD1eS
2. Open Anaconda Prompt and enter `git clone https://github.com/AvianaGlobal/nemesis-mbmi.git`
3. Using Windows Explorer, unzip the folder you downloaded in Step (1) to your `nemesis-mbmi` folder.
4. To launch `Nemesis Model Builder`, switch to Anaconda Prompt and enter the following commands:
- - (Note: equivalent to double-clicking `mb.cmd`)
- `call nemesis-mbmi/nemesis_env/scripts/activate.bat && cd nemesis-mbmi`.
- `cd rparser && python setup.py install`
- `cd ../main && python setup.py install`
- `python -m elite.app.builder.main`
5. To launch `Nemesis Model Inspector`, switch to Anaconda Prompt and enter the following commands:
\n(Note: equivalent to double-clicking `mi.cmd`)
- `call nemesis-mbmi/nemesis_env/scripts/activate.bat && cd nemesis-mbmi`.
- `cd rparser && python setup.py install`
- `cd ../main && python setup.py install`
- `python -m elite.app.inspector.main`

