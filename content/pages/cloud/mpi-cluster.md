---
title: Quick MPI Cluster Setup on Azure
shortTitle: MPI Cluster Setup on Azure
order: 10
---

{% call alert(type="info") %}
This page is still a work in progress because the notes and inputs/outputs are not well explained yet.
{% endcall %}

## Create compute nodes

The Azure CLI makes it pretty easy to create a cluster of nodes nowadays:

```bash
# create resource group
az group create --name glocktestrg --location eastus

# create proximity placement group
az ppg create --name glocktestppg --resource-group glocktestrg --intent-vm-sizes Standard_DS1_v2

# create four VMs
az vm create --name glocluster \
             --resource-group glocktestrg \
             --image UbuntuLTS \
             --ppg glocktestppg \
             --generate-ssh-keys \
             --size Standard_DS1_v2 \
             --accelerated-networking true \
             --admin-username glock \
             --custom-data cloud-init.txt \
             --count 4
```

If you want to use something other than the `UbuntuLTS` image (which is an alias for Ubuntu 18.04, which is quite old) you can scroll through the output of `az vm image list -p canonical -o table --all`.  A newer Ubuntu can be used via the image named `Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest`, for example.

To see everything this command created:

```
$ az resource list --resource-group glocktestrg -o table

Name                   ResourceGroup    Location    Type                                          Status
---------------------  ---------------  ----------  --------------------------------------------  --------
glocktestppg           glocktestrg      eastus      Microsoft.Compute/proximityPlacementGroups
gloclusterPublicIP3    glocktestrg      eastus      Microsoft.Network/publicIPAddresses
gloclusterNSG          glocktestrg      eastus      Microsoft.Network/networkSecurityGroups
gloclusterPublicIP2    glocktestrg      eastus      Microsoft.Network/publicIPAddresses
...
```

The VMs created all have public IPs and share a common subnet on a common VNet within close physical proximity thanks to our proximity placement group.  You can list the public and private IP addresses of your cluster:

```
$ az vm list-ip-addresses -g glocktestrg -o table

VirtualMachine    PublicIPAddresses    PrivateIPAddresses
----------------  -------------------  --------------------
glocluster0       20.25.28.201         10.0.0.7
glocluster1       20.25.25.225         10.0.0.6
glocluster2       20.25.24.166         10.0.0.4
glocluster3       20.169.149.181       10.0.0.5
```

You will need to get the name of the subnet of the vnet you just created:

```
az network vnet subnet list --resource-group glocktestrg --vnet-name gloclusterVNET -o table

AddressPrefix    Name              PrivateEndpointNetworkPolicies    PrivateLinkServiceNetworkPolicies    ProvisioningState    ResourceGroup
---------------  ----------------  --------------------------------  -----------------------------------  -------------------  ---------------
10.0.0.0/24      gloclusterSubnet  Disabled                          Enabled                              Succeeded            glocktestrg
```

The `az vm create` command creates a user for you on your VMs with the same name as your local user (in my case, `glock`) and puts your local ssh key `~/.ssh/id_rsa.pub` in there.  So at this point, you should be able to log into your head node:

```
ssh 20.25.28.201
exit
```

Copy your private ssh key from your local laptop to remote node so you can then ssh from your login node to your other nodes.

```
scp ~/.ssh/id_rsa 20.25.28.201:.ssh/
```

### Generate a hosts file
We'll add our cluster nodes to the hosts file so we don't have to remember their IP addresses.  Use the output from the `az vm list-ip-addresses -g glocktestrg -o table` command above, or try some fancy querying:

```
$ az vm list-ip-addresses -g glocktestrg --query '[*].virtualMachine.[name, network.privateIpAddresses[0]]' -o table

Column1      Column2
-----------  ---------
glocluster0  10.0.0.7
glocluster1  10.0.0.6
glocluster2  10.0.0.4
glocluster3  10.0.0.5
```

So log into your cluster head node:

