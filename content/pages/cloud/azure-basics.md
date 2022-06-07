---
title: Azure Basics
---

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
