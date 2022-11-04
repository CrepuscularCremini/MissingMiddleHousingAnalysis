# MissingMiddleHousingAnalysis
Several functions to calculate the feasibility of missing middle housing at the parcel level. This is primarily an exploratory and visual tool allowing you to explore the current and potential future housing environment. All calculations are purely spatial and do not consider any regulations that may exist. **These calculations do not necessarily reflect the actual development environment.**

### Acknowledgements
- The default dimensions for each missing middle housing type is based on the "ideal specifications" for each type as developed by [Opticos Design](https://missingmiddlehousing.com/types). More information about missing middle housing can be viewed on their website.
- These functions contain convenience wrappers for several methods from the [OSMNX package](https://osmnx.readthedocs.io/en/stable/). Future iterations of these calculations will lean on that package even more.

### Main Functions
1. addon_feasibility - this calculates if there is space to add an **accessory dwelling unit** (or other accessory building) to a property, given the existing buildings on the property (i.e. a house and a garage)
2. development_feasibility - this calculates if there is space to build a **new development** of a certain type of missing middle housing. The calculation is based on an empty parcel.
3. conversion_feasibility - this calculates the potential to **convert existing buildings** (such as garages) that are already on the property to accessory dwelling units or other accessory buildings. This is limited to building footprints that have a separate classification as the main building, which means some attached garages may be missed.

Each method calculates feasibility for **every** parcel. For example, this means parcels with existing buildings are included in the calculation for new development as if there was no building present. Additionally, parking garages that have been classified as 'garage' may be included in the conversion_feasibility analysis.

This was done intentionally as it allows exploration of future scenarios in addition to existing conditions.

Joining these layers to zoning and other regulatory layers, you can filter the outputs to get an idea of what the existing conditions are:
1. where is vacant land that can be developed as missing middle housing?
2. how many single family homes have the potential to add an ADU in their back yard?

However having the calculations for every parcel means you can ask hypotheticals as well:
1. what if we allowed ADUs in xyz zoning district, how many housing units could be added?
2. what types of missing middle housing could by built on abc property if they took down their single family home?

### Methods
Currently there is only the "simple" methods for each function which make more assumptions about the geometries but are faster. Other methods that are more accurate to the spatial configuration of the properties are currently in development.

### Helper Functions
There are several helper functions that help prepare your data to be used in the main functions. I have included an [example script](./example_script.py) (of how to run a full analysis, showing how to use the helper functions and the order they should be executed in while an actual documentation is in progress.

### Installation and Use
1. clone the repo
2. dependencies are located in env.yml
3. at the top of your script add:
```
import sys
sys.path.append(path_to_repo)
import mmh_spatial
```
