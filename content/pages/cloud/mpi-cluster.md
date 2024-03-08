---
title: Quick MPI Cluster Setup on Azure
shortTitle: MPI Cluster Setup on Azure
order: 10
---

{% call alert(type="info") %}
This page is still a work in progress because the notes and inputs/outputs are not well explained yet.
{% endcall %}

These instructions show the most basic way to create a cluster that's capable
of running MPI across the general-purpose network in Azure.  This is meant to
be a _simple_ illustration of how to do it, using the most basic steps, to show
what the process looks like. This is _not_ how you would create a production
HPC cluster for real; [CycleCloud][] and similar tools automate and simplify
most of this, but my goal here is to show what is happening underneath those
automations so you can play around.

We will use the [Azure CLI][] to do everything and assume you have already
set that up with your Azure account and subscription.

[clush]: https://clustershell.readthedocs.io/en/latest/tools/clush.html
[CycleCloud]: https://learn.microsoft.com/en-us/azure/cyclecloud/overview?view=cyclecloud-8
[Azure CLI]: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli
[cloud-init]: https://cloudinit.readthedocs.io/en/latest/
[OpenMPI]: https://www.open-mpi.org/

## Create compute nodes

On your local machine (same place you'll run your <kbd>az</kbd> commands),
create a file called `cloud-init.txt` that contains this:

```
#cloud-config
package_upgrade: true
packages:
  - clustershell
  - openmpi-bin
  - libopenmpi-dev
```

We'll pass this [cloud-init][] file into Azure's VM provisioning process to
preinstall [clush][] (which lets us run the same command across all our nodes)
and [OpenMPI][] (which we need to build and run MPI applications) as part of
the VM provisioning process.  If you want to get fancy, you can also jam an
entire bash script into this text file to have it run verbatim upon VM boot.

The first Azure resource we create is a _resource group_. This is just a logical
container that will group all our cluster parts.

<div class="codehilite"><pre>
$ <kbd>az group create --name <span style="color:#1b9e77">glocktestrg</span> --location eastus</kbd>
</pre></div>

Once this resource group is created, we can start creating compute nodes inside
it. There are two ways to do this: the cheap/easy way and the proper/expensive
way.

### Cheap (Ethernet) nodes

Create a _proximity placement group_ (ppg). Every VM we put in here will be
within the same low-latency network bubble.

<div class="codehilite"><pre>
$ <kbd>az ppg create --name <span style="color:#a65628">glocktestppg</span> \
               --resource-group <span style="color:#1b9e77">glocktestrg</span> \
               --intent-vm-sizes <span style="color:#e7298a">Standard_DS1_v2</span></kbd>
</pre></div>

Now we create a group of four compute nodes in that ppg.  The [Azure CLI][]
makes this pretty easy nowadays.

<div class="codehilite"><pre>
$ <kbd>az vm create --name <span style="color:#ff7f00">glocluster</span> \
             --resource-group <span style="color:#1b9e77">glocktestrg</span> \
             --image UbuntuLTS \
             --ppg <span style="color:#a65628">glocktestppg</span> \
             --generate-ssh-keys \
             --size <span style="color:#e7298a">Standard_DS1_v2</span> \
             --accelerated-networking true \
             --custom-data cloud-init.txt \
             --count 4</kbd>
</pre></div>

What this means:

- the nodes will be named
  <code><span style="color:#ff7f00">glocluster</span>0</code>,
  <code><span style="color:#ff7f00">glocluster</span>1</code>,
  <code><span style="color:#ff7f00">glocluster</span>2</code>,
  <code><span style="color:#ff7f00">glocluster</span>3</code>,
- `--image UbuntuLTS` installs Ubuntu on each VM. This aliases to an old (18.04)
  version; if you want something else, use `az vm image list -p canonical
  -o table --all` to find all Ubuntu (canonical) images.  For example,
  `Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest` will use
  Ubuntu 22.04 instead.
- `--generate-ssh-keys` puts your local ssh key `~/.ssh/id_rsa.pub`
  into the `authorized_keys` file in all the nodes you're creating
- `--size Standard_DS1_v2` says to use [DS1\_v2][ds1v2] VM types
- `--accelerated-networking true` says to pass the NIC through to your VM
  using SR-IOV. It doesn't cost anything, so I don't really know why you would
  _not_ want this.
- `--custom-data cloud-init.txt` passes in our cloud-init.txt file to the
  provisioning process
- `--count 4` says to make four VMs total.

[ds1v2]: https://learn.microsoft.com/en-us/azure/virtual-machines/dv2-dsv2-series

This command will block until all VMs are up and running. Then, we can see what
all was created using:

<div class="codehilite"><pre>
$ <kbd>az resource list --resource-group <span style="color:#1b9e77">glocktestrg</span> -o table</kbd>

Name                   ResourceGroup    Location    Type                                          Status
---------------------  ---------------  ----------  --------------------------------------------  --------
<span style="color:#a65628">glocktestppg</span>           <span style="color:#1b9e77">glocktestrg</span>      eastus      Microsoft.Compute/proximityPlacementGroups
<span style="color:#ff7f00">glocluster</span>PublicIP3    <span style="color:#1b9e77">glocktestrg</span>      eastus      Microsoft.Network/publicIPAddresses
<span style="color:#ff7f00">glocluster</span>NSG          <span style="color:#1b9e77">glocktestrg</span>      eastus      Microsoft.Network/networkSecurityGroups
<span style="color:#ff7f00">glocluster</span>PublicIP2    <span style="color:#1b9e77">glocktestrg</span>      eastus      Microsoft.Network/publicIPAddresses
...
</div></pre>

The VMs created all have public IPs and share a common subnet on a common VNet
within close physical proximity thanks to our proximity placement group.

### Proper (InfiniBand) nodes

InfiniBand is only available on HPC (read: expensive) VM types, and provisioning
nodes on the same InfiniBand fabric requires creating a VM Scale Set (VMSS)
instead of individual VMs. To create a VMSS of HBv2 nodes with InfiniBand,

<div class="codehilite"><pre>
<kbd>az vmss create --name <span style="color:#ff7f00">glocluster</span> \
               --resource-group <span style="color:#1b9e77">glocktestrg</span> \
               --image Microsoft-dsvm:ubuntu-hpc:2204:latest \
               --generate-ssh-keys \
               --vm-sku <span style="color:#e7298a">Standard_HB120rs_v2</span> \
               --accelerated-networking true \
               --public-ip-per-vm \
               --custom-data cloud-init.txt \
               --instance-count 4 </kbd>
</div></pre>

What this means:

- the nodes' name will be prefixed with <span style="color:#ff7f00">glocluster</span>
  followed by some hexadecimal number to uniquely identify them.
- `--image Microsoft-dsvm:ubuntu-hpc:2204:latest` installs the special Azure HPC
  flavor of Ubuntu on each VM. This VM image includes all the InfiniBand
  drivers.
- `--generate-ssh-keys` puts your local ssh key `~/.ssh/id_rsa.pub`
  into the `authorized_keys` file in all the nodes you're creating.
- `--size Standard_HB120rs_v2` says to use [HBv2][hbv2] VM types.
- `--accelerated-networking true` says to pass the NIC through to your VM
  using SR-IOV. It doesn't cost anything, so I don't really know why you would
  _not_ want this.
- `--public-ip-per-vm` assigns a public IP address to each node. This makes it
  easier for you to connect to them in this example, but each public IP does
  cost money.
- `--custom-data cloud-init.txt` passes in our cloud-init.txt file to the
  provisioning process.
- `--instance-count 4` says to make four VMs total to start. You can manually
  scale this up or down with a single command (`az vmss scale`) later.

VMSSes are nice because they essentially establish a VM template from which VMs
can be instantiated and torn down with a single command. In combination with
a well-formed cloud-init script, you can get a VMSS set up just the way you
like it, then spin up a whole cluster (using `az vmss scale`) and have nodes
just come online and be ready to use. At the end of the day, you can then scale
the VMSS down to zero nodes to stop racking up costs without losing your VMSS
configuration. When it's time to spin up, you just use `az vmss scale` again to
go from zero nodes to however many you want to play with.

[hbv2]: https://learn.microsoft.com/en-us/azure/virtual-machines/hbv2-series

## Log into nodes

At this point you should have a cluster of running VMs.

### SSH to your cluster

First, list the public and private IP addresses of your cluster.  We'll need to
SSH to one of the nodes using its public IP address:

<div class="codehilite"><pre>
$ <kbd>az vm list-ip-addresses --resource-group <span style="color:#1b9e77">glocktestrg</span> -o table</kbd>

VirtualMachine    PublicIPAddresses    PrivateIPAddresses
----------------  -------------------  --------------------
glocluster0       <span style="color:#d95f02">20.25.28.201</span>         10.0.0.7
glocluster1       20.25.25.225         10.0.0.6
glocluster2       20.25.24.166         10.0.0.4
glocluster3       20.169.149.181       10.0.0.5
</pre></div>

The <kbd>az vm create</kbd> command created a user for you on your VMs with
the same name as your local user (the one who ran the `az` command; in my case,
`glock`, but you can override this using `--admin-username`). It also puts your
local ssh key (`~/.ssh/id_rsa.pub`) in each VM's `authorized_keys` file.  So
at this point, you should be able to log into your head node:

<div class="codehilite"><pre>
$ <kbd>ssh <span style="color:#d95f02">20.25.28.201</span></kbd>
$ <kbd>exit</kbd>
</pre></div>

Copy your private ssh key from your local laptop to remote node so you can then
ssh from your login node to your other nodes.

<div class="codehilite"><pre>
$ <kbd>scp ~/.ssh/id_rsa <span style="color:#d95f02">20.25.28.201</span>:.ssh/</kbd>
</pre></div>

Note this is **very bad security practice** that you shouldn't do unless you're
messing around, since you shouldn't be sharing private keys between your home
computer and this cluster (think: if someone breaks into our cloud cluster, they
have the same key you use at home).

### Configure inter-host connectivity

These VMs can already resolve each others' hostnames thanks to Azure magic, so
there's no need to add `glocluster0`, `glocluster1`, etc to `/etc/hosts`.

To get passwordless ssh up and working (so we can noninteractively
run commands on other nodes through SSH), first add all the compute nodes' host
keys to your SSH `known_hosts` file:

<div class="codehilite"><pre>
$ <kbd>for i in {0..3};do ssh-keyscan glocluster${i};done > ~/.ssh/known_hosts</kbd>
</pre></div>

The `ssh-keyscan` command just connects to another hosts and retrieves its host
keys, which we then store in `~/.ssh/known_hosts` on our main `glocluster0`
node.

Now the `clush` command (which we installed via [cloud-init][]) will work and
don't have to keep using bash for loops to do something on all our nodes.
Make sure clush works across all nodes:

<div class="codehilite"><pre>
$ <kbd>clush -w glocluster[0-3] uname -n</kbd>
</pre></div>

Then copy your `known_hosts` and private key to all cluster nodes using
`clush -c`:

<div class="codehilite"><pre>
$ <kbd>clush -w glocluster[0-3] -c ~/.ssh/id_rsa ~/.ssh/known_hosts</kbd>
</pre></div>

Now we have passwordless ssh working between all our nodes, and we are ready to
run an MPI application!

### Run MPI hello world

Create a file called `hello.c` and stick the following code in it:

```c
#include <stdio.h>
#include <unistd.h>
#include <mpi.h>

int main (int argc, char **argv)
{
    int mpi_rank, mpi_size;
    char host[1024];

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &mpi_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &mpi_size);

    gethostname(host, 1024);
    printf("Hello from rank %d of %d running on on %s\n", 
        mpi_rank, 
        mpi_size, 
        host);

    MPI_Finalize();
    return 0;
}
```

Compile the above using `mpicc hello.c -o hello`.

Then copy it to all your nodes:

<div class="codehilite"><pre>
$ <kbd>clush -w glocluster[0-3] -c hello</kbd>
</pre></div>

Now make sure MPI works:

<div class="codehilite"><pre>
$ <kbd>mpirun --host glocluster0,glocluster1,glocluster2,glocluster3 ./hello</kbd>
</pre></div>

You might get some stupid warnings about `openib` like this:

<div class="codehilite"><pre>
--------------------------------------------------------------------------
[[50939,1],0]: A high-performance Open MPI point-to-point messaging module
was unable to find any relevant network interfaces:
  
Module: OpenFabrics (openib)
  Host: glocluster3
</pre></div>

It's harmless, but you can make these go away by explicitly telling OpenMPI to only use TCP, shared memory (`vader`), and application memory:

<div class="codehilite"><pre>
$ <kbd>mpirun --host glocluster0,glocluster1,glocluster2,glocluster3 --mca btl tcp,vader,self ./hello</kbd>
</pre></div>

If you want to do some basic performance testing, try the [OSU Micro-Benchmarks][].  First build them:

[OSU Micro-Benchmarks]: https://mvapich.cse.ohio-state.edu/benchmarks/

<div class="codehilite"><pre>
$ <kbd>sudo apt -y install make g++</kbd>

$ <kbd>wget https://mvapich.cse.ohio-state.edu/download/mvapich/osu-micro-benchmarks-6.1.tar.gz</kbd>

$ <kbd>tar zxf osu-micro-benchmarks-6.1.tar.gz</kbd>

$ <kbd>cd osu-micro-benchmarks-6.1/</kbd>

$ <kbd>./configure --prefix $PWD/install CC=mpicc CXX=mpicxx</kbd>

$ <kbd>make && make install</kbd>
</pre></div>

Copy the compiled app everywhere:

<div class="codehilite"><pre>
$ <kbd>cd</kbd>
$ <kbd>clush -w glocluster[0-3] -c osu-micro-benchmarks-6.1</kbd>
</pre></div>

Then try measuring latency!

<div class="codehilite"><pre>
$ <kbd>mpirun -np 2 --host glocluster1,glocluster2 ./osu-micro-benchmarks-6.1/install/libexec/osu-micro-benchmarks/mpi/pt2pt/osu_latency</kbd>

# OSU MPI Latency Test v6.1
# Size          Latency (us)
0                      31.28
1                      27.95
2                      26.76
4                      28.75
</pre></div>

## Create a shared file system

Using `clush` to copy your binaries and files to your home directory on every
compute node is really tedious.  An easier way to manage data is to put this
shared data in a shared network file system.  Here we show how to do this the
easy way (just export a directory from your head node) and cool way (mount an
object container using NFS).

In both cases, first install the NFS client packages and create the directory
where we'll mount this NFS volume (`/scratch`):

<div class="codehilite"><pre>
# install the nfs client and server on all nodes
$ <kbd>clush -w glocluster[0-3] sudo apt -y install nfs-common nfs-kernel-server</kbd>

# create the shared mountpoint on all nodes
$ <kbd>clush -w glocluster[0-3] sudo mkdir /scratch</kbd>
</pre></div>

### Exporting from a node

The simplest way to share data via NFS is by exporting a directory from one
of your nodes (like the main node) and mounting it across all nodes.  This is
_not_ scalable, but it's good enough for messing around.

First create a local directory on our primary node called `/shared` with the
goal to mount it everywhere as the `/scratch` directory:

<div class="codehilite"><pre>
# make the directory we're going to share and make sure we can write to it
$ <kbd>sudo mkdir /shared</kbd>
$ <kbd>sudo chown glock:glock /shared</kbd>

# share the directory - limit it only to our subnet (10.0.&#42;) though since all our nodes have public IP addresses
$ <kbd>sudo bash -c 'echo "/shared 10.0.&#42;(rw,no_root_squash,no_subtree_check)" >> /etc/exports'</kbd>
$ <kbd>sudo exportfs -a</kbd>
</pre></div>

Remember that our main node's IP address is 10.0.0.7 (if you forget, just check using `ip addr list`)

<div class="codehilite"><pre>
$ <kbd>clush -w glocluster[0-3] sudo mount -t nfs -o vers=3,rsize=1048576,wsize=1048576,nolock,proto=tcp,nconnect=8 10.0.0.7:/shared /scratch</kbd>
</pre></div>

Make sure it works:

<div class="codehilite"><pre>
$ <kbd>touch /scratch/hello</kbd>

$ <kbd>clush -w glocluster[0-3] ls -l /scratch</kbd>

glocluster0: total 0
glocluster0: -rw-rw-r-- 1 glock glock 0 Sep 25 23:24 hello
glocluster3: total 0
...
</pre></div>

### Using Blob NFS

Create a slow storage account:

<div class="codehilite"><pre>
$ <kbd>az storage account create --name glockteststorage \
                          --resource-group <span style="color:#1b9e77">glocktestrg</span> \
                          --sku Standard_LRS \
                          --enable-hierarchical-namespace true \
                          --enable-nfs-v3 true \
                          --default-action deny</kbd>
</pre></div>

Or an SSD-backed storage account:

<div class="codehilite"><pre>
$ <kbd>az storage account create --name glockteststorage \
                          --resource-group <span style="color:#1b9e77">glocktestrg</span> \
                          --kind BlockBlobStorage \
                          --sku Premium_LRS \
                          --enable-hierarchical-namespace true \
                          --enable-nfs-v3 true \
                          --default-action deny</kbd>
</pre></div>

Blob NFS would be super insecure since it uses NFS v3 and relies on access control via the network which is decidedly un-cloudlike since storage accounts otherwise are meant to be accessed from the public Internet.  This requires us to set `--default-action deny` to disallow all traffic by default and only allow traffic from specific subnets.  Let's add ours:

You will need to get the name of the subnet of the vnet you just created:

<div class="codehilite"><pre>
$ <kbd>az network vnet subnet list --resource-group <span style="color:#1b9e77">glocktestrg</span> --vnet-name gloclusterVNET -o table</kbd>

AddressPrefix    Name              PrivateEndpointNetworkPolicies    PrivateLinkServiceNetworkPolicies    ProvisioningState    ResourceGroup
---------------  ----------------  --------------------------------  -----------------------------------  -------------------  ---------------
10.0.0.0/24      gloclusterSubnet  Disabled                          Enabled                              Succeeded            <span style="color:#1b9e77">glocktestrg</span>
</pre></div>

<div class="codehilite"><pre>
# enable the service endpoint for Azure Storage on our subnet
$ <kbd>az network vnet subnet update --resource-group <span style="color:#1b9e77">glocktestrg</span> \
                              --vnet-name gloclusterVNET \
                              --name gloclusterSubnet \
                              --service-endpoints Microsoft.Storage</kbd>

# add a network rule to the storage account allowing access from our vnet
$ <kbd>az storage account network-rule add --resource-group <span style="color:#1b9e77">glocktestrg</span> \
                                    --account-name glockteststorage \
                                    --vnet-name gloclusterVNET \
                                    --subnet gloclusterSubnet</kbd>

# confirm that access is now allowed
$ <kbd>az storage account network-rule list --resource-group <span style="color:#1b9e77">glocktestrg</span> \
                                     --account-name glockteststorage \
                                     --query virtualNetworkRules</kbd>
</pre></div>

You will probably also have to add your home IP address (or whatever IP address Azure will see when you try to connect directly to it; try using the address that shows up when you run `who` on your cluster) as a rule:

<div class="codehilite"><pre>
$ <kbd>az storage account network-rule add --resource-group <span style="color:#1b9e77">glocktestrg</span> \
                                    --account-name glockteststorage \
                                    --ip-address 136.24.220.92</kbd>
</pre></div>

Then you can create a storage _container_ which will also act as your NFS export:

<div class="codehilite"><pre>
$ <kbd>az storage fs create --name glocktestscratch \
                     --account-name glockteststorage \
                     --auth-mode login</kbd>
</pre></div>

That `--auth-mode` bit uses the same credentials the rest of your `az` commands are using. It's there because, unlike the other `az` commands we've been running, `az storage fs create` is actually talking to the Azure Storage data plane and using the same interface you'd use if you were reading or writing data.

Anyway, with this container now created, get our service endpoint:

<div class="codehilite"><pre>
$ <kbd>az storage account show --resource-group <span style="color:#1b9e77">glocktestrg</span> \
                          --name glockteststorage \
                          --query primaryEndpoints</kbd>

{
  "blob": "https://glockteststorage.blob.core.windows.net/",
  "dfs": "https://glockteststorage.dfs.core.windows.net/",
  "file": "https://glockteststorage.file.core.windows.net/",
  "internetEndpoints": null,
  "microsoftEndpoints": null,
  "queue": "https://glockteststorage.queue.core.windows.net/",
  "table": "https://glockteststorage.table.core.windows.net/",
  "web": "https://glockteststorage.z13.web.core.windows.net/"
}
</pre></div>

Then from our cluster, we can mount it:

<div class="codehilite"><pre>
$ <kbd>clush -w glocluster[0-3] sudo mount -t nfs -o vers=3,rsize=1048576,wsize=1048576,hard,nolock,proto=tcp,nconnect=8 glockteststorage.blob.core.windows.net:/glockteststorage/glocktestscratch /scratch</kbd>
</pre></div>

The container gets mounted as nobody and cannot be accessed by anyone, but we can open it up with root and create a user directory in there:

<div class="codehilite"><pre>
$ <kbd>sudo chmod o+rx /scratch</kbd>

$ <kbd>sudo mkdir /scratch/glock</kbd>
$ <kbd>sudo chown glock:glock /scratch/glock</kbd>
</pre></div>

Now we can work in it as a regular user:

<div class="codehilite"><pre>
$ <kbd>touch /scratch/glock/hello</kbd>

$ <kbd>clush -w glocluster[0-3] ls -l /scratch/glock/hello</kbd>
glocluster0: -rw-rw-r-- 1 glock glock 0 Sep 26 00:14 /scratch/glock/hello
glocluster1: -rw-rw-r-- 1 glock glock 0 Sep 26 00:14 /scratch/glock/hello
</pre></div>

## Deleting public IPs of non-primary nodes

Note we do NOT start at node0 - we need that public IP to connect in!

<div class="codehilite"><pre>
<kbd>for i in {1..3}; do
    az network nic ip-config update --resource-group <span style="color:#1b9e77">glocktestrg</span> \
                                    --name ipconfigglocluster${i} \
                                    --nic-name gloclusterVMNic${i} \
                                    --remove PublicIpAddress
    az network public-ip delete --resource-group <span style="color:#1b9e77">glocktestrg</span> \
                                --name gloclusterPublicIP${i}
done</kbd>
</pre></div>
