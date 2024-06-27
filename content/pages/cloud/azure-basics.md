---
title: Azure Basics
order: 100
---

I'm still figuring out techniques and best practices for using Azure coming from
a background in HPC.  A lot of the documentation takes a
Windows/Powershell/GUI-first approach which does not compute for me, so I'm
taking notes here so I don't lose track of how to do common tasks.

So far I'm converging on using a combination of [Azure CLI][] and [Bicep][] as
the foundational tools for standing up infrastructure in Azure.  I'm not sure
this is the best way to start for people who are new to both Azure itself and
infrastructure-as-code since the declarative approach to IaC adds extra
verbosity and syntactic complexity to operations, so I think starting with the
imperative [Azure CLI][] approach is a good place to start.

[Azure CLI]: https://docs.microsoft.com/en-us/cli/azure/
[Bicep]: https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/overview

## Getting instance metadata

Every VM can access the [Azure Instance Metadata Service (IMDS)][imds] which is
a magic REST endpoint that allows you to inspect properties of a VM from inside
that VM. For example, this is how you can get the managed identity of a VM
from within that VM:

    curl 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https%3A%2F%2Fmanagement.azure.com%2F' -H Metadata:true -s

where `169.254.169.254` is the magical REST endpoint for the [IMDS][imds].

[imds]: https://learn.microsoft.com/en-us/azure/virtual-machines/linux/instance-metadata-service

## Getting physical server info

In addition to the Instance Metadata Service which lets you learn about
the VM in which you are running, you can also query the hypervisor for
information about the bare metal server on which you are running. This relies
on a service referred to as KVP:

```
cat /var/lib/hyperv/.kvp_pool_3 | tr -s '\000' '\n'
HostName
CO2AA1050611004
HostingSystemEditionId
168
HostingSystemNestedLevel
0
HostingSystemOsMajor
10
HostingSystemOsMinor
0
HostingSystemProcessorArchitecture
9
HostingSystemProcessorIdleStateMax
0
HostingSystemProcessorThrottleMax
100
HostingSystemProcessorThrottleMin
100
HostingSystemSpMajor
0
HostingSystemSpMinor
0
PhysicalHostName
CO2AA1050611004
PhysicalHostNameFullyQualified
CO2AA1050611004
VirtualMachineDynamicMemoryBalancingEnabled
0
VirtualMachineId
670093CC-C644-4167-8076-E9678D22C459
VirtualMachineName
902d6ba5-9ac4-4223-a8d9-1c7ca05a9a2c
```

It is fully documented on [Azure's KVP/Hyper-V Data Exchange][kvp] page.

[kvp]: https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2012-R2-and-2012/dn798287(v=ws.11)#linux-guests

## VM SKU / hypervisor conflicts

I tried this:

```
$ az deployment group create --resource-group glock-rg \
                             --template-file template.bicep \
                             --parameters @parameters.json

The selected VM size 'Standard_A1_v2' cannot boot Hypervisor Generation '2'. If
this was a Create operation please check that the Hypervisor Generation of the
Image matches the Hypervisor Generation of the selected VM Size. If this was
an Update operation please select a Hypervisor Generation '2' VM Size.
```

It turns out this is because my `properties.storageProfile.imageReference.sku`
was `18_04-lts-gen2` - the `gen2` was the incompatible part.  To find all the
compatible VMs:

```
$ az vm image list-skus --location westcentralus --publisher Canonical --offer UbuntuServer --output table
Location       Name
-------------  --------------------
westcentralus  12.04.5-LTS
westcentralus  14.04.0-LTS
westcentralus  14.04.1-LTS
westcentralus  14.04.2-LTS
...
```

See [this page](https://docs.microsoft.com/en-us/azure/virtual-machines/linux/cli-ps-findimage) for the full documentation.

## Query filtering

Figuring out what you can do in a subscription often involves running a bunch of
`az XYZ list -o table` commands and poring through the results.  For example, you
may wish to look up how much quota you have for H-series VMs:

```
az vm list-usage --location "East US" -o table | grep 'Standard H'
```

But a better way to do this may be to filter the query as such:

```
az vm list-usage --location "East US" --query '[?contains(name.localizedValue, `Standard H`)]' -o table
```

This works because the `az vm list-usage` command returns a list of dicts of
the form

```json
[
  {
    "currentValue": "0",
    "limit": "8",
    "localName": "Standard H Family vCPUs",
    "name": {
      "localizedValue": "Standard H Family vCPUs",
      "value": "standardHFamily"
    }
  },
  ...
]
```

## Searching for capacity

Specialized VM types (like those used in HPC) are not available in all regions,
so requesting quota for them requires knowing which region to target. I haven't
figured out the API for this yet, but there is a website that lets you search
for service availability by region.  To search for NDv2 (8-way NVIDIA V100
instances), you can check out [this example](https://azure.microsoft.com/en-us/explore/global-infrastructure/products-by-region/?regions=&products=ndv2-series,virtual-machines).
