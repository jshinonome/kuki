## Kdb Ultimate pacKage Installer

- use the same registry site as the npm, recommend to use [Verdaccio](https://verdaccio.org/)
- use file `$HOME/.kukirc.json` to configure local registry site and token

### Command: kuki

#### config

use format 'field=value'

#### init

#### publish

#### download

#### install

#### uninstall

### Command: krun

## Setup Verdaccio without npmjs Proxy

```bash
# pull image
sudo docker pull verdaccio/verdaccio

# start verdaccio
sudo docker run -it --rm --name verdaccio -p 4873:4873 verdaccio/verdaccio

# find the container id
sudo docker ps -a

# cp config file
sudo docker cp $CONTAINER_ID:/verdaccio/conf/config.yaml .

# comment out "proxy: npmjs" and "uplinks" session
vi config.yaml

# cp back to container
sudo docker cp ./config.yaml $CONTAINER_ID:/verdaccio/conf/config.yaml

# commit the change
sudo docker commit da3d4765421f verdaccio:patched

# run patched version
sudo docker run -it --rm --name verdaccio -p 4873:4873 verdaccio:patched
```