```
$ ssh 20.25.28.201
$ sudo vi /etc/hosts

# paste in the above mappings

$ cat /etc/hosts
127.0.0.1 localhost

# The following lines are desirable for IPv6 capable hosts
::1 ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
ff02::3 ip6-allhosts

glocknode0  10.0.0.4
glocknode1  10.0.0.5
glocknode2  10.0.0.8
glocknode3  10.0.0.7
glocknode4  10.0.0.6
```

Now we need to get passwordless ssh up and working.  First add all the compute nodes to your known hosts file:

```
for i in {0..3};do ssh-keyscan glocluster${i};done > ~/.ssh/known_hosts
```

This allows the `clush` command to work which we'll use to avoid having to keep using these for loops to do something on all our nodes.   Make sure clush works:

```
$ clush -w glocluster[0-3] uname -n
```

Then copy your `known_hosts` and private key to all cluster nodes:

```
clush -w glocluster[0-3] -c ~/.ssh/id_rsa ~/.ssh/known_hosts
```

## Run MPI hello world

```
$ cat hello.c 
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

Compile the above:

```bash
mpicc hello.c
```

Then copy it to all your nodes:

```
clush -w glocluster[0-3] -c a.out
```

Now make sure MPI works:

```
mpirun --host glocluster0,glocluster1,glocluster2,glocluster3 ./a.out
```

You might get some stupid warnings about `openib` like this:

```
--------------------------------------------------------------------------
[[50939,1],0]: A high-performance Open MPI point-to-point messaging module
was unable to find any relevant network interfaces:
  
Module: OpenFabrics (openib)
  Host: glocluster3
```

It's harmless, but you can make these go away by explicitly telling OpenMPI to only use TCP, shared memory (`vader`), and application memory:

```
mpirun --host glocluster0,glocluster1,glocluster2,glocluster3 --mca btl tcp,vader,self ./a.out
```

If you want to do some basic performance testing, try the OSU Micro-Benchmarks.  First build them:

```
$ sudo apt -y install make g++

$ wget https://mvapich.cse.ohio-state.edu/download/mvapich/osu-micro-benchmarks-6.1.tar.gz

$ tar zxf osu-micro-benchmarks-6.1.tar.gz

$ cd osu-micro-benchmarks-6.1/

$ ./configure --prefix $PWD/install CC=mpicc CXX=mpicxx

$ make && make install

$ cd

# copy the compiled app everywhere
$ clush -w glocluster[0-3] -c osu-micro-benchmarks-6.1
```

Then try measuring latency!

```
$ mpirun -np 2 --host glocluster0,glocluster1,glocluster2,glocluster3 ./osu-micro-benchmarks-6.1/install/libexec/osu-micro-benchmarks/mpi/pt2pt/osu_latency
# OSU MPI Latency Test v6.1
# Size          Latency (us)
0                      31.28
1                      27.95
2                      26.76
4                      28.75
```

## Create an NFS share

Using `clush` to copy your binaries and files to your home directory on every compute node is really tedious.  An easier way to manage data is to have your main node share a directory via NFS.

Let's create a local directory on our primary node called `/shared` with the goal to mount it everywhere as the `/scratch` directory:

```bash
# make the directory we're going to share and make sure we can write to it
$ sudo mkdir /shared
$ sudo chown glock:glock /shared

# create the shared mountpoint on all nodes
$ clush -w glocluster[0-3] sudo mkdir /scratch

# install the nfs client and server on all nodes
$ clush -w glocluster[0-3] sudo apt -y install nfs-common nfs-kernel-server

# share the directory - limit it only to our subnet (10.0.*) though since all our nodes have public IP addresses
$ sudo bash -c 'echo "/shared 10.0.*(rw,no_root_squash,no_subtree_check)" >> /etc/exports'
$ sudo exportfs -a
```

Remember that our main node's IP address is 10.0.0.7 (if you forget, just check using `ip addr list`)
```
$ clush -w glocluster[0-3] sudo mount -t nfs -o vers=3,rsize=1048576,wsize=1048576,nolock,proto=tcp,nconnect=8 10.0.0.7:/shared /scratch
```

Make sure it works:

```
$ touch /scratch/hello

