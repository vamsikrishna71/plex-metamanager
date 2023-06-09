# Metadata Set Creator

Metadata Set Creator is an open source Python 3 project that has been created to create a Plex Meta Manager metadata file and associated set file for a list.

## Installing Metadata Set Creator

Generally, Metadata Set Creator can be installed in one of two ways:

1. Running on a system as a Python script [we will refer to this as a "local" install]
2. Running as a Docker container

GENERALLY SPEAKING, running as a Docker container is simpler, as you won't have to be concerned about installing Python, or support libraries, or any possible system conflicts generated by those actions.

For this reason, it's generally recommended that you install via Docker rather than directly on the host.

If you have some specific reason to avoid Docker, or you prefer running it as a Python script for some particular reason, then this general recommendation is not aimed at you.  It's aimed at someone who doesn't have an existing compelling reason to choose one over the other.

### Install Walkthroughs

There are no detailed walkthroguhs specifically for Metadata Set Creator but the process is extremely similar to how you would do it with [Plex Meta Manager](https://metamanager.wiki/en/latest/home/installation.html#install-walkthroughs).

### Local Install Overview

Metadata Set Creator is compatible with Python 3.11. Later versions may function but are untested.

These are high-level steps which assume the user has knowledge of python and pip, and the general ability to troubleshoot issues. 

1. Clone or [download and unzip](https://github.com/meisnate12/Metadata-Set-Creator/archive/refs/heads/master.zip) the repo.

```shell
git clone https://github.com/meisnate12/Metadata-Set-Creator
```
2. Install dependencies:

```shell
pip install -r requirements.txt
```

3. If the above command fails, run the following command:

```shell
pip install -r requirements.txt --ignore-installed
```

At this point Metadata-Set-Creator has been installed, and you can verify installation by running:

```shell
python metadata_set_creator.py
```

### Docker Install Overview

#### Docker Run:

```shell
docker run -v <PATH_TO_CONFIG>:/config:rw meisnate12/metadata-set-creator
```
* The `-v <PATH_TO_CONFIG>:/config:rw` flag mounts the location you choose as a persistent volume to store your files.
  * Change `<PATH_TO_CONFIG>` to a folder where your .env and other files are.
  * If your directory has spaces (such as "My Documents"), place quotation marks around your directory pathing as shown here: `-v "<PATH_TO_CONFIG>:/config:rw"`

Example Docker Run command:

These docs are assuming you have a basic understanding of Docker concepts.  One place to get familiar with Docker would be the [official tutorial](https://www.docker.com/101-tutorial/).

```shell
docker run -v "X:\Media\Metadata Set Creator\config:/config:rw" meisnate12/metadata-set-creator
```

#### Docker Compose:

Example Docker Compose file:
```yaml
version: "2.1"
services:
  plex-meta-manager:
    image: meisnate12/metadata-set-creator
    container_name: metadata-set-creator
    environment:
      - TZ=TIMEZONE #optional
    volumes:
      - /path/to/config:/config
    restart: unless-stopped
```

#### Dockerfile

A `Dockerfile` is included within the GitHub repository for those who require it, although this is only suggested for those with knowledge of dockerfiles. The official Metadata Set Creator build is available on the [Dockerhub Website](https://hub.docker.com/r/meisnate12/metadata-set-creator).

## Options

Each option can be applied in three ways:

1. Use the Shell Command when launching.
2. Setting the Environment Variable.
3. Adding the Environment Variables to `config/.env` 

| Option                  | Description                                                                                                                                                                                                                                                          | Required |
|:------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------:|
| List URL                | TMDb List, TMDb Collection, IMDb List, Trakt List, or MDbList List URL. <br>**Shell Command:** `-u` or `--url "https://trakt.tv/users/movistapp/lists/christmas-movies"` <br>**Environment Variable:** `URL=https://trakt.tv/users/movistapp/lists/christmas-movies` | &#9989;  |
| PMM Config              | Path to PMM Config with TMDb/Trakt configured. **Default:** `config/config.yml`<br>**Shell Command:** `-pm` or `--pmm-config "C:\Plex Meta Manager\config\config.yml"`<br>**Environment Variable:** `PMM_CONFIG=C:\Plex Meta Manager\config\config.yml`              | &#10060; |
| Timeout                 | Timeout can be any number greater then 0. **Default:** `600`<br>**Shell Command:** `-ti` or `--timeout 1000`<br>**Environment Variable:** `TIMEOUT=1000`                                                                                                             | &#10060; |
| TPDb Placeholders       | Add TPDb placeholders over url placeholders.<br>**Shell Command:** `-tp` or `--tpdb`<br>**Environment Variable:** `TPDB=True`                                                                                                                                        | &#10060; |
| Background Placeholders | Add Background placeholders.<br>**Shell Command:** `-b` or `--background`<br>**Environment Variable:** `BACKGROUND=True`                                                                                                                                             | &#10060; |
| Season Placeholders     | Add Season posters placeholders.<br>**Shell Command:** `-s` or `--season`<br>**Environment Variable:** `SEASON=True`                                                                                                                                                 | &#10060; |
| Episode Placeholders    | Add Episode posters placeholders.<br>**Shell Command:** `-e` or `--episode`<br>**Environment Variable:** `EPISODE=True`                                                                                                                                              | &#10060; |
| Trace Logs              | Run with extra trace logs.<br>**Shell Command:** `-tr` or `--trace`<br>**Environment Variable:** `TRACE=True`                                                                                                                                                        | &#10060; |
| Log Requests            | Run with every request logged.<br>**Shell Command:** `-lr` or `--log-requests`<br>**Environment Variable:** `LOG_REQUESTS=True`                                                                                                                                      | &#10060; |

### Example .env File
```
URL=https://trakt.tv/users/movistapp/lists/christmas-movies
PMM_CONFIG=C:\Plex Meta Manager\config\config.yml
TIMEOUT=600
TPDB=True
BACKGROUND=False
SEASON=True
Episode=True
TRACE=False
LOG_REQUESTS=False
```