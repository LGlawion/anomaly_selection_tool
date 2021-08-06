[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/LGlawion/anomaly_selection_tool.git/main)

# Anomaly_selection_tool
Python tool for flagging and classifying anomalies in netCDF time series datasets

Commercial microwave link (CML) signal level data, used for deriving rainfall information, 
can show anourmales signal fluctuations.
These anomalies can make accurate rain rate determination challenging.
For various reasons, the availability of a dataset with flagged anomalies is beneficial. 
E.g., for machine learning applications, or to quantify spatial and temporal occurrence.

## Usage

Anomaly_selection_tool can be used to assigne time periods to different anomaly classes. 
Flags are written directly into a netCDF. Correction is possible.
A reference variable helps to distinguish between anomalies and normal signal fluctuations.

The ast_example jupyter notebook showcase the principle usecase of anomaly_selection_tool.

## Reference

 Polz, J., Schmidt, L., Glawion, L., Graf, M., Werner, C., Chwala, C., Mollenhauer, H., Rebmann, C., Kunstmann, H., and Bumberger, J.: Supervised and unsupervised machine-learning for automated quality control of environmental sensor data, EGU General Assembly 2021, online, 19–30 Apr 2021, EGU21-14485, https://doi.org/10.5194/egusphere-egu21-14485, 2021. 
 
 Chwala, C., Graf, M., Polz, J., Rothermel, S., Glawion, L., Winterrath, T., Smiatek, G., and Kunstmann, H.: Recent improvements of CML rainfall estimation and CML-Radar combination in Germany, EGU General Assembly 2021, online, 19–30 Apr 2021, EGU21-15207, https://doi.org/10.5194/egusphere-egu21-15207, 2021. 

