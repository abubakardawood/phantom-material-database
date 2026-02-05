# Phantom Material Database

This repository provides an open-access database of soft silicone phantoms and accompanying analysis code for use as mechanically equivalent surrogates for human soft tissues under compressive loading.

The database comprises thirteen silicone phantoms fabricated from three EcoFlex families (00-10, 00-30, and 00-50) with systematically varied thinner concentrations. The resulting phantoms span an elastic modulus range of 5.42–152.70 kPa, covering the stiffness range of a wide variety of healthy and pathological human soft tissues, including muscle, dermis, liver, prostate, kidney, and adipose tissue.

Each phantom was characterised through repeated uniaxial compression testing. Both engineering and true stress–strain responses were used to estimate parameters for commonly used hyperelastic material models. The resulting dataset provides validated elastic moduli, material compositions, and model parameters, enabling reproducible biomechanical simulations, experimental benchmarking, and fabrication of tissue-mimicking phantoms.

---

## Repository Contents

- **Data**  
  Experimentally measured elastic moduli and phantom compositions derived from compression testing.

- **Analysis Scripts**  
  Scripts to reproduce figures from the manuscript, including the elastic modulus versus thinner concentration plots.

- **Inverse Design Framework**  
  A gap-aware inverse design approach that maps a target elastic modulus to a reproducible phantom fabrication recipe, restricted to experimentally validated ranges.

---

## Inverse Design of Phantom Composition

Within each EcoFlex family, the experimentally observed relationship between thinner concentration and elastic modulus is monotonic. This property enables shape-preserving interpolation and inversion from a target elastic modulus to the corresponding thinner concentration.

To ensure physical validity, the inverse design framework incorporates a **gap-aware policy**. Predictions are restricted to experimentally validated stiffness ranges, and no extrapolation is performed across untested regions of the design space. When a target modulus lies within an unvalidated gap, the framework reports the nearest lower and upper experimentally tested compositions instead of generating unsupported predictions.

This design strategy enables controlled fabrication of mechanically equivalent tissue phantoms while maintaining strict adherence to experimental evidence.

---

## Data Location

The canonical dataset corresponding to Table 1 of the manuscript is provided at:

data/processed/phantoms_table.csv


This table is used to reproduce the elastic modulus trends, define validated stiffness ranges, and support the inverse design framework.

---

## Intended Use

This repository is intended to support:
- Fabrication of mechanically equivalent silicone phantoms for human soft tissues
- Reproducible estimation of hyperelastic material parameters
- Benchmarking of biomechanical models and medical devices
- Experimental design and validation where biological tissue variability is undesirable

The phantoms are not intended to replicate biological tissue structure or physiology, but to provide controlled mechanical equivalence within the investigated stiffness range.

---

## License

- Source code in this repository is released under the MIT License.
- Experimental data and derived datasets are released under the Creative Commons Attribution 4.0 (CC BY 4.0) license.

See `LICENSE` and `DATA_LICENSE.md` for details.

---

## Citation

If you use this dataset or framework, please cite the associated publication:

*A. B. Dawood et al., “A Database of Materials for Modeling Human Tissues Across Varying Stiffnesses,”*
