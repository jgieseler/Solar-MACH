# Solar MAgnetic Connection Haus tool

Adapted from [github.com/esdc-esac-esa-int/Solar-MACH](https://github.com/esdc-esac-esa-int/Solar-MACH) and modified to [run with Streamlit](https://solar-mach.github.io). Slightly extended functionality (provide reference longitude in Stonyhurst coordinates, download bodies coordinates list).

To install and start a local server using `streamlit` run the following commands in your terminal:

```python
# optional: create and activate virtual environment in python (alternatively use anaconda)
python3 -m venv env
source env/bin/activate

# install requirements with pip (alternatively use anaconda)
pip3 install -r requirements.txt

# run the actual streamlit app
streamlit run streamlit_app.py 
```

Afterwards the app should open in your browser.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://solar-mach.github.io)


## Python package

In addition, all the functionality is available in the streamlit-independent python package [**solarmach**](https://github.com/jgieseler/solarmach). It requires python >= 3.6 and can be installed either from [PyPI](https://pypi.org/project/solarmach/) using:

``` bash
pip install solarmach
```
    
or from [conda](https://anaconda.org/conda-forge/solarmach/) using:

``` bash
conda install -c conda-forge solarmach
```

See https://github.com/jgieseler/solarmach for a more detailled description.