$ clush -w glocluster[0-3] ls -l /scratch

glocluster0: total 0
glocluster0: -rw-rw-r-- 1 glock glock 0 Sep 25 23:24 hello
glocluster3: total 0
...
```

### Blob NFS

Create a slow storage account:
```bash
az storage account create --name glockteststorage \
                          --resource-group glocktestrg \
                          --sku Standard_LRS \
                          --enable-hierarchical-namespace true \
                          --enable-nfs-v3 true \
                          --default-action deny
```

Or an SSD-backed storage account:

```bash
az storage account create --name glockteststorage \
                          --resource-group glocktestrg \
                          --kind BlockBlobStorage \
                          --sku Premium_LRS \
                          --enable-hierarchical-namespace true \
                          --enable-nfs-v3 true \
                          --default-action deny
```

Blob NFS would be super insecure since it uses NFS v3 and relies on access control via the network which is decidedly un-cloudlike since storage accounts otherwise are meant to be accessed from the public Internet.  This requires us to set `--default-action deny` to disallow all traffic by default and only allow traffic from specific subnets.  Let's add ours:

```bash
# enable the service endpoint for Azure Storage on our subnet
az network vnet subnet update --resource-group glocktestrg \
                              --vnet-name gloclusterVNET \
                              --name gloclusterSubnet \
                              --service-endpoints Microsoft.Storage

# add a network rule to the storage account allowing access from our vnet
az storage account network-rule add --resource-group glocktestrg \
                                    --account-name glockteststorage \
                                    --vnet-name gloclusterVNET \
                                    --subnet gloclusterSubnet

# confirm that access is now allowed
az storage account network-rule list --resource-group glocktestrg \
                                     --account-name glockteststorage \
                                     --query virtualNetworkRules
```

You will probably also have to add your home IP address (or whatever IP address Azure will see when you try to connect directly to it; try using the address that shows up when you run `who` on your cluster) as a rule:

```
az storage account network-rule add --resource-group glocktestrg \
                                    --account-name glockteststorage \
                                    --ip-address 136.24.220.92
```

Then you can create a storage _container_ which will also act as your NFS export:

```
az storage fs create --name glocktestscratch \
                     --account-name glockteststorage \
                     --auth-mode login
```

That `--auth-mode` bit uses the same credentials the rest of your `az` commands are using. It's there because, unlike the other `az` commands we've been running, `az storage fs create` is actually talking to the Azure Storage data plane and using the same interface you'd use if you were reading or writing data.

Anyway, with this container now created, get our service endpoint:

```
$ az storage account show --resource-group glocktestrg \
                          --name glockteststorage \
                          --query primaryEndpoints

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
```

Then from our cluster, we can mount it:

```
$ clush -w glocluster[0-3] sudo mount -t nfs -o vers=3,rsize=1048576,wsize=1048576,hard,nolock,proto=tcp,nconnect=8 glockteststorage.blob.core.windows.net:/glockteststorage/glocktestscratch /scratch
```

The container gets mounted as nobody and cannot be accessed by anyone, but we can open it up with root and create a user directory in there:

```
$ sudo chmod o+rx /scratch

$ sudo mkdir /scratch/glock
$ sudo chown glock:glock /scratch/glock
```

Now we can work in it as a regular user:

```
$ touch /scratch/glock/hello

$ clush -w glocluster[0-3] ls -l /scratch/glock/hello
glocluster0: -rw-rw-r-- 1 glock glock 0 Sep 26 00:14 /scratch/glock/hello
glocluster1: -rw-rw-r-- 1 glock glock 0 Sep 26 00:14 /scratch/glock/hello
```

## Deleting public IPs of non-primary nodes

```bash
# note we do NOT start at node0 - we need that public IP to connect in!
for i in {1..3}; do
    az network nic ip-config update --resource-group glocktestrg \
                                    --name ipconfigglocluster${i} \
                                    --nic-name gloclusterVMNic${i} \
                                    --remove PublicIpAddress
    az network public-ip delete --resource-group glocktestrg \
                                --name gloclusterPublicIP${i}
done
```
