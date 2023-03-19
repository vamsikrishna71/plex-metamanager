# Docker Walkthrough

This article will walk you through getting Plex-Meta-Manager [PMM] set up and running via Docker.  It will cover:

1. Installing Docker
2. Retrieving the image
3. Setting up the initial config file
4. Setting up a metadata file and creating a couple sample collections
5. Creating a docker container that will keep running in the background

The specific steps you will be taking:
1. Verify that Docker is installed and install it if not
2. Use `docker` to retrieve the PMM Docker image
3. Create a directory for your config files and learn how to tell Docker to use it
4. Gather two things that the script requires:
   1. TMDb API Key
   2. Plex URL and Token
5. Then, iteratively:
   1. use `docker` to run the image
   2. use a text editor to modify a couple of text files until you have a working config file and a single working metadata file.

Note that running a Docker container is inherently a pretty technical process.  If you are unable or unwilling to learn the rudiments of using Docker, this may not be the tool for you.

If the idea of editing YAML files by hand is daunting, this may not be the tool for you.  All the configuration of PMM is done via YAML text files, so if you are unable or unwilling to learn how those work, you should stop here.

Finally, this walkthrough is intended to give you a basic grounding in how to get the script running.  It doesn't cover how to create your own collections, or how to add overlays, or any of the myriad other things PMM is capable of.  It provides a simple "Getting Started" guide for those for whom the standard install instructions make no sense; presumably because you've never run a Docker container before.


## Prerequisites.

Anywhere you see

```
something like this
```

That’s a command you’re going to type or paste into your terminal (OSX or Linux) or Powershell (Windows).

**IMPORTANT NOTES:**

* This walkthrough is going to be pretty pedantic.  I’m assuming you’re reading it because you have no idea how to get a Docker container going, so I’m proceeding from the assumption that you want to be walked through every little detail.  You’re going to deliberately cause errors and then fix them as you go through it.  This is to help you understand what exactly is going on behind the scenes so that when you see these sorts of problems in the wild you will have some background to understand what’s happening.  If I only give you the happy path walkthrough, then when you make a typo later on you’ll have no idea where that typo might be or why it’s breaking things.

* I am assuming you do not have any of these tools already installed.  When writing this up I started with a brand new Windows 10 install.

* I'm also assuming you are doing this on a computer, not through a NAS interface or the like.  You can do all this through something like the Synology NAS UI or Portainer or the like, but those aren't documented here.  This uses the docker command line because it works the same on all platforms.

