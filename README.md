# Solar MAgnetic Connection Haus tool

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://solar-mach.github.io)
  [![DOI](https://zenodo.org/badge/374606976.svg)](https://zenodo.org/badge/latestdoi/374606976)  [![Python](https://img.shields.io/pypi/pyversions/solarmach?style=flat&logo=python)](https://pypi.org/project/solarmach/)

Streamlit frontend to the PyPI package [solarmach](https://pypi.org/project/solarmach/), used for [solar-mach.github.io](https://solar-mach.github.io).

To install and start a local Streamlit server, run the following commands in your terminal:

```python
# optional: create and activate virtual environment in python (alternatively use conda)
python3 -m venv env
source env/bin/activate

# install requirements with pip (alternatively use conda)
pip3 install -r requirements.txt

# run the actual streamlit app
streamlit run streamlit_app.py 
```

Afterwards the app should open in your browser.

## Python package

In addition, all the functionality is available in the streamlit-independent python package [**solarmach**](https://github.com/jgieseler/solarmach). It requires python >= 3.10 and can be installed either from [PyPI](https://pypi.org/project/solarmach/) using:

``` bash
pip install solarmach
```

or from [conda](https://anaconda.org/conda-forge/solarmach/) using:

``` bash
conda install -c conda-forge solarmach
```

See [https://github.com/jgieseler/solarmach](https://github.com/jgieseler/solarmach) for a more detailled description.

## Contributing

Contributions to this project are very much welcome and encouraged! Contributions to the streamlit web-version that is used for [solar-mach.github.io](https://solar-mach.github.io) can take the form of [issues](https://github.com/jgieseler/Solar-MACH/issues) to report bugs and request new features or [pull requests](https://github.com/jgieseler/Solar-MACH/pulls) to submit new code. 

Please make contributions that are general to the [**solarmach**](https://github.com/jgieseler/solarmach) package and not specific to the streamlit web-version in the corresponding repository at [github.com/jgieseler/solarmach](https://github.com/jgieseler/solarmach/).

## Citation

Please cite the following paper if you use **Solar-MACH** in your publication:

Gieseler, J., Dresing, N., Palmroos, C., von Forstner, J.L.F., Price, D.J., Vainio, R. et al. (2023).
Solar-MACH: An open-source tool to analyze solar magnetic connection configurations. *Front. Astronomy Space Sci.* 9. [doi:10.3389/fspas.2022.1058810](https://doi.org/10.3389/fspas.2022.1058810)
