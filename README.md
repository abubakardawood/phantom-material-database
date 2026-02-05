# phantom-material-database
Open-access database of silicone phantoms for modelling the mechanical behaviour of human soft tissues, including compression-based hyperelastic material parameters and a gap-aware inverse design framework.

# Phantom Material Database

This repository provides an open-access database of soft silicone phantoms and accompanying analysis code for modelling the mechanical behaviour of human soft tissues under compressive loading.

The database comprises thirteen silicone phantoms fabricated from three EcoFlex families (00-10, 00-30, and 00-50) with systematically varied thinner concentrations, spanning an elastic modulus range of 5.42–152.70 kPa. This range covers the stiffness of a wide variety of healthy and pathological human soft tissues, including muscle, dermis, liver, prostate, kidney, and adipose tissue.

Each phantom was characterised through repeated uniaxial compression testing. Both engineering and true stress–strain responses were used to estimate parameters for commonly used hyperelastic material models. The resulting dataset provides validated material parameters, raw experimental data, and model performance metrics to support reproducible biomechanical simulation, surgical training, and medical device evaluation.

## Inverse Design of Phantom Composition

In addition to passive material characterisation, the repository includes an inverse design framework that maps a target elastic modulus to a reproducible phantom fabrication recipe.

Within each EcoFlex family, the experimentally observed relationship between thinner concentration and elastic modulus is monotonic. This property enables stable inversion using shape-preserving interpolation, while maintaining strict adherence to experimentally validated behaviour.

A gap-aware policy is incorporated to prevent extrapolation across unvalidated regions of the design space. When a target modulus lies outside the validated range of all silicone families, the framework reports the nearest lower and upper experimentally tested compositions instead of producing unsupported predictions.


## License

- The source code in this repository is released under the MIT License.
- The experimental data and derived datasets are released under the Creative Commons Attribution 4.0 (CC BY 4.0) license.