* You may want to take an hour to get familiar with Docker fundamentals with the [official tutorial](https://www.docker.com/101-tutorial/).

* DO NOT MAKE ANY CHANGES BELOW if you want this to just work.  Don't change the docker image [`linuxserver.io` will not work for this, for example]; don't change the paths, etc.

### Prepare a small test library [optional]

```{include} wt/wt-test-library.md
```

### Starting up your terminal.

Since most of this is typing commands into a terminal, you'll need to have a terminal open.

````{tab} Linux
<br/>
If your Linux system is remote to your computer, connect to it via SSH.  That SSH session is the terminal you will be using, so leave it open.

If you are running this on a desktop Linux machine, start up the Terminal application.  That window will be the terminal you will type commands into throughout this walkthrough, so leave it open.
<br/>
````
````{tab} OS X:
Open the Terminal app; this window will be the place you type commands throughout this walkthrough, so leave it open.  The Terminal app is in Applications -> Utilities.

You can also use iTerm or some other terminal app if you wish.  If you don't know what that means, use Terminal.
<br/>
````
````{tab} Windows:
Use the Start menu to open PowerShell.  This will be the window into which you type commands throughout this walkthrough, so leave it open.
<br/>
````

### Installing Docker.

To run Docker images, you need to have Docker installed.  It is not typically installed on new Mac, Linux, or Windows machines.

The Docker install is discussed here: [Installing Docker](https://docs.docker.com/engine/install/)

Once you have Docker installed, test it at the command line with:

[type this into your terminal]
```
docker run --rm hello-world
```
You should see something that starts with:
```
Hello from Docker!
This message shows that your installation appears to be working correctly.
...
```

If that doesn't work, stop here until you fix that.  Diagnoing and repairing Docker install problems is out of the scope of this walkthrough.

---

#### Important note on Docker images

This tutorial uses the official image, and you should, too.  Don't change `meisnate12/plex-meta-manager` to the `linuxserver.io` image or any other; other images may have [idiosyncracies](images.md) that will prevent this walkthrough from working.  The official image *will* behave exactly as documented below.  Others very possibly won't.

The great thing about Docker is that all the setup you'd have to do to run PMM is already done inside the docker image.

That means we can just jump right into running it.  At the command prompt, type:

```
docker run --rm meisnate12/plex-meta-manager --run

```

This is going to fail with an error.  That's expected.

You should see something like this:

```
Unable to find image 'meisnate12/plex-meta-manager:latest' locally
latest: Pulling from meisnate12/plex-meta-manager
7d63c13d9b9b: Already exists
6ad2a11ca37b: Already exists
8076cdef4689: Pull complete
0ba90f5a7dd0: Pull complete
27c191df269f: Pull complete
c75e4c0924fa: Pull complete
ed6716577767: Pull complete
0547721ab7a3: Pull complete
ea4d35bce959: Pull complete
Digest: sha256:472be179a75259e07e68a3da365851b58c2f98383e02ac815804299da6f99824
Status: Downloaded newer image for meisnate12/plex-meta-manager:latest
Config Error: config not found at //config
```

That error means you don’t have a config file, but we know that most everything is in place to run the image.

### Setting up a volume map

PMM, inside that Docker container, can only see other things *inside the container*.  We want to add our own files for config and metadata, so we need to set something up that lets PMM see files we create *outside* the container.  This is called a "volume map".

Go to your home directory and create a new directory:

[type this into your terminal]

```
cd ~
mkdir plex-meta-manager
```

cd into that directory and create another directory:

[type this into your terminal]

```
cd ~/plex-meta-manager
mkdir config
```

get the full path:

[type this into your terminal]

```
pwd
```

This will display a full path:

````{tab} Linux
```
/home/YOURUSERNAME/plex-meta-manager
```
````
````{tab} OS X
```
/Users/YOURUSERNAME/plex-meta-manager
```
````
````{tab} Windows
```
C:\Users\YOURUSERNAME\plex-meta-manager
```
````

Add "config" onto the end of that to get the host path to your config directory, for example:

````{tab} Linux
```
/home/YOURUSERNAME/plex-meta-manager/config
```
````
````{tab} OS X
```
/Users/YOURUSERNAME/plex-meta-manager/config
```
````
````{tab} Windows
```
C:\Users\YOURUSERNAME\plex-meta-manager\config
```
````

You'll need to add this to the docker command every time you run it, like this:

````{tab} Linux
```
docker run --rm -it -v "/home/YOURUSERNAME/plex-meta-manager/config:/config:rw" meisnate12/plex-meta-manager
```
````
````{tab} OS X
```
docker run --rm -it -v "/Users/YOURUSERNAME/plex-meta-manager/config:/config:rw" meisnate12/plex-meta-manager
```
````
````{tab} Windows
```
docker run --rm -it -v "C:\Users\YOURUSERNAME\plex-meta-manager\config:/config:rw" meisnate12/plex-meta-manager
```
````

If you run that command now it will display a similar error to before, but without all the image loading:

```
 $ docker run --rm -it -v "/Users/mroche/plex-meta-manager/config:/config:rw" meisnate12/plex-meta-manager --run
Config Error: config not found at //config
```

Note that I show the example path there.

<details>
  <summary>Why did we create that `config' directory?</summary>

  This was done so that from here on in the instructions match between this walkthrough and the [Local walkthrough](local) are the same.

</details>


### Create a directory to quiet an error later

The default config file contains a reference to a directory that will show an error in the output later.  That error can safely be ignored, but it causes some confusion with new users from time to time.

We'll create it here so the error doesn't show up later.

````{tab} Linux
[type this into your terminal]
```
mkdir config/assets
```
````
````{tab} OS X
[type this into your terminal]
```
mkdir config/assets
```
````
````{tab} Windows
[type this into your terminal]
```
mkdir config\assets
```
````

### Setting up the initial config file

```{include} wt/wt-01-basic-config.md
```

#### Editing the config template

First, make a copy of the template:

````{tab} Linux
Get a copy of the template to edit [type this into your terminal]:
```
curl -fLvo config/config.yml https://raw.githubusercontent.com/meisnate12/Plex-Meta-Manager/master/config/config.yml.template
```
````
````{tab} OS X
Get a copy of the template to edit [type this into your terminal]:
```
curl -fLvo config/config.yml https://raw.githubusercontent.com/meisnate12/Plex-Meta-Manager/master/config/config.yml.template
```
````
````{tab} Windows
Go to [this URL](https://raw.githubusercontent.com/meisnate12/Plex-Meta-Manager/master/config/config.yml.template) using a web browser; choose the "Save" command, then save the file at:
```
C:\Users\YOURUSERNAME\plex-meta-manager\config\config.yml
```
````

Now open the copy in an editor:

```{include} wt/wt-editor.md
```

```{include} wt/wt-02-config-bad-library.md
```

#### Testing the config file

Save the file:

```{include} wt/wt-save.md
```

Then run the script again:

```{include} wt/wt-run-docker.md
```

```{include} wt/wt-03-lib-err-and-fix.md
```


### Creating a few sample collections.

```{include} wt/wt-04-default-intro.md
```

So let's run the script and see this happen:


```{include} wt/wt-run-docker.md
```

```{include} wt/wt-04b-default-after.md
```

### Setting up a metadata file and creating a few sample collections.

```{include} wt/wt-05-local-file.md
```

Save the file:

```{include} wt/wt-save.md
```

Then run the script again:

```{include} wt/wt-run-docker.md
```

```{include} wt/wt-06-local-after.md
```

### Adding Overlays to movies.

```{include} wt/wt-07-overlay-add.md
```

Save the file:

```{include} wt/wt-save.md
```

Then run the script again:

```{include} wt/wt-run-docker.md
```

```{include} wt/wt-08-overlay-after.md
```

```{include} wt/wt-09-next-steps.md
```

## Other Topics

### Scheduling

```{include} wt/wt-10-scheduling.md
```

### I want to use the develop branch

Add the `develop` tag to the image name in your run command [or wherever you specify the image in your environment]

```
docker run --rm -it -v "PMM_PATH_GOES_HERE:/config:rw" meisnate12/plex-meta-manager:develop --run
                                                                                    ^^^^^^^
```

This may not work if you are not using the official image; for example, it does not work with the lsio image.

### I want to use the nightly branch

Add the `nightly` tag to the image name in your run command [or wherever you specify the image in your environment]

```
docker run --rm -it -v "PMM_PATH_GOES_HERE:/config:rw" meisnate12/plex-meta-manager:nightly --run
                                                                                    ^^^^^^^
```

This may not work if you are not using the official image; for example, it does not work with the lsio image.

### I want to ensure I am using the master branch

Add the `latest` tag to the image name in your run command [or wherever you specify the image in your environment]

```
docker run --rm -it -v "PMM_PATH_GOES_HERE:/config:rw" meisnate12/plex-meta-manager:latest --run
                                                                                    ^^^^^^
```

This is the only version tag supplied by the lsio image.

