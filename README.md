# SAR-Deforestation-Detection

Project for the course "Remote Sensing Data" of the master MVA at ENS Paris-Saclay. This project was done by Chloé 
Sekkat and Arnaud Louys.

The goal was to implement the algorithm described in the paper "Use of the SAR Shadowing Effect for Deforestation 
Detection with Sentinel-1 Time Series", which you can read [here](https://www.mdpi.com/2072-4292/10/8/1250).

```
Bouvet, A.; Mermoz, S.; Ballère, M.; Koleck, T.; Le Toan, T. Use of the SAR Shadowing Effect for Deforestation 
Detection with Sentinel-1 Time Series. Remote Sens. 2018, 10, 1250. https://doi.org/10.3390/rs10081250 
```

## Installation

Tested with Python3.8

```
pip install -r requirements.txt
```

## Download the data

1. Create an account: https://peps.cnes.fr/rocket/#/home
2. Add your creds in a file `peps.txt` (in the current directory): email@address password

To see a demo, please refer to the notebook `retrieve_sentinel1_data.ipynb`.

## Add SRTM tile for future ortho-rectification:

From this [website](https://dwtkns.com/srtm30m/), DL the following tiles:

- S06W075
- S06W075
- S06W077
- S07W075
- S07W075
- S07W077

## Use S1Tiling with docker

After many failed attempts to get everything working to use S1Tiling to process the images downlaoded from PEPS, we resorted to use the docker image provided by the project, and it was the right call (maybe we should have started there...).

To do it here is what you need to do :

```bash
docker run                            \
    -v $DATAFOLDER:/data
    -v ./source:/source                 \
    -v $HOME/.config/eodag:/eo_config \
    --rm -it registry.orfeo-toolbox.org/s1-tiling/s1tiling:0.3.2-ubuntu-otb7.4.0 \
    /source/S1Processor.cfg
```

Use the script `./process_images.sh DATAFOLDER` provided in `./source` for convenience. In DATAFOLDER, please use the following tree structure :

```raw
.
├── data
├── processed
├── s1_images
│   ├── S1A_IW_GRDH_1SSV_20141025T232647_20141025T232712_002992_003680_322D
│   │   └── S1A_IW_GRDH_1SSV_20141025T232647_20141025T232712_002992_003680_322D.SAFE
│   ├── S1A_IW_GRDH_1SSV_20141025T232712_20141025T232737_002992_003680_4227
│   │   └── S1A_IW_GRDH_1SSV_20141025T232712_20141025T232737_002992_003680_4227.SAFE
│   └── ...
└── SRTM
    ├── S06W075.hgt
    ├── S06W076.hgt
    └── ...
```

S1Tiling can also be used to automatically download the images from PEPS, to do that fill up the credentials information in `source/eo_config` with your PEPS account (be sure not to git it). If needed you can tune the performance of the processing by choosing the ram allocated to each process, I did not do much testing but with my 48Go of RAM and 8C/16T CPU, 8 tasks with 2 threads and 4Go of RAM seems right. With these parameters, I used around 20Go of RAM and while not fully occupied my CPUs was working quite hard. Processing the images from 2014-08-01 to 2019-07-31 on tiles 18MUU,18MVU took 15m 15s

## Showcase

Please refer to the folder ``notebooks`` to discover some of our results. Have also a look at our final report !

# Acknowledgements

Script `peps_download.py` has been taken from: https://github.com/olivierhagolle/peps_download and has been adapted to
accept more parameters for the request to PEPS' API.

Script `mvalab.py` has been taken from https://perso.telecom-paristech.fr/dalsasso/TPSAR/mvalab.py
